import random
import re
from flask import (Blueprint, render_template, request, redirect, url_for, flash, jsonify,
                   send_from_directory, abort)

from app.auth.decorators import login_required, requiere_rol
from app.db import get_client_db
from app.productos_util import (calcular_cuotas, guardar_imagen, borrar_imagen,
                                carpeta_imagenes_cliente)

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
    cuotas = {p["id"]: calcular_cuotas(p["precio_venta"]) for p in productos}
    return render_template("stock/lista.html", productos=productos,
                           categorias_presentes=categorias_presentes, cuotas=cuotas)


@bp.route("/imagen/<int:producto_id>")
@login_required
def imagen(producto_id):
    """Sirve la imagen del producto (cualquier rol logueado, solo de SU cliente). ?descargar=1 la baja."""
    db = get_client_db()
    p = db.execute("SELECT nombre, imagen FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if p is None or not p["imagen"] or not re.fullmatch(r"[a-f0-9]{16}\.jpg", p["imagen"]):
        abort(404)
    descargar = request.args.get("descargar") == "1"
    nombre_dl = re.sub(r"[^A-Za-z0-9_-]+", "_", p["nombre"]).strip("_") or "producto"
    resp = send_from_directory(carpeta_imagenes_cliente(), p["imagen"], mimetype="image/jpeg",
                               as_attachment=descargar, download_name=f"{nombre_dl}.jpg",
                               max_age=3600)
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp


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

    imagen_nombre = None
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        try:
            imagen_nombre = guardar_imagen(archivo)
        except ValueError as e:
            flash(str(e), "warning")
            return redirect(url_for("stock.nuevo"))

    try:
        db.execute(
            """INSERT INTO productos
               (nombre, codigo_barras, categoria_id, precio_venta, precio_costo, stock_actual, stock_minimo, imagen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nombre, codigo_barras, categoria_id, precio_venta, precio_costo, stock_actual, stock_minimo,
             imagen_nombre)
        )
        db.commit()
        flash(f"Producto '{nombre}' creado.", "success")
    except Exception as e:
        borrar_imagen(imagen_nombre)
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

    imagen_nombre = producto["imagen"]
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        try:
            nueva = guardar_imagen(archivo)
            borrar_imagen(imagen_nombre)
            imagen_nombre = nueva
        except ValueError as e:
            flash(str(e), "warning")
            return redirect(url_for("stock.editar", producto_id=producto_id))
    elif request.form.get("quitar_imagen"):
        borrar_imagen(imagen_nombre)
        imagen_nombre = None

    try:
        db.execute(
            """UPDATE productos SET nombre=?, codigo_barras=?, categoria_id=?, precio_venta=?,
               precio_costo=?, stock_actual=?, stock_minimo=?, imagen=? WHERE id=?""",
            (nombre, codigo_barras, categoria_id, precio_venta, precio_costo,
             stock_actual, stock_minimo, imagen_nombre, producto_id)
        )
        db.commit()
    except Exception as e:
        flash("Ya existe un producto con ese código de barras." if "UNIQUE" in str(e)
              else "Error al guardar el producto.", "danger")
        return redirect(url_for("stock.editar", producto_id=producto_id))
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
