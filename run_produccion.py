"""
Servidor de produccion para empleados_abm.
Usa Waitress como servidor WSGI productivo en Windows.
Sirve la aplicacion bajo el prefijo /sge definido por DispatcherMiddleware.
"""
from waitress import serve
from app import create_prefixed_app
from config.settings import Config


application = create_prefixed_app()


if __name__ == '__main__':
    print('Iniciando servidor de produccion con Waitress...')
    print(f"Escuchando en http://0.0.0.0:5000/sge ({Config.SERVER_THREADS} hilos)")
    print('Presiona CTRL+C para detener.')

    serve(
        application,
        host='0.0.0.0',
        port=5000,
        threads=Config.SERVER_THREADS,
        asyncore_use_poll=True,
        clear_untrusted_proxy_headers=True,
    )
