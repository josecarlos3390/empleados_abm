# empleados_routes.py (actualizado)
# -----------------------------------------------------------------------------
# ESTE ARCHIVO ESTÁ COMPLETO Y ACTUALIZADO CON:
# ✔ Subida con registro de usuario
# ✔ Eliminación de anexos
# ✔ Opción A (todos los archivos en /uploads con prefijo del empleado)
# ✔ Metadata derivada del nombre del archivo
# -----------------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, send_from_directory, session
from utils.security import login_required, admin_required
from db.empleados import get_all_empleados, get_empleado_by_id, create_empleado, update_empleado, delete_empleado, listar_historial_empleado
from utils.excel_utils import empleados_to_excel
from datetime import datetime
import os, io

from werkzeug.utils import secure_filename
from config.constants import MOTIVOS_DESVINCULACION, EVALUACIONES_INTERNAS

empleados_bp = Blueprint('empleados', __name__, url_prefix='/')

# =============================================================================
# LISTA DE EMPLEADOS
# =============================================================================
@empleados_bp.route('/', endpoint='lista_empleados')
@login_required
def lista_empleados():
    query = request.args.get('q', '').lower().strip()
    empleados = sorted(get_all_empleados(), key=lambda x: x['id'])

    if query:
        empleados = [e for e in empleados if any(query in str(v).lower() for v in e.values())]

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    for e in empleados:
        anexos = []
        try:
            for fn in os.listdir(upload_folder):
                if fn.startswith(f"{e['id']}_"):
                    anexos.append(fn)
        except FileNotFoundError:
            anexos = []
        e['anexos'] = anexos

    return render_template('empleados/list.html', empleados=empleados, query=query, upload_folder=upload_folder)


# =============================================================================
# AGREGAR EMPLEADO
# =============================================================================
@empleados_bp.route('/add', methods=['GET', 'POST'], endpoint='agregar_empleado')
@login_required
def agregar_empleado():
    if request.method == 'POST':
        fecha_ingreso = request.form.get('fecha_ingreso')
        fecha_salida = request.form.get('fecha_salida')

        try:
            fecha_ingreso = datetime.strptime(fecha_ingreso, "%d/%m/%Y").date() if fecha_ingreso else None
        except: fecha_ingreso = None
        try:
            fecha_salida = datetime.strptime(fecha_salida, "%d/%m/%Y").date() if fecha_salida else None
        except: fecha_salida = None

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

        empleado_id = create_empleado(data)

        # --- Guardar anexos
        try:
            upload_folder_cfg = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            upload_dir = os.path.join(current_app.root_path, upload_folder_cfg)
            os.makedirs(upload_dir, exist_ok=True)

            archivos = request.files.getlist('anexos')
            usuario = session.get("user", {}).get("username", "Sistema")

            for f in archivos:
                if f and f.filename:
                    nombre_seguro = secure_filename(f.filename)
                    nombre_final = f"{empleado_id}__{usuario}__{nombre_seguro}"
                    f.save(os.path.join(upload_dir, nombre_final))

        except Exception:
            flash("Empleado creado, pero hubo un error guardando anexos.", "warning")

        flash('Empleado agregado correctamente', 'success')
        return redirect(url_for('empleados.lista_empleados'))

    return render_template('empleados/add.html', motivos=MOTIVOS_DESVINCULACION, evaluaciones=EVALUACIONES_INTERNAS)


# =============================================================================
# EDITAR EMPLEADO
# =============================================================================
@empleados_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='editar_empleado')
@login_required
def editar_empleado(id):
    empleado = get_empleado_by_id(id)
    if not empleado:
        flash("Empleado no encontrado", "danger")
        return redirect(url_for('empleados.lista_empleados'))

    if request.method == 'GET':
        return render_template('empleados/edit.html', empleado=empleado, motivos=MOTIVOS_DESVINCULACION, evaluaciones=EVALUACIONES_INTERNAS)

    fecha_ingreso = request.form.get('fecha_ingreso')
    fecha_salida = request.form.get('fecha_salida')

    try: fecha_ingreso = datetime.strptime(fecha_ingreso, "%d/%m/%Y").date() if fecha_ingreso else None
    except: fecha_ingreso = None
    try: fecha_salida = datetime.strptime(fecha_salida, "%d/%m/%Y").date() if fecha_salida else None
    except: fecha_salida = None

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
        'usuario_modificador': session.get('user', {}).get('username'),
        'fecha_modificacion': datetime.now()
    }

    data = {k: v for k, v in data.items() if v is not None}
    update_empleado(id, data, session["user"]["id"])

    flash("Empleado actualizado correctamente", "success")
    return redirect(url_for('empleados.lista_empleados'))


# =============================================================================
# ELIMINAR EMPLEADO
# =============================================================================
@empleados_bp.route('/delete/<int:id>', endpoint='delete_employee')
@login_required
def eliminar_empleado(id):
    delete_empleado(id)
    flash("Empleado eliminado", "info")
    return redirect(url_for('empleados.lista_empleados'))


# =============================================================================
# EXPORTAR EXCEL
# =============================================================================
@empleados_bp.route('/export', endpoint='export_excel')
@login_required
def export_excel():
    # Leer filtros de la URL
    empresa = request.args.get('empresa')
    estado = request.args.get('estado')
    cargo = request.args.get('cargo')
    orden = request.args.get('orden')

    query = """
        SELECT e.*,
           (SELECT COUNT(*) FROM empleados_anexos a WHERE a.empleado_id = e.id) AS total_anexos
        FROM empleados e
        WHERE 1=1
    """

    if empresa:
        query += f" AND e.empresa = '{empresa}'"
    if estado:
        query += f" AND e.estado = '{estado}'"
    if cargo:
        query += f" AND e.cargo LIKE '%{cargo}%'"

    # Ordenamiento actual
    if orden:
        col, direction = orden.split("_")
        query += f" ORDER BY {col} {direction.upper()}"
    else:
        query += " ORDER BY e.id DESC"

    empleados = db.fetch_all(query)
    data = empleados_to_excel(empleados)

    return send_file(
        io.BytesIO(data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='empleados.xlsx'
    )



# =============================================================================
# HISTORIAL DE CAMBIOS
# =============================================================================
@empleados_bp.route('/empleado/<int:empleado_id>/historial', endpoint='historial_empleado')
@login_required
def historial_empleado(empleado_id):
    if session.get("user", {}).get("rol") != "admin":
        flash("No tienes permisos para ver el historial", "danger")
        return redirect(url_for('empleados.lista_empleados'))

    empleado = get_empleado_by_id(empleado_id)
    historial = listar_historial_empleado(empleado_id)
    return render_template('empleados/historial.html', empleado=empleado, historial=historial)


# =============================================================================
# DESCARGAR ANEXO
# =============================================================================
@empleados_bp.route('/empleados/anexo/<path:anexo_id>', endpoint='download_anexo')
@login_required
def download_anexo(anexo_id):
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_folder, anexo_id)

    if not os.path.exists(file_path):
        flash("Archivo no encontrado", "warning")
        return redirect(url_for('empleados.lista_empleados'))

    return send_from_directory(upload_folder, anexo_id, as_attachment=True)


# =============================================================================
# VER ANEXOS DETALLADOS
# =============================================================================
@empleados_bp.route('/empleados/<int:empleado_id>/anexos', endpoint='ver_anexos')
@login_required
def ver_anexos(empleado_id):
    empleado = get_empleado_by_id(empleado_id)
    if not empleado:
        flash("Empleado no encontrado", "danger")
        return redirect(url_for('empleados.lista_empleados'))

    upload_folder_cfg = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    upload_dir = os.path.join(current_app.root_path, upload_folder
