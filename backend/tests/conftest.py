import os

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "chinook")
os.environ.setdefault("DB_USER", "chinook")
os.environ.setdefault("DB_PASSWORD", "chinook")
os.environ.setdefault("SKIP_DB_INIT", "1")
