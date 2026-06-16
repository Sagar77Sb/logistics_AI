from services.mysql_service import run_select_query

def get_customer_by_id(customer_id):
    query = """
        SELECT
            id,
            customer_name,
            cust_address,
            cust_contact,
            cust_email,
            cust_main_branch,
            cust_domain,
            created_at
        FROM customer_data
        WHERE id = %s
        LIMIT 1
    """
    rows = run_select_query(query, (customer_id,))
    return rows[0] if rows else {"message": "Customer not found"}

def search_customers(customer_name=None, branch=None, domain=None, limit=10):
    query = """
        SELECT
            id,
            customer_name,
            cust_address,
            cust_contact,
            cust_email,
            cust_main_branch,
            cust_domain,
            created_at
        FROM customer_data
        WHERE 1 = 1
    """
    params = []

    if customer_name:
        query += " AND customer_name LIKE %s"
        params.append(f"%{customer_name}%")

    if branch:
        query += " AND cust_main_branch LIKE %s"
        params.append(f"%{branch}%")

    if domain:
        query += " AND cust_domain LIKE %s"
        params.append(f"%{domain}%")

    query += " ORDER BY id DESC LIMIT %s"
    params.append(int(limit))

    return run_select_query(query, tuple(params))

def get_customer_summary():
    query = """
        SELECT
            COUNT(*) AS total_customers,
            COUNT(DISTINCT cust_main_branch) AS total_branches,
            COUNT(DISTINCT cust_domain) AS total_domains
        FROM customer_data
    """
    rows = run_select_query(query)
    return rows[0] if rows else {}

def get_customer_branch_summary():
    query = """
        SELECT
            cust_main_branch,
            COUNT(*) AS total_customers
        FROM customer_data
        GROUP BY cust_main_branch
        ORDER BY total_customers DESC
    """
    return run_select_query(query)

def get_route_by_id(route_id):
    query = """
        SELECT
            r.id,
            r.from_city,
            r.to_city,
            r.latitude,
            r.longitude,
            r.traveling_time,
            r.customer_id,
            c.customer_name,
            c.cust_main_branch,
            c.cust_domain,
            r.total_km,
            r.total_cost,
            r.vehicle_no,
            r.driver_id,
            r.cns_number
        FROM routes_data r
        LEFT JOIN customer_data c ON r.customer_id = c.id
        WHERE r.id = %s
        LIMIT 1
    """
    rows = run_select_query(query, (route_id,))
    return rows[0] if rows else {"message": "Route not found"}

def get_route_by_cns(cns_number):
    query = """
        SELECT
            r.id,
            r.from_city,
            r.to_city,
            r.latitude,
            r.longitude,
            r.traveling_time,
            r.customer_id,
            c.customer_name,
            c.cust_contact,
            c.cust_email,
            c.cust_main_branch,
            c.cust_domain,
            r.total_km,
            r.total_cost,
            r.vehicle_no,
            r.driver_id,
            r.cns_number
        FROM routes_data r
        LEFT JOIN customer_data c ON r.customer_id = c.id
        WHERE r.cns_number = %s
        LIMIT 1
    """
    rows = run_select_query(query, (cns_number,))
    return rows[0] if rows else {"message": "CNS number not found"}

def search_routes(from_city=None, to_city=None, vehicle_no=None, driver_id=None, customer_id=None, limit=10):
    query = """
        SELECT
            r.id,
            r.from_city,
            r.to_city,
            r.traveling_time,
            r.customer_id,
            c.customer_name,
            r.total_km,
            r.total_cost,
            r.vehicle_no,
            r.driver_id,
            r.cns_number
        FROM routes_data r
        LEFT JOIN customer_data c ON r.customer_id = c.id
        WHERE 1 = 1
    """
    params = []

    if from_city:
        query += " AND r.from_city LIKE %s"
        params.append(f"%{from_city}%")

    if to_city:
        query += " AND r.to_city LIKE %s"
        params.append(f"%{to_city}%")

    if vehicle_no:
        query += " AND r.vehicle_no = %s"
        params.append(vehicle_no)

    if driver_id:
        query += " AND r.driver_id = %s"
        params.append(driver_id)

    if customer_id:
        query += " AND r.customer_id = %s"
        params.append(customer_id)

    query += " ORDER BY r.id DESC LIMIT %s"
    params.append(int(limit))

    return run_select_query(query, tuple(params))

def get_route_summary():
    query = """
        SELECT
            COUNT(*) AS total_routes,
            SUM(total_km) AS total_km,
            SUM(total_cost) AS total_cost,
            AVG(total_km) AS average_km,
            AVG(total_cost) AS average_cost,
            COUNT(DISTINCT vehicle_no) AS total_vehicles,
            COUNT(DISTINCT driver_id) AS total_drivers,
            COUNT(DISTINCT customer_id) AS total_customers
        FROM routes_data
    """
    rows = run_select_query(query)
    return rows[0] if rows else {}

def get_city_route_summary():
    query = """
        SELECT
            from_city,
            to_city,
            COUNT(*) AS total_routes,
            SUM(total_km) AS total_km,
            SUM(total_cost) AS total_cost,
            AVG(total_cost) AS average_cost
        FROM routes_data
        GROUP BY from_city, to_city
        ORDER BY total_routes DESC
        LIMIT 20
    """
    return run_select_query(query)

def get_customer_route_summary(customer_id):
    query = """
        SELECT
            c.id AS customer_id,
            c.customer_name,
            c.cust_main_branch,
            c.cust_domain,
            COUNT(r.id) AS total_routes,
            SUM(r.total_km) AS total_km,
            SUM(r.total_cost) AS total_cost,
            AVG(r.total_cost) AS average_cost
        FROM customer_data c
        LEFT JOIN routes_data r ON c.id = r.customer_id
        WHERE c.id = %s
        GROUP BY c.id, c.customer_name, c.cust_main_branch, c.cust_domain
    """
    rows = run_select_query(query, (customer_id,))
    return rows[0] if rows else {"message": "Customer route summary not found"}

def get_top_cost_routes(limit=10):
    query = """
        SELECT
            r.id,
            r.from_city,
            r.to_city,
            r.customer_id,
            c.customer_name,
            r.total_km,
            r.total_cost,
            r.vehicle_no,
            r.driver_id,
            r.cns_number
        FROM routes_data r
        LEFT JOIN customer_data c ON r.customer_id = c.id
        ORDER BY r.total_cost DESC
        LIMIT %s
    """
    return run_select_query(query, (int(limit),))

def get_top_distance_routes(limit=10):
    query = """
        SELECT
            r.id,
            r.from_city,
            r.to_city,
            r.customer_id,
            c.customer_name,
            r.total_km,
            r.total_cost,
            r.vehicle_no,
            r.driver_id,
            r.cns_number
        FROM routes_data r
        LEFT JOIN customer_data c ON r.customer_id = c.id
        ORDER BY r.total_km DESC
        LIMIT %s
    """
    return run_select_query(query, (int(limit),))