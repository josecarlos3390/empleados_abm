import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10485760))
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'empleados_db')
    DB_USER = os.getenv('DB_USER', 'bagit')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'bagit!.')

    # Configuración de SQL Server (facturación / transacciones)
    SQLSERVER_HOST = os.getenv('SQLSERVER_HOST', 'localhost')
    SQLSERVER_PORT = int(os.getenv('SQLSERVER_PORT', 1433))
    SQLSERVER_DB = os.getenv('SQLSERVER_DB', '')
    SQLSERVER_USER = os.getenv('SQLSERVER_USER', '')
    SQLSERVER_PASSWORD = os.getenv('SQLSERVER_PASSWORD', '')

    # Limite de tickets por impresion para evitar abuso o saturacion
    MAX_TICKETS_POR_IMPRESION = int(os.getenv('MAX_TICKETS_POR_IMPRESION', 50))
