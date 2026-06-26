import re
from flask import (
    Blueprint, render_template, request, flash, redirect, url_for, send_file
)

from config.settings import Config
from db.sqlserver import buscar_transaccion
from db.tickets import (
    ya_fue_impresa,
    obtener_impresion,
    obtener_impresion_por_id,
    registrar_impresion,
    registrar_reimpresion,
    listar_impresiones_paginada,
    contar_impresiones,
    contar_reimpresiones,
)
from utils.pdf_utils import generar_pdf_tickets
from utils.security import admin_required, login_required


tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')

# Denominaciones de tickets permitidas (Bs)
DENOMINACIONES = (300, 500)

# Patrón para TransactionId alfanumérico (ej. T1SC100380726)
_TRANSACTION_ID_RE = re.compile(r'^[A-Za-z0-9\-_]+$')


def _validar_transaction_id(transaction_id):
    """Valida que el número de transacción sea seguro y no vacío."""
    if not transaction_id:
        return False
    if len(transaction_id) > 100:
        return False
    return bool(_TRANSACTION_ID_RE.fullmatch(transaction_id))


@tickets_bp.route('/', methods=['GET', 'POST'])
def tickets():
    """Página pública para consultar una transacción y elegir tickets."""
    transaction_id = ''
    transaccion = None
    opciones = []
    ya_impresa = False
    impresion = None

    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id', '').strip().upper()

        if not _validar_transaction_id(transaction_id):
            flash('Número de transacción inválido.', 'danger')
        else:
            # Verificar si ya fue impresa (MySQL)
            impresion = obtener_impresion(transaction_id)
            if impresion:
                ya_impresa = True
                flash('Esta transacción ya fue impresa. No se permite reimprimir.', 'warning')
            else:
                # Consultar en SQL Server
                transaccion = buscar_transaccion(transaction_id)
                if not transaccion:
                    flash('No se encontró la transacción en el sistema.', 'danger')
                else:
                    total = transaccion['total']
                    for denom in DENOMINACIONES:
                        cantidad = int(total // denom)
                        if 0 < cantidad <= Config.MAX_TICKETS_POR_IMPRESION:
                            opciones.append({
                                'denominacion': denom,
                                'cantidad': cantidad,
                                'total_impreso': cantidad * denom,
                                'restante': round(total - (cantidad * denom), 2),
                            })

                    if not opciones:
                        cantidad_300 = int(total // 300)
                        cantidad_500 = int(total // 500)
                        if cantidad_300 > Config.MAX_TICKETS_POR_IMPRESION or cantidad_500 > Config.MAX_TICKETS_POR_IMPRESION:
                            flash(
                                f'El total de la factura supera el límite permitido de {Config.MAX_TICKETS_POR_IMPRESION} tickets. '
                                'Contactá al administrador para gestionar esta transacción.',
                                'danger'
                            )
                        else:
                            flash(
                                'El total de la factura no alcanza para imprimir tickets de 300 o 500 Bs.',
                                'warning'
                            )

    return render_template(
        'tickets/tickets.html',
        transaction_id=transaction_id,
        transaccion=transaccion,
        opciones=opciones,
        ya_impresa=ya_impresa,
        impresion=impresion,
        modo_descarga=Config.TICKET_MODO_DESCARGA,
    )


@tickets_bp.route('/comprobante/<transaction_id>')
def comprobante(transaction_id):
    """Muestra una pantalla de resumen del ticket impreso."""
    if not _validar_transaction_id(transaction_id):
        flash('Número de transacción inválido.', 'danger')
        return redirect(url_for('tickets.tickets'))

    impresion = obtener_impresion(transaction_id)
    if not impresion:
        flash('No se encontró la impresión de esa transacción.', 'danger')
        return redirect(url_for('tickets.tickets'))

    return render_template('tickets/comprobante.html', impresion=impresion)


@tickets_bp.route('/previsualizar/<transaction_id>')
@login_required
def previsualizar(transaction_id):
    """
    Muestra una previsualización HTML de los tickets lista para imprimir
    con el diálogo de impresión del navegador.
    """
    if not _validar_transaction_id(transaction_id):
        flash('Número de transacción inválido.', 'danger')
        return redirect(url_for('tickets.tickets'))

    impresion = obtener_impresion(transaction_id)
    if not impresion:
        flash('No se encontró la impresión de esa transacción.', 'danger')
        return redirect(url_for('tickets.tickets'))

    es_reimpresion = request.args.get('reimpresion', 'false').lower() == 'true'

    return render_template(
        'tickets/previsualizar.html',
        impresion=impresion,
        es_reimpresion=es_reimpresion,
        modo_descarga=Config.TICKET_MODO_DESCARGA,
    )


@tickets_bp.route('/admin')
@login_required
@admin_required
def admin_tickets():
    """Panel de administración para listar transacciones impresas."""
    pagina = request.args.get('page', 1, type=int)
    por_pagina = request.args.get('per_page', 20, type=int)
    busqueda = request.args.get('q', '').strip().upper() or None

    if pagina < 1:
        pagina = 1
    if por_pagina < 1:
        por_pagina = 20

    total = contar_impresiones(busqueda)
    impresiones = listar_impresiones_paginada(pagina, por_pagina, busqueda)
    total_paginas = (total + por_pagina - 1) // por_pagina if total > 0 else 1

    return render_template(
        'tickets/admin.html',
        impresiones=impresiones,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        total=total,
        busqueda=busqueda or '',
    )


@tickets_bp.route('/admin/reimprimir/<transaction_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def reimprimir_ticket(transaction_id):
    """
    Permite a un administrador reimprimir una transacción ya impresa.
    Registra la reimpresión y redirige a la previsualización.
    """
    if not _validar_transaction_id(transaction_id):
        flash('Número de transacción inválido.', 'danger')
        return redirect(url_for('tickets.admin_tickets'))

    impresion = obtener_impresion(transaction_id)
    if not impresion:
        flash('No se encontró la impresión de esa transacción.', 'danger')
        return redirect(url_for('tickets.admin_tickets'))

    # Validar que la transacción sigue existiendo en SQL Server
    transaccion = buscar_transaccion(transaction_id)
    if not transaccion:
        flash('La transacción no se encuentra disponible en el sistema origen.', 'danger')
        return redirect(url_for('tickets.admin_tickets'))

    # Registrar la reimpresión
    reimpreso_por = session.get('user', {}).get('username')
    try:
        registrar_reimpresion(impresion['id'], transaction_id, reimpreso_por)
    except Exception:
        flash('Error al registrar la reimpresión. Intente nuevamente.', 'danger')
        return redirect(url_for('tickets.admin_tickets'))

    flash('Reimpresión registrada. Se generó la previsualización.', 'success')
    return redirect(url_for('tickets.previsualizar', transaction_id=transaction_id, reimpresion='true'))


@tickets_bp.route('/imprimir', methods=['POST'])
@login_required
def imprimir():
    """
    Genera los tickets, registra la impresión y:
    - Modo descarga (TICKET_MODO_DESCARGA=true): descarga el PDF.
    - Modo previsualización (TICKET_MODO_DESCARGA=false): redirige a la vista
      de previsualización lista para imprimir con window.print().
    """
    transaction_id = request.form.get('transaction_id', '').strip().upper()
    denominacion_raw = request.form.get('denominacion', '')

    if not _validar_transaction_id(transaction_id):
        flash('Número de transacción inválido.', 'danger')
        return redirect(url_for('tickets.tickets'))

    if denominacion_raw not in ('300', '500'):
        flash('Denominación de ticket no válida.', 'danger')
        return redirect(url_for('tickets.tickets'))

    denominacion = int(denominacion_raw)

    # Bloquear reimpresión
    if ya_fue_impresa(transaction_id):
        flash('Esta transacción ya fue impresa. No se permite reimprimir.', 'danger')
        return redirect(url_for('tickets.tickets'))

    # Volver a consultar para asegurar que existe y obtener el total actual
    transaccion = buscar_transaccion(transaction_id)
    if not transaccion:
        flash('No se encontró la transacción en el sistema.', 'danger')
        return redirect(url_for('tickets.tickets'))

    total = transaccion['total']
    cantidad = int(total // denominacion)
    if cantidad <= 0:
        flash('El total no alcanza para imprimir tickets de esa denominación.', 'danger')
        return redirect(url_for('tickets.tickets'))

    if cantidad > Config.MAX_TICKETS_POR_IMPRESION:
        flash(
            f'La cantidad de tickets a imprimir ({cantidad}) supera el límite permitido de {Config.MAX_TICKETS_POR_IMPRESION}. '
            'Probá con una denominación mayor o contactá al administrador.',
            'danger'
        )
        return redirect(url_for('tickets.tickets'))

    total_impreso = cantidad * denominacion
    cajero = session.get('user', {}).get('username')

    # Registrar en MySQL
    try:
        registrar_impresion(transaction_id, total, denominacion, cantidad, total_impreso, cajero)
    except Exception:
        flash('Error al registrar la impresión. Intente nuevamente.', 'danger')
        return redirect(url_for('tickets.tickets'))

    if Config.TICKET_MODO_DESCARGA:
        # Modo descarga: generar PDF y entregarlo
        pdf_buffer = generar_pdf_tickets(transaction_id, total, denominacion, cantidad)
        filename = f'tickets_{transaction_id}_{denominacion}.pdf'
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )

    # Modo previsualización: redirigir a la vista de impresión
    return redirect(url_for('tickets.previsualizar', transaction_id=transaction_id))
