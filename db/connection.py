import mysql.connector
from mysql.connector import pooling
from config.settings import Config

class Database:
    def __init__(self):
        self.pool = pooling.MySQLConnectionPool(
            pool_name='empleados_pool',
            pool_size=Config.DB_POOL_SIZE,
            pool_reset_session=True,
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4',
        )

    def execute_query(self, query, params=None):
        conn = self.pool.get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(query, params or ())
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self.pool.get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(query, params or ())
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def fetch_one(self, query, params=None):
        conn = self.pool.get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(query, params or ())
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

db = Database()
