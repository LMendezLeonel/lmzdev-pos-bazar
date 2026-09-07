import io
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from fpdf import FPDF


def excel_ventas(totales, mas_vendidos, ganancia, desde, hasta):
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de ventas"

    titulo_font = Font(bold=True, size=14)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0E2E29", end_color="0E2E29", fill_type="solid")

    ws["A1"] = "Reporte de ventas"
    ws["A1"].font = titulo_font
    ws["A2"] = f"Período: {desde or 'inicio'} a {hasta or 'hoy'}"

    ws["A4"] = "Cantidad de ventas"
    ws["B4"] = totales["cantidad_ventas"]
    ws["A5"] = "Total vendido"
    ws["B5"] = totales["total_vendido"]
    ws["A6"] = "Ganancia estimada"
    ws["B6"] = ganancia

    fila = 8
    ws.cell(row=fila, column=1, value="Producto").font = header_font
    ws.cell(row=fila, column=2, value="Cantidad vendida").font = header_font
    ws.cell(row=fila, column=3, value="Total generado").font = header_font
    for col in range(1, 4):
        ws.cell(row=fila, column=col).fill = header_fill

    for p in mas_vendidos:
        fila += 1
        ws.cell(row=fila, column=1, value=p["nombre"])
        ws.cell(row=fila, column=2, value=p["cantidad_total"])
        ws.cell(row=fila, column=3, value=p["total_generado"])

    for col, ancho in zip("ABC", (30, 20, 20)):
        ws.column_dimensions[col].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def pdf_ventas(totales, mas_vendidos, ganancia, desde, hasta):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de ventas", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Periodo: {desde or 'inicio'} a {hasta or 'hoy'}", ln=True)
    pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Cantidad de ventas: {totales['cantidad_ventas']}", ln=True)
    pdf.cell(0, 7, f"Total vendido: ${totales['total_vendido']:.2f}", ln=True)
    pdf.cell(0, 7, f"Ganancia estimada: ${ganancia:.2f}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Productos mas vendidos", ln=True)
    pdf.set_fill_color(14, 46, 41)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 8, "Producto", border=1, fill=True)
    pdf.cell(45, 8, "Cantidad", border=1, fill=True, align="C")
    pdf.cell(45, 8, "Total generado", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for p in mas_vendidos:
        pdf.cell(90, 8, _limpiar(p["nombre"]), border=1)
        pdf.cell(45, 8, str(p["cantidad_total"]), border=1, align="C")
        pdf.cell(45, 8, f"${p['total_generado']:.2f}", border=1, align="C")
        pdf.ln()

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer


def excel_stock(productos, totales):
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock y precios"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0E2E29", end_color="0E2E29", fill_type="solid")

    ws["A1"] = "Reporte de Stock y Precios"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A3"] = "Unidades en stock"
    ws["B3"] = totales["total_unidades"]
    ws["A4"] = "Valor a costo"
    ws["B4"] = totales["total_costo"]
    ws["A5"] = "Valor a precio de venta"
    ws["B5"] = totales["total_venta"]

    columnas = ["Producto", "Categoría", "Precio venta", "Precio costo", "Stock", "Valor (costo)", "Valor (venta)"]
    fila = 7
    for i, col in enumerate(columnas, start=1):
        celda = ws.cell(row=fila, column=i, value=col)
        celda.font = header_font
        celda.fill = header_fill

    for p in productos:
        fila += 1
        ws.cell(row=fila, column=1, value=p["nombre"])
        ws.cell(row=fila, column=2, value=p["categoria_nombre"] or "-")
        ws.cell(row=fila, column=3, value=p["precio_venta"])
        ws.cell(row=fila, column=4, value=p["precio_costo"])
        ws.cell(row=fila, column=5, value=p["stock_actual"])
        ws.cell(row=fila, column=6, value=p["valor_costo"])
        ws.cell(row=fila, column=7, value=p["valor_venta"])

    for col, ancho in zip("ABCDEFG", (28, 18, 14, 14, 10, 15, 15)):
        ws.column_dimensions[col].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def pdf_stock(productos, totales):
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Stock y Precios", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Unidades: {totales['total_unidades']}   |   Valor a costo: ${totales['total_costo']:.2f}   |   Valor a venta: ${totales['total_venta']:.2f}", ln=True)
    pdf.ln(4)

    anchos = [55, 40, 30, 30, 20, 30, 30]
    encabezados = ["Producto", "Categoria", "P. venta", "P. costo", "Stock", "Valor costo", "Valor venta"]

    pdf.set_fill_color(14, 46, 41)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(anchos, encabezados):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for p in productos:
        pdf.cell(anchos[0], 7, _limpiar(p["nombre"]), border=1)
        pdf.cell(anchos[1], 7, _limpiar(p["categoria_nombre"] or "-"), border=1)
        pdf.cell(anchos[2], 7, f"${p['precio_venta']:.2f}", border=1, align="C")
        pdf.cell(anchos[3], 7, f"${p['precio_costo']:.2f}", border=1, align="C")
        pdf.cell(anchos[4], 7, str(p["stock_actual"]), border=1, align="C")
        pdf.cell(anchos[5], 7, f"${p['valor_costo']:.2f}", border=1, align="C")
        pdf.cell(anchos[6], 7, f"${p['valor_venta']:.2f}", border=1, align="C")
        pdf.ln()

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer


def _limpiar(texto):
    """FPDF con fuentes core no soporta todo UTF-8 (ej. ñ en negrita); reemplazamos lo problemático."""
    return (texto or "").encode("latin-1", "replace").decode("latin-1")


def excel_lista_precios(productos):
    """Versión liviana para el rol Vendedor: sin costos ni márgenes, solo precio de venta y stock."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Lista de precios"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0E2E29", end_color="0E2E29", fill_type="solid")

    ws["A1"] = "Lista de precios"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    columnas = ["Producto", "Categoría", "Código", "Precio", "Stock"]
    fila = 4
    for i, col in enumerate(columnas, start=1):
        celda = ws.cell(row=fila, column=i, value=col)
        celda.font = header_font
        celda.fill = header_fill

    for p in productos:
        fila += 1
        ws.cell(row=fila, column=1, value=p["nombre"])
        ws.cell(row=fila, column=2, value=p["categoria_nombre"] or "-")
        ws.cell(row=fila, column=3, value=p["codigo_barras"] or "-")
        ws.cell(row=fila, column=4, value=p["precio_venta"])
        ws.cell(row=fila, column=5, value=p["stock_actual"])

    for col, ancho in zip("ABCDE", (30, 20, 18, 14, 10)):
        ws.column_dimensions[col].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def pdf_lista_precios(productos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Lista de precios", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(4)

    anchos = [70, 40, 30, 25, 20]
    encabezados = ["Producto", "Categoria", "Codigo", "Precio", "Stock"]

    pdf.set_fill_color(14, 46, 41)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    for w, h in zip(anchos, encabezados):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for p in productos:
        pdf.cell(anchos[0], 7, _limpiar(p["nombre"]), border=1)
        pdf.cell(anchos[1], 7, _limpiar(p["categoria_nombre"] or "-"), border=1)
        pdf.cell(anchos[2], 7, _limpiar(p["codigo_barras"] or "-"), border=1)
        pdf.cell(anchos[3], 7, f"${p['precio_venta']:.2f}", border=1, align="C")
        pdf.cell(anchos[4], 7, str(p["stock_actual"]), border=1, align="C")
        pdf.ln()

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer
