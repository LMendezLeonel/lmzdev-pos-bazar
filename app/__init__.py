from flask import Flask, redirect, url_for
from flask_wtf import CSRFProtect

from app import db as db_module

csrf = CSRFProtect()


def create_app(config_object="config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db_module.init_app(app)
    csrf.init_app(app)

    from app.auth.routes import bp as auth_bp
    from app.pos.routes import bp as pos_bp
    from app.stock.routes import bp as stock_bp
    from app.caja.routes import bp as caja_bp
    from app.reportes.routes import bp as reportes_bp
    from app.admin.routes import bp as admin_bp
    from app.promociones.routes import bp as promociones_bp
    from app.control.routes import bp as control_bp
    from app.notas.routes import bp as notas_bp
    from app.usuarios.routes import bp as usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(caja_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(promociones_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(notas_bp)
    app.register_blueprint(usuarios_bp)

    @app.route("/")
    def raiz():
        return redirect(url_for("auth.login"))

    return app
