# app/database.py
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    print(f"DEBUG: DATABASE_URL from environment: {database_url}")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        return None

    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print("DEBUG: Database connection successful (pre-cursor)")  # Keep this for now
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None