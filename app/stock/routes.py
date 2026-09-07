import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.auth.decorators import login_required, requiere_rol
from app.db import get_client_db

bp = Blueprint("stock", __name__, url_prefix="/stock")


def _generar_codigo_unico(db):
    """Genera un código interno único (formato INTxxxxxxxxx) para productos sin código de fábrica."""
    for _ in range(20):
        codigo = "INT" + "".join(str(random.randint(0, 9)) for _ in range(9))
        existe = db.execute("SELECT 1 FROM productos WHERE codigo_barras = ?", (codigo,)).fetchone()
        if not existe:
            return codigo
    raise RuntimeError("No se pudo generar un código único, intentá de nuevo.")


@bp.route("/generar-codigo")
@requiere_rol("dueño")
def generar_codigo():
    db = get_client_db()
    return jsonify({"codigo": _generar_codigo_unico(db)})


@bp.route("/")
@login_required
def index():
    db = get_client_db()
    productos = db.execute(
        """SELECT p.*, c.nombre AS categoria_nombre
           FROM productos p
           LEFT JOIN categorias c ON p.categoria_id = c.id
           WHERE p.activo = 1
           ORDER BY p.nombre"""
    ).fetchall()
    categorias_presentes = sorted({p["categoria_nombre"] for p in productos if p["categoria_nombre"]})
    return render_template("stock/lista.html", productos=productos, categorias_presentes=categorias_presentes)


@bp.route("/nuevo", methods=["GET", "POST"])
@requiere_rol("dueño")
def nuevo():
    db = get_client_db()

    if request.method == "GET":
        categorias = db.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
        return render_template("stock/form.html", producto=None, categorias=categorias)

    nombre = request.form.get("nombre", "").strip()
    codigo_barras = request.form.get("codigo_barras", "").strip() or None
    categoria_id = request.form.get("categoria_id") or None
    precio_venta = float(request.form.get("precio_venta", 0) or 0)
    precio_costo = float(request.form.get("precio_costo", 0) or 0)
    stock_actual = int(request.form.get("stock_actual", 0) or 0)
    stock_minimo = int(request.form.get("stock_minimo", 0) or 0)

    if not nombre:
        flash("El nombre es obligatorio.", "warning")
        return redirect(url_for("stock.nuevo"))

    try:
        db.execute(
            """INSERT INTO productos
               (nombre, codigo_barras, categoria_id, precio_venta, precio_costo, stock_actual, stock_minimo)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, codigo_barras, categoria_id, precio_venta, precio_costo, stock_actual, stock_minimo)
        )
        db.commit()
        flash(f"Producto '{nombre}' creado.", "success")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            flash("Ya existe un producto con ese código de barras.", "danger")
        else:
            flash("Error al crear el producto.", "danger")
        return redirect(url_for("stock.nuevo"))

    return redirect(url_for("stock.index"))


@bp.route("/editar/<int:producto_id>", methods=["GET", "POST"])
@requiere_rol("dueño")
def editar(producto_id):
    db = get_client_db()
    producto = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

    if producto is None:
        flash("Producto no encontrado.", "danger")
        return redirect(url_for("stock.index"))

    if request.method == "GET":
        categorias = db.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
        return render_template("stock/form.html", producto=producto, categorias=categorias)

    nombre = request.form.get("nombre", "").strip()
    codigo_barras = request.form.get("codigo_barras", "").strip() or None
    categoria_id = request.form.get("categoria_id") or None
    precio_venta = float(request.form.get("precio_venta", 0) or 0)
    precio_costo = float(request.form.get("precio_costo", 0) or 0)
    stock_actual = int(request.form.get("stock_actual", 0) or 0)
    stock_minimo = int(request.form.get("stock_minimo", 0) or 0)

    db.execute(
        """UPDATE productos SET nombre=?, codigo_barras=?, categoria_id=?, precio_venta=?,
           precio_costo=?, stock_actual=?, stock_minimo=? WHERE id=?""",
        (nombre, codigo_barras, categoria_id, precio_venta, precio_costo,
         stock_actual, stock_minimo, producto_id)
    )
    db.commit()
    flash(f"Producto '{nombre}' actualizado.", "success")
    return redirect(url_for("stock.index"))


@bp.route("/eliminar/<int:producto_id>", methods=["POST"])
@requiere_rol("dueño")
def eliminar(producto_id):
    db = get_client_db()
    db.execute("UPDATE productos SET activo = 0 WHERE id = ?", (producto_id,))
    db.commit()
    flash("Producto eliminado.", "info")
    return redirect(url_for("stock.index"))


@bp.route("/categorias", methods=["GET", "POST"])
@requiere_rol("dueño")
def categorias():
    db = get_client_db()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if nombre:
            try:
                db.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
                db.commit()
                flash(f"Categoría '{nombre}' creada.", "success")
            except Exception:
                flash("Esa categoría ya existe.", "warning")
        return redirect(url_for("stock.categorias"))

    lista = db.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
    return render_template("stock/categorias.html", categorias=lista)


@bp.route("/etiqueta/<int:producto_id>")
@requiere_rol("dueño")
def etiqueta(producto_id):
    db = get_client_db()
    producto = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

    if producto is None or not producto["codigo_barras"]:
        flash("Este producto no tiene código de barras cargado.", "warning")
        return redirect(url_for("stock.index"))

    return render_template("stock/etiqueta.html", producto=producto)
