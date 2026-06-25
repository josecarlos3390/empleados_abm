from io import BytesIO
from datetime import datetime
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# Ancho estandar de impresora termica de 80 mm
ANCHO_TICKET = 80 * mm
# Alto compacto por ticket para ahorrar rollo
ALTO_TICKET = 100 * mm
MARGEN_SUPERIOR = 5 * mm
MARGEN_INFERIOR = 5 * mm


def generar_pdf_tickets(transaction_id, total_documento, denominacion, cantidad_tickets):
    """
    Genera un PDF optimizado para impresora termica de rollo (80 mm de ancho).
    Todos los tickets se apilan en una sola pagina continua.
    Cada ticket sigue el formato de campos manuales para el cliente.
    Retorna un BytesIO listo para descargar.
    """
    buffer = BytesIO()

    # Altura total del rollo segun la cantidad de tickets
    alto_total = MARGEN_SUPERIOR + (cantidad_tickets * ALTO_TICKET) + MARGEN_INFERIOR
    c = canvas.Canvas(buffer, pagesize=(ANCHO_TICKET, alto_total))

    fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    for i in range(1, cantidad_tickets + 1):
        # Posicion Y inicial de este ticket (de arriba hacia abajo)
        y_base = alto_total - MARGEN_SUPERIOR - (i * ALTO_TICKET)

        x_centro = ANCHO_TICKET / 2
        margen_x = 6 * mm

        # Borde del ticket (rectangulo fino)
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setLineWidth(0.5)
        c.rect(2 * mm, y_base + 2 * mm, ANCHO_TICKET - 4 * mm, ALTO_TICKET - 4 * mm, fill=0, stroke=1)

        y = y_base + 92 * mm

        # Titulo
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(x_centro, y, f'TICKET / {denominacion} BS')

        # Instruccion
        y -= 7 * mm
        c.setFont('Helvetica', 9)
        c.drawCentredString(x_centro, y, 'Completa tus datos y deposita')
        y -= 4.2 * mm
        c.drawCentredString(x_centro, y, 'este ticket en la anfora para')
        y -= 4.2 * mm
        c.drawCentredString(x_centro, y, 'participar del sorteo.')

        # Transaccion y correlativo
        y -= 7.5 * mm
        c.setFont('Helvetica-Bold', 10)
        c.drawString(margen_x, y, f'TRANS: {transaction_id}')
        c.drawRightString(ANCHO_TICKET - margen_x, y, f'TICKET {i}/{cantidad_tickets}')

        # Campos manuales
        y -= 8 * mm
        campos = ['NOMBRE', 'CELULAR', 'CORREO', 'DIRECCION', 'SUCURSAL']
        c.setFont('Helvetica-Bold', 10)
        for campo in campos:
            c.drawString(margen_x, y, f'{campo}:')
            c.setLineWidth(0.4)
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.line(margen_x + 22 * mm, y + 1 * mm, ANCHO_TICKET - margen_x, y + 1 * mm)
            y -= 7 * mm

        # Pie
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(x_centro, y, 'MUCHA SUERTE!')
        y -= 5.5 * mm
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(x_centro, y, 'TU CASA, TU MUNDIAL')

        # Fecha de impresion
        y -= 6 * mm
        c.setFont('Helvetica', 7)
        c.drawCentredString(x_centro, y, f'Impreso: {fecha_hora}')

    c.save()
    buffer.seek(0)
    return buffer
