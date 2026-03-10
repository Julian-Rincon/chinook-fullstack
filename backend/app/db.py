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


def init_app_tables():
    if os.getenv("SKIP_DB_INIT") == "1":
        return

    conn = psycopg.connect(
        host=_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=_env("DB_NAME"),
        user=_env("DB_USER"),
        password=_env("DB_PASSWORD"),
        row_factory=dict_row,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_user (
                    user_id SERIAL PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        conn.commit()
    finally:
        conn.close()
