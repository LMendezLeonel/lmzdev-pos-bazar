from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from app.auth.decorators import requiere_rol
from app.db import get_client_db

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.route("/")
@requiere_rol("dueño")
def index():
    db = get_client_db()
    lista = db.execute("SELECT * FROM usuarios ORDER BY activo DESC, nombre").fetchall()
    return render_template("usuarios/lista.html", usuarios=lista)


@bp.route("/nuevo", methods=["GET", "POST"])
@requiere_rol("dueño")
def nuevo():
    if request.method == "GET":
        return render_template("usuarios/form.html", usuario=None)

    nombre = request.form.get("nombre", "").strip()
    usuario = request.form.get("usuario", "").strip()
    password = request.form.get("password", "")
    rol = request.form.get("rol")

    if not all([nombre, usuario, password, rol]) or rol not in ("dueño", "empleado", "vendedor"):
        flash("Completá todos los campos correctamente.", "warning")
        return redirect(url_for("usuarios.nuevo"))

    db = get_client_db()
    try:
        db.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, usuario, generate_password_hash(password), rol)
        )
        db.commit()
        flash(f"Usuario '{usuario}' creado con rol {rol}.", "success")
        return redirect(url_for("usuarios.index"))
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            flash("Ya existe un usuario con ese nombre de usuario.", "danger")
        else:
            flash("No se pudo crear el usuario.", "danger")
        return redirect(url_for("usuarios.nuevo"))


@bp.route("/editar/<int:usuario_id>", methods=["GET", "POST"])
@requiere_rol("dueño")
def editar(usuario_id):
    db = get_client_db()
    u = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()

    if u is None:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("usuarios.index"))

    if request.method == "GET":
        return render_template("usuarios/form.html", usuario=u)

    nombre = request.form.get("nombre", "").strip()
    rol = request.form.get("rol")
    password = request.form.get("password", "").strip()

    if password:
        db.execute(
            "UPDATE usuarios SET nombre=?, rol=?, password_hash=? WHERE id=?",
            (nombre, rol, generate_password_hash(password), usuario_id)
        )
    else:
        db.execute("UPDATE usuarios SET nombre=?, rol=? WHERE id=?", (nombre, rol, usuario_id))

    db.commit()
    flash(f"Usuario '{u['usuario']}' actualizado.", "success")
    return redirect(url_for("usuarios.index"))


@bp.route("/activar/<int:usuario_id>", methods=["POST"])
@requiere_rol("dueño")
def activar(usuario_id):
    if usuario_id == session.get("user_id"):
        flash("No podés desactivar tu propio usuario.", "warning")
        return redirect(url_for("usuarios.index"))

    db = get_client_db()
    u = db.execute("SELECT activo FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if u:
        db.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (0 if u["activo"] else 1, usuario_id))
        db.commit()
    return redirect(url_for("usuarios.index"))
