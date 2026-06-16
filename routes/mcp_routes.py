from flask import Blueprint, request, jsonify
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

mcp_bp = Blueprint("mcp", __name__)

@mcp_bp.route("/customer/<int:customer_id>", methods=["GET"])
def customer_by_id(customer_id):
    return jsonify(get_customer_by_id(customer_id))

@mcp_bp.route("/customer/search", methods=["POST"])
def customer_search():
    data = request.get_json() or {}
    return jsonify(search_customers(
        customer_name=data.get("customer_name"),
        branch=data.get("branch"),
        domain=data.get("domain"),
        limit=data.get("limit", 10)
    ))

@mcp_bp.route("/customer/summary", methods=["GET"])
def customer_summary():
    return jsonify(get_customer_summary())

@mcp_bp.route("/customer/branch-summary", methods=["GET"])
def customer_branch_summary():
    return jsonify(get_customer_branch_summary())

@mcp_bp.route("/route/<int:route_id>", methods=["GET"])
def route_by_id(route_id):
    return jsonify(get_route_by_id(route_id))

@mcp_bp.route("/route/cns/<cns_number>", methods=["GET"])
def route_by_cns(cns_number):
    return jsonify(get_route_by_cns(cns_number))

@mcp_bp.route("/route/search", methods=["POST"])
def route_search():
    data = request.get_json() or {}
    return jsonify(search_routes(
        from_city=data.get("from_city"),
        to_city=data.get("to_city"),
        vehicle_no=data.get("vehicle_no"),
        driver_id=data.get("driver_id"),
        customer_id=data.get("customer_id"),
        limit=data.get("limit", 10)
    ))

@mcp_bp.route("/route/summary", methods=["GET"])
def route_summary():
    return jsonify(get_route_summary())

@mcp_bp.route("/route/city-summary", methods=["GET"])
def city_route_summary():
    return jsonify(get_city_route_summary())

@mcp_bp.route("/route/customer-summary/<int:customer_id>", methods=["GET"])
def customer_route_summary(customer_id):
    return jsonify(get_customer_route_summary(customer_id))

@mcp_bp.route("/route/top-cost", methods=["POST"])
def top_cost_routes():
    data = request.get_json() or {}
    return jsonify(get_top_cost_routes(data.get("limit", 10)))

@mcp_bp.route("/route/top-distance", methods=["POST"])
def top_distance_routes():
    data = request.get_json() or {}
    return jsonify(get_top_distance_routes(data.get("limit", 10)))