import logging
from databricks import sql as databricks_sql
from .config import DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_HTTP_PATH

logger = logging.getLogger(__name__)

_connection = None


def get_connection():
    global _connection
    if _connection is None:
        _connection = databricks_sql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
        )
    return _connection


def query_one(sql: str, params: list = None) -> dict | None:
    """Execute a query and return one row as a dict."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(columns, row))
    finally:
        cursor.close()


def query_all(sql: str, params: list = None) -> list[dict]:
    """Execute a query and return all rows as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()


def execute_write(sql: str, params: list = None) -> None:
    """Execute a write statement (INSERT/MERGE)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])
    finally:
        cursor.close()
