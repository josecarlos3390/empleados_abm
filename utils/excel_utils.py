from openpyxl import Workbook
from io import BytesIO

def empleados_to_excel(empleados):
    wb = Workbook()
    ws = wb.active
    # header
    if empleados:
        header = list(empleados[0].keys())
        ws.append(header)
        for e in empleados:
            ws.append([e.get(h) for h in header])
    else:
        ws.append(['No data'])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.getvalue()
