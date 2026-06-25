import pyodbc
from config.settings import Config


def _detect_driver():
    """Selecciona el primer driver ODBC moderno de SQL Server disponible."""
    for driver in pyodbc.drivers():
        if 'ODBC Driver' in driver and 'SQL Server' in driver:
            return driver
    # Fallback a driver genérico si no hay uno moderno
    return '{SQL Server}'


def get_sqlserver_connection():
    """Crea y retorna una conexión a SQL Server usando pyodbc."""
    driver = _detect_driver()
    conn_str = (
        f'DRIVER={driver};'
        f'SERVER={Config.SQLSERVER_HOST},{Config.SQLSERVER_PORT};'
        f'DATABASE={Config.SQLSERVER_DB};'
        f'UID={Config.SQLSERVER_USER};'
        f'PWD={Config.SQLSERVER_PASSWORD};'
        'Timeout=10;'
    )
    return pyodbc.connect(conn_str)


def buscar_transaccion(transaction_id):
    """
    Busca una transacción en SQL Server por su TransactionId.
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
