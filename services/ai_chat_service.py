import json
import inspect

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from services.agent_graph import get_agent
from services.agent_tools import MCP_TOOL_NAMES, RAG_TOOL_NAME
from services.mcp_mysql_service import search_customers_paginated, search_routes_paginated
from services.response_utils import error_response, success_response

MAX_AGENT_STEPS = 8
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

PAGINATED_DB_TOOLS = {
    "search_customers_tool": search_customers_paginated,
    "search_routes_tool": search_routes_paginated,
}


def _normalize_pagination(page=None, limit=None):
    page = int(page or DEFAULT_PAGE)
    limit = int(limit or DEFAULT_LIMIT)

    if page < 1:
        raise ValueError("page must be greater than or equal to 1")

    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    return page, limit


def _build_agent_message(message, page, limit):
    return (
        f"{message}\n\n"
        f"[Pagination context: when using list/search database tools, "
        f"you must use page={page} and limit={limit}.]"
    )


def _safe_parse_tool_content(content):
    if isinstance(content, (dict, list)):
        return content
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content


def _extract_tool_trace(messages):
    tool_call_map = {}

    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_call_map[tool_call["id"]] = {
                    "name": tool_call.get("name"),
                    "args": tool_call.get("args"),
                }

    tool_results = []
    tools_used = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        call_meta = tool_call_map.get(message.tool_call_id, {})
        tool_name = call_meta.get("name")
        tool_args = call_meta.get("args")

        if tool_name:
            tools_used.append(tool_name)

        tool_results.append(
            {
                "tool": tool_name,
                "args": tool_args,
                "data": _safe_parse_tool_content(message.content),
            }
        )

    return tool_results, tools_used


