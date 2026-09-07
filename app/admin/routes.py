import re
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash

from app.db import get_master_db, crear_cliente, conectar_client_db_directo
from app.rate_limit import esta_bloqueado, registrar_intento_fallido, limpiar_intentos

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Solo letras, números, guion y guion bajo. Nada de "/", "..", espacios, etc.
CODIGO_NEGOCIO_VALIDO = re.compile(r"^[a-z0-9_-]{3,40}$")


def requiere_superadmin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_superadmin"):
            flash("Acceso restringido.", "danger")
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return wrapper


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("is_superadmin"):
            return redirect(url_for("admin.index"))
        return render_template("admin/login.html")

    password = request.form.get("password", "")
    ip = request.remote_addr

    if esta_bloqueado(ip):
        flash("Demasiados intentos fallidos. Esperá unos minutos antes de volver a intentar.", "danger")
        return redirect(url_for("admin.login"))

    if password == current_app.config["SUPERADMIN_PASSWORD"]:
        limpiar_intentos(ip)
        session["is_superadmin"] = True
        return redirect(url_for("admin.index"))

    registrar_intento_fallido(ip)
    flash("Clave incorrecta.", "danger")
    return redirect(url_for("admin.login"))


@bp.route("/logout")
def logout():
    session.pop("is_superadmin", None)
    return redirect(url_for("admin.login"))


@bp.route("/")
@requiere_superadmin
def index():
    db = get_master_db()
    clientes = db.execute("SELECT * FROM clientes ORDER BY fecha_alta DESC").fetchall()
    return render_template("admin/index.html", clientes=clientes)


@bp.route("/nuevo", methods=["GET", "POST"])
@requiere_superadmin
def nuevo():
    if request.method == "GET":
        return render_template("admin/nuevo.html")

    nombre_bazar = request.form.get("nombre_bazar", "").strip()
    codigo_negocio = request.form.get("codigo_negocio", "").strip().lower()
    usuario_dueno = request.form.get("usuario_dueno", "").strip()
    password_dueno = request.form.get("password_dueno", "")
    nombre_dueno = request.form.get("nombre_dueno", "").strip()

    if not all([nombre_bazar, codigo_negocio, usuario_dueno, password_dueno, nombre_dueno]):
        flash("Completá todos los campos.", "warning")
        return redirect(url_for("admin.nuevo"))

    if not CODIGO_NEGOCIO_VALIDO.match(codigo_negocio):
        flash("El código de negocio solo puede tener letras minúsculas, números, guiones y guion bajo (3-40 caracteres).", "danger")
        return redirect(url_for("admin.nuevo"))

    db_filename = f"{codigo_negocio}.db"

    try:
        # 1. Clona _template.db y registra el cliente en master.db
        crear_cliente(nombre_bazar, db_filename, usuario_dueno)

        # 2. Crea el primer usuario (Dueño) dentro del .db recién clonado
        conn = conectar_client_db_directo(db_filename)
        conn.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol) VALUES (?, ?, ?, 'dueño')",
            (nombre_dueno, usuario_dueno, generate_password_hash(password_dueno))
        )
        conn.commit()
        conn.close()

        flash(f"Cliente '{nombre_bazar}' creado. Código de negocio: {codigo_negocio}", "success")
        return redirect(url_for("admin.index"))

    except FileExistsError:
        flash("Ya existe un cliente con ese código de negocio.", "danger")
        return redirect(url_for("admin.nuevo"))
