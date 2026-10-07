import os
from datetime import timedelta

# Carpeta donde vive el código (se reemplaza en cada deploy — solo para archivos fuente)
CODE_DIR = os.path.abspath(os.path.dirname(__file__))

# Carpeta donde viven los DATOS (bases de datos). Es DISTINTA de CODE_DIR a propósito:
# en Railway (o cualquier hosting), el código se reemplaza en cada deploy, pero un
# volumen persistente montado en DATA_DIR sobrevive entre deploys.
# En tu compu, si no configurás DATA_DIR, usa la misma carpeta del proyecto (como hasta ahora).
DATA_DIR = os.environ.get("DATA_DIR", CODE_DIR)

# Plantillas SQL (van con el código, se versionan en git)
MASTER_SCHEMA_PATH = os.path.join(CODE_DIR, "master_schema.sql")
SCHEMA_SQL_PATH = os.path.join(CODE_DIR, "schema.sql")

# Tu base: registro de todos los clientes (bazares) dados de alta — vive en DATA_DIR
MASTER_DB_PATH = os.path.join(DATA_DIR, "master.db")

# Carpeta donde vive el .db de cada cliente — vive en DATA_DIR
CLIENTS_DB_DIR = os.path.join(DATA_DIR, "clients_db")

# Plantilla vacía que se clona al dar de alta un cliente nuevo
TEMPLATE_DB_PATH = os.path.join(CLIENTS_DB_DIR, "_template.db")

# IMPORTANTE antes de subir a producción:
# Estas dos claves se leen de variables de entorno si existen.
# En tu compu, si no configurás nada, usa los valores por defecto (sirve para probar).
# En el hosting (Render/Railway/etc.), configurá SECRET_KEY y SUPERADMIN_PASSWORD
# como variables de entorno reales, con valores largos y aleatorios.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-clave-cambiar-en-produccion")
SUPERADMIN_PASSWORD = os.environ.get("SUPERADMIN_PASSWORD", "cambiar-esta-clave")

# Cuánto dura la sesión cuando el usuario tilda "Mantener sesión iniciada"
PERMANENT_SESSION_LIFETIME = timedelta(days=30)

# --- Seguridad de cookies ---
# SESSION_COOKIE_SECURE: la cookie de sesión solo viaja por HTTPS.
# En tu compu (http://127.0.0.1) tiene que estar en 0, si no el login no funciona.
# En Railway (o cualquier hosting con HTTPS) hay que ponerla en 1.
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# DEBUG: apagado por defecto (seguro). En tu compu, si querés recarga automática
# al guardar cambios, corré con la variable de entorno FLASK_DEBUG=1.
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# --- Imágenes de productos ---
# Se guardan en DATA_DIR/uploads/<cliente>/ (separado por cliente, y fuera del código).
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
# Tamaño máximo de archivo subido (el servidor lo redimensiona igual a 1000px)
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
IMAGEN_MAX_LADO = 1000

# --- Venta en cuotas ---
# Se pide de entrega el 50% del precio; el otro 50% lleva 80% de interés y se divide en 3 cuotas.
CUOTAS_ENTREGA_PCT = 50
CUOTAS_INTERES_PCT = 80
CUOTAS_CANTIDAD = 3
