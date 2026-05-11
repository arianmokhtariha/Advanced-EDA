import pandas as pd
from sqlalchemy import create_engine, text
from db_config import DB_CONFIG

def get_engine():
    """Returns a SQLAlchemy engine connected to the PostgreSQL database."""
    '''pandas → SQLAlchemy → psycopg2 → PostgreSQL'''
    try:
        cfg = DB_CONFIG
        url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"
        return create_engine(url)
    except Exception:
        print("❌ Database connection failed. Check your .env file.")
        return None

def run_query(query, params=None):
    """Executes a query and returns the results as a Pandas DataFrame."""
    engine = get_engine()
    if engine is None:
        return None
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)