def _extract_final_answer(messages):
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content and not message.tool_calls:
            if isinstance(message.content, str):
                return message.content
            if isinstance(message.content, list):
                text_parts = [
                    part.get("text", "")
                    for part in message.content
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                return "".join(text_parts).strip()
    return "I could not generate an answer for this request."


def _normalize_database_result(tool_name, tool_args, data):
    if isinstance(data, dict) and "records" in data and "pagination" in data:
        return {
            "tool": tool_name,
            "filters": data.get("filters") or tool_args or {},
            "records": data.get("records", []),
            "pagination": data.get("pagination"),
            "row_count": data.get("pagination", {}).get("total", len(data.get("records", []))),
        }

    if isinstance(data, list):
        return {
            "tool": tool_name,
            "filters": tool_args or {},
            "records": data,
            "pagination": None,
            "row_count": len(data),
        }

    if isinstance(data, dict) and data:
        return {
            "tool": tool_name,
            "filters": tool_args or {},
            "record": data,
            "row_count": 1,
        }

    return {
        "tool": tool_name,
        "filters": tool_args or {},
        "records": [],
        "row_count": 0,
    }


def _refresh_paginated_database(tool_results, page, limit):
    for result in reversed(tool_results):
        tool_name = result.get("tool")
        search_fn = PAGINATED_DB_TOOLS.get(tool_name)
        if not search_fn:
            continue

        args = result.get("args") or {}
        valid_keys = set(inspect.signature(search_fn).parameters.keys())
        filtered_args = {
            key: value
            for key, value in args.items()
            if key in valid_keys and key not in {"page", "limit"}
        }
        refreshed = search_fn(**filtered_args, page=page, limit=limit)
        return _normalize_database_result(tool_name, args, refreshed)

    return None


def _build_list_answer(database, entity_label):
    pagination = database.get("pagination") or {}
    records = database.get("records") or []
    total = pagination.get("total", database.get("row_count", len(records)))
    page = pagination.get("page", 1)
    total_pages = pagination.get("total_pages", 1)

    answer = (
        f"Found {total} {entity_label}. "
        f"Showing page {page} of {total_pages} ({len(records)} record(s) on this page)."
    )

    if pagination.get("has_next"):
        next_page = pagination.get("next_page", page + 1)
        answer += (
            f" Send the same request with \"page\": {next_page} "
            f"to view the next page."
        )

    return answer


def _build_answer(route, rag_result, database, llm_answer):
    if route == "both" and isinstance(database, dict) and database.get("records"):
        db_answer = _build_list_answer(database, "matching record(s)")
        rag_answer = (rag_result or {}).get("answer")
        if rag_answer:
            return f"{db_answer}\n\nDocument summary:\n{rag_answer}"
        return db_answer

    if route == "database" and isinstance(database, dict) and database.get("records"):
        entity = "customer(s)"
        if database.get("tool") == "search_routes_tool":
            entity = "route(s)"
        return _build_list_answer(database, entity)

    if route == "rag" and isinstance(rag_result, dict):
        return rag_result.get("answer") or llm_answer

    if route == "database" and isinstance(database, dict) and database.get("record"):
        record = database["record"]
        if isinstance(record, dict) and record.get("customer_name"):
            return (
                f"Customer {record['customer_name']} (ID: {record.get('id')}) "
                f"from branch {record.get('cust_main_branch')}."
            )
        return llm_answer

    return llm_answer


def _build_source_results(tool_results, page, limit):
    rag_result = None
    database = _refresh_paginated_database(tool_results, page, limit)
    database_results = []

    if not database:
        for result in tool_results:
            tool_name = result.get("tool")
            tool_args = result.get("args") or {}
            data = result.get("data")

            if tool_name == RAG_TOOL_NAME:
                rag_result = data
            elif tool_name in MCP_TOOL_NAMES:
                database_results.append(
                    _normalize_database_result(tool_name, tool_args, data)
                )

        if len(database_results) == 1:
            database = database_results[0]
        elif len(database_results) > 1:
            database = database_results
    else:
        for result in tool_results:
            if result.get("tool") == RAG_TOOL_NAME:
                rag_result = result.get("data")
                break

    route = "agent"
    if rag_result and database:
        route = "both"
    elif rag_result:
        route = "rag"
    elif database:
        route = "database"

    return route, rag_result, database


def _build_success_message(route, database):
    if route == "both":
        return "Request completed successfully using documents and database data."
    if route == "database":
        total = 0
        if isinstance(database, dict):
            total = database.get("row_count", 0)
        return f"Request completed successfully. Found {total} matching database record(s)."
    if route == "rag":
        return "Request completed successfully using uploaded documents."
    return "Request completed successfully."


def _build_client_data(answer, route, rag_result, database):
    data = {"answer": answer}

    if isinstance(database, dict):
        if database.get("records") is not None:
            data["records"] = database["records"]
        elif database.get("record"):
            data["record"] = database["record"]

    if rag_result and route in ("rag", "both"):
        sources = rag_result.get("sources")
        if sources:
            data["sources"] = sources

    return data


def _build_client_meta(database, debug=False, tool_results=None):
    meta = {}

    if isinstance(database, dict) and database.get("pagination"):
        meta["pagination"] = database["pagination"]

    if debug and tool_results is not None:
        meta["tool_results"] = tool_results

    return meta


def ai_chat(message, page=DEFAULT_PAGE, limit=DEFAULT_LIMIT, debug=False):
    try:
        page, limit = _normalize_pagination(page, limit)
    except ValueError as exc:
        return error_response(
            message="Invalid pagination parameters.",
            code="VALIDATION_ERROR",
            details=str(exc),
            status_code=400,
        )

    agent = get_agent()
    agent_message = _build_agent_message(message, page, limit)

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=agent_message)]},
            config={"recursion_limit": MAX_AGENT_STEPS},
        )
    except Exception as exc:
        return error_response(
            message="AI service failed to process the request.",
            code="AGENT_ERROR",
            details=str(exc),
            status_code=500,
        )

    messages = result.get("messages", [])
    tool_results, _tools_used = _extract_tool_trace(messages)
    route, rag_result, database = _build_source_results(tool_results, page, limit)
    llm_answer = _extract_final_answer(messages)
    answer = _build_answer(route, rag_result, database, llm_answer)

    data = _build_client_data(answer, route, rag_result, database)
    meta = _build_client_meta(database, debug=debug, tool_results=tool_results)

    return success_response(
        message=_build_success_message(route, database),
        data=data,
        meta=meta,
        status_code=200,
    )
