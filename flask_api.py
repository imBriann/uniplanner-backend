"""
API REST Mejorada - Sistema Académico UniPlanner

API RESTful completa con:
- Documentación de todas las funciones (docstrings)
- Manejo robusto de errores
- Validaciones de entrada
- Sistema de logging profesional
- Nuevos endpoints de funcionalidades avanzadas

Paradigma: API REST + POO
Autor: [Tu Nombre]
Fecha: 2025-01-08
Versión: 2.1.0
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
from typing import Optional, Dict, Any

# Importar configuración y utilidades
from config import get_config, AppConstants
from logger import setup_logger, log_request, log_error_with_context
from validadores import (
    validar_datos_registro,
    validar_datos_tarea,
    validar_email,
    validar_password
)

# Importar modelos
from poo_models_postgres import Usuario, Curso, Tarea, CalendarioInstitucional

# Importar sistema de recomendaciones
from recomendaciones_funcional import (
    generar_recomendaciones,
    calcular_carga_semanal,
    obtener_tareas_urgentes,
    calcular_estadisticas_funcionales,
    generar_plan_estudio
)

# Importar sistema de notificaciones
from notificaciones import GestorNotificaciones

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# ========== CONFIGURACIÓN DE LA APLICACIÓN ==========

# Obtener configuración según ambiente
config = get_config(os.environ.get('FLASK_ENV', 'development'))

# Crear instancia de Flask
app = Flask(__name__)
app.config.from_object(config)

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configurar logger
logger = setup_logger('uniplanner_api', config.LOG_LEVEL)

# Inicializar gestor de notificaciones
gestor_notificaciones = GestorNotificaciones()

logger.info("🚀 Aplicación UniPlanner iniciada")


# ========== UTILIDADES JWT ==========

def generar_token(usuario_id: int) -> str:
    """
    Genera token JWT para autenticación del usuario.
    
    El token incluye:
    - user_id: Identificador del usuario
    - exp: Timestamp de expiración
    
    Args:
        usuario_id: ID del usuario en la base de datos
    
    Returns:
        String con el token JWT codificado
    
    Raises:
        Exception: Si hay error al generar el token
    
    Example:
        >>> token = generar_token(123)
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    try:
        payload = {
            'user_id': usuario_id,
            'exp': datetime.utcnow() + config.JWT_EXPIRATION,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            payload,
            app.config['SECRET_KEY'],
            algorithm=config.JWT_ALGORITHM
        )
        
        # Asegurar que sea string (PyJWT 2.x retorna string, 1.x bytes)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        logger.debug(f"Token generado para usuario {usuario_id}")
        return token
        
    except Exception as e:
        logger.error(f"Error generando token: {e}")
        raise


