from db.connection import db
from datetime import datetime

# =============================
#  OBTENER EMPLEADOS
# =============================
def get_all_empleados():
    query = """
        SELECT 
            e.*,
            (SELECT COUNT(*) 
            FROM empleados_anexos a 
            WHERE a.empleado_id = e.id) AS total_anexos
        FROM empleados e
        ORDER BY e.id DESC
    """
    return db.fetch_all(query)


def get_empleado_by_id(eid):
    return db.fetch_one("SELECT * FROM empleados WHERE id = %s", (eid,))

# =============================
#  CREAR EMPLEADO
# =============================
def create_empleado(data):
    """
    Inserta un empleado y retorna el ID del empleado creado.
    """
    cols = ', '.join(data.keys())
    vals = tuple(data.values())
    placeholders = ', '.join(['%s'] * len(vals))

    query = f"""
        INSERT INTO empleados ({cols})
        VALUES ({placeholders})
    """

    # db.execute_query debe retornar el last_insert_id()
    return db.execute_query(query, vals)

# =============================
#  HISTORIAL DE CAMBIOS
# =============================
def registrar_cambio_historial(empleado_id, campo, valor_anterior, valor_nuevo, cambiado_por):
    query = """
        INSERT INTO empleados_historial
            (empleado_id, campo, valor_anterior, valor_nuevo, cambiado_por, fecha)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """
    db.execute_query(query, (
        empleado_id,
        campo,
        valor_anterior,
        valor_nuevo,
        cambiado_por
    ))

# =============================
#  ACTUALIZAR EMPLEADO
# =============================
def update_empleado(eid, data, user_id):

    empleado_actual = db.fetch_one("SELECT * FROM empleados WHERE id = %s", (eid,))
    if not empleado_actual:
        return None

    # Registrar solo cambios reales
    for campo, nuevo_valor in data.items():
        valor_anterior = empleado_actual.get(campo)
        if str(valor_anterior) != str(nuevo_valor):
            registrar_cambio_historial(
                empleado_id=eid,
                campo=campo,
                valor_anterior=valor_anterior,
                valor_nuevo=nuevo_valor,
                cambiado_por=user_id
            )

    # Actualizar empleado
    set_clause = ', '.join([f"{k}=%s" for k in data.keys()])
    vals = tuple(data.values()) + (eid,)

    query = f"UPDATE empleados SET {set_clause} WHERE id = %s"
    return db.execute_query(query, vals)

# =============================
#  ELIMINAR EMPLEADO
# =============================
def delete_empleado(eid):
    return db.execute_query("DELETE FROM empleados WHERE id = %s", (eid,))

# =============================
#  HISTORIAL EMPLEADO
# =============================
def listar_historial_empleado(eid):
    query = """
        SELECT 
            h.id,
            h.campo,
            h.valor_anterior,
            h.valor_nuevo,
            h.cambiado_por,
            h.fecha,
            DATE_FORMAT(h.fecha, '%d/%m/%Y %H:%i:%S') AS fecha_formateada,
            u.nombre AS usuario_nombre
        FROM empleados_historial h
        LEFT JOIN usuarios u ON h.cambiado_por = u.id
        WHERE h.empleado_id = %s
        ORDER BY h.fecha DESC
    """
    return db.fetch_all(query, (eid,))

# =============================
#  ANEXOS (LISTAR / INSERTAR / ELIMINAR)
# =============================

def listar_anexos(empleado_id):
    query = """
        SELECT 
            id,
            empleado_id,
            nombre_archivo,
            tipo_archivo,
            tamano_archivo,
            fecha_subida,
            usuario_subida,
            DATE_FORMAT(fecha_subida, '%d/%m/%Y %H:%i') AS fecha_formateada
        FROM empleados_anexos
        WHERE empleado_id = %s
        ORDER BY fecha_subida DESC
    """
    return db.fetch_all(query, (empleado_id,))


def insertar_anexo(empleado_id, nombre_archivo, tipo_archivo, tamano_archivo, usuario_subida):
    query = """
        INSERT INTO empleados_anexos 
            (empleado_id, nombre_archivo, tipo_archivo, tamano_archivo, fecha_subida, usuario_subida)
        VALUES (%s, %s, %s, %s, NOW(), %s)
    """
    return db.execute_query(query, (
        empleado_id,
        nombre_archivo,
        tipo_archivo,
        tamano_archivo,
        usuario_subida
    ))


def eliminar_anexo(anexo_id):
    return db.execute_query(
        "DELETE FROM empleados_anexos WHERE id = %s",
        (anexo_id,)
    )


def get_anexo_by_id(anexo_id):
    return db.fetch_one(
        "SELECT * FROM empleados_anexos WHERE id = %s",
        (anexo_id,)
    )
