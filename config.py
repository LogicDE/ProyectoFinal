import os
from datetime import timedelta

class Config:
    # Configuración de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-secreta-muy-segura'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Configuración de la base de datos
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', '')
    MYSQL_DB = os.environ.get('DB_NAME', 'proyecto_final')

    
    # Configuración de subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit

class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_DATABASE_CHARSET = 'utf8mb4'

class ProductionConfig(Config):
    DEBUG = False
    # Configuración de producción (usar variables de entorno en producción)
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
