from io import BytesIO
from datetime import datetime
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# Ancho estandar de impresora termica de 80 mm
ANCHO_TICKET = 80 * mm
ALTO_TICKET = 120 * mm
MARGEN_SUPERIOR = 10 * mm
MARGEN_INFERIOR = 10 * mm


def generar_pdf_tickets(transaction_id, total_documento, denominacion, cantidad_tickets):
    """
    Genera un PDF optimizado para impresora termica de rollo (80 mm de ancho).
    Todos los tickets se apilan en una sola pagina continua para facilitar la impresion.
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

        # Encabezado
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(ANCHO_TICKET / 2, y_base + 100 * mm, 'TICKET DE PAGO')

        # Linea separadora
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.line(5 * mm, y_base + 92 * mm, ANCHO_TICKET - 5 * mm, y_base + 92 * mm)

        # Datos del ticket
        y = y_base + 80 * mm
        c.setFont('Helvetica', 10)
        c.drawCentredString(ANCHO_TICKET / 2, y, 'Transaccion:')

        y -= 6 * mm
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(ANCHO_TICKET / 2, y, str(transaction_id))

        y -= 14 * mm
        c.setFont('Helvetica', 10)
        c.drawCentredString(ANCHO_TICKET / 2, y, 'Monto ticket:')

        y -= 7 * mm
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(ANCHO_TICKET / 2, y, f'Bs {denominacion:,.2f}')

        y -= 12 * mm
        c.setFont('Helvetica', 9)
        c.drawCentredString(ANCHO_TICKET / 2, y, f'Total documento: Bs {total_documento:,.2f}')

        y -= 10 * mm
        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(ANCHO_TICKET / 2, y, f'Ticket {i} de {cantidad_tickets}')

        y -= 10 * mm
        c.setFont('Helvetica', 8)
        c.drawCentredString(ANCHO_TICKET / 2, y, f'Impreso: {fecha_hora}')

        # Linea de corte punteada entre tickets (excepto despues del ultimo)
        if i < cantidad_tickets:
            c.setDash(3, 3)
            c.setStrokeColorRGB(0.4, 0.4, 0.4)
            c.line(10 * mm, y_base + 5 * mm, ANCHO_TICKET - 10 * mm, y_base + 5 * mm)
            c.setDash()

    c.save()
    buffer.seek(0)
    return buffer
