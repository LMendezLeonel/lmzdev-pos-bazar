from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.auth.decorators import requiere_rol
from app.db import get_client_db

bp = Blueprint("notas", __name__, url_prefix="/notas")


@bp.route("/")
@requiere_rol("dueño", "empleado")
def index():
    db = get_client_db()
    notas = db.execute(
        """SELECT n.*, u.nombre AS autor
           FROM notas n LEFT JOIN usuarios u ON n.usuario_id = u.id
           ORDER BY n.hecha ASC, n.fecha_creacion DESC"""
    ).fetchall()
    return render_template("notas/index.html", notas=notas)


@bp.route("/nueva", methods=["POST"])
@requiere_rol("dueño", "empleado")
def nueva():
    contenido = request.form.get("contenido", "").strip()
    if contenido:
        db = get_client_db()
        db.execute(
            "INSERT INTO notas (contenido, usuario_id) VALUES (?, ?)",
            (contenido, session["user_id"])
        )
        db.commit()
    return redirect(url_for("notas.index"))


@bp.route("/marcar/<int:nota_id>", methods=["POST"])
@requiere_rol("dueño", "empleado")
def marcar(nota_id):
    db = get_client_db()
    nota = db.execute("SELECT hecha FROM notas WHERE id = ?", (nota_id,)).fetchone()
    if nota:
        db.execute("UPDATE notas SET hecha = ? WHERE id = ?", (0 if nota["hecha"] else 1, nota_id))
        db.commit()
    return redirect(url_for("notas.index"))


@bp.route("/eliminar/<int:nota_id>", methods=["POST"])
@requiere_rol("dueño", "empleado")
def eliminar(nota_id):
    db = get_client_db()
    db.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
    db.commit()
    return redirect(url_for("notas.index"))
