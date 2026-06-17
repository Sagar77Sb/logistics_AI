from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from langchain_core.tools import tool

from services.mcp_mysql_service import (
    get_customer_by_id,
    search_customers_paginated,
    get_customer_summary,
    get_customer_branch_summary,
    get_route_by_id,
    get_route_by_cns,
    search_routes_paginated,
    get_route_summary,
    get_city_route_summary,
    get_customer_route_summary,
    get_top_cost_routes,
    get_top_distance_routes,
)
from services.rag_service import ask_rag

RAG_TOOL_NAME = "ask_documents"

MCP_TOOL_NAMES = {
    "search_customers_tool",
    "get_customer_by_id_tool",
    "get_customer_summary_tool",
    "get_customer_branch_summary_tool",
    "get_route_by_id_tool",
    "get_route_by_cns_tool",
    "search_routes_tool",
    "get_route_summary_tool",
    "get_city_route_summary_tool",
    "get_customer_route_summary_tool",
    "get_top_cost_routes_tool",
    "get_top_distance_routes_tool",
}


def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


@tool
def ask_documents(question: str) -> dict:
    """Search uploaded logistics PDFs for policies, SOPs, procedures, guidelines, and manuals.
    Use for document or process questions. Do NOT use for live customer, route, or database data."""
    return _serialize(ask_rag(question))


@tool
def search_customers_tool(
    customer_name: Optional[str] = None,
    branch: Optional[str] = None,
    domain: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """Search live customer records by name, main branch (cust_main_branch), or domain.
    Use page and limit for pagination when listing customers."""
    return _serialize(
        search_customers_paginated(
            customer_name=customer_name,
            branch=branch,
            domain=domain,
            page=page,
            limit=limit,
        )
    )


@tool
def get_customer_by_id_tool(customer_id: int) -> dict:
    """Get a single customer by numeric ID from the live database."""
    return _serialize(get_customer_by_id(customer_id))


@tool
def get_customer_summary_tool() -> dict:
    """Get overall customer statistics: total customers, branches, and domains."""
    return _serialize(get_customer_summary())


@tool
def get_customer_branch_summary_tool() -> list:
    """Get customer counts grouped by main branch."""
    return _serialize(get_customer_branch_summary())


@tool
def get_route_by_id_tool(route_id: int) -> dict:
    """Get a single route by numeric route ID."""
    return _serialize(get_route_by_id(route_id))


@tool
def get_route_by_cns_tool(cns_number: str) -> dict:
    """Get route details by CNS number such as CNS12345."""
    return _serialize(get_route_by_cns(cns_number))


@tool
def search_routes_tool(
    from_city: Optional[str] = None,
    to_city: Optional[str] = None,
    vehicle_no: Optional[str] = None,
    driver_id: Optional[str] = None,
    customer_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """Search live routes by from city, to city, vehicle number, driver ID, or customer ID.
    Use page and limit for pagination when listing routes."""
    return _serialize(
        search_routes_paginated(
            from_city=from_city,
            to_city=to_city,
            vehicle_no=vehicle_no,
            driver_id=driver_id,
            customer_id=customer_id,
            page=page,
            limit=limit,
        )
    )


@tool
def get_route_summary_tool() -> dict:
    """Get overall route statistics: totals, averages, vehicles, and drivers."""
    return _serialize(get_route_summary())


@tool
def get_city_route_summary_tool() -> list:
    """Get route statistics grouped by from_city and to_city."""
    return _serialize(get_city_route_summary())


@tool
def get_customer_route_summary_tool(customer_id: int) -> dict:
    """Get route performance summary for a specific customer ID."""
    return _serialize(get_customer_route_summary(customer_id))


@tool
def get_top_cost_routes_tool(limit: int = 10) -> list:
    """Get the highest cost routes."""
    return _serialize(get_top_cost_routes(limit))


@tool
def get_top_distance_routes_tool(limit: int = 10) -> list:
    """Get the longest distance routes."""
    return _serialize(get_top_distance_routes(limit))


ALL_TOOLS = [
    ask_documents,
    search_customers_tool,
    get_customer_by_id_tool,
    get_customer_summary_tool,
    get_customer_branch_summary_tool,
    get_route_by_id_tool,
    get_route_by_cns_tool,
    search_routes_tool,
    get_route_summary_tool,
    get_city_route_summary_tool,
    get_customer_route_summary_tool,
    get_top_cost_routes_tool,
    get_top_distance_routes_tool,
]
