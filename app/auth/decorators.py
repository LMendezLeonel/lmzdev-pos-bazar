from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Exige que haya un usuario logueado (cualquier rol)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Tenés que iniciar sesión.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def requiere_rol(*roles_permitidos):
    """
    Exige un rol específico. Uso:
        @requiere_rol('dueño')
        @requiere_rol('dueño', 'empleado')
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Tenés que iniciar sesión.", "warning")
                return redirect(url_for("auth.login"))

            if session.get("rol") not in roles_permitidos:
                flash("No tenés permiso para acceder a esta sección.", "danger")
                return redirect(url_for("pos.index"))

            return f(*args, **kwargs)
        return wrapper
    return decorador
