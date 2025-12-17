from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
from typing import Optional, Dict, Any

# Importar modelos
from poo_models_postgres import Usuario, Curso, Tarea, CalendarioInstitucional

# Intentar importar módulos opcionales (no críticos)
try:
    from config import get_config, AppConstants
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️  Módulo config.py no disponible, usando configuración por defecto")

try:
    from logger import setup_logger, log_request, log_error_with_context
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    print("⚠️  Módulo logger.py no disponible, usando print por defecto")
    
try:
    from validadores import (
        validar_datos_registro,
        validar_datos_tarea,
        validar_email,
        validar_password
    )
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    print("⚠️  Módulo validadores.py no disponible, usando validación básica")

try:
    from r_funcional import (
        generar_recomendaciones,
        calcular_carga_semanal,
        obtener_tareas_urgentes,
        calcular_estadisticas_funcionales,
        generar_plan_estudio
    )
    RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    RECOMMENDATIONS_AVAILABLE = False
    print("⚠️  Módulo recomendaciones_funcional.py no disponible")

try:
    from notificaciones import GestorNotificaciones
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("⚠️  Módulo notificaciones.py no disponible")

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# ========== CONFIGURACIÓN DE LA APLICACIÓN ==========

# Obtener configuración según ambiente
if CONFIG_AVAILABLE:
    config = get_config(os.environ.get('FLASK_ENV', 'development'))
else:
    # Configuración por defecto si no hay módulo config
    class DefaultConfig:
        SECRET_KEY = os.environ.get('SECRET_KEY')
        CORS_ORIGINS = ['*']
        LOG_LEVEL = 'INFO'
        JWT_EXPIRATION = timedelta(hours=24)
        JWT_ALGORITHM = 'HS256'
        HORAS_ESTUDIO_INTENSIVO = 6
        HORAS_ESTUDIO_MODERADO = 4
        HORAS_ESTUDIO_LEVE = 2.5
    config = DefaultConfig()

# Crear instancia de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JSON_AS_ASCII'] = False

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configurar logger
if LOGGER_AVAILABLE:
    logger = setup_logger('uniplanner_api', config.LOG_LEVEL)
    logger.info("🚀 Aplicación UniPlanner iniciada")
else:
    # Logger dummy si no está disponible
    class DummyLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    logger = DummyLogger()

# Inicializar gestor de notificaciones
if NOTIFICATIONS_AVAILABLE:
    gestor_notificaciones = GestorNotificaciones()
else:
    gestor_notificaciones = None


# ========== UTILIDADES JWT ==========

