import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

pool = MySQLConnectionPool(
    pool_name="logistics_pool",
    pool_size=5,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)

def get_connection():
    return pool.get_connection()

def run_select_query(query, params=None):
    lowered = query.strip().lower()

    forbidden = [
        "insert", "update", "delete", "drop", "alter",
        "truncate", "create", "replace", "grant", "revoke"
    ]

    if not lowered.startswith("select"):
        raise Exception("Only SELECT queries are allowed")

    for word in forbidden:
        if word in lowered:
            raise Exception("Write operations are not allowed")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()