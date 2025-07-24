import psycopg2
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'))

try:
    conn = psycopg2.connect(
        host=os.getenv("RDS_HOST"),
        port=os.getenv("RDS_PORT"),
        dbname=os.getenv("RDS_DB"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        sslmode='require'
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
