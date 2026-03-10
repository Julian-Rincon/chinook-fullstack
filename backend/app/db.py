import os
import psycopg
from psycopg.rows import dict_row


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_conn():
    conn = psycopg.connect(
        host=_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=_env("DB_NAME"),
        user=_env("DB_USER"),
        password=_env("DB_PASSWORD"),
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        conn.close()
