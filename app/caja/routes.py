from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.auth.decorators import requiere_rol
from app.db import get_client_db, obtener_caja_abierta

bp = Blueprint("caja", __name__, url_prefix="/caja")


@bp.route("/")
@requiere_rol("dueño", "empleado")
def index():
    caja = obtener_caja_abierta()
    resumen = None

    if caja:
        db = get_client_db()
        resumen = db.execute(
            """SELECT medio_pago, COUNT(*) as cantidad, SUM(total) as total
               FROM ventas WHERE caja_id = ? GROUP BY medio_pago""",
            (caja["id"],)
        ).fetchall()

    return render_template("caja/index.html", caja=caja, resumen=resumen)


@bp.route("/abrir", methods=["POST"])
@requiere_rol("dueño", "empleado")
def abrir():
    if obtener_caja_abierta():
        flash("Ya hay una caja abierta.", "warning")
        return redirect(url_for("caja.index"))

    monto_inicial = float(request.form.get("monto_inicial", 0) or 0)

    db = get_client_db()
    db.execute(
        "INSERT INTO caja (monto_inicial, usuario_id, estado) VALUES (?, ?, 'abierta')",
        (monto_inicial, session["user_id"])
    )
    db.commit()
    flash("Caja abierta.", "success")
    return redirect(url_for("pos.index"))


@bp.route("/cerrar", methods=["POST"])
@requiere_rol("dueño", "empleado")
def cerrar():
    caja = obtener_caja_abierta()
    if caja is None:
        flash("No hay caja abierta.", "warning")
        return redirect(url_for("caja.index"))

    monto_final = float(request.form.get("monto_final", 0) or 0)

    db = get_client_db()
    db.execute(
        "UPDATE caja SET fecha_cierre = CURRENT_TIMESTAMP, monto_final = ?, estado = 'cerrada' WHERE id = ?",
        (monto_final, caja["id"])
    )
    db.commit()
    flash("Caja cerrada.", "info")
    return redirect(url_for("caja.index"))
