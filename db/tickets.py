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


def crear_tabla_reimpresiones():
    """Crea la tabla de historial de reimpresiones si no existe."""
    query = """
        CREATE TABLE IF NOT EXISTS tickets_reimpresiones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            impresion_id INT NOT NULL,
            transaction_id VARCHAR(100) NOT NULL,
            reimpreso_por VARCHAR(100) DEFAULT NULL,
            fecha_reimpresion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (impresion_id) REFERENCES tickets_impresos(id)
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


def obtener_impresion_por_id(impresion_id):
    """Retorna el registro de impresión por su id o None."""
    query = "SELECT * FROM tickets_impresos WHERE id = %s"
    return db.fetch_one(query, (impresion_id,))


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


def registrar_reimpresion(impresion_id, transaction_id, reimpreso_por=None):
    """
    Registra una reimpresión de tickets en MySQL.
    Retorna el id generado.
    """
    query = """
        INSERT INTO tickets_reimpresiones
        (impresion_id, transaction_id, reimpreso_por)
        VALUES (%s, %s, %s)
    """
    return db.execute_query(
        query,
        (impresion_id, transaction_id, reimpreso_por)
    )


def contar_impresiones(busqueda=None):
    """Retorna la cantidad total de impresiones registradas."""
    if busqueda:
        query = "SELECT COUNT(*) AS total FROM tickets_impresos WHERE transaction_id LIKE %s"
        params = (f"%{busqueda}%",)
    else:
        query = "SELECT COUNT(*) AS total FROM tickets_impresos"
        params = ()
    resultado = db.fetch_one(query, params)
    return resultado['total'] if resultado else 0


def listar_impresiones_paginada(pagina=1, por_pagina=20, busqueda=None):
    """
    Retorna una lista paginada de impresiones registradas.
    Ordenado por fecha_impresion descendente.
    """
    offset = (pagina - 1) * por_pagina
    if busqueda:
        query = """
            SELECT * FROM tickets_impresos
            WHERE transaction_id LIKE %s
            ORDER BY fecha_impresion DESC
            LIMIT %s OFFSET %s
        """
        params = (f"%{busqueda}%", por_pagina, offset)
    else:
        query = """
            SELECT * FROM tickets_impresos
            ORDER BY fecha_impresion DESC
            LIMIT %s OFFSET %s
        """
        params = (por_pagina, offset)
    return db.fetch_all(query, params)


def contar_reimpresiones(transaction_id):
    """Retorna la cantidad de reimpresiones de una transacción."""
    query = "SELECT COUNT(*) AS total FROM tickets_reimpresiones WHERE transaction_id = %s"
    resultado = db.fetch_one(query, (transaction_id,))
    return resultado['total'] if resultado else 0
