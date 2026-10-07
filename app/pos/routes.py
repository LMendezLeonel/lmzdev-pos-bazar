from flask import Blueprint, render_template, session, request, jsonify, send_file

from app.auth.decorators import login_required, requiere_rol
from app.db import get_client_db, obtener_caja_abierta
from app.reportes import exportar
from app.productos_util import calcular_cuotas

bp = Blueprint("pos", __name__, url_prefix="/pos")


def _carrito():
    """Carrito de la sesión actual (lista de dicts)."""
    if "carrito" not in session:
        session["carrito"] = []
    return session["carrito"]


def _total_carrito(carrito):
    return round(sum(item["precio"] * item["cantidad"] for item in carrito), 2)


@bp.route("/")
@login_required
def index():
    if session.get("rol") == "vendedor":
        return render_template("pos/consulta.html")

    caja = obtener_caja_abierta()
    carrito = _carrito()
    return render_template(
        "pos/index.html",
        caja=caja,
        carrito=carrito,
        total=_total_carrito(carrito)
    )


@bp.route("/productos")
@login_required
def productos_todos():
    """Devuelve el catálogo completo activo (usado por la vista de Vendedor)."""
    db = get_client_db()
    productos = db.execute(
        """SELECT p.id, p.nombre, p.codigo_barras, p.precio_venta, p.stock_actual,
                  c.nombre AS categoria_nombre, (p.imagen IS NOT NULL) AS tiene_imagen
           FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
           WHERE p.activo = 1 ORDER BY p.nombre"""
    ).fetchall()
    resultado = []
    for p in productos:
        d = dict(p)
        d["tiene_imagen"] = bool(d["tiene_imagen"])
        d["cuotas"] = calcular_cuotas(d["precio_venta"])
        resultado.append(d)
    return jsonify(resultado)


@bp.route("/buscar", methods=["POST"])
@login_required
def buscar():
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify([])

    db = get_client_db()

    # 1. Intento exacto por código de barras (lo típico al escanear)
    producto = db.execute(
        "SELECT * FROM productos WHERE codigo_barras = ? AND activo = 1",
        (query,)
    ).fetchone()

    if producto:
        return jsonify([dict(producto)])

    # 2. Si no hay match exacto, busco por nombre parcial
    productos = db.execute(
        "SELECT * FROM productos WHERE nombre LIKE ? AND activo = 1 LIMIT 15",
        (f"%{query}%",)
    ).fetchall()

    return jsonify([dict(p) for p in productos])


@bp.route("/carrito/agregar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def carrito_agregar():
    data = request.get_json(force=True)
    producto_id = data.get("producto_id")

    db = get_client_db()
    producto = db.execute(
        "SELECT * FROM productos WHERE id = ? AND activo = 1", (producto_id,)
    ).fetchone()

    if producto is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    carrito = _carrito()

    # Si ya está en el carrito, sumo cantidad; si no, lo agrego
    for item in carrito:
        if item["producto_id"] == producto["id"]:
            nueva_cantidad = item["cantidad"] + 1
            if nueva_cantidad > producto["stock_actual"]:
                return jsonify({"error": f"Solo hay {producto['stock_actual']} en stock"}), 400
            item["cantidad"] = nueva_cantidad
            break
    else:
        if producto["stock_actual"] < 1:
            return jsonify({"error": "Sin stock disponible"}), 400
        carrito.append({
            "producto_id": producto["id"],
            "nombre": producto["nombre"],
            "precio": producto["precio_venta"],
            "cantidad": 1
        })

    session["carrito"] = carrito
    session.modified = True
    return jsonify({"carrito": carrito, "total": _total_carrito(carrito)})


@bp.route("/carrito/actualizar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def carrito_actualizar():
    data = request.get_json(force=True)
    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad")

    db = get_client_db()
    producto = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

    if producto and cantidad > producto["stock_actual"]:
        return jsonify({"error": f"Solo hay {producto['stock_actual']} en stock"}), 400

    carrito = _carrito()
    if cantidad <= 0:
        carrito = [i for i in carrito if i["producto_id"] != producto_id]
    else:
        for item in carrito:
            if item["producto_id"] == producto_id:
                item["cantidad"] = cantidad
                break

    session["carrito"] = carrito
    session.modified = True
    return jsonify({"carrito": carrito, "total": _total_carrito(carrito)})


@bp.route("/carrito/quitar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def carrito_quitar():
    data = request.get_json(force=True)
    producto_id = data.get("producto_id")

    carrito = [i for i in _carrito() if i["producto_id"] != producto_id]
    session["carrito"] = carrito
    session.modified = True
    return jsonify({"carrito": carrito, "total": _total_carrito(carrito)})


@bp.route("/carrito/vaciar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def carrito_vaciar():
    session["carrito"] = []
    session.modified = True
    return jsonify({"carrito": [], "total": 0})


@bp.route("/cobrar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def cobrar():
    caja = obtener_caja_abierta()
    if caja is None:
        return jsonify({"error": "No hay una caja abierta. Abrí caja antes de cobrar."}), 400

    carrito = _carrito()
    if not carrito:
        return jsonify({"error": "El carrito está vacío"}), 400

    data = request.get_json(force=True)
    medio_pago = data.get("medio_pago", "efectivo")
    monto_recibido = data.get("monto_recibido")
    promocion_id = data.get("promocion_id")

    db = get_client_db()

    # Revalidar stock justo antes de cobrar (por si cambió desde que se armó el carrito)
    for item in carrito:
        producto = db.execute(
            "SELECT stock_actual FROM productos WHERE id = ?", (item["producto_id"],)
        ).fetchone()
        if producto is None or producto["stock_actual"] < item["cantidad"]:
            return jsonify({"error": f"Sin stock suficiente de '{item['nombre']}'"}), 400

    subtotal = _total_carrito(carrito)
    descuento = 0
    promo_valida_id = None

    if promocion_id:
        promo = db.execute(
            "SELECT * FROM promociones WHERE id = ? AND activa = 1", (promocion_id,)
        ).fetchone()
        if promo and (promo["medio_pago"] is None or promo["medio_pago"] == medio_pago):
            if promo["tipo"] == "porcentaje":
                descuento = round(subtotal * (promo["valor"] / 100), 2)
            else:
                descuento = min(round(promo["valor"], 2), subtotal)
            promo_valida_id = promo["id"]

    total = round(subtotal - descuento, 2)

    vuelto = None
    if medio_pago == "efectivo" and monto_recibido is not None:
        if monto_recibido < total:
            return jsonify({"error": "El monto recibido es menor al total"}), 400
        vuelto = round(monto_recibido - total, 2)

    cursor = db.execute(
        """INSERT INTO ventas (usuario_id, caja_id, promocion_id, subtotal, descuento, total, medio_pago, monto_recibido, vuelto)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session["user_id"], caja["id"], promo_valida_id, subtotal, descuento, total, medio_pago, monto_recibido, vuelto)
    )
    venta_id = cursor.lastrowid

    for item in carrito:
        subtotal_item = round(item["precio"] * item["cantidad"], 2)
        db.execute(
            """INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
               VALUES (?, ?, ?, ?, ?)""",
            (venta_id, item["producto_id"], item["cantidad"], item["precio"], subtotal_item)
        )
        db.execute(
            "UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?",
            (item["cantidad"], item["producto_id"])
        )

    db.commit()

    session["carrito"] = []
    session.modified = True

    return jsonify({
        "ok": True,
        "venta_id": venta_id,
        "subtotal": subtotal,
        "descuento": descuento,
        "total": total,
        "medio_pago": medio_pago,
        "monto_recibido": monto_recibido,
        "vuelto": vuelto,
        "items": carrito
    })


def _productos_para_lista_precios():
    db = get_client_db()
    return db.execute(
        """SELECT p.*, c.nombre AS categoria_nombre
           FROM productos p
           LEFT JOIN categorias c ON p.categoria_id = c.id
           WHERE p.activo = 1
           ORDER BY p.nombre"""
    ).fetchall()


@bp.route("/lista-precios/excel")
@login_required
def lista_precios_excel():
    productos = _productos_para_lista_precios()
    buffer = exportar.excel_lista_precios(productos)
    return send_file(buffer, as_attachment=True, download_name="lista_precios.xlsx",
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@bp.route("/lista-precios/pdf")
@login_required
def lista_precios_pdf():
    productos = _productos_para_lista_precios()
    buffer = exportar.pdf_lista_precios(productos)
    return send_file(buffer, as_attachment=True, download_name="lista_precios.pdf", mimetype="application/pdf")


@bp.route("/ticket/<int:venta_id>")
@requiere_rol("dueño", "empleado")
def ticket(venta_id):
    db = get_client_db()

    venta = db.execute(
        """SELECT v.*, u.nombre AS cajero
           FROM ventas v
           LEFT JOIN usuarios u ON v.usuario_id = u.id
           WHERE v.id = ?""",
        (venta_id,)
    ).fetchone()

    if venta is None:
        return "Venta no encontrada", 404

    items = db.execute(
        """SELECT dv.*, p.nombre AS producto_nombre
           FROM detalle_venta dv
           JOIN productos p ON dv.producto_id = p.id
           WHERE dv.venta_id = ?""",
        (venta_id,)
    ).fetchall()

    return render_template("pos/ticket.html", venta=venta, items=items)
