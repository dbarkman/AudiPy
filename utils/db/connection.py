"""
Database connection utilities for AudiPy web interface
"""

import os
import mysql.connector
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'audipy'),
    'user': os.getenv('DB_USER', 'audipy'),
    'password': os.getenv('DB_PASSWORD'),
    'charset': 'utf8mb4',
    'autocommit': True
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False 