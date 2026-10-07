"""Utilidades de producto: imágenes (por cliente) y cálculo de cuotas."""
import os
import re
import secrets

from flask import current_app, session
from PIL import Image, ImageOps


# ---------------- CUOTAS ----------------

def calcular_cuotas(precio):
    """
    Entrega = X% del precio (50%). El resto lleva interés (80%) y se divide en N cuotas (3).
    Ej: precio 100000 -> entrega 50000, saldo con interés 90000, 3 cuotas de 30000, total 140000.
    """
    cfg = current_app.config
    n = int(cfg.get("CUOTAS_CANTIDAD", 3))
    entrega = precio * cfg.get("CUOTAS_ENTREGA_PCT", 50) / 100
    saldo = precio - entrega
    saldo_con_interes = saldo * (1 + cfg.get("CUOTAS_INTERES_PCT", 80) / 100)
    cuota = saldo_con_interes / n
    return {
        "entrega": round(entrega, 2),
        "saldo": round(saldo, 2),
        "saldo_con_interes": round(saldo_con_interes, 2),
        "cantidad": n,
        "cuota": round(cuota, 2),
        "total": round(entrega + saldo_con_interes, 2),
        "interes_pct": cfg.get("CUOTAS_INTERES_PCT", 80),
    }


# ---------------- IMÁGENES ----------------

def carpeta_imagenes_cliente():
    """Carpeta de imágenes del cliente logueado (una por cliente = aislamiento)."""
    base = re.sub(r"[^a-z0-9_-]", "_", os.path.splitext(session["db_filename"])[0].lower())
    carpeta = os.path.join(current_app.config["UPLOADS_DIR"], base)
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def guardar_imagen(archivo):
    """
    Valida con Pillow que sea una imagen real, corrige rotación, achica a 1000px y
    guarda como JPG. Devuelve el nombre de archivo guardado. Lanza ValueError si no sirve.
    """
    try:
        img = Image.open(archivo.stream)
        img.verify()
        archivo.stream.seek(0)
        img = Image.open(archivo.stream)
        formato = img.format
        img = ImageOps.exif_transpose(img)
    except Exception:
        raise ValueError("El archivo no es una imagen válida (usá JPG, PNG o WEBP).")

    if formato not in ("JPEG", "PNG", "WEBP"):
        raise ValueError("Formato no permitido. Usá JPG, PNG o WEBP.")

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.split()[-1])
        img = fondo
    else:
        img = img.convert("RGB")

    lado = current_app.config.get("IMAGEN_MAX_LADO", 1000)
    img.thumbnail((lado, lado))

    nombre = f"{secrets.token_hex(8)}.jpg"
    img.save(os.path.join(carpeta_imagenes_cliente(), nombre), "JPEG", quality=85, optimize=True)
    return nombre


def borrar_imagen(nombre):
    if not nombre or not re.fullmatch(r"[a-f0-9]{16}\.jpg", nombre):
        return
    try:
        os.remove(os.path.join(carpeta_imagenes_cliente(), nombre))
    except OSError:
        pass