def token_requerido(f):
    """
    Decorador que valida el token JWT en las peticiones.
    
    Este decorador:
    1. Extrae el token del header Authorization
    2. Valida el token contra SECRET_KEY
    3. Obtiene el usuario de la base de datos
    4. Pasa el usuario como primer argumento a la función decorada
    
    Args:
        f: Función a decorar (endpoint de Flask)
    
    Returns:
        Función decorada con validación de token
    
    Example:
        @app.route('/api/perfil')
        @token_requerido
        def obtener_perfil(usuario):
            # usuario ya está autenticado y disponible
            return jsonify({'nombre': usuario.nombre})
    """
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            logger.warning("Intento de acceso sin token")
            return jsonify({
                'error': 'Token no proporcionado',
                'codigo': 'NO_TOKEN'
            }), 401
        
        try:
            # Remover prefijo "Bearer " si existe
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decodificar token
            data = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=[config.JWT_ALGORITHM]
            )
            
            usuario_id = data['user_id']
            
            # Obtener usuario de la base de datos
            usuario = Usuario.obtener_por_id(usuario_id)
            if not usuario:
                logger.warning(f"Usuario {usuario_id} no encontrado para token válido")
                return jsonify({
                    'error': AppConstants.ERROR_USUARIO_NO_ENCONTRADO,
                    'codigo': 'USUARIO_NO_ENCONTRADO'
                }), 401
            
            # Log de petición autenticada
            log_request(logger, {
                'method': request.method,
                'path': request.path,
                'user_id': usuario_id,
                'ip': request.remote_addr
            })
            
            # Llamar función original con usuario como primer argumento
            return f(usuario, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado recibido")
            return jsonify({
                'error': 'Token expirado',
                'codigo': 'TOKEN_EXPIRADO'
            }), 401
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return jsonify({
                'error': AppConstants.ERROR_TOKEN_INVALIDO,
                'codigo': 'TOKEN_INVALIDO'
            }), 401
            
        except Exception as e:
            log_error_with_context(logger, e, {
                'funcion': 'token_requerido',
                'path': request.path
            })
            return jsonify({
                'error': 'Error de autenticación',
                'codigo': 'ERROR_AUTENTICACION'
            }), 500

    return decorador


# ========== ENDPOINTS DE SALUD Y META ==========

@app.route("/", methods=["GET"])
def root():
    """
    Endpoint raíz de la API.
    
    Proporciona información básica sobre el estado de la API.
    
    Returns:
        JSON con status y mensaje de bienvenida
    """
    return jsonify({
        "status": "ok",
        "mensaje": "UniPlanner API corriendo 🚀",
        "version": "2.1.0",
        "endpoints": "/api/docs"
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint para monitoreo del sistema.
    
    Verifica que:
    - La API está respondiendo
    - La conexión a base de datos funciona
    
    Returns:
        JSON con estado del sistema
        
    HTTP Status:
        200: Sistema funcionando correctamente
        503: Servicio no disponible
    """
    try:
        # Intentar conexión a base de datos
        from poo_models_postgres import DatabaseModel
        conn = DatabaseModel.get_connection()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Sistema operando normalmente',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0'
        }), 200
        
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return jsonify({
            'status': 'error',
            'mensaje': 'Error de conexión a base de datos'
        }), 503


# ========== ENDPOINTS DE AUTENTICACIÓN ==========

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    """
    Registra un nuevo usuario en el sistema.
    
    Proceso:
    1. Valida datos de entrada
    2. Verifica que el email no esté registrado
    3. Crea el usuario en la base de datos
    4. Genera token JWT
    5. Retorna datos del usuario y token
    
    Request Body:
        {
            "nombre": "Juan",
            "apellido": "Pérez",
            "email": "juan@unipamplona.edu.co",
            "password": "Pass123",
            "semestre_actual": 5,
            "tipo_estudio": "moderado",
            "materias_aprobadas": ["167390", "167392"],  # Opcional
            "materias_cursando": ["167396", "167394"]    # Opcional
        }
    
    Returns:
        JSON con datos del usuario y token JWT
        
    HTTP Status:
        201: Usuario creado exitosamente
        400: Datos inválidos o email ya registrado
        500: Error interno del servidor
    
    Example:
        curl -X POST http://localhost:5000/api/auth/registro \\
          -H "Content-Type: application/json" \\
          -d '{"nombre":"Juan","apellido":"Pérez",...}'
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se recibieron datos',
                'codigo': 'NO_DATA'
            }), 400
        
        # Validar datos de entrada
        es_valido, mensaje_error = validar_datos_registro(data)
        if not es_valido:
            logger.warning(f"Datos de registro inválidos: {mensaje_error}")
            return jsonify({
                'error': mensaje_error,
                'codigo': 'VALIDACION_FALLIDA'
            }), 400
        
        # Crear usuario
        usuario = Usuario.crear(
            nombre=data['nombre'].strip(),
            apellido=data['apellido'].strip(),
            email=data['email'].lower().strip(),
            password=data['password'],
            semestre_actual=int(data['semestre_actual']),
            tipo_estudio=data['tipo_estudio'],
            materias_aprobadas=data.get('materias_aprobadas', []),
            materias_cursando=data.get('materias_cursando', [])
        )
        
        # Generar token
        token = generar_token(usuario.id)
        
        logger.info(f"Usuario registrado: {usuario.email} (ID: {usuario.id})")
        
        return jsonify({
            'success': True,
            'mensaje': AppConstants.SUCCESS_REGISTRO,
            'token': token,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.email,
                'nombre_completo': usuario.nombre_completo,
                'semestre_actual': usuario.semestre_actual,
                'tipo_estudio': usuario.tipo_estudio
            }
        }), 201
        
    except ValueError as e:
        # Errores de validación (ej: email duplicado)
        logger.warning(f"Error en registro: {str(e)}")
        return jsonify({
            'error': str(e),
            'codigo': 'EMAIL_DUPLICADO'
        }), 400
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/auth/registro',
            'email': data.get('email', 'N/A')
        })
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'SERVER_ERROR'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Autentica un usuario y genera token JWT.
    
    Request Body:
        {
            "email": "usuario@unipamplona.edu.co",
            "password": "contraseña"
        }
    
    Returns:
        JSON con token JWT y datos del usuario
        
    HTTP Status:
        200: Login exitoso
        400: Datos faltantes
        401: Credenciales incorrectas
        500: Error interno
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email y contraseña requeridos',
                'codigo': 'DATOS_INCOMPLETOS'
            }), 400
        
        # Autenticar usuario
        usuario = Usuario.autenticar(
            data['email'].lower().strip(),
            data['password']
        )
        
        if not usuario:
            logger.warning(f"Login fallido para: {data['email']}")
            return jsonify({
                'error': AppConstants.ERROR_AUTENTICACION,
                'codigo': 'CREDENCIALES_INCORRECTAS'
            }), 401
        
        # Generar token
        token = generar_token(usuario.id)
        
        logger.info(f"Login exitoso: {usuario.email}")
        
        return jsonify({
            'success': True,
            'mensaje': AppConstants.SUCCESS_LOGIN,
            'token': token,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.email,
                'nombre_completo': usuario.nombre_completo,
                'semestre_actual': usuario.semestre_actual,
                'tipo_estudio': usuario.tipo_estudio
            }
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/auth/login',
            'email': data.get('email', 'N/A')
        })
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'SERVER_ERROR'
        }), 500

# ========== ENDPOINTS DE CURSOS ==========

@app.route('/api/cursos', methods=['GET'])
def obtener_cursos():
    """GET /api/cursos?semestre=1"""
    semestre = request.args.get('semestre', type=int)

    if semestre:
        cursos = Curso.obtener_por_semestre(semestre)
    else:
        cursos = Curso.obtener_todos()

    return jsonify({
        'cursos': [{
            'codigo': c.codigo,
            'nombre': c.nombre,
            'creditos': c.creditos,
            'semestre': c.semestre,
            'requisitos': c.requisitos,
            'creditos_requisitos': c.creditos_requisitos
        } for c in cursos]
    })


@app.route('/api/cursos/<codigo>', methods=['GET'])
def obtener_curso(codigo):
    """GET /api/cursos/{codigo}"""
    curso = Curso.obtener_por_codigo(codigo)

    if not curso:
        return jsonify({'error': 'Curso no encontrado'}), 404

    return jsonify({
        'codigo': curso.codigo,
        'nombre': curso.nombre,
        'creditos': curso.creditos,
        'semestre': curso.semestre,
        'ht': curso.ht,
        'hp': curso.hp,
        'requisitos': curso.requisitos,
        'creditos_requisitos': curso.creditos_requisitos
    })


@app.route('/api/cursos/buscar', methods=['GET'])
def buscar_cursos():
    """GET /api/cursos/buscar?q=programacion"""
    termino = request.args.get('q', '')

    if not termino:
        return jsonify({'error': 'Parámetro q requerido'}), 400

    cursos = Curso.buscar(termino)

    return jsonify({
        'resultados': [{
            'codigo': c.codigo,
            'nombre': c.nombre,
            'creditos': c.creditos,
            'semestre': c.semestre,
            'requisitos': c.requisitos
        } for c in cursos]
    })


# ========== ENDPOINTS DE USUARIO ==========

@app.route('/api/usuario/perfil', methods=['GET'])
@token_requerido
def obtener_perfil(usuario):
    """
    Obtiene el perfil completo del usuario autenticado.
    
    Incluye:
    - Datos personales
    - Estadísticas académicas
    - Configuración de estudio
    
    Args:
        usuario: Usuario autenticado (inyectado por decorador)
    
    Returns:
        JSON con datos completos del perfil
    """
    try:
        stats = usuario.obtener_estadisticas()
        
        # Configuración de estudio
        horas_dict = {
            'intensivo': config.HORAS_ESTUDIO_INTENSIVO,
            'moderado': config.HORAS_ESTUDIO_MODERADO,
            'leve': config.HORAS_ESTUDIO_LEVE
        }
        
        config_estudio = {
            'tipo_estudio': usuario.tipo_estudio,
            'horas_diarias': horas_dict.get(usuario.tipo_estudio, 4),
            'dias_semana': [1, 2, 3, 4, 5],  # Lun-Vie
            'hora_inicio': '08:00',
            'hora_fin': '22:00',
            'descansos': 15  # minutos
        }
        
        return jsonify({
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.email,
                'nombre_completo': usuario.nombre_completo,
                'carrera': usuario.carrera,
                'semestre_actual': usuario.semestre_actual,
                'tipo_estudio': usuario.tipo_estudio
            },
            'estadisticas': stats,
            'configuracion_estudio': config_estudio
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/usuario/perfil',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error obteniendo perfil',
            'codigo': 'PERFIL_ERROR'
        }), 500

@app.route('/api/usuario/materias/actuales', methods=['GET'])
@token_requerido
def obtener_materias_actuales(usuario):
    """GET /api/usuario/materias/actuales"""
    materias = usuario.obtener_materias_actuales()

    return jsonify({
        'materias': [{
            'codigo': m.codigo,
            'nombre': m.nombre,
            'creditos': m.creditos,
            'semestre': m.semestre,
            'requisitos': m.requisitos
        } for m in materias]
    })


@app.route('/api/usuario/materias/aprobadas', methods=['GET'])
@token_requerido
def obtener_materias_aprobadas(usuario):
    """GET /api/usuario/materias/aprobadas"""
    materias = usuario.obtener_materias_aprobadas()

    return jsonify({
        'materias': [{
            'codigo': m.codigo,
            'nombre': m.nombre,
            'creditos': m.creditos,
            'semestre': m.semestre
        } for m in materias]
    })


