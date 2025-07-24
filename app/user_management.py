import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os

from password_util import hash_password, verify_password

load_dotenv()

def _get_db_env(var, default=None):
    value = os.getenv(var, default)
    if not value:
        raise RuntimeError(f"Missing required DB environment variable: {var}")
    return value

def _can_connect_to_db():
    """Check if DB host is reachable before initializing the pool."""
    import socket
    host = os.getenv('RDS_HOST')
    port = int(os.getenv('RDS_PORT', 5432))
    try:
        socket.gethostbyname(host)
        # Optionally, try to open a socket connection (uncomment if needed)
        # with socket.create_connection((host, port), timeout=2):
        #     pass
        return True
    except Exception:
        return False

connection_pool = None
if _can_connect_to_db():
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=int(os.getenv('DB_POOL_MIN', 1)),
        maxconn=int(os.getenv('DB_POOL_MAX', 5)),
        host=_get_db_env('RDS_HOST'),
        port=_get_db_env('RDS_PORT'),
        database=_get_db_env('RDS_DB'),
        user=_get_db_env('RDS_USER'),
        password=_get_db_env('RDS_PASSWORD')
    )
else:
    connection_pool = None  # Prevents OperationalError on import

def register_user(username: str, password: str, full_name: str, role: str = 'user'):
    if not connection_pool:
        # Optionally, log or print a clear error for debugging
        # print("Database connection pool is not initialized.")
        return False
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            hashed_password = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (%s, %s, %s, %s)",
                (username, hashed_password, full_name, role)
            )
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        return False
    except Exception:
        return False
    finally:
        if conn:
            connection_pool.putconn(conn)

def authenticate_user(username: str, password: str) -> dict:
    if not connection_pool:
        # Optionally, log or print a clear error for debugging
        # print("Database connection pool is not initialized.")
        return None
    conn = None
    try:
        conn = connection_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, password_hash, full_name, role FROM users "
                "WHERE username = %s",
                (username,))
            user = cur.fetchone()
            if user and verify_password(password, user[2]):
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'full_name': user[3],
                    'role': user[4]
                }
            return None
    except Exception:
        return None
    finally:
        if conn:
            connection_pool.putconn(conn)

__all__ = ["register_user", "authenticate_user"]