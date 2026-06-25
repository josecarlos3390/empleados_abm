from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, send_from_directory, session
from utils.security import login_required, admin_required
from db.empleados import (
    get_all_empleados, get_empleado_by_id, create_empleado, update_empleado,
    delete_empleado, listar_historial_empleado,
    listar_anexos, insertar_anexo, eliminar_anexo, get_anexo_by_id
)

from utils.excel_utils import empleados_to_excel
from datetime import datetime
import os, io

# 🔹 ADICIÓN: Importar secure_filename para nombres seguros de archivos subidos
from werkzeug.utils import secure_filename

# Importar listas desde constants.py
from config.constants import MOTIVOS_DESVINCULACION, EVALUACIONES_INTERNAS

# Definir el blueprint principal de empleados
empleados_bp = Blueprint('empleados', __name__, url_prefix='/')


# ===========================================================
# LISTA DE EMPLEADOS
# ===========================================================
@empleados_bp.route('/', endpoint='lista_empleados')
@login_required
def lista_empleados():
    """
    Vista: Listado de empleados
    - Permite búsqueda en todos los campos.
    - Evita errores de 'current_app' y 'os' no definidos en Jinja2.
    - Precalcula rutas de anexos en Python.
    """

    # Obtener parámetro de búsqueda
    query = request.args.get('q', '').lower().strip()

    # Obtener rol del usuario
    rol = session.get("user", {}).get("rol", "").lower()

    # Obtener todos los empleados
    empleados = sorted(get_all_empleados(), key=lambda e: e['id'])

    # =============================
    # 🔥 REGLA: si NO hay búsqueda
    # =============================
    if not query:
        # Solo admin ve la lista completa
        if rol != "admin":
            empleados = []   # Editor y viewer ven la tabla vacía

    # =============================
    # 🔥 REGLA: si HAY búsqueda
    # =============================
    else:
        empleados = [
            e for e in empleados
            if any(query in str(value).lower() for value in e.values())
        ]


    # Carpeta de carga
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    # Listar anexos por empleado
    for e in empleados:
        anexos = []
        try:
            for fn in os.listdir(upload_folder):
                if fn.startswith(f"{e['id']}_"):
                    anexos.append(fn)
        except FileNotFoundError:
            anexos = []

        e['anexos'] = anexos

    return render_template(
        'empleados/list.html',
        empleados=empleados,
        query=query,
        upload_folder=upload_folder
    )


# ===========================================================
# AGREGAR EMPLEADO + ANEXOS
# ===========================================================
@empleados_bp.route('/add', methods=['GET', 'POST'], endpoint='agregar_empleado')
@login_required
def agregar_empleado():
    if request.method == 'POST':

        # ----------------------------------
        # Convertir fechas
        # ----------------------------------
        fecha_ingreso = request.form.get('fecha_ingreso')
        fecha_salida = request.form.get('fecha_salida')

        try:
            fecha_ingreso = datetime.strptime(fecha_ingreso, "%d/%m/%Y").date() if fecha_ingreso else None
        except:
            fecha_ingreso = None

        try:
            fecha_salida = datetime.strptime(fecha_salida, "%d/%m/%Y").date() if fecha_salida else None
        except:
            fecha_salida = None

        # ----------------------------------
        # Construcción de datos del empleado
        # ----------------------------------
        data = {
            'empresa_sucursal': request.form.get('empresa_sucursal'),
            'nombre': request.form.get('nombre'),
            'apellido_paterno': request.form.get('apellido_paterno'),
            'apellido_materno': request.form.get('apellido_materno'),
            'carnet_identidad': request.form.get('carnet_identidad'),
            'cargo': request.form.get('cargo'),
            'fecha_ingreso': fecha_ingreso,
            'fecha_salida': fecha_salida,
            'motivo_desvinculacion': request.form.get('motivo_desvinculacion'),
            'evaluacion_interna': request.form.get('evaluacion_interna'),
            'observaciones': request.form.get('observaciones'),
            'usuario_creador': session.get('user', {}).get('username')
        }

        # ----------------------------------
        # Crear empleado y obtener ID
        # ----------------------------------
        empleado_id = create_empleado(data)

        # ==========================================
        # GUARDAR ANEXOS (ARCHIVOS)
        # ==========================================

        archivos = request.files.getlist("anexos")
        usuario_subida = session.get('user', {}).get('username')

        # Carpeta física --> /uploads/empleados/<id>/
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'empleados', str(empleado_id))
        os.makedirs(upload_dir, exist_ok=True)

        for archivo in archivos:
            if archivo and archivo.filename:

                nombre_original = secure_filename(archivo.filename)

                # Nombre único
                timestamp = int(datetime.now().timestamp())
                nombre_final = f"{empleado_id}_{timestamp}_{nombre_original}"

                destino = os.path.join(upload_dir, nombre_final)

                # Guardar físicamente
                archivo.save(destino)

                # Obtener tamaño real del archivo en disco
                tamano_real = os.path.getsize(destino)

                # Registrar en BD
                insertar_anexo(
                    empleado_id=empleado_id,
                    nombre_archivo=nombre_final,
                    tipo_archivo=archivo.mimetype,
                    tamano_archivo=tamano_real,
                    usuario_subida=usuario_subida
                )



        flash("Empleado agregado correctamente", "success")
        return redirect(url_for('empleados.lista_empleados'))

    # GET
    return render_template(
        'empleados/add.html',
        motivos=MOTIVOS_DESVINCULACION,
        evaluaciones=EVALUACIONES_INTERNAS
    )


# ===========================================================
# EDITAR EMPLEADO  (con historial)
# ===========================================================
@empleados_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='editar_empleado')
@login_required
def editar_empleado(id):
    # Buscar empleado por ID
    empleado = get_empleado_by_id(id)
    if not empleado:
        flash('Empleado no encontrado', 'danger')
        return redirect(url_for('empleados.lista_empleados'))

    # ============ GET ============
    if request.method == 'GET':
        return render_template(
            'empleados/edit.html',
            empleado=empleado,
            motivos=MOTIVOS_DESVINCULACION,
            evaluaciones=EVALUACIONES_INTERNAS
        )

    # ============ POST: ACTUALIZACIÓN ============

    # Convertir fechas desde dd/mm/yyyy
    fecha_ingreso = request.form.get('fecha_ingreso')
    fecha_salida = request.form.get('fecha_salida')

    try:
        fecha_ingreso = datetime.strptime(fecha_ingreso, "%d/%m/%Y").date() if fecha_ingreso else None
    except:
        fecha_ingreso = None

    try:
        fecha_salida = datetime.strptime(fecha_salida, "%d/%m/%Y").date() if fecha_salida else None
    except:
        fecha_salida = None

    # Construir diccionario de cambios
    data = {
        'empresa_sucursal': request.form.get('empresa_sucursal'),
        'nombre': request.form.get('nombre'),
        'apellido_paterno': request.form.get('apellido_paterno'),
        'apellido_materno': request.form.get('apellido_materno'),
        'carnet_identidad': request.form.get('carnet_identidad'),
        'cargo': request.form.get('cargo'),
        'fecha_ingreso': fecha_ingreso,
        'fecha_salida': fecha_salida,
        'motivo_desvinculacion': request.form.get('motivo_desvinculacion'),
        'evaluacion_interna': request.form.get('evaluacion_interna'),
        'observaciones': request.form.get('observaciones'),

        # 🔥 Muy importante: registrar quién modifica
        'usuario_modificador': session.get('user', {}).get('username'),
        'fecha_modificacion': datetime.now()
    }

    # Quitar valores None
    data = {k: v for k, v in data.items() if v is not None}

    # Registrar actualización + historial
    update_empleado(id, data, session["user"]["id"])

    flash('Empleado actualizado correctamente', 'success')
    return redirect(url_for('empleados.lista_empleados'))


# ===========================================================
# ELIMINAR EMPLEADO
# ===========================================================
@empleados_bp.route('/delete/<int:id>', endpoint='delete_employee')
@login_required
def eliminar_empleado(id):
    delete_empleado(id)
    flash('Empleado eliminado', 'info')
    return redirect(url_for('empleados.lista_empleados'))


# ===========================================================
# EXPORTAR A EXCEL (respetando filtro y orden)
# ===========================================================
@empleados_bp.route('/export', endpoint='export_excel')
@login_required
def export_excel():
    # Parámetros: q para filtro (igual que la búsqueda), order_by (columna) y order_dir (asc|desc)
    q = request.args.get('q', '').strip().lower()
    order_by = request.args.get('order_by', 'id')
    order_dir = request.args.get('order_dir', 'asc').lower()   # <-- debe ser asc, igual que la vista

    # Obtener todos (modelo existente) y aplicar filtro en Python igual que en lista_empleados
    empleados = get_all_empleados()

    if q:
        empleados = [
            e for e in empleados
            if any(q in (str(value) or '').lower() for value in e.values())
        ]

    # MAPA de columnas permitidas -> clave en dict empleado
    allowed_cols = {
        'id': 'id',
        'empresa': 'empresa_sucursal',
        'nombre': 'nombre',
        'apellido_paterno': 'apellido_paterno',
        'apellido_materno': 'apellido_materno',
        'ci': 'carnet_identidad',
        'cargo': 'cargo',
        'fecha_ingreso': 'fecha_ingreso',
        'fecha_salida': 'fecha_salida',
        'usuario_creador': 'usuario_creador'
        # añade más si necesitas permitir orden por otras columnas
    }

    key = allowed_cols.get(order_by, 'id')

    # Intentar ordenar por la clave; manejamos fechas y valores faltantes.
    def sort_key(e):
        v = e.get(key)
        # Si es fecha (datetime.date or datetime), devolver comparable
        try:
            if hasattr(v, 'year') and hasattr(v, 'month'):
                return v
        except Exception:
            pass
        # Normal fallback: cadena en minúsculas
        return (str(v) if v is not None else '').lower()

    reverse = (order_dir == 'desc')
    try:
        empleados = sorted(empleados, key=sort_key, reverse=reverse)
    except Exception:
        # en caso de que algo falle, mantener la lista sin ordenar
        pass

    # Generar excel
    data = empleados_to_excel(empleados)
    return send_file(
        io.BytesIO(data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='empleados.xlsx'
    )



# ===========================================================
# HISTORIAL DE CAMBIOS POR EMPLEADO
# ===========================================================
@empleados_bp.route('/empleado/<int:empleado_id>/historial', endpoint='historial_empleado')
@login_required
def historial_empleado(empleado_id):
    if session.get("user", {}).get("rol") != "admin":
        flash("No tienes permisos para ver el historial.", "danger")
        return redirect(url_for("empleados.lista_empleados"))

    empleado = get_empleado_by_id(empleado_id)
    if not empleado:
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for("empleados.lista_empleados"))

    historial = listar_historial_empleado(empleado_id)

    return render_template(
        'empleados/historial.html',
        empleado=empleado,
        historial=historial
    )


# ===========================================================
# DESCARGAR ANEXO (DB)
# ===========================================================
@empleados_bp.route('/empleados/anexo/<int:anexo_id>', endpoint='download_anexo')
@login_required
def download_anexo(anexo_id):
    anexo = get_anexo_by_id(anexo_id)
    if not anexo:
        flash("Archivo no encontrado en la base de datos.", "warning")
        return redirect(url_for('empleados.lista_empleados'))

    upload_folder_cfg = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    # 🔥 reconstruimos la ruta donde realmente está guardado
    file_path = os.path.join(
        current_app.root_path,
        upload_folder_cfg,
        'empleados',
        str(anexo["empleado_id"]),
        anexo["nombre_archivo"]
    )

    # verificar existencia real
    if not os.path.exists(file_path):
        flash("El archivo ya no existe en el servidor.", "warning")
        return redirect(url_for('empleados.ver_anexos', empleado_id=anexo["empleado_id"]))

    return send_file(file_path, as_attachment=True)


