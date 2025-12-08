"""
Configuración Centralizada del Sistema UniPlanner

Este módulo contiene todas las configuraciones del sistema, separadas
por ambientes (desarrollo, producción) siguiendo el patrón de configuración
recomendado por Flask.

"""

import os
from datetime import timedelta
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

class Config:
    """
    Clase base de configuración con valores comunes para todos los ambientes.
    
    Attributes:
        SECRET_KEY (str): Clave secreta para JWT y sesiones
        DATABASE_URL (str): URL de conexión a PostgreSQL
        JWT_EXPIRATION (timedelta): Tiempo de expiración de tokens
        MAX_CONTENT_LENGTH (int): Tamaño máximo de archivos subidos
    """
    
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    
    # Base de datos PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Seguridad JWT
    JWT_EXPIRATION = timedelta(hours=24)
    JWT_ALGORITHM = 'HS256'
    
    # Límites de la aplicación
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    
    # CORS (Cross-Origin Resource Sharing)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Configuración de recomendaciones
    RECOMENDACIONES_LIMITE_DEFAULT = 5
    TAREAS_URGENTES_DIAS = 3
    
    # Configuración de estudio
    HORAS_ESTUDIO_INTENSIVO = 6
    HORAS_ESTUDIO_MODERADO = 4
    HORAS_ESTUDIO_LEVE = 2.5
    
    @staticmethod
    def init_app(app):
        """
        Inicializa configuraciones específicas de la aplicación.
        
        Args:
            app: Instancia de Flask
        """
        pass


class DevelopmentConfig(Config):
    """
    Configuración para ambiente de desarrollo.
    
    Activa el modo debug y usa configuraciones más permisivas
    para facilitar el desarrollo.
    """
    DEBUG = True
    TESTING = False
    
    # En desarrollo, tokens pueden durar más
    JWT_EXPIRATION = timedelta(days=7)


class ProductionConfig(Config):
    """
    Configuración para ambiente de producción.
    
    Desactiva debug y usa configuraciones de seguridad estrictas.
    """
    DEBUG = False
    TESTING = False
    
    # En producción, validar que SECRET_KEY sea segura
    @classmethod
    def init_app(cls, app):
        """
        Validaciones adicionales para producción.
        
        Args:
            app: Instancia de Flask
            
        Raises:
            ValueError: Si SECRET_KEY no está configurada adecuadamente
        """
        Config.init_app(app)
        
        # Validar SECRET_KEY
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError(
                "⚠️  CRITICAL: Debes configurar SECRET_KEY en producción"
            )
        
        # Validar DATABASE_URL
        if not cls.DATABASE_URL:
            raise ValueError(
                "⚠️  CRITICAL: DATABASE_URL no está configurada"
            )


class TestingConfig(Config):
    """
    Configuración para pruebas automatizadas.
    
    Usa base de datos en memoria y configuraciones aisladas.
    """
    TESTING = True
    DEBUG = True
    
    # Usar base de datos de prueba
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    
    # JWT con expiración muy corta para testing
    JWT_EXPIRATION = timedelta(minutes=5)


# Diccionario de configuraciones disponibles
config_by_name: Dict[str, type] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Config:
    """
    Obtiene la configuración según el ambiente especificado.
    
    Args:
        config_name: Nombre del ambiente ('development', 'production', 'testing')
                     Si es None, usa la variable de entorno FLASK_ENV
    
    Returns:
        Instancia de la clase de configuración correspondiente
    
    Example:
        >>> config = get_config('production')
        >>> print(config.DEBUG)
        False
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config_by_name.get(config_name, DevelopmentConfig)


# Constantes de la aplicación
class AppConstants:
    """
    Constantes usadas en toda la aplicación.
    
    Centralizar constantes facilita el mantenimiento y evita
    valores mágicos dispersos en el código.
    """
    
    # Estados de materias
    ESTADO_ACTIVO = 'activo'
    ESTADO_CANCELADO = 'cancelado'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_REPROBADO = 'reprobado'
    
    # Tipos de tareas
    TIPOS_TAREA = ['parcial', 'final', 'proyecto', 'taller', 'exposicion', 'lectura', 'laboratorio']
    
    # Tipos de estudio
    TIPOS_ESTUDIO = ['intensivo', 'moderado', 'leve']
    
    # Niveles de dificultad (1-5)
    DIFICULTAD_MIN = 1
    DIFICULTAD_MAX = 5
    
    # Rangos de créditos
    CREDITOS_MIN = 1
    CREDITOS_MAX = 6
    
    # Mensajes de error comunes
    ERROR_AUTENTICACION = 'Credenciales incorrectas'
    ERROR_TOKEN_INVALIDO = 'Token inválido o expirado'
    ERROR_USUARIO_NO_ENCONTRADO = 'Usuario no encontrado'
    ERROR_PERMISO_DENEGADO = 'No tienes permiso para realizar esta acción'
    
    # Mensajes de éxito
    SUCCESS_REGISTRO = 'Usuario registrado exitosamente'
    SUCCESS_LOGIN = 'Inicio de sesión exitoso'
    SUCCESS_TAREA_CREADA = 'Tarea creada exitosamente'
    SUCCESS_TAREA_COMPLETADA = 'Tarea completada exitosamente'


if __name__ == '__main__':
    print("Probando configuraciones...\n")
    
    for env_name, config_class in config_by_name.items():
        print(f"Ambiente: {env_name}")
        print(f"  DEBUG: {config_class.DEBUG}")
        print(f"  JWT_EXPIRATION: {config_class.JWT_EXPIRATION}")
        print(f"  LOG_LEVEL: {config_class.LOG_LEVEL}")
        print()