# app/db_schemas.py
from app.database import get_db_connection  # Corrected import

def create_cve_table():
    conn = get_db_connection()
    if conn:
        cur = None  # Initialize cur
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cves (
                    cve_id VARCHAR(255) PRIMARY KEY,
                    published TIMESTAMP WITH TIME ZONE,
                    last_modified TIMESTAMP WITH TIME ZONE,
                    description TEXT,
                    base_score_v3 NUMERIC,
                    base_score_v2 NUMERIC,
                    raw_data JSONB
                );
            """)
            conn.commit()
            print("CVE table created (or already exists).")
        except Exception as e:
            print(f"Error creating table: {e}")
            conn.rollback()
        finally:
            if cur:
                cur.close()
            conn.close()


if __name__ == "__main__":
    create_cve_table()