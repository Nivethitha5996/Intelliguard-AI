# database.py
import psycopg2
from psycopg2 import pool, sql, extras
import os
import logging
import time
from contextlib import contextmanager
import atexit
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceDB:
    _connection_pool = None
    _initialized = False

    @classmethod
    def initialize_pool(cls, max_retries=3):
        """Initialize connection pool with retry logic and clear error reporting"""
        if cls._initialized and cls._connection_pool:
            return True

        load_dotenv()  # Ensure environment variables are loaded
        
        db_config = {
            'host': os.getenv('RDS_HOST'),
            'port': os.getenv('RDS_PORT', '5432'),
            'dbname': os.getenv('RDS_DB'),
            'user': os.getenv('RDS_USER'),
            'password': os.getenv('RDS_PASSWORD'),
            'minconn': int(os.getenv('DB_POOL_MIN', 1)),
            'maxconn': int(os.getenv('DB_POOL_MAX', 5))
        }

        # Check for missing config and log error
        missing = [k for k, v in db_config.items() if not v and k not in ('minconn', 'maxconn')]
        if missing:
            logger.error(f"Missing DB config values: {missing}")
            raise RuntimeError(f"Missing DB config values: {missing}")

        retry_count = 0
        while retry_count < max_retries:
            try:
                # Close existing pool if exists
                if cls._connection_pool:
                    cls._connection_pool.closeall()

                cls._connection_pool = pool.SimpleConnectionPool(
                    minconn=db_config['minconn'],
                    maxconn=db_config['maxconn'],
                    host=db_config['host'],
                    port=db_config['port'],
                    dbname=db_config['dbname'],
                    user=db_config['user'],
                    password=db_config['password'],
                    connect_timeout=5
                )
                
                # Test the connection
                conn = cls._connection_pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                finally:
                    cls._connection_pool.putconn(conn)
                
                cls._initialized = True
                logger.info("Database connection pool initialized successfully")
                return True

            except Exception as e:
                retry_count += 1
                logger.error(f"Connection attempt {retry_count} failed: {str(e)}")
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Failed to initialize connection pool.")
                    cls._connection_pool = None
                    # Print detailed config for debugging
                    logger.error(f"DB config used: {db_config}")
                    raise RuntimeError(f"Could not initialize database connection pool: {e}")
                time.sleep(2 ** retry_count)  # Exponential backoff

    def __init__(self):
        if not ComplianceDB.initialize_pool():
            raise RuntimeError("Could not initialize database connection pool")
        if self._connection_pool is None:
            raise RuntimeError("Database connection pool is not available. Check DB credentials and connectivity.")
        # self.ensure_tables_exist()  # <-- Remove or comment out this line

    @contextmanager
    def _managed_cursor(self):
        """Properly managed cursor with connection handling"""
        if self._connection_pool is None:
            raise RuntimeError("Database connection pool is not initialized. Cannot get a connection.")
        conn = None
        try:
            conn = self._connection_pool.getconn()
            if conn.closed:
                # Reconnect if the connection is closed
                conn = psycopg2.connect(
                    host=os.getenv('RDS_HOST'),
                    port=os.getenv('RDS_PORT', '5432'),
                    dbname=os.getenv('RDS_DB'),
                    user=os.getenv('RDS_USER'),
                    password=os.getenv('RDS_PASSWORD'),
                    connect_timeout=5
                )
            with conn.cursor() as cur:
                yield cur
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    if not conn.closed and self._connection_pool is not None:
                        self._connection_pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection: {str(e)}")
                    if conn and not conn.closed:
                        conn.close()

    def create_new_user(self, username, password, email):
        try:
            with self._managed_cursor() as cur:
                # Check if email already exists
                cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return False, "Email already exists"
                cur.execute("""
                    INSERT INTO users (
                        email, username, password_hash
                    ) VALUES (
                        %s, %s, %s
                    )
                """, (email, username, password))
                cur.connection.commit()
            return True, "User created successfully"
        except Exception as e:
            return False, f"DB error: {str(e)}"

    def check_username_exists(self, username):
        """Check if username exists in database"""
        try:
            with self._managed_cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking username: {str(e)}")
            return False

    def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate user using email and plain text password comparison"""
        try:
            with self._managed_cursor() as cur:
                cur.execute("""
                    SELECT password_hash 
                    FROM users 
                    WHERE email = %s
                """, (email,))
                result = cur.fetchone()
                if not result:
                    return False
                stored_password = result[0]
                return password == stored_password
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def get_compliance_stats(self):
        """Return compliance statistics for dashboard."""
        try:
            with self._managed_cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_checks,
                        COALESCE(SUM(CASE WHEN violations_count = 0 THEN 1 ELSE 0 END), 0) as compliant,
                        COALESCE(SUM(CASE WHEN violations_count > 0 THEN 1 ELSE 0 END), 0) as violations,
                        COALESCE(SUM(CASE WHEN anomaly_status = 'warning' THEN 1 ELSE 0 END), 0) as warnings,
                        COALESCE(SUM(CASE WHEN anomaly_status = 'critical' THEN 1 ELSE 0 END), 0) as critical
                    FROM compliance_logs
                """)
                result = cur.fetchone()
                return {
                    'total_checks': result[0] if result else 0,
                    'compliant': result[1] if result else 0,
                    'violations': result[2] if result else 0,
                    'warnings': result[3] if result else 0,
                    'critical': result[4] if result else 0
                }
        except Exception as e:
            logger.error(f"Error getting compliance stats: {e}")
            return {
                'total_checks': 0,
                'compliant': 0,
                'violations': 0,
                'warnings': 0,
                'critical': 0
            }

    def log_violation(self, violation_data):
        """
        Log a PPE violation or a list of violations to the compliance_logs and violation_details tables.
        violation_data: dict with keys:
            - violations: list of dicts (each with at least 'violation_type', 'confidence', 'bbox')
            - image_path: str
            - location: str
            - camera_id: str
            - employee_id: str or None
        """
        try:
            with self._managed_cursor() as cur:
                # Insert into compliance_logs
                cur.execute("""
                    INSERT INTO compliance_logs (
                        timestamp, violations_count, anomaly_status, processed, details
                    ) VALUES (
                        NOW(), %s, %s, %s, %s
                    ) RETURNING log_id
                """, (
                    len(violation_data.get('violations', [])),
                    'critical' if len(violation_data.get('violations', [])) > 0 else 'normal',
                    True,
                    extras.Json({
                        "location": violation_data.get("location"),
                        "camera_id": violation_data.get("camera_id"),
                        "employee_id": violation_data.get("employee_id"),
                        "image_path": violation_data.get("image_path")
                    })
                ))
                log_id = cur.fetchone()[0]

                # Insert each violation into violation_details
                for v in violation_data.get('violations', []):
                    bbox = v.get("bbox")
                    if bbox is None:
                        bbox = (0, 0, 0, 0)
                    # Ensure bbox is stored as JSON for jsonb column
                    bbox_json = extras.Json({
                        "x1": bbox[0],
                        "y1": bbox[1],
                        "x2": bbox[2],
                        "y2": bbox[3]
                    }) if bbox else extras.Json({"x1": 0, "y1": 0, "x2": 0, "y2": 0})
                    cur.execute("""
                        INSERT INTO violation_details (
                            log_id, violation_type, confidence, bounding_box
                        ) VALUES (
                            %s, %s, %s, %s
                        )
                    """, (
                        log_id,
                        v.get("violation_type"),
                        v.get("confidence"),
                        bbox_json
                    ))
        except Exception as e:
            logger.error(f"Error logging violation: {e}")
            raise


# Cleanup on exit
@atexit.register
def cleanup_db_connections():
    """Clean up database connections when application exits"""
    if ComplianceDB._connection_pool:
        try:
            ComplianceDB._connection_pool.closeall()
            logger.info("Closed all database connections on exit")
        except Exception as e:
            logger.error(f"Error closing connection pool: {str(e)}")