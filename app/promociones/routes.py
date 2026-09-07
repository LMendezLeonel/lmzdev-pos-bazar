from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.auth.decorators import requiere_rol, login_required
from app.db import get_client_db

bp = Blueprint("promociones", __name__, url_prefix="/promociones")


@bp.route("/")
@requiere_rol("dueño")
def index():
    db = get_client_db()
    promos = db.execute("SELECT * FROM promociones ORDER BY activa DESC, nombre").fetchall()
    return render_template("promociones/lista.html", promos=promos)


@bp.route("/nuevo", methods=["GET", "POST"])
@requiere_rol("dueño")
def nuevo():
    if request.method == "GET":
        return render_template("promociones/form.html", promo=None)

    nombre = request.form.get("nombre", "").strip()
    tipo = request.form.get("tipo")
    valor = float(request.form.get("valor", 0) or 0)
    medio_pago = request.form.get("medio_pago") or None

    if not nombre or tipo not in ("porcentaje", "monto_fijo") or valor <= 0:
        flash("Completá los datos de la promoción correctamente.", "warning")
        return redirect(url_for("promociones.nuevo"))

    db = get_client_db()
    db.execute(
        "INSERT INTO promociones (nombre, tipo, valor, medio_pago) VALUES (?, ?, ?, ?)",
        (nombre, tipo, valor, medio_pago)
    )
    db.commit()
    flash(f"Promoción '{nombre}' creada.", "success")
    return redirect(url_for("promociones.index"))


@bp.route("/editar/<int:promo_id>", methods=["GET", "POST"])
@requiere_rol("dueño")
def editar(promo_id):
    db = get_client_db()
    promo = db.execute("SELECT * FROM promociones WHERE id = ?", (promo_id,)).fetchone()

    if promo is None:
        flash("Promoción no encontrada.", "danger")
        return redirect(url_for("promociones.index"))

    if request.method == "GET":
        return render_template("promociones/form.html", promo=promo)

    nombre = request.form.get("nombre", "").strip()
    tipo = request.form.get("tipo")
    valor = float(request.form.get("valor", 0) or 0)
    medio_pago = request.form.get("medio_pago") or None

    db.execute(
        "UPDATE promociones SET nombre=?, tipo=?, valor=?, medio_pago=? WHERE id=?",
        (nombre, tipo, valor, medio_pago, promo_id)
    )
    db.commit()
    flash(f"Promoción '{nombre}' actualizada.", "success")
    return redirect(url_for("promociones.index"))


@bp.route("/activar/<int:promo_id>", methods=["POST"])
@requiere_rol("dueño")
def activar(promo_id):
    db = get_client_db()
    promo = db.execute("SELECT activa FROM promociones WHERE id = ?", (promo_id,)).fetchone()
    nueva_activa = 0 if promo["activa"] else 1
    db.execute("UPDATE promociones SET activa = ? WHERE id = ?", (nueva_activa, promo_id))
    db.commit()
    flash("Promoción actualizada.", "info")
    return redirect(url_for("promociones.index"))


@bp.route("/disponibles")
@login_required
def disponibles():
    """Usado por el POS: promociones activas, en JSON, para armar el selector."""
    db = get_client_db()
    promos = db.execute(
        "SELECT id, nombre, tipo, valor, medio_pago FROM promociones WHERE activa = 1"
    ).fetchall()
    return jsonify([dict(p) for p in promos])