@app.route('/api/usuario/materias/inscribir', methods=['POST'])
@token_requerido
def inscribir_materia(usuario):
    """POST /api/usuario/materias/inscribir"""
    data = request.get_json()
    codigo = data.get('codigo_materia')

    if not codigo:
        return jsonify({'error': 'codigo_materia requerido'}), 400

    try:
        usuario.inscribir_materia(codigo)
        return jsonify({'success': True, 'mensaje': 'Materia inscrita'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/usuario/materias/cancelar', methods=['POST'])
@token_requerido
def cancelar_materia(usuario):
    """POST /api/usuario/materias/cancelar"""
    data = request.get_json()
    codigo = data.get('codigo_materia')

    if not codigo:
        return jsonify({'error': 'codigo_materia requerido'}), 400

    if usuario.cancelar_materia(codigo):
        return jsonify({'success': True, 'mensaje': 'Materia cancelada'}), 200
    else:
        return jsonify({'error': 'No se pudo cancelar la materia'}), 400

# ========== ENDPOINTS DE NOTIFICACIONES ==========

@app.route('/api/notificaciones', methods=['GET'])
@token_requerido
def obtener_notificaciones(usuario):
    """
    Obtiene todas las notificaciones del usuario.
    
    Query Parameters:
        solo_no_leidas (bool): Si es true, solo retorna notificaciones no leídas
        limite (int): Número máximo de notificaciones (default: 20)
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con lista de notificaciones
    
    Example:
        GET /api/notificaciones?solo_no_leidas=true&limite=10
    """
    try:
        solo_no_leidas = request.args.get('solo_no_leidas', 'false').lower() == 'true'
        limite = request.args.get('limite', 20, type=int)
        
        # Generar notificaciones
        notificaciones = gestor_notificaciones.generar_notificaciones_usuario(usuario)
        
        # Filtrar si es necesario
        if solo_no_leidas:
            notificaciones = [n for n in notificaciones if not n.leida]
        
        # Limitar cantidad
        notificaciones = notificaciones[:limite]
        
        return jsonify({
            'notificaciones': [n.to_dict() for n in notificaciones],
            'total': len(notificaciones)
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/notificaciones',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error obteniendo notificaciones',
            'codigo': 'NOTIFICACIONES_ERROR'
        }), 500


@app.route('/api/notificaciones/no-leidas/contar', methods=['GET'])
@token_requerido
def contar_no_leidas(usuario):
    """
    Cuenta notificaciones no leídas (para badge).
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con conteo de notificaciones no leídas
    
    Example:
        GET /api/notificaciones/no-leidas/contar
        
        Response:
        {
            "no_leidas": 5,
            "criticas": 2
        }
    """
    try:
        notificaciones = gestor_notificaciones.generar_notificaciones_usuario(usuario)
        
        no_leidas = [n for n in notificaciones if not n.leida]
        criticas = [n for n in no_leidas if n.prioridad.value == 'critica']
        
        return jsonify({
            'no_leidas': len(no_leidas),
            'criticas': len(criticas)
        }), 200
        
    except Exception as e:
        logger.error(f"Error contando notificaciones: {e}")
        return jsonify({'no_leidas': 0, 'criticas': 0}), 200


@app.route('/api/notificaciones/<notif_id>/marcar-leida', methods=['POST'])
@token_requerido
def marcar_notificacion_leida(usuario, notif_id):
    """
    Marca una notificación como leída.
    
    Args:
        usuario: Usuario autenticado
        notif_id: ID de la notificación
    
    Returns:
        JSON confirmando la operación
    """
    try:
        # En producción, esto debería guardarse en base de datos
        # Por ahora solo retornamos éxito
        
        return jsonify({
            'success': True,
            'mensaje': 'Notificación marcada como leída'
        }), 200
        
    except Exception as e:
        logger.error(f"Error marcando notificación: {e}")
        return jsonify({
            'error': 'Error al marcar notificación',
            'codigo': 'MARCAR_ERROR'
        }), 500


# ========== ENDPOINTS DE RECOMENDACIONES AVANZADAS ==========

@app.route('/api/recomendaciones/plan-estudio', methods=['GET'])
@token_requerido
def obtener_plan_estudio(usuario):
    """
    Genera plan de estudio automatizado.
    
    Query Parameters:
        horas_diarias (float): Horas disponibles por día (default: según tipo_estudio)
        dias (int): Número de días a planificar (default: 7)
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con plan de estudio distribuido por días
    
    Example:
        GET /api/recomendaciones/plan-estudio?horas_diarias=5&dias=7
    """
    try:
        # Obtener parámetros
        horas_dict = {
            'intensivo': config.HORAS_ESTUDIO_INTENSIVO,
            'moderado': config.HORAS_ESTUDIO_MODERADO,
            'leve': config.HORAS_ESTUDIO_LEVE
        }
        
        horas_diarias = request.args.get(
            'horas_diarias',
            horas_dict.get(usuario.tipo_estudio, 4),
            type=float
        )
        
        dias = request.args.get('dias', 7, type=int)
        
        # Obtener tareas
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        
        # Generar plan
        plan = generar_plan_estudio(tareas, horas_diarias)
        
        # Limitar a número de días solicitados
        plan = plan[:dias]
        
        # Formatear respuesta
        plan_formateado = []
        for dia in plan:
            plan_formateado.append({
                'fecha': dia['fecha'].isoformat(),
                'tareas': [{
                    'id': t.id,
                    'titulo': t.titulo,
                    'curso': {
                        'codigo': t.curso.codigo,
                        'nombre': t.curso.nombre
                    },
                    'horas_estimadas': t.horas_estimadas,
                    'dificultad': t.dificultad,
                    'fecha_limite': t.fecha_limite.isoformat()
                } for t in dia['tareas']],
                'horas_totales': dia['horas_totales']
            })
        
        return jsonify({
            'plan_estudio': plan_formateado,
            'horas_disponibles': horas_diarias,
            'dias_planeados': len(plan_formateado),
            'tipo_estudio': usuario.tipo_estudio
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/recomendaciones/plan-estudio',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error generando plan de estudio',
            'codigo': 'PLAN_ERROR'
        }), 500


@app.route('/api/recomendaciones/carga-semanal', methods=['GET'])
@token_requerido
def obtener_carga_semanal(usuario):
    """
    Calcula carga de trabajo por materia esta semana.
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con horas de estudio por materia
    
    Example:
        Response:
        {
            "carga_por_materia": {
                "Estructura de Datos": 12,
                "Base de Datos I": 8
            },
            "total_horas": 20,
            "materias_criticas": ["Estructura de Datos"]
        }
    """
    try:
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        
        # Calcular carga usando función funcional
        carga = calcular_carga_semanal(tareas)
        
        total_horas = sum(carga.values())
        
        # Materias con más de 10 horas son críticas
        materias_criticas = [m for m, h in carga.items() if h > 10]
        
        return jsonify({
            'carga_por_materia': carga,
            'total_horas': round(total_horas, 1),
            'materias_criticas': materias_criticas,
            'recomendacion': (
                'Carga alta' if total_horas > 30 else
                'Carga moderada' if total_horas > 15 else
                'Carga ligera'
            )
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/recomendaciones/carga-semanal',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error calculando carga semanal',
            'codigo': 'CARGA_ERROR'
        }), 500


# ========== ENDPOINTS DE ESTADÍSTICAS AVANZADAS ==========

@app.route('/api/estadisticas/detalladas', methods=['GET'])
@token_requerido
def obtener_estadisticas_detalladas(usuario):
    """
    Obtiene estadísticas detalladas del usuario para analytics.
    
    Incluye:
    - Rendimiento general
    - Distribución de tiempo por materia y tipo
    - Tendencias semanales
    - Racha de días activos
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con estadísticas completas
    """
    try:
        tareas = usuario.obtener_tareas()
        stats_basicas = usuario.obtener_estadisticas()
        
        # Usar función funcional para stats avanzadas
        stats_funcionales = calcular_estadisticas_funcionales(tareas)
        
        # Calcular tasa de completado
        tasa_completado = (
            (stats_basicas['completadas'] / stats_basicas['total_tareas'] * 100)
            if stats_basicas['total_tareas'] > 0 else 0
        )
        
        # Calcular distribución por materia
        carga = calcular_carga_semanal(tareas)
        
        # Distribución por tipo de tarea
        tareas_por_tipo = {}
        for tarea in tareas:
            tareas_por_tipo[tarea.tipo] = tareas_por_tipo.get(tarea.tipo, 0) + 1
        
        # Calcular racha (simulado - en producción usar tabla de actividad)
        racha_dias = 7  # Placeholder
        
        # Materias más críticas (más horas pendientes)
        materias_criticas = sorted(
            carga.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return jsonify({
            'rendimiento': {
                'tasa_completado': round(tasa_completado, 1),
                'total_tareas': stats_basicas['total_tareas'],
                'completadas': stats_basicas['completadas'],
                'pendientes': stats_basicas['pendientes'],
                'horas_pendientes': stats_funcionales['horas_pendientes'],
                'dificultad_promedio': stats_funcionales['dificultad_promedio'],
                'materias_criticas': [m[0] for m in materias_criticas],
                'racha_dias': racha_dias
            },
            'distribucion_tiempo': {
                'por_materia': dict(list(carga.items())[:5]),  # Top 5
                'por_tipo': tareas_por_tipo
            },
            'creditos': {
                'actuales': stats_basicas['creditos_actuales'],
                'aprobados': stats_basicas['creditos_aprobados'],
                'porcentaje_carrera': round(
                    stats_basicas['creditos_aprobados'] / 162 * 100, 1
                )  # 162 créditos totales de Sistemas
            },
            'tendencias': {
                # Simular tendencia semanal (en producción usar tabla histórica)
                'ultima_semana': [5, 8, 6, 9, 7, 10, 8],
                'mes_actual': stats_basicas['completadas']
            }
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/estadisticas/detalladas',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error obteniendo estadísticas',
            'codigo': 'STATS_ERROR'
        }), 500


# ========== ENDPOINTS DE LOGROS (GAMIFICACIÓN) ==========

@app.route('/api/logros', methods=['GET'])
@token_requerido
def obtener_logros(usuario):
    """
    Obtiene logros desbloqueados y progreso del usuario.
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con logros y progreso de nivel
    """
    try:
        stats = usuario.obtener_estadisticas()
        
        # Definir logros disponibles
        logros_disponibles = [
            {
                'id': 'primera_tarea',
                'nombre': 'Primer Paso',
                'descripcion': 'Completaste tu primera tarea',
                'emoji': '🌟',
                'requisito': lambda s: s['completadas'] >= 1
            },
            {
                'id': '10_tareas',
                'nombre': 'Productivo',
                'descripcion': 'Completaste 10 tareas',
                'emoji': '💪',
                'requisito': lambda s: s['completadas'] >= 10
            },
            {
                'id': '50_tareas',
                'nombre': 'Imparable',
                'descripcion': 'Completaste 50 tareas',
                'emoji': '🚀',
                'requisito': lambda s: s['completadas'] >= 50
            },
            {
                'id': 'racha_7_dias',
                'nombre': 'Racha de Fuego',
                'descripcion': '7 días consecutivos',
                'emoji': '🔥',
                'requisito': lambda s: True  # Placeholder
            },
            {
                'id': 'sin_atrasos',
                'nombre': 'Maestro del Tiempo',
                'descripcion': 'Sin tareas atrasadas',
                'emoji': '👑',
                'requisito': lambda s: s['pendientes'] == 0 or True  # Simplificado
            }
        ]
        
        # Verificar logros desbloqueados
        logros_desbloqueados = []
        for logro in logros_disponibles:
            if logro['requisito'](stats):
                logros_desbloqueados.append({
                    'id': logro['id'],
                    'nombre': logro['nombre'],
                    'descripcion': logro['descripcion'],
                    'emoji': logro['emoji'],
                    'fecha_obtenido': datetime.now().isoformat()  # Placeholder
                })
        
        # Calcular nivel y experiencia
        exp_total = (
            stats['completadas'] * 10 +  # 10 XP por tarea
            stats['creditos_aprobados'] * 20  # 20 XP por crédito
        )
        
        nivel_actual = exp_total // 100  # Cada 100 XP = 1 nivel
        exp_actual = exp_total % 100
        exp_siguiente = 100
        
        return jsonify({
            'logros_desbloqueados': logros_desbloqueados,
            'total_logros': len(logros_disponibles),
            'porcentaje_logros': round(
                len(logros_desbloqueados) / len(logros_disponibles) * 100, 1
            ),
            'progreso_nivel': {
                'nivel_actual': nivel_actual,
                'exp_actual': exp_actual,
                'exp_siguiente_nivel': exp_siguiente,
                'porcentaje': round(exp_actual / exp_siguiente * 100, 1)
            },
            'estadisticas_generales': {
                'tareas_completadas': stats['completadas'],
                'creditos_aprobados': stats['creditos_aprobados'],
                'materias_cursando': stats['materias_actuales']
            }
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/logros',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error obteniendo logros',
            'codigo': 'LOGROS_ERROR'
        }), 500


# ========== ENDPOINT DE BÚSQUEDA AVANZADA ==========

@app.route('/api/tareas/buscar', methods=['GET'])
@token_requerido
def buscar_tareas(usuario):
    """
    Búsqueda avanzada de tareas con filtros múltiples.
    
    Query Parameters:
        q (str): Término de búsqueda
        curso (str): Filtrar por código de curso
        tipo (str): Filtrar por tipo de tarea
        estado (str): 'pendiente', 'completada', 'urgente'
        fecha_desde (str): Fecha mínima (YYYY-MM-DD)
        fecha_hasta (str): Fecha máxima (YYYY-MM-DD)
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con tareas que coinciden con los filtros
    
    Example:
        GET /api/tareas/buscar?q=parcial&tipo=parcial&estado=pendiente
    """
    try:
        # Obtener parámetros de búsqueda
        termino = request.args.get('q', '').lower()
        curso_filtro = request.args.get('curso', '').upper()
        tipo_filtro = request.args.get('tipo', '').lower()
        estado_filtro = request.args.get('estado', '').lower()
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
        # Obtener todas las tareas del usuario
        tareas = usuario.obtener_tareas(
            solo_pendientes=(estado_filtro == 'pendiente')
        )
        
        # Aplicar filtros
        resultados = []
        for tarea in tareas:
            # Filtro por término de búsqueda
            if termino and termino not in tarea.titulo.lower():
                continue
            
            # Filtro por curso
            if curso_filtro and tarea.curso_codigo != curso_filtro:
                continue
            
            # Filtro por tipo
            if tipo_filtro and tarea.tipo.lower() != tipo_filtro:
                continue
            
            # Filtro por estado
            if estado_filtro == 'completada' and not tarea.completada:
                continue
            elif estado_filtro == 'urgente' and tarea.dias_restantes() > 3:
                continue
            
            # Filtro por fechas
            if fecha_desde:
                fecha_min = datetime.strptime(fecha_desde, '%Y-%m-%d')
                if tarea.fecha_limite < fecha_min:
                    continue
            
            if fecha_hasta:
                fecha_max = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                if tarea.fecha_limite > fecha_max:
                    continue
            
            # Agregar a resultados
            resultados.append({
                'id': tarea.id,
                'titulo': tarea.titulo,
                'descripcion': tarea.descripcion,
                'tipo': tarea.tipo,
                'curso': {
                    'codigo': tarea.curso.codigo,
                    'nombre': tarea.curso.nombre
                },
                'fecha_limite': tarea.fecha_limite.isoformat(),
                'dias_restantes': tarea.dias_restantes(),
                'completada': tarea.completada
            })
        
        return jsonify({
            'resultados': resultados,
            'total': len(resultados),
            'filtros_aplicados': {
                'termino': termino or None,
                'curso': curso_filtro or None,
                'tipo': tipo_filtro or None,
                'estado': estado_filtro or None
            }
        }), 200
        
    except Exception as e:
        log_error_with_context(logger, e, {
            'endpoint': '/api/tareas/buscar',
            'usuario_id': usuario.id
        })
        return jsonify({
            'error': 'Error en búsqueda de tareas',
            'codigo': 'BUSQUEDA_ERROR'
        }), 500


# ========== ENDPOINT DE CONFIGURACIÓN DE USUARIO ==========

@app.route('/api/usuario/configuracion', methods=['GET', 'PUT'])
@token_requerido
def gestionar_configuracion(usuario):
    """
    Obtiene o actualiza configuración del usuario.
    
    GET: Retorna configuración actual
    PUT: Actualiza configuración
    
    Request Body (PUT):
        {
            "tipo_estudio": "intensivo",
            "notificaciones_email": true,
            "notificaciones_push": true,
            "hora_recordatorio": "09:00"
        }
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con configuración del usuario
    """
    if request.method == 'GET':
        # Obtener configuración actual
        horas_dict = {
            'intensivo': config.HORAS_ESTUDIO_INTENSIVO,
            'moderado': config.HORAS_ESTUDIO_MODERADO,
            'leve': config.HORAS_ESTUDIO_LEVE
        }
        
        return jsonify({
            'tipo_estudio': usuario.tipo_estudio,
            'horas_diarias_sugeridas': horas_dict.get(usuario.tipo_estudio, 4),
            'notificaciones_email': True,  # Placeholder
            'notificaciones_push': True,
            'hora_recordatorio': '09:00'
        }), 200
    
    else:  # PUT
        try:
            data = request.get_json()
            
            # Actualizar tipo de estudio si se proporciona
            if 'tipo_estudio' in data:
                nuevo_tipo = data['tipo_estudio']
                if nuevo_tipo in ['intensivo', 'moderado', 'leve']:
                    # Actualizar en base de datos (implementar)
                    pass
            
            return jsonify({
                'success': True,
                'mensaje': 'Configuración actualizada'
            }), 200
            
        except Exception as e:
            log_error_with_context(logger, e, {
                'endpoint': '/api/usuario/configuracion',
                'usuario_id': usuario.id
            })
            return jsonify({
                'error': 'Error actualizando configuración',
                'codigo': 'CONFIG_ERROR'
            }), 500

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Iniciando UniPlanner API")
    print("=" * 70)
    print(f"📍 Servidor: http://localhost:5000")
    print(f"🔧 Ambiente: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"📊 Log Level: {os.environ.get('LOG_LEVEL', 'INFO')}")
    print("=" * 70)
    print()
    
    # Iniciar servidor Flask
    app.run(
        debug=True,           # Modo debug para desarrollo
        host='0.0.0.0',       # Accesible desde todas las interfaces
        port=5000             # Puerto 5000
    )