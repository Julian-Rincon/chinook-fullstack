import os
from psycopg import connect
from psycopg.rows import dict_row

def get_conn():
    conn = connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "chinook"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        conn.close()
