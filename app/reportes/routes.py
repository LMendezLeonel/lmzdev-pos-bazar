from flask import Blueprint, render_template, request, send_file

from app.auth.decorators import requiere_rol
from app.db import get_client_db
from app.reportes import exportar

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _obtener_datos_ventas(desde, hasta):
    db = get_client_db()
    filtro_fecha = ""
    params = []
    if desde:
        filtro_fecha += " AND date(v.fecha) >= date(?)"
        params.append(desde)
    if hasta:
        filtro_fecha += " AND date(v.fecha) <= date(?)"
        params.append(hasta)

    totales = db.execute(
        f"SELECT COUNT(*) as cantidad_ventas, COALESCE(SUM(total),0) as total_vendido "
        f"FROM ventas v WHERE 1=1 {filtro_fecha}",
        params
    ).fetchone()

    mas_vendidos = db.execute(
        f"""SELECT p.nombre, SUM(dv.cantidad) as cantidad_total, SUM(dv.subtotal) as total_generado
            FROM detalle_venta dv
            JOIN ventas v ON dv.venta_id = v.id
            JOIN productos p ON dv.producto_id = p.id
            WHERE 1=1 {filtro_fecha}
            GROUP BY p.id
            ORDER BY cantidad_total DESC
            LIMIT 10""",
        params
    ).fetchall()

    ganancia = db.execute(
        f"""SELECT COALESCE(SUM((p.precio_venta - p.precio_costo) * dv.cantidad), 0) as ganancia_estimada
            FROM detalle_venta dv
            JOIN ventas v ON dv.venta_id = v.id
            JOIN productos p ON dv.producto_id = p.id
            WHERE 1=1 {filtro_fecha}""",
        params
    ).fetchone()

    return totales, mas_vendidos, ganancia["ganancia_estimada"]


@bp.route("/")
@requiere_rol("dueño")
def index():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    totales, mas_vendidos, ganancia = _obtener_datos_ventas(desde, hasta)

    return render_template(
        "reportes/index.html",
        totales=totales,
        mas_vendidos=mas_vendidos,
        ganancia=ganancia,
        desde=desde,
        hasta=hasta
    )


@bp.route("/exportar/excel")
@requiere_rol("dueño")
def exportar_excel():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    totales, mas_vendidos, ganancia = _obtener_datos_ventas(desde, hasta)
    buffer = exportar.excel_ventas(totales, mas_vendidos, ganancia, desde, hasta)
    return send_file(buffer, as_attachment=True, download_name="reporte_ventas.xlsx",
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@bp.route("/exportar/pdf")
@requiere_rol("dueño")
def exportar_pdf():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    totales, mas_vendidos, ganancia = _obtener_datos_ventas(desde, hasta)
    buffer = exportar.pdf_ventas(totales, mas_vendidos, ganancia, desde, hasta)
    return send_file(buffer, as_attachment=True, download_name="reporte_ventas.pdf", mimetype="application/pdf")


@bp.route("/stock-precios")
@requiere_rol("dueño")
def stock_precios():
    productos, totales = _obtener_datos_stock()
    categorias_presentes = sorted({p["categoria_nombre"] for p in productos if p["categoria_nombre"]})
    return render_template("reportes/stock_precios.html", productos=productos, totales=totales, categorias_presentes=categorias_presentes)


@bp.route("/stock-precios/exportar/excel")
@requiere_rol("dueño")
def stock_precios_excel():
    productos, totales = _obtener_datos_stock()
    buffer = exportar.excel_stock(productos, totales)
    return send_file(buffer, as_attachment=True, download_name="stock_precios.xlsx",
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@bp.route("/stock-precios/exportar/pdf")
@requiere_rol("dueño")
def stock_precios_pdf():
    productos, totales = _obtener_datos_stock()
    buffer = exportar.pdf_stock(productos, totales)
    return send_file(buffer, as_attachment=True, download_name="stock_precios.pdf", mimetype="application/pdf")


def _obtener_datos_stock():
    db = get_client_db()

    productos = db.execute(
        """SELECT p.*, c.nombre AS categoria_nombre,
                  (p.stock_actual * p.precio_costo) AS valor_costo,
                  (p.stock_actual * p.precio_venta) AS valor_venta
           FROM productos p
           LEFT JOIN categorias c ON p.categoria_id = c.id
           WHERE p.activo = 1
           ORDER BY p.nombre"""
    ).fetchall()

    totales = db.execute(
        """SELECT COALESCE(SUM(stock_actual * precio_costo), 0) as total_costo,
                  COALESCE(SUM(stock_actual * precio_venta), 0) as total_venta,
                  COALESCE(SUM(stock_actual), 0) as total_unidades
           FROM productos WHERE activo = 1"""
    ).fetchone()

    return productos, totales
