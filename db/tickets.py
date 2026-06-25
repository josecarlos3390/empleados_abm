from db.connection import db


def crear_tabla_tickets():
    """Crea la tabla de control de tickets impresos si no existe."""
    query = """
        CREATE TABLE IF NOT EXISTS tickets_impresos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(100) NOT NULL,
            total_documento DECIMAL(18,2) NOT NULL,
            denominacion INT NOT NULL,
            cantidad_tickets INT NOT NULL,
            total_impreso DECIMAL(18,2) NOT NULL,
            cajero VARCHAR(100) DEFAULT NULL,
            fecha_impresion DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_transaction_id (transaction_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    db.execute_query(query)


def ya_fue_impresa(transaction_id):
    """Retorna True si la transacción ya tiene tickets impresos."""
    query = "SELECT id FROM tickets_impresos WHERE transaction_id = %s"
    return db.fetch_one(query, (transaction_id,)) is not None


def obtener_impresion(transaction_id):
    """Retorna el registro de impresión de una transacción o None."""
    query = "SELECT * FROM tickets_impresos WHERE transaction_id = %s"
    return db.fetch_one(query, (transaction_id,))


def registrar_impresion(transaction_id, total_documento, denominacion, cantidad_tickets, total_impreso, cajero=None):
    """
    Registra una impresión de tickets en MySQL.
    Retorna el id generado.
    """
    query = """
        INSERT INTO tickets_impresos
        (transaction_id, total_documento, denominacion, cantidad_tickets, total_impreso, cajero)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return db.execute_query(
        query,
        (transaction_id, total_documento, denominacion, cantidad_tickets, total_impreso, cajero)
    )
