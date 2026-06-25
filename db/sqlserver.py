import pyodbc
from dbutils.pooled_db import PooledDB
from config.settings import Config


def _detect_driver():
    """Selecciona el primer driver ODBC moderno de SQL Server disponible."""
    for driver in pyodbc.drivers():
        if 'ODBC Driver' in driver and 'SQL Server' in driver:
            return driver
    # Fallback a driver generico si no hay uno moderno
    return '{SQL Server}'


_DRIVER = _detect_driver()


# Pool de conexiones persistentes a SQL Server.
# mincached: conexiones mantenidas calentadas desde el inicio.
# maxconnections: limite total de conexiones simultaneas.
_sqlserver_pool = PooledDB(
    creator=pyodbc.connect,
    mincached=2,
    maxcached=Config.SQLSERVER_POOL_SIZE,
    maxconnections=Config.SQLSERVER_POOL_SIZE,
    blocking=True,
    maxusage=None,
    DRIVER=_DRIVER,
    SERVER=f'{Config.SQLSERVER_HOST},{Config.SQLSERVER_PORT}',
    DATABASE=Config.SQLSERVER_DB,
    UID=Config.SQLSERVER_USER,
    PWD=Config.SQLSERVER_PASSWORD,
    Timeout=10,
)


def get_sqlserver_connection():
    """Obtiene una conexion del pool de SQL Server."""
    return _sqlserver_pool.connection()


def buscar_transaccion(transaction_id):
    """
    Busca una transaccion en SQL Server por su TransactionId.
    Retorna un dict {'transaction_id': str, 'total': float} o None si no existe.
    """
    query = """
        SELECT TOP 1 TransactionId, Total
        FROM TrxTransaction
        WHERE TransactionId = ?
    """
    conn = get_sqlserver_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (transaction_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'transaction_id': row.TransactionId,
            'total': float(row.Total) if row.Total is not None else 0.0,
        }
    finally:
        conn.close()
