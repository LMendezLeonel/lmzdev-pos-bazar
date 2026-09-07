import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash

from app.db import get_master_db, get_client_db
from app.rate_limit import esta_bloqueado, registrar_intento_fallido, limpiar_intentos

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("pos.index"))
        return render_template("auth/login.html")

    codigo_negocio = request.form.get("codigo_negocio", "").strip().lower()
    usuario = request.form.get("usuario", "").strip()
    password = request.form.get("password", "")
    mantener_sesion = request.form.get("mantener_sesion") == "on"

    ip = request.remote_addr
    if esta_bloqueado(ip):
        flash("Demasiados intentos fallidos. Esperá unos minutos antes de volver a intentar.", "danger")
        return redirect(url_for("auth.login"))

    if not codigo_negocio or not usuario or not password:
        flash("Completá todos los campos.", "warning")
        return redirect(url_for("auth.login"))

    # 1. Buscar el bazar por su código de negocio en master.db
    db_filename = f"{codigo_negocio}.db"
    master_db = get_master_db()
    cliente = master_db.execute(
        "SELECT * FROM clientes WHERE db_filename = ? AND activo = 1",
        (db_filename,)
    ).fetchone()

    if cliente is None:
        registrar_intento_fallido(ip)
        flash("Código de negocio incorrecto.", "danger")
        return redirect(url_for("auth.login"))

    # 2. Guardar el .db del cliente en sesión ANTES de consultar sus usuarios
    session["db_filename"] = db_filename

    # 3. Buscar el usuario dentro de la base de ESE cliente
    client_db = get_client_db()
    fila_usuario = client_db.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND activo = 1",
        (usuario,)
    ).fetchone()

    if fila_usuario is None or not check_password_hash(fila_usuario["password_hash"], password):
        session.clear()
        registrar_intento_fallido(ip)
        flash("Usuario o contraseña incorrectos.", "danger")
        return redirect(url_for("auth.login"))

    # 4. Login OK: completar la sesión
    limpiar_intentos(ip)
    session.permanent = mantener_sesion
    session["user_id"] = fila_usuario["id"]
    session["usuario"] = fila_usuario["usuario"]
    session["nombre"] = fila_usuario["nombre"]
    session["rol"] = fila_usuario["rol"]
    session["nombre_bazar"] = cliente["nombre_bazar"]

    flash(f"Bienvenido, {fila_usuario['nombre']}.", "success")
    return redirect(url_for("pos.index"))


@bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
