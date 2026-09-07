"""
Límite simple de intentos de login por IP, para frenar ataques de fuerza bruta.
Guardado en memoria (se reinicia si el servidor se reinicia) — suficiente para
este proyecto, que corre como un solo proceso.
"""
import time

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 5 * 60  # 5 minutos

_intentos_fallidos = {}  # { ip: [timestamp1, timestamp2, ...] }


def _limpiar_viejos(ip):
    ahora = time.time()
    _intentos_fallidos[ip] = [t for t in _intentos_fallidos.get(ip, []) if ahora - t < VENTANA_SEGUNDOS]


def esta_bloqueado(ip):
    _limpiar_viejos(ip)
    return len(_intentos_fallidos.get(ip, [])) >= MAX_INTENTOS


def registrar_intento_fallido(ip):
    _limpiar_viejos(ip)
    _intentos_fallidos.setdefault(ip, []).append(time.time())


def limpiar_intentos(ip):
    _intentos_fallidos.pop(ip, None)
