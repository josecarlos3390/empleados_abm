from flask import Flask, session, redirect
from config.settings import Config
from routes.auth_routes import auth_bp
from routes.empleados_routes import empleados_bp
from routes.usuarios_routes import usuarios_bp
from routes.tickets_routes import tickets_bp
import os
from datetime import datetime

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
from werkzeug.serving import run_simple


def create_flask_app():
    """Crea y configura la aplicación Flask principal (sin prefijo)."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    app.secret_key = app.config.get('SECRET_KEY', 'dev_secret')

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    # Crear tablas de tickets si no existen (ignorar errores de conexión transitorios)
    try:
        from db.tickets import crear_tabla_tickets, crear_tabla_reimpresiones
        crear_tabla_tickets()
        crear_tabla_reimpresiones()
    except Exception:
        app.logger.warning('No se pudieron crear las tablas de tickets', exc_info=True)

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(empleados_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(tickets_bp)

    # Inyectar datos globales
    @app.context_processor
    def inject_globals():
        user = session.get('user')

        def has_permission(perm):
            if not user:
                return False
            return perm == 'manage_users' and user.get('rol') == 'admin'

        return {
            'user': user,
            'has_permission': has_permission,
            'current_year': datetime.now().year
        }

    # Ruta por defecto dentro del prefijo /sge
    @app.route('/')
    def index():
        return redirect('/sge/empleados')

    return app


def create_prefixed_app():
    """
    Envuelve la app Flask para vivir bajo /sge usando DispatcherMiddleware.
    """
    base_app = create_flask_app()

    application = DispatcherMiddleware(
        Response("Not Found", status=404),
        {
            "/sge": base_app   # Prefijo global
        }
    )
    return application


if __name__ == '__main__':
    application = create_prefixed_app()

    # Servidor principal
    run_simple(
        hostname="0.0.0.0",
        port=5000,
        application=application,
        use_reloader=True,
        use_debugger=True
    )
