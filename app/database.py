import json
import sqlite3
from datetime import datetime, timezone

from app import config


def init_db():
    """Create the requests table if it does not exist."""
    connection = sqlite3.connect(config.DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_ip TEXT,
            user_agent TEXT,
            target_index TEXT,
            status_code INTEGER,
            query TEXT
        )
        """
    )
    connection.commit()
    connection.close()


def save_request(source_ip, user_agent, target_index, status_code, query):
    """Store one request in the log."""
    # Keep the query only if LOG_QUERY is on
    if config.LOG_QUERY:
        query_text = json.dumps(query)
    else:
        query_text = None

    created_at = datetime.now(timezone.utc).isoformat()

    connection = sqlite3.connect(config.DB_PATH)
    connection.execute(
        """
        INSERT INTO requests (created_at, source_ip, user_agent, target_index, status_code, query)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (created_at, source_ip, user_agent, target_index, status_code, query_text),
    )
    connection.commit()
    connection.close()
