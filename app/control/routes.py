from flask import Blueprint, render_template

from app.auth.decorators import requiere_rol
from app.db import get_client_db

bp = Blueprint("control", __name__, url_prefix="/control")


@bp.route("/")
@requiere_rol("dueño")
def index():
    db = get_client_db()

    # Ticket promedio
    ticket = db.execute(
        "SELECT COALESCE(AVG(total), 0) as promedio, COUNT(*) as cantidad FROM ventas"
    ).fetchone()

    # Categoría más vendida (por ingresos)
    top_categoria = db.execute(
        """SELECT c.nombre, SUM(dv.subtotal) as total
           FROM detalle_venta dv
           JOIN productos p ON dv.producto_id = p.id
           LEFT JOIN categorias c ON p.categoria_id = c.id
           GROUP BY c.id ORDER BY total DESC LIMIT 1"""
    ).fetchone()

    # Uso de promociones
    uso_promos = db.execute(
        """SELECT COUNT(*) as cantidad, COALESCE(SUM(descuento), 0) as total_descontado
           FROM ventas WHERE promocion_id IS NOT NULL"""
    ).fetchone()

    # Ventas por hora del día (0-23), sobre TODAS las ventas históricas
    ventas_por_hora = db.execute(
        """SELECT CAST(strftime('%H', fecha) AS INTEGER) as hora, COUNT(*) as cantidad, SUM(total) as total
           FROM ventas GROUP BY hora ORDER BY hora"""
    ).fetchall()
    horas_dict = {h["hora"]: h["total"] for h in ventas_por_hora}
    datos_hora = [round(horas_dict.get(h, 0), 2) for h in range(24)]

    # Ingresos por día, últimos 14 días con datos
    ingresos_dia = db.execute(
        """SELECT date(fecha) as dia, SUM(total) as total
           FROM ventas GROUP BY dia ORDER BY dia DESC LIMIT 14"""
    ).fetchall()
    ingresos_dia = list(reversed(ingresos_dia))

    # Margen total generado (rentabilidad)
    margen = db.execute(
        """SELECT COALESCE(SUM((p.precio_venta - p.precio_costo) * dv.cantidad), 0) as margen_total
           FROM detalle_venta dv JOIN productos p ON dv.producto_id = p.id"""
    ).fetchone()

    # Valor total del inventario actual (a precio de costo)
    valor_inventario = db.execute(
        "SELECT COALESCE(SUM(stock_actual * precio_costo), 0) as valor FROM productos WHERE activo = 1"
    ).fetchone()

    return render_template(
        "control/index.html",
        ticket=ticket,
        top_categoria=top_categoria,
        uso_promos=uso_promos,
        datos_hora=datos_hora,
        ingresos_dia=ingresos_dia,
        margen=margen["margen_total"],
        valor_inventario=valor_inventario["valor"]
    )