# ===========================================================
# VER ANEXOS (DB)
# ===========================================================
@empleados_bp.route('/empleados/<int:empleado_id>/anexos', endpoint='ver_anexos')
@login_required
def ver_anexos(empleado_id):
    empleado = get_empleado_by_id(empleado_id)
    if not empleado:
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for('empleados.lista_empleados'))

    anexos = listar_anexos(empleado_id)

    return render_template(
        'empleados/anexos.html',
        empleado=empleado,
        anexos=anexos
    )
# ===========================================================
# SUBIR ANEXOS (DB)
# ===========================================================
@empleados_bp.route('/empleados/<int:empleado_id>/anexos/upload', methods=['POST'])
@login_required
def upload_anexo(empleado_id):
    empleado = get_empleado_by_id(empleado_id)
    if not empleado:
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for('empleados.lista_empleados'))

    archivos = request.files.getlist('archivos')
    if not archivos:
        flash("No se seleccionaron archivos.", "warning")
        return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))

    upload_folder_cfg = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    upload_dir = os.path.join(current_app.root_path, upload_folder_cfg, 'empleados', str(empleado_id))
    os.makedirs(upload_dir, exist_ok=True)


    usuario = session.get("user", {}).get("username", "Sistema")

    guardados = 0
    for f in archivos:
        if f and f.filename:

            nombre_seguro = secure_filename(f.filename)

            # 🔥 Guardar archivo físicamente
            timestamp = int(datetime.now().timestamp())
            nombre_final = f"{empleado_id}_{timestamp}_{nombre_seguro}"
            destino = os.path.join(upload_dir, nombre_final)
            f.save(destino)

            # 🔥 Registrar en Base de Datos
            insertar_anexo(
                empleado_id=empleado_id,
                nombre_archivo=nombre_final,
                tipo_archivo=f.content_type,
                tamano_archivo=os.path.getsize(destino),
                usuario_subida=usuario
            )

            guardados += 1

    flash(f"{guardados} archivo(s) subido(s) correctamente.", "success")
    return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))


# ===========================================================
# ELIMINAR ANEXO (DB)
# ===========================================================
@empleados_bp.route('/empleados/anexo/delete/<int:anexo_id>/<int:empleado_id>', methods=['POST'])
@login_required
def delete_anexo(anexo_id, empleado_id):
    anexo = get_anexo_by_id(anexo_id)
    if not anexo:
        flash("El archivo no existe o ya fue eliminado.", "warning")
        return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))

    rol = session.get("user", {}).get("rol")
    if rol not in ['admin', 'editor']:
        flash("No tienes permisos para eliminar anexos.", "danger")
        return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))

    upload_folder_cfg = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    upload_dir = os.path.join(current_app.root_path, upload_folder_cfg)
    file_path = os.path.join(
        current_app.root_path,
        upload_folder_cfg,
        'empleados',
        str(empleado_id),
        anexo["nombre_archivo"]
    )

    # 🔥 Primero borramos archivo físico
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            flash("Error eliminando archivo físico.", "danger")
            return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))

    # 🔥 Luego lo eliminamos de la base
    eliminar_anexo(anexo_id)

    flash("Anexo eliminado correctamente.", "success")
    return redirect(url_for('empleados.ver_anexos', empleado_id=empleado_id))


# ===========================================================
# COMPATIBILIDAD CON ENDPOINTS ANTIGUOS
# ===========================================================
from flask import redirect

@empleados_bp.route('/old_anexos/<int:id>', endpoint='view_anexos_legacy')
def view_anexos_legacy(id):
    return redirect(url_for('empleados.ver_anexos', empleado_id=id))

@empleados_bp.route('/legacy/view_anexos/<int:id>')
def view_anexos_alias(id):
    return redirect(url_for('empleados.ver_anexos', empleado_id=id))
