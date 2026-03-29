"""Databricks SQL Connector wrapper for reading/writing Delta tables."""

import os
import logging
from typing import Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DatabricksClient:
    """Wraps databricks-sql-connector for reading/writing Delta Lake tables."""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST", "")
        self.token = os.getenv("DATABRICKS_TOKEN", "")
        self.http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        self._connection = None

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.token and self.http_path)

    def _get_connection(self):
        if not self.is_configured:
            logger.warning("Databricks not configured — using mock data")
            return None

        if self._connection is None:
            try:
                from databricks import sql
                self._connection = sql.connect(
                    server_hostname=self.host,
                    http_path=self.http_path,
                    access_token=self.token,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Databricks: {e}")
                return None
        return self._connection

    def query(self, sql_query: str) -> list[dict[str, Any]]:
        conn = self._get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def execute(self, sql_statement: str):
        conn = self._get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(sql_statement)
            cursor.close()
        except Exception as e:
            logger.error(f"Execute failed: {e}")

    def get_farmer_profile(self, farmer_id: str) -> dict | None:
        rows = self.query(
            f"SELECT * FROM krishirin.loan_advisory.silver_farmer_profile WHERE farmer_id = '{farmer_id}'"
        )
        return rows[0] if rows else None

    def get_scored_profile(self, farmer_id: str) -> dict | None:
        rows = self.query(
            f"SELECT * FROM krishirin.loan_advisory.scored_profiles WHERE farmer_id = '{farmer_id}'"
        )
        return rows[0] if rows else None

    def get_loan_strategy(self, farmer_id: str) -> dict | None:
        rows = self.query(
            f"SELECT * FROM krishirin.loan_advisory.loan_strategies WHERE farmer_id = '{farmer_id}'"
        )
        return rows[0] if rows else None

    def get_agri_advisory(self, farmer_id: str) -> dict | None:
        rows = self.query(
            f"SELECT * FROM krishirin.loan_advisory.agri_advisory_plans WHERE farmer_id = '{farmer_id}'"
        )
        return rows[0] if rows else None

    def log_conversation_turn(
        self, farmer_id: str, turn_number: int, speaker: str, text: str, call_type: str
    ):
        """Fire-and-forget conversation logging to Delta."""
        self.execute(
            f"""INSERT INTO krishirin.loan_advisory.conversation_log
            (farmer_id, turn_number, speaker, text_content, call_type, timestamp)
            VALUES ('{farmer_id}', {turn_number}, '{speaker}', '{text.replace("'", "''")}', '{call_type}', current_timestamp())"""
        )

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


# Singleton instance
db = DatabricksClient()