def generar_token(usuario_id: int) -> str:
    """
    Genera token JWT para autenticación del usuario.
    
    Args:
        usuario_id: ID del usuario en la base de datos
    
    Returns:
        String con el token JWT codificado
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
        
        # Asegurar que sea string
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
                    'error': 'Usuario no encontrado',
                    'codigo': 'USUARIO_NO_ENCONTRADO'
                }), 401
            
            # Log de petición autenticada
            if LOGGER_AVAILABLE:
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
                'error': 'Token inválido',
                'codigo': 'TOKEN_INVALIDO'
            }), 401
            
        except Exception as e:
            if LOGGER_AVAILABLE:
                log_error_with_context(logger, e, {
                    'funcion': 'token_requerido',
                    'path': request.path
                })
            else:
                logger.error(f"Error en autenticación: {e}")
            return jsonify({
                'error': 'Error de autenticación',
                'codigo': 'ERROR_AUTENTICACION'
            }), 500

    return decorador


# ========== ENDPOINTS DE SALUD Y META ==========

@app.route("/", methods=["GET"])
def root():
    """Endpoint raíz de la API."""
    return jsonify({
        "status": "ok",
        "mensaje": "UniPlanner API corriendo 🚀",
        "version": "2.1.0",
        "endpoints": "/api/docs"
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint para monitoreo del sistema."""
    try:
        # Intentar conexión a base de datos
        from poo_models_postgres import DatabaseModel
        conn = DatabaseModel.get_connection()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Sistema operando normalmente',
            'timestamp': datetime.now().isoformat(),
            'version': '2.1.0',
            'modules': {
                'config': CONFIG_AVAILABLE,
                'logger': LOGGER_AVAILABLE,
                'validators': VALIDATORS_AVAILABLE,
                'recommendations': RECOMMENDATIONS_AVAILABLE,
                'notifications': NOTIFICATIONS_AVAILABLE
            }
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
    """Registra un nuevo usuario en el sistema."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se recibieron datos',
                'codigo': 'NO_DATA'
            }), 400
        
        # Validar datos de entrada
        if VALIDATORS_AVAILABLE:
            es_valido, mensaje_error = validar_datos_registro(data)
            if not es_valido:
                logger.warning(f"Datos de registro inválidos: {mensaje_error}")
                return jsonify({
                    'error': mensaje_error,
                    'codigo': 'VALIDACION_FALLIDA'
                }), 400
        else:
            # Validación básica manual
            campos_requeridos = ['nombre', 'apellido', 'email', 'password', 
                                'semestre_actual', 'tipo_estudio']
            for campo in campos_requeridos:
                if campo not in data:
                    return jsonify({'error': f'Campo requerido: {campo}'}), 400
            
            if data['tipo_estudio'] not in ['intensivo', 'moderado', 'leve']:
                return jsonify({'error': 'tipo_estudio debe ser: intensivo, moderado o leve'}), 400
        
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
            'mensaje': 'Usuario registrado exitosamente',
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
        logger.warning(f"Error en registro: {str(e)}")
        return jsonify({
            'error': str(e),
            'codigo': 'EMAIL_DUPLICADO'
        }), 400
        
    except Exception as e:
        if LOGGER_AVAILABLE:
            log_error_with_context(logger, e, {
                'endpoint': '/api/auth/registro',
                'email': data.get('email', 'N/A')
            })
        else:
            logger.error(f"Error en registro: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'SERVER_ERROR'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Autentica un usuario y genera token JWT."""
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
                'error': 'Credenciales incorrectas',
                'codigo': 'CREDENCIALES_INCORRECTAS'
            }), 401
        
        # Generar token
        token = generar_token(usuario.id)
        
        logger.info(f"Login exitoso: {usuario.email}")
        
        return jsonify({
            'success': True,
            'mensaje': 'Inicio de sesión exitoso',
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
        if LOGGER_AVAILABLE:
            log_error_with_context(logger, e, {
                'endpoint': '/api/auth/login',
                'email': data.get('email', 'N/A')
            })
        else:
            logger.error(f"Error en login: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'SERVER_ERROR'
        }), 500

@app.route('/api/auth/restablecer', methods=['POST'])
def restablecer_contrasena():
    """Solicita restablecer contrasena."""
    try:
        data = request.get_json()

        if not data or not data.get('email'):
            return jsonify({
                'error': 'Email requerido',
                'codigo': 'EMAIL_REQUERIDO'
            }), 400

        email = data['email'].lower().strip()

        if VALIDATORS_AVAILABLE:
            valido, error = validar_email(email)
            if not valido:
                return jsonify({
                    'error': error,
                    'codigo': 'EMAIL_INVALIDO'
                }), 400
        elif '@' not in email:
            return jsonify({
                'error': 'Email invalido',
                'codigo': 'EMAIL_INVALIDO'
            }), 400

        logger.info(f"Solicitud de restablecer para: {email}")

        return jsonify({
            'success': True,
            'mensaje': 'Solicitud enviada'
        }), 200

    except Exception as e:
        logger.error(f"Error restableciendo contrasena: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'SERVER_ERROR'
        }), 500

# ========== ENDPOINTS DE CURSOS ==========

