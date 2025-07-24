import os
import bcrypt
import boto3
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# Database connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=int(os.getenv('DB_POOL_MIN', 1)),
    maxconn=int(os.getenv('DB_POOL_MAX', 5)),
    host=os.getenv('RDS_HOST'),
    port=os.getenv('RDS_PORT'),
    database=os.getenv('RDS_DB'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD')
)

# AWS Rekognition client
rekognition = boto3.client('rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1'
)

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_face(image_bytes):
    try:
        response = rekognition.search_faces_by_image(
            CollectionId=os.getenv('REKOGNITION_COLLECTION'),
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=90
        )
        if response['FaceMatches']:
            return response['FaceMatches'][0]['Face']['ExternalImageId']
    except rekognition.exceptions.InvalidParameterException:
        return None
    return None

def get_user_by_face(face_id):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE face_id = %s", (face_id,))
            return cur.fetchone()
    finally:
        connection_pool.putconn(conn)

def get_user_by_username(username):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        connection_pool.putconn(conn)

def face_login(image_bytes) -> str | None:
    """
    Perform face login using AWS Rekognition.
    Returns the username if face is recognized, else None.
    """
    face_id = authenticate_face(image_bytes)
    if not face_id:
        return None
    user = get_user_by_face(face_id)
    if user:
        # Assuming username is at index 1 in the users table
        return user[1]
    return None