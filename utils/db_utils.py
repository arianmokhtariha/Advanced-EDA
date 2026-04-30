import psycopg2
import pandas as pd
from db_config import DB_CONFIG

def get_connection():
    """Returns a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception:
        print("❌ Database connection failed. Check your .env file.")
        return None

def run_query(query, params=None):
    """Executes a query and returns the results as a Pandas DataFrame."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()