@app.route('/api/cursos', methods=['GET'])
def obtener_cursos():
    """GET /api/cursos?semestre=1"""
    try:
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
    except Exception as e:
        logger.error(f"Error obteniendo cursos: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cursos/<codigo>', methods=['GET'])
def obtener_curso(codigo):
    """GET /api/cursos/{codigo}"""
    try:
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
    except Exception as e:
        logger.error(f"Error obteniendo curso: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cursos/buscar', methods=['GET'])
def buscar_cursos():
    """GET /api/cursos/buscar?q=programacion"""
    try:
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
    except Exception as e:
        logger.error(f"Error buscando cursos: {e}")
        return jsonify({'error': str(e)}), 500


# ========== ENDPOINTS DE USUARIO ==========

@app.route('/api/usuario/perfil', methods=['GET'])
@token_requerido
def obtener_perfil(usuario):
    """Obtiene el perfil completo del usuario autenticado."""
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
            'dias_semana': [1, 2, 3, 4, 5],
            'hora_inicio': '08:00',
            'hora_fin': '22:00',
            'descansos': 15
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
        if LOGGER_AVAILABLE:
            log_error_with_context(logger, e, {
                'endpoint': '/api/usuario/perfil',
                'usuario_id': usuario.id
            })
        else:
            logger.error(f"Error en perfil: {e}")
        return jsonify({
            'error': 'Error obteniendo perfil',
            'codigo': 'PERFIL_ERROR'
        }), 500

@app.route('/api/usuario/materias/actuales', methods=['GET'])
@token_requerido
def obtener_materias_actuales(usuario):
    """GET /api/usuario/materias/actuales"""
    try:
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
    except Exception as e:
        logger.error(f"Error obteniendo materias actuales: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/usuario/materias/aprobadas', methods=['GET'])
@token_requerido
def obtener_materias_aprobadas(usuario):
    """GET /api/usuario/materias/aprobadas"""
    try:
        materias = usuario.obtener_materias_aprobadas()
        
        return jsonify({
            'materias': [{
                'codigo': m.codigo,
                'nombre': m.nombre,
                'creditos': m.creditos,
                'semestre': m.semestre
            } for m in materias]
        })
    except Exception as e:
        logger.error(f"Error obteniendo materias aprobadas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/usuario/materias/inscribir', methods=['POST'])
@token_requerido
def inscribir_materia(usuario):
    """POST /api/usuario/materias/inscribir"""
    try:
        data = request.get_json()
        codigo = data.get('codigo_materia')
        
        if not codigo:
            return jsonify({'error': 'codigo_materia requerido'}), 400
        
        usuario.inscribir_materia(codigo)
        return jsonify({'success': True, 'mensaje': 'Materia inscrita'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error inscribiendo materia: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/usuario/materias/cancelar', methods=['POST'])
@token_requerido
def cancelar_materia(usuario):
    """POST /api/usuario/materias/cancelar"""
    try:
        data = request.get_json()
        codigo = data.get('codigo_materia')
        
        if not codigo:
            return jsonify({'error': 'codigo_materia requerido'}), 400
        
        if usuario.cancelar_materia(codigo):
            return jsonify({'success': True, 'mensaje': 'Materia cancelada'}), 200
        else:
            return jsonify({'error': 'No se pudo cancelar la materia'}), 400
    except Exception as e:
        logger.error(f"Error cancelando materia: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINTS DE TAREAS ==========

@app.route('/api/tareas', methods=['GET'])
@token_requerido
def obtener_tareas(usuario):
    """GET /api/tareas?pendientes=true"""
    try:
        solo_pendientes = request.args.get('pendientes', 'false').lower() == 'true'
        
        tareas = usuario.obtener_tareas(solo_pendientes=solo_pendientes)
        
        return jsonify({
            'tareas': [{
                'id': t.id,
                'titulo': t.titulo,
                'descripcion': t.descripcion,
                'tipo': t.tipo,
                'curso': {
                    'codigo': t.curso.codigo,
                    'nombre': t.curso.nombre,
                    'creditos': t.curso.creditos
                },
                'fecha_limite': t.fecha_limite.isoformat(),
                'hora_limite': '23:59',
                'horas_estimadas': t.horas_estimadas,
                'dificultad': t.dificultad,
                'prioridad': t.prioridad,
                'completada': t.completada,
                'porcentaje_completado': t.porcentaje_completado,
                'dias_restantes': t.dias_restantes()
            } for t in tareas]
        })
    except Exception as e:
        logger.error(f"Error obteniendo tareas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tareas', methods=['POST'])
@token_requerido
def crear_tarea(usuario):
    """POST /api/tareas"""
    try:
        data = request.get_json()
        
        # Validar datos si el validador está disponible
        if VALIDATORS_AVAILABLE:
            es_valido, mensaje_error = validar_datos_tarea(data)
            if not es_valido:
                return jsonify({'error': mensaje_error}), 400
        else:
            # Validación básica
            campos_requeridos = ['curso_codigo', 'titulo', 'tipo', 'fecha_limite']
            for campo in campos_requeridos:
                if campo not in data:
                    return jsonify({'error': f'Campo requerido: {campo}'}), 400

        horas_estimadas = data.get('horas_estimadas', 4)
        dificultad = data.get('dificultad', 3)

        try:
            horas_estimadas = float(horas_estimadas)
        except (TypeError, ValueError):
            return jsonify({'error': 'horas_estimadas debe ser un numero'}), 400

        try:
            dificultad = int(dificultad)
        except (TypeError, ValueError):
            return jsonify({'error': 'dificultad debe ser un numero'}), 400

        if dificultad < 1 or dificultad > 5:
            return jsonify({'error': 'dificultad debe estar entre 1 y 5'}), 400

        tarea = usuario.agregar_tarea(
            curso_codigo=data['curso_codigo'],
            titulo=data['titulo'],
            tipo=data['tipo'],
            fecha_limite=data['fecha_limite'],
            descripcion=data.get('descripcion', ''),
            horas_estimadas=horas_estimadas,
            dificultad=dificultad
        )
        
        return jsonify({
            'success': True,
            'tarea': {
                'id': tarea.id,
                'titulo': tarea.titulo,
                'curso': tarea.curso.nombre
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando tarea: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
@token_requerido
def eliminar_tarea(usuario, tarea_id):
    """DELETE /api/tareas/{id}"""
    try:
        tarea = Tarea.obtener_por_id(tarea_id)
        
        if not tarea or tarea.usuario_id != usuario.id:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        tarea.eliminar()
        return jsonify({'success': True, 'mensaje': 'Tarea eliminada'}), 200
    except Exception as e:
        logger.error(f"Error eliminando tarea: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tareas/<int:tarea_id>/completar', methods=['POST'])
@token_requerido
def completar_tarea(usuario, tarea_id):
    """POST /api/tareas/{id}/completar"""
    try:
        tarea = Tarea.obtener_por_id(tarea_id)
        
        if not tarea or tarea.usuario_id != usuario.id:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        tarea.marcar_completada()
        return jsonify({'success': True, 'mensaje': 'Tarea completada'}), 200
    except Exception as e:
        logger.error(f"Error completando tarea: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tareas/<int:tarea_id>/progreso', methods=['POST'])
@token_requerido
def actualizar_progreso(usuario, tarea_id):
    """POST /api/tareas/{id}/progreso"""
    try:
        tarea = Tarea.obtener_por_id(tarea_id)
        
        if not tarea or tarea.usuario_id != usuario.id:
            return jsonify({'error': 'Tarea no encontrada'}), 404
        
        data = request.get_json()
        porcentaje = data.get('porcentaje')
        
        if porcentaje is None:
            return jsonify({'error': 'porcentaje requerido'}), 400
        
        tarea.actualizar_progreso(int(porcentaje))
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error actualizando progreso: {e}")
        return jsonify({'error': str(e)}), 500


# ========== ENDPOINTS DE RECOMENDACIONES ==========

@app.route('/api/recomendaciones', methods=['GET'])
@token_requerido
def obtener_recomendaciones(usuario):
    """GET /api/recomendaciones?limite=5"""
    try:
        limite = request.args.get('limite', 5, type=int)
        
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        
        # Si está disponible el módulo de recomendaciones, usarlo
        if RECOMMENDATIONS_AVAILABLE:
            tareas_recomendadas = generar_recomendaciones(tareas, limite=limite)
        else:
            # Fallback: ordenar por fecha
            tareas_recomendadas = sorted(tareas, key=lambda t: t.fecha_limite)[:limite]
        
        return jsonify({
            'recomendaciones': [{
                'id': t.id,
                'titulo': t.titulo,
                'curso': t.curso.nombre,
                'fecha_limite': t.fecha_limite.isoformat(),
                'dias_restantes': t.dias_restantes(),
                'horas_estimadas': t.horas_estimadas,
                'dificultad': t.dificultad
            } for t in tareas_recomendadas]
        })
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recomendaciones/tareas-urgentes', methods=['GET'])
@token_requerido
def obtener_urgentes(usuario):
    """GET /api/recomendaciones/tareas-urgentes?dias=3"""
    try:
        dias = request.args.get('dias', 3, type=int)
        
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        
        if RECOMMENDATIONS_AVAILABLE:
            urgentes = obtener_tareas_urgentes(tareas, dias_umbral=dias)
        else:
            urgentes = [t for t in tareas if t.dias_restantes() <= dias]
        
        return jsonify({
            'tareas_urgentes': [{
                'id': t.id,
                'titulo': t.titulo,
                'curso': t.curso.nombre,
                'fecha_limite': t.fecha_limite.isoformat(),
                'dias_restantes': t.dias_restantes()
            } for t in urgentes]
        })
    except Exception as e:
        logger.error(f"Error obteniendo urgentes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticas', methods=['GET'])
@token_requerido
def obtener_estadisticas(usuario):
    """GET /api/estadisticas"""
    try:
        stats = usuario.obtener_estadisticas()
        stats['horas_pendientes'] = stats['pendientes'] * 4
        
        return jsonify({'estadisticas': stats})
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticas/detalladas', methods=['GET'])
@token_requerido
def obtener_estadisticas_detalladas(usuario):
    """GET /api/estadisticas/detalladas"""
    try:
        tareas = usuario.obtener_tareas()
        tareas_pendientes = [t for t in tareas if not t.completada]

        if RECOMMENDATIONS_AVAILABLE:
            stats_funcionales = calcular_estadisticas_funcionales(tareas)
        else:
            total_tareas = len(tareas)
            completadas = len([t for t in tareas if t.completada])
            pendientes = total_tareas - completadas
            horas_pendientes = sum(
                (getattr(t, 'horas_estimadas', 0) or 0)
                for t in tareas_pendientes
            )
            if pendientes:
                dificultad_promedio = sum(
                    (getattr(t, 'dificultad', 0) or 0)
                    for t in tareas_pendientes
                ) / pendientes
            else:
                dificultad_promedio = 0

            stats_funcionales = {
                'total_tareas': total_tareas,
                'completadas': completadas,
                'pendientes': pendientes,
                'horas_pendientes': round(horas_pendientes, 1),
                'dificultad_promedio': round(dificultad_promedio, 2)
            }

        total_tareas = stats_funcionales.get('total_tareas', len(tareas))
        completadas = stats_funcionales.get('completadas', 0)
        pendientes = stats_funcionales.get('pendientes', 0)
        horas_pendientes = stats_funcionales.get('horas_pendientes', 0)
        dificultad_promedio = stats_funcionales.get('dificultad_promedio', 0)

        tasa_completado = round(
            (completadas / total_tareas) * 100, 1
        ) if total_tareas else 0
        racha_dias = min(completadas, 7) if completadas else 0

        distribucion_materia = {}
        distribucion_tipo = {}
        for tarea in tareas_pendientes:
            materia = (
                tarea.curso.nombre
                if tarea.curso
                else (tarea.curso_codigo or 'Sin curso')
            )
            horas = getattr(tarea, 'horas_estimadas', 0) or 0
            distribucion_materia[materia] = round(
                distribucion_materia.get(materia, 0) + horas, 1
            )

            tipo = tarea.tipo or 'General'
            distribucion_tipo[tipo] = round(
                distribucion_tipo.get(tipo, 0) + horas, 1
            )

        materias_criticas = []
        for tarea in tareas_pendientes:
            try:
                if tarea.dias_restantes() <= 2:
                    materia = (
                        tarea.curso.nombre
                        if tarea.curso
                        else (tarea.curso_codigo or 'Sin curso')
                    )
                    if materia not in materias_criticas:
                        materias_criticas.append(materia)
            except Exception:
                continue

        if not materias_criticas and distribucion_materia:
            materias_criticas = [
                materia for materia, _ in sorted(
                    distribucion_materia.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
            ]

        stats_usuario = usuario.obtener_estadisticas()
        creditos_aprobados = stats_usuario.get('creditos_aprobados', 0)
        creditos_actuales = stats_usuario.get('creditos_actuales', 0)
        total_creditos = 162
        porcentaje_carrera = round(
            (creditos_aprobados / total_creditos) * 100, 1
        ) if total_creditos else 0

        return jsonify({
            'rendimiento': {
                'tasa_completado': tasa_completado,
                'horas_pendientes': horas_pendientes,
                'racha_dias': racha_dias,
                'completadas': completadas,
                'pendientes': pendientes,
                'dificultad_promedio': dificultad_promedio,
                'materias_criticas': materias_criticas
            },
            'distribucion_tiempo': {
                'por_materia': distribucion_materia,
                'por_tipo': distribucion_tipo
            },
            'creditos': {
                'aprobados': creditos_aprobados,
                'actuales': creditos_actuales,
                'porcentaje_carrera': porcentaje_carrera
            }
        }), 200
    except Exception as e:
        logger.error(f"Error obteniendo estadisticas detalladas: {e}")
        return jsonify({'error': str(e)}), 500


# ========== ENDPOINTS DE CALENDARIO (CORREGIDO) ==========

@app.route('/api/calendario/eventos', methods=['GET'])
def obtener_eventos_calendario():
    """GET /api/calendario/eventos?semestre=2025-1"""
    try:
        semestre = request.args.get('semestre')
        
        if semestre:
            eventos = CalendarioInstitucional.obtener_por_semestre(semestre)
        else:
            eventos = CalendarioInstitucional.obtener_proximos(dias=90)
        
        return jsonify({
            'eventos': [{
                'id': e.id,
                'nombre_evento': e.nombre_evento,
                'descripcion': e.descripcion if hasattr(e, 'descripcion') else '',
                'fecha_inicio': e.fecha_inicio.isoformat() if hasattr(e.fecha_inicio, 'isoformat') else str(e.fecha_inicio),
                'fecha_fin': e.fecha_fin.isoformat() if e.fecha_fin and hasattr(e.fecha_fin, 'isoformat') else (str(e.fecha_fin) if e.fecha_fin else None),
                'tipo': e.tipo,
                'semestre': e.semestre,
                'icono': e.icono if hasattr(e, 'icono') else '📅',
                'color': e.color
            } for e in eventos]
        })
    except Exception as e:
        logger.error(f"Error obteniendo eventos calendario: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error obteniendo calendario: {str(e)}'}), 500


# ========== ENDPOINTS AVANZADOS (con fallback si módulos no disponibles) ==========

@app.route('/api/recomendaciones/plan-estudio', methods=['GET'])
@token_requerido
def obtener_plan_estudio(usuario):
    """Genera plan de estudio automatizado."""
    try:
        if not RECOMMENDATIONS_AVAILABLE:
            return jsonify({
                'error': 'Módulo de recomendaciones no disponible',
                'codigo': 'MODULE_NOT_AVAILABLE'
            }), 503
        
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
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        plan = generar_plan_estudio(tareas, horas_diarias)
        plan = plan[:dias]
        
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
        if LOGGER_AVAILABLE:
            log_error_with_context(logger, e, {
                'endpoint': '/api/recomendaciones/plan-estudio',
                'usuario_id': usuario.id
            })
        else:
            logger.error(f"Error generando plan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recomendaciones/carga-semanal', methods=['GET'])
@token_requerido
def obtener_carga_semanal(usuario):
    """Calcula carga de trabajo por materia esta semana."""
    try:
        if not RECOMMENDATIONS_AVAILABLE:
            return jsonify({
                'error': 'Módulo de recomendaciones no disponible',
                'codigo': 'MODULE_NOT_AVAILABLE'
            }), 503
        
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        carga = calcular_carga_semanal(tareas)
        total_horas = sum(carga.values())
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
        logger.error(f"Error calculando carga: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notificaciones', methods=['GET'])
@token_requerido
def obtener_notificaciones(usuario):
    """Obtiene todas las notificaciones del usuario."""
    try:
        if not NOTIFICATIONS_AVAILABLE:
            return jsonify({
                'notificaciones': [],
                'total': 0,
                'mensaje': 'Módulo de notificaciones no disponible'
            }), 200
        
        solo_no_leidas = request.args.get('solo_no_leidas', 'false').lower() == 'true'
        limite = request.args.get('limite', 20, type=int)
        
        notificaciones = gestor_notificaciones.generar_notificaciones_usuario(usuario)
        
        if solo_no_leidas:
            notificaciones = [n for n in notificaciones if not n.leida]
        
        notificaciones = notificaciones[:limite]
        
        return jsonify({
            'notificaciones': [n.to_dict() for n in notificaciones],
            'total': len(notificaciones)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo notificaciones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notificaciones/<notif_id>/marcar-leida', methods=['POST'])
@token_requerido
def marcar_notificacion_leida(usuario, notif_id):
    """Marca una notificacion como leida (sin persistencia)."""
    try:
        return jsonify({
            'success': True,
            'id': notif_id
        }), 200
    except Exception as e:
        logger.error(f"Error marcando notificacion: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notificaciones/no-leidas/contar', methods=['GET'])
@token_requerido
def contar_notificaciones_no_leidas(usuario):
    """Cuenta notificaciones no leidas del usuario."""
    try:
        if not NOTIFICATIONS_AVAILABLE:
            return jsonify({
                'no_leidas': 0,
                'mensaje': 'Modulo de notificaciones no disponible'
            }), 200

        notificaciones = gestor_notificaciones.generar_notificaciones_usuario(usuario)
        no_leidas = len([n for n in notificaciones if not n.leida])

        return jsonify({'no_leidas': no_leidas}), 200
    except Exception as e:
        logger.error(f"Error contando notificaciones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logros', methods=['GET'])
@token_requerido
def obtener_logros(usuario):
    """Obtiene logros desbloqueados y progreso del usuario."""
    try:
        stats = usuario.obtener_estadisticas()
        
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
            }
        ]
        
        logros_desbloqueados = []
        for logro in logros_disponibles:
            if logro['requisito'](stats):
                logros_desbloqueados.append({
                    'id': logro['id'],
                    'nombre': logro['nombre'],
                    'descripcion': logro['descripcion'],
                    'emoji': logro['emoji'],
                    'fecha_obtenido': datetime.now().isoformat()
                })
        
        exp_total = stats['completadas'] * 10 + stats['creditos_aprobados'] * 20
        nivel_actual = exp_total // 100
        exp_actual = exp_total % 100
        exp_siguiente = 100

        estadisticas_generales = {
            'tareas_completadas': stats.get('completadas', 0),
            'creditos_aprobados': stats.get('creditos_aprobados', 0),
            'materias_cursando': stats.get('materias_actuales', 0)
        }
        
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
            'estadisticas_generales': estadisticas_generales
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo logros: {e}")
        return jsonify({'error': str(e)}), 500


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    """Maneja rutas no encontradas (404)."""
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Maneja errores internos del servidor (500)."""
    return jsonify({'error': 'Error interno del servidor'}), 500


# ========== MAIN ==========

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Iniciando UniPlanner API")
    print("=" * 70)
    print(f"📍 Servidor: http://localhost:5000")
    print(f"🔧 Ambiente: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"📦 Módulos cargados:")
    print(f"   - Config: {'✅' if CONFIG_AVAILABLE else '❌'}")
    print(f"   - Logger: {'✅' if LOGGER_AVAILABLE else '❌'}")
    print(f"   - Validators: {'✅' if VALIDATORS_AVAILABLE else '❌'}")
    print(f"   - Recommendations: {'✅' if RECOMMENDATIONS_AVAILABLE else '❌'}")
    print(f"   - Notifications: {'✅' if NOTIFICATIONS_AVAILABLE else '❌'}")
    print("=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
