import re
from langchain_google_genai import ChatGoogleGenerativeAI
from services.rag_service import ask_rag
from services.mcp_mysql_service import (
    get_customer_by_id,
    search_customers,
    get_customer_summary,
    get_customer_branch_summary,
    get_route_by_id,
    get_route_by_cns,
    search_routes,
    get_route_summary,
    get_city_route_summary,
    get_customer_route_summary,
    get_top_cost_routes,
    get_top_distance_routes
)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0
)

def extract_number_after_words(message, words):
    for word in words:
        pattern = rf"{word}\s*[:#-]?\s*(\d+)"
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None

def extract_cns(message):
    match = re.search(r"\bCNS\d+\b", message, re.IGNORECASE)
    return match.group(0).upper() if match else None

def extract_vehicle_no(message):
    match = re.search(r"\b[A-Z]{2}\d{2}[A-Z]{2}\d{4}\b", message, re.IGNORECASE)
    return match.group(0).upper() if match else None

def extract_driver_id(message):
    match = re.search(r"\b(DRV|DVR|TCI|DR)\d{3}\b", message, re.IGNORECASE)
    return match.group(0).upper() if match else None

def extract_city_pair(message):
    text = message.lower()

    from_city = None
    to_city = None

    from_match = re.search(r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+)", text)
    if from_match:
        from_city = from_match.group(1).strip().title()
        to_city = from_match.group(2).strip().title()

    return from_city, to_city

def decide_route(message):
    text = message.lower()

    rag_keywords = [
        "policy", "sop", "rule", "rules", "process", "procedure",
        "guideline", "document", "pdf", "manual", "explain",
        "how to", "what is"
    ]

    mcp_keywords = [
        "customer", "route", "routes", "cns", "vehicle", "driver",
        "cost", "distance", "km", "city", "branch", "domain",
        "summary", "top", "highest", "lowest", "from", "to"
    ]

    has_rag = any(word in text for word in rag_keywords)
    has_mcp = any(word in text for word in mcp_keywords)

    if has_rag and has_mcp:
        return "both"

    if has_mcp:
        return "mcp"

    return "rag"

def run_mcp_tools(message):
    text = message.lower()

    cns_number = extract_cns(message)
    vehicle_no = extract_vehicle_no(message)
    driver_id = extract_driver_id(message)

    customer_id = extract_number_after_words(
        message,
        ["customer id", "customer", "cust id", "cust"]
    )

    route_id = extract_number_after_words(
        message,
        ["route id", "route"]
    )

    from_city, to_city = extract_city_pair(message)

    if cns_number:
        return {
            "tool": "get_route_by_cns",
            "data": get_route_by_cns(cns_number)
        }

    if "customer route summary" in text and customer_id:
        return {
            "tool": "get_customer_route_summary",
            "data": get_customer_route_summary(customer_id)
        }

    if customer_id and "route" in text:
        return {
            "tool": "get_customer_route_summary",
            "data": get_customer_route_summary(customer_id)
        }

    if customer_id:
        return {
            "tool": "get_customer_by_id",
            "data": get_customer_by_id(customer_id)
        }

    if route_id:
        return {
            "tool": "get_route_by_id",
            "data": get_route_by_id(route_id)
        }

    if "top cost" in text or "highest cost" in text or "costly" in text or "maximum cost" in text:
        return {
            "tool": "get_top_cost_routes",
            "data": get_top_cost_routes(10)
        }

    if "top distance" in text or "highest distance" in text or "maximum km" in text or "longest" in text:
        return {
            "tool": "get_top_distance_routes",
            "data": get_top_distance_routes(10)
        }

    if "city summary" in text or "city wise" in text or "city-wise" in text:
        return {
            "tool": "get_city_route_summary",
            "data": get_city_route_summary()
        }

    if "branch summary" in text or "branch wise" in text or "branch-wise" in text:
        return {
            "tool": "get_customer_branch_summary",
            "data": get_customer_branch_summary()
        }

    if "customer summary" in text or "total customers" in text:
        return {
            "tool": "get_customer_summary",
            "data": get_customer_summary()
        }

    if "route summary" in text or "total routes" in text or "route performance" in text:
        return {
            "tool": "get_route_summary",
            "data": get_route_summary()
        }

    if vehicle_no:
        return {
            "tool": "search_routes",
            "data": search_routes(vehicle_no=vehicle_no, limit=10)
        }

    if driver_id:
        return {
            "tool": "search_routes",
            "data": search_routes(driver_id=driver_id, limit=10)
        }

    if from_city or to_city:
        return {
            "tool": "search_routes",
            "data": search_routes(from_city=from_city, to_city=to_city, limit=10)
        }

    return {
        "tool": "get_route_summary",
        "data": get_route_summary()
    }

def generate_final_answer(message, rag_result=None, mcp_result=None):
    prompt = f"""
You are a logistics AI assistant.

User question:
{message}

RAG document result:
{rag_result}

MCP MySQL result:
{mcp_result}

Instructions:
1. Answer in simple professional English.
2. Use RAG result for policy, SOP, document, or process-related answers.
3. Use MCP MySQL result for customer, route, CNS, vehicle, driver, cost, distance, and live database answers.
4. Do not mention SQL query.
5. Do not say that you updated, inserted, deleted, or changed any database record.
6. If data is not available, clearly say data is not available.
7. Keep the answer concise and useful.
"""

    response = llm.invoke(prompt)
    return response.content

def ai_chat(message):
    route = decide_route(message)

    rag_result = None
    mcp_result = None

    if route == "rag":
        rag_result = ask_rag(message)

    elif route == "mcp":
        mcp_result = run_mcp_tools(message)

    else:
        rag_result = ask_rag(message)
        mcp_result = run_mcp_tools(message)

    answer = generate_final_answer(
        message=message,
        rag_result=rag_result,
        mcp_result=mcp_result
    )

    return {
        "route": route,
        "answer": answer,
        "rag_result": rag_result,
        "mcp_result": mcp_result
    }