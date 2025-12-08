"""
Sistema de Logging Profesional para UniPlanner

Implementa un sistema de logging estructurado con:
- Niveles apropiados de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Colores en consola para desarrollo
- Rotación automática de archivos
- Formato detallado con timestamps y contexto

Paradigma: Programación Estructurada
Autor: [Tu Nombre]
Fecha: 2025-01-08
Versión: 1.0.0
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict


class ColoredFormatter(logging.Formatter):
    """
    Formateador personalizado que agrega colores ANSI a los logs en consola.
    
    Facilita la identificación visual de diferentes niveles de log
    durante el desarrollo y debugging.
    
    Attributes:
        COLORS (dict): Mapeo de niveles de log a códigos ANSI de color
    
    Example:
        >>> formatter = ColoredFormatter()
        >>> handler.setFormatter(formatter)
    """
    
    # Códigos ANSI para colores en terminal
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """
        Formatea el registro de log con colores según el nivel.
        
        Args:
            record (logging.LogRecord): Registro de logging a formatear
            
        Returns:
            str: String formateado con colores ANSI si es terminal
        """
        # Obtener color según nivel de log
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        
        # Formatear el mensaje base usando el formatter padre
        log_message = super().format(record)
        
        # Agregar color solo si la salida es un terminal (no archivo)
        # os.isatty(2) verifica si stderr es un terminal
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            return f"{color}{log_message}{self.COLORS['RESET']}"
        
        return log_message


def setup_logger(
    name: str = 'uniplanner',
    log_level: str = 'INFO',
    log_to_file: bool = True,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    Configura y retorna un logger con handlers para consola y archivo.
    
    El sistema de logging incluye:
    - Salida a consola con colores (para desarrollo)
    - Archivo rotativo con límite de tamaño (para producción)
    - Formato estructurado con timestamp, nivel, módulo y mensaje
    
    Args:
        name (str): Nombre del logger (aparece en los logs)
        log_level (str): Nivel mínimo de logging 
                         ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file (bool): Si es True, guarda logs en archivo
        log_dir (str): Directorio donde guardar archivos de log
    
    Returns:
        logging.Logger: Instancia configurada del logger
    
    Raises:
        ValueError: Si log_level no es válido
        OSError: Si no se puede crear el directorio de logs
    
    Example:
        >>> logger = setup_logger('mi_app', 'DEBUG')
        >>> logger.info('Aplicación iniciada')
        >>> logger.error('Ocurrió un error', exc_info=True)
        
        >>> # Logger solo para consola
        >>> logger = setup_logger('test', 'DEBUG', log_to_file=False)
    """
    # Validar nivel de log
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    log_level = log_level.upper()
    
    if log_level not in valid_levels:
        raise ValueError(
            f"log_level debe ser uno de: {', '.join(valid_levels)}"
        )
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Evitar duplicación de handlers si el logger ya existe
    if logger.handlers:
        return logger
    
    # Formato detallado para logs
    # Incluye: fecha/hora | nivel | nombre:función:línea | mensaje
    log_format = (
        '%(asctime)s | '
        '%(levelname)-8s | '
        '%(name)s:%(funcName)s:%(lineno)d | '
        '%(message)s'
    )
    
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # ========== HANDLER PARA CONSOLA (con colores) ==========
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Usar formatter con colores para consola
    console_formatter = ColoredFormatter(
        log_format,
        datefmt=date_format
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ========== HANDLER PARA ARCHIVO (si está habilitado) ==========
    
    if log_to_file:
        try:
            # Crear directorio de logs si no existe
            os.makedirs(log_dir, exist_ok=True)
            
            # Nombre de archivo con fecha actual
            log_filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            log_filepath = os.path.join(log_dir, log_filename)
            
            # Handler con rotación automática
            # - Tamaño máximo: 10MB
            # - Mantiene 5 archivos de backup (total ~50MB)
            file_handler = RotatingFileHandler(
                log_filepath,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            # Archivo solo registra INFO en adelante (no DEBUG)
            file_handler.setLevel(logging.INFO)
            
            # Formato sin colores para archivos
            file_formatter = logging.Formatter(
                log_format,
                datefmt=date_format
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Log inicial indicando que archivo está activo
            logger.debug(f"Logging a archivo: {log_filepath}")
            
        except OSError as e:
            # Si no se puede crear archivo, continuar solo con consola
            logger.warning(
                f"No se pudo crear archivo de log: {e}. "
                "Continuando solo con logging a consola."
            )
        except Exception as e:
            logger.warning(f"Error configurando file handler: {e}")
    
    return logger


def log_request(logger: logging.Logger, request_data: Dict[str, str]):
    """
    Registra información de una petición HTTP de manera estructurada.
    
    Útil para auditoría, debugging y análisis de tráfico de la API.
    
    Args:
        logger (logging.Logger): Instancia del logger a usar
        request_data (dict): Diccionario con datos de la petición
            - method (str): Método HTTP (GET, POST, etc.)
            - path (str): Ruta del endpoint
            - user_id (int/str): ID del usuario (opcional)
            - ip (str): Dirección IP del cliente (opcional)
            - status (int): Código de respuesta HTTP (opcional)
    
    Example:
        >>> log_request(logger, {
        ...     'method': 'POST',
        ...     'path': '/api/tareas',
        ...     'user_id': 123,
        ...     'ip': '192.168.1.1',
        ...     'status': 201
        ... })
        2025-01-08 10:30:45 | INFO | REQUEST POST /api/tareas | User: 123 | IP: 192.168.1.1 | Status: 201
    """
    method = request_data.get('method', 'UNKNOWN')
    path = request_data.get('path', '/')
    user_id = request_data.get('user_id', 'anonymous')
    ip = request_data.get('ip', 'unknown')
    status = request_data.get('status', '')
    
    # Construir mensaje estructurado
    message = f"REQUEST {method} {path} | User: {user_id} | IP: {ip}"
    
    if status:
        message += f" | Status: {status}"
    
    logger.info(message)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict] = None
):
    """
    Registra un error con contexto adicional para debugging.
    
    Incluye el stack trace completo y contexto personalizado
    para facilitar la identificación y resolución de errores.
    
    Args:
        logger (logging.Logger): Instancia del logger
        error (Exception): Excepción capturada
        context (dict, optional): Información adicional de contexto
            Puede incluir: función, parámetros, estado, etc.
    
    Example:
        >>> try:
        ...     resultado = dividir(10, 0)
        ... except Exception as e:
        ...     log_error_with_context(logger, e, {
        ...         'funcion': 'dividir',
        ...         'parametros': {'a': 10, 'b': 0},
        ...         'usuario_id': 123
        ...     })
        
        2025-01-08 10:30:45 | ERROR | ERROR: ZeroDivisionError: division by zero | Context: funcion=dividir, parametros={'a': 10, 'b': 0}
        Traceback (most recent call last):
        ...
    """
    # Construir mensaje de error
    error_msg = f"ERROR: {type(error).__name__}: {str(error)}"
    
    # Agregar contexto si está disponible
    if context:
        context_str = " | ".join(
            f"{key}={value}" for key, value in context.items()
        )
        error_msg += f" | Context: {context_str}"
    
    # Registrar con stack trace completo (exc_info=True)
    logger.error(error_msg, exc_info=True)


class LoggerMixin:
    """
    Mixin que agrega capacidades de logging a cualquier clase.
    
    Al heredar de este mixin, cualquier clase obtiene automáticamente
    un atributo 'logger' configurado con el nombre de la clase.
    
    Example:
        >>> class MiClase(LoggerMixin):
        ...     def mi_metodo(self):
        ...         self.logger.info("Método ejecutado")
        ...         self.logger.debug("Valor: %s", self.valor)
        
        >>> obj = MiClase()
        >>> obj.mi_metodo()
        2025-01-08 10:30:45 | INFO | MiClase:mi_metodo:3 | Método ejecutado
    """
    
    @property
    def logger(self) -> logging.Logger:
        """
        Retorna un logger con el nombre de la clase.
        
        El logger se crea solo una vez (lazy initialization) y
        se reutiliza en llamadas subsecuentes.
        
        Returns:
            logging.Logger: Logger configurado para la clase actual
        """
        # Lazy initialization: crear solo si no existe
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(
                name=self.__class__.__name__,
                log_level=os.environ.get('LOG_LEVEL', 'INFO')
            )
        return self._logger


# Logger global para uso rápido en módulos
# Uso: from logger import app_logger
app_logger = setup_logger()


# ========== FUNCIONES AUXILIARES ==========

def set_log_level(logger: logging.Logger, level: str):
    """
    Cambia el nivel de log dinámicamente.
    
    Útil para debugging temporal sin reiniciar la aplicación.
    
    Args:
        logger (logging.Logger): Logger a modificar
        level (str): Nuevo nivel ('DEBUG', 'INFO', etc.)
    
    Example:
        >>> set_log_level(logger, 'DEBUG')
        >>> # Ahora verás mensajes de debug
        >>> logger.debug("Esto ahora se muestra")
    """
    level = level.upper()
    logger.setLevel(getattr(logging, level))
    logger.info(f"Nivel de log cambiado a: {level}")


def log_performance(logger: logging.Logger, func_name: str, duration: float):
    """
    Registra tiempo de ejecución de una función.
    
    Args:
        logger (logging.Logger): Logger a usar
        func_name (str): Nombre de la función
        duration (float): Duración en segundos
    
    Example:
        >>> import time
        >>> start = time.time()
        >>> # ... código a medir ...
        >>> duration = time.time() - start
        >>> log_performance(logger, 'procesar_datos', duration)
    """
    logger.info(f"PERFORMANCE {func_name} | Duration: {duration:.4f}s")


# ========== DEMO Y PRUEBAS ==========

if __name__ == '__main__':
    """
    Demostración del sistema de logging.
    Ejecutar: python logger.py
    """
    print("🔍 Sistema de Logging UniPlanner\n")
    print("=" * 70)
    
    # Crear logger de prueba
    logger = setup_logger('test_logger', 'DEBUG')
    
    print("\n📋 Probando todos los niveles de log:\n")
    
    # Probar todos los niveles
    logger.debug("Mensaje de DEBUG - detalles técnicos para desarrollo")
    logger.info("Mensaje de INFO - operación normal del sistema")
    logger.warning("Mensaje de WARNING - algo sospechoso pero no crítico")
    logger.error("Mensaje de ERROR - error que debe ser investigado")
    logger.critical("Mensaje de CRITICAL - falla grave del sistema")
    
    # Probar logging de petición HTTP
    print("\n📡 Log de petición HTTP:\n")
    log_request(logger, {
        'method': 'POST',
        'path': '/api/auth/login',
        'user_id': 123,
        'ip': '192.168.1.100',
        'status': 200
    })
    
    # Probar logging de error con contexto
    print("\n❌ Log de error con contexto:\n")
    try:
        resultado = 10 / 0
    except Exception as e:
        log_error_with_context(logger, e, {
            'operacion': 'division',
            'a': 10,
            'b': 0,
            'usuario': 'test_user'
        })
    
    # Probar Mixin
    print("\n🎨 Probando LoggerMixin:\n")
    
    class MiClase(LoggerMixin):
        def metodo_ejemplo(self):
            self.logger.info("Método ejecutado desde MiClase")
            self.logger.debug("Detalle interno del método")
    
    obj = MiClase()
    obj.metodo_ejemplo()
    
    # Probar log de performance
    print("\n⏱️  Log de performance:\n")
    import time
    start = time.time()
    time.sleep(0.1)  # Simular operación
    duration = time.time() - start
    log_performance(logger, 'operacion_simulada', duration)
    
    print("\n" + "=" * 70)
    print("✅ Sistema de logging funcionando correctamente")
    print(f"📁 Logs guardados en: {os.path.abspath('logs')}")
    print("\nPuedes revisar los archivos de log en la carpeta 'logs/'")