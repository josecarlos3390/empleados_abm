import re
from flask import (
    Blueprint, render_template, request, flash, redirect, url_for, send_file
)

from config.settings import Config
from db.sqlserver import buscar_transaccion
from db.tickets import (
    ya_fue_impresa,
    obtener_impresion,
    registrar_impresion,
)
from utils.pdf_utils import generar_pdf_tickets


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


@tickets_bp.route('/imprimir', methods=['POST'])
def imprimir():
    """Genera el PDF de tickets, registra la impresión y lo descarga."""
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

    # Generar PDF en memoria
    pdf_buffer = generar_pdf_tickets(transaction_id, total, denominacion, cantidad)

    # Registrar en MySQL antes de entregar el archivo
    try:
        registrar_impresion(transaction_id, total, denominacion, cantidad, total_impreso)
    except Exception:
        flash('Error al registrar la impresión. Intente nuevamente.', 'danger')
        return redirect(url_for('tickets.tickets'))

    filename = f'tickets_{transaction_id}_{denominacion}.pdf'
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )
