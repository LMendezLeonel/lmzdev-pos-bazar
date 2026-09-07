import sqlite3
import shutil
import os
from flask import g, session, current_app


# ============================================================
# MASTER DB — tu base: qué clientes existen y su archivo .db
# ============================================================

def get_master_db():
    """Conexión a master.db (se reutiliza durante el request con 'g')."""
    if "master_db" not in g:
        g.master_db = sqlite3.connect(current_app.config["MASTER_DB_PATH"])
        g.master_db.row_factory = sqlite3.Row
        g.master_db.execute("PRAGMA foreign_keys = ON")
    return g.master_db


def buscar_cliente_por_usuario(usuario_admin):
    """Dado el usuario de login, devuelve la fila del cliente (bazar) en master.db."""
    db = get_master_db()
    return db.execute(
        "SELECT * FROM clientes WHERE usuario_admin = ? AND activo = 1",
        (usuario_admin,)
    ).fetchone()


def _ruta_segura_cliente(db_filename):
    """
    Arma la ruta al .db de un cliente y verifica que no se escape de la carpeta
    clients_db/ (protección contra path traversal, ej: '../../etc/algo').
    """
    ruta = os.path.abspath(os.path.join(current_app.config["CLIENTS_DB_DIR"], db_filename))
    carpeta_clientes = os.path.abspath(current_app.config["CLIENTS_DB_DIR"])
    if not ruta.startswith(carpeta_clientes + os.sep):
        raise ValueError("Nombre de archivo de cliente inválido.")
    return ruta


def crear_cliente(nombre_bazar, db_filename, usuario_admin):
    """
    Alta de un cliente nuevo:
    1. Clona _template.db con el nombre de archivo indicado
    2. Registra el cliente en master.db
    Se usa desde el panel admin (app/admin/routes.py).
    """
    destino = _ruta_segura_cliente(db_filename)

    if os.path.exists(destino):
        raise FileExistsError(f"Ya existe una base con el nombre '{db_filename}'")

    shutil.copyfile(current_app.config["TEMPLATE_DB_PATH"], destino)

    db = get_master_db()
    db.execute(
        "INSERT INTO clientes (nombre_bazar, db_filename, usuario_admin) VALUES (?, ?, ?)",
        (nombre_bazar, db_filename, usuario_admin)
    )
    db.commit()


# ============================================================
# CLIENT DB — la base del bazar logueado (aislada por sesión)
# ============================================================

def get_client_db():
    """
    Conexión al .db del bazar actual.
    Requiere que 'db_filename' ya esté guardado en session (se setea en el login).
    """
    if "db_filename" not in session:
        raise RuntimeError("No hay cliente en sesión. El login debe setear session['db_filename'].")

    if "client_db" not in g:
        ruta = _ruta_segura_cliente(session["db_filename"])
        g.client_db = sqlite3.connect(ruta)
        g.client_db.row_factory = sqlite3.Row
        g.client_db.execute("PRAGMA foreign_keys = ON")

    return g.client_db


# ============================================================
# Cierre de conexiones al terminar cada request
# ============================================================

def close_db(e=None):
    master_db = g.pop("master_db", None)
    if master_db is not None:
        master_db.close()

    client_db = g.pop("client_db", None)
    if client_db is not None:
        client_db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    inicializar_almacenamiento(app)


def inicializar_almacenamiento(app):
    """
    Se corre al arrancar la app. Si es la primera vez (volumen vacío,
    típico del primer deploy), crea master.db y la plantilla de clientes.
    Si ya existen (deploys siguientes, o en tu compu), no toca nada.
    """
    os.makedirs(app.config["CLIENTS_DB_DIR"], exist_ok=True)

    if not os.path.exists(app.config["MASTER_DB_PATH"]):
        conn = sqlite3.connect(app.config["MASTER_DB_PATH"])
        with open(app.config["MASTER_SCHEMA_PATH"], "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()

    if not os.path.exists(app.config["TEMPLATE_DB_PATH"]):
        conn = sqlite3.connect(app.config["TEMPLATE_DB_PATH"])
        with open(app.config["SCHEMA_SQL_PATH"], "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()


def conectar_client_db_directo(db_filename):
    """
    Conexión directa a un .db de cliente, SIN pasar por session.
    Se usa desde el panel admin al crear el primer usuario Dueño
    de un cliente recién dado de alta (todavía no hay sesión de ese cliente).
    Quien la use es responsable de cerrarla.
    """
    ruta = _ruta_segura_cliente(db_filename)
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def obtener_caja_abierta():
    """Devuelve la fila de la caja abierta actual del cliente en sesión, o None."""
    db = get_client_db()
    return db.execute(
        "SELECT * FROM caja WHERE estado = 'abierta' ORDER BY id DESC LIMIT 1"
    ).fetchone()
