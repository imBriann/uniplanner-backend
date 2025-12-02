"""
API REST con Flask - Sistema Académico Unipamplona
ACTUALIZADO para la estructura correcta de BD
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps

# Importar modelos actualizados
from poo_models_postgres import Usuario, Curso, Tarea, CalendarioInstitucional

# Configuración
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False

# ========== AUTENTICACIÓN JWT ==========

def generar_token(usuario_id: int) -> str:
    """Genera un token JWT para el usuario"""
    payload = {
        'user_id': usuario_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_requerido(f):
    """Decorator para endpoints que requieren autenticación"""
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            usuario_id = data['user_id']
            
            usuario = Usuario.obtener_por_id(usuario_id)
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 401
            
            return f(usuario, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
    
    return decorador


# ========== ENDPOINTS DE AUTENTICACIÓN ==========

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    """POST /api/auth/registro"""
    try:
        data = request.get_json()
        
        campos_requeridos = ['nombre', 'apellido', 'email', 'password', 
                            'semestre_actual', 'tipo_estudio']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'error': f'Campo requerido: {campo}'}), 400
        
        if data['tipo_estudio'] not in ['intensivo', 'moderado', 'leve']:
            return jsonify({'error': 'tipo_estudio debe ser: intensivo, moderado o leve'}), 400
        
        usuario = Usuario.crear(
            nombre=data['nombre'],
            apellido=data['apellido'],
            email=data['email'],
            password=data['password'],
            semestre_actual=int(data['semestre_actual']),
            tipo_estudio=data['tipo_estudio'],
            materias_aprobadas=data.get('materias_aprobadas', []),
            materias_cursando=data.get('materias_cursando', [])
        )
        
        token = generar_token(usuario.id)
        
        # Asegurar que el token es string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
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
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """POST /api/auth/login"""
    try:
        data = request.get_json()
        print(f"📩 Intento de login: {data.get('email')}")
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña requeridos'}), 400
        
        usuario = Usuario.autenticar(data['email'], data['password'])
        
        if not usuario:
            print("❌ Usuario no encontrado o contraseña incorrecta")
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        print(f"✅ Usuario encontrado: {usuario.id}")
        
        token = generar_token(usuario.id)
        
        # Asegurar que el token es string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        print(f"🔑 Token generado: {token[:10]}...")
        
        return jsonify({
            'success': True,
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
        import traceback
        traceback.print_exc()
        print(f"🔥 ERROR CRÍTICO: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


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
    """GET /api/usuario/perfil"""
    stats = usuario.obtener_estadisticas()
    
    # Configuración ficticia para compatibilidad
    config = {
        'tipo_estudio': usuario.tipo_estudio,
        'horas_diarias': {'intensivo': 6, 'moderado': 4, 'leve': 2.5}.get(usuario.tipo_estudio, 4),
        'dias_semana': [1,2,3,4,5],
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
        'configuracion_estudio': config
    })


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


# ========== ENDPOINTS DE TAREAS ==========

@app.route('/api/tareas', methods=['GET'])
@token_requerido
def obtener_tareas(usuario):
    """GET /api/tareas?pendientes=true"""
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


@app.route('/api/tareas', methods=['POST'])
@token_requerido
def crear_tarea(usuario):
    """POST /api/tareas"""
    try:
        data = request.get_json()
        
        campos_requeridos = ['curso_codigo', 'titulo', 'tipo', 'fecha_limite']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'error': f'Campo requerido: {campo}'}), 400
        
        tarea = usuario.agregar_tarea(
            curso_codigo=data['curso_codigo'],
            titulo=data['titulo'],
            tipo=data['tipo'],
            fecha_limite=data['fecha_limite'],
            descripcion=data.get('descripcion', '')
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
        return jsonify({'error': str(e)}), 400


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
@token_requerido
def eliminar_tarea(usuario, tarea_id):
    """DELETE /api/tareas/{id}"""
    tarea = Tarea.obtener_por_id(tarea_id)
    
    if not tarea or tarea.usuario_id != usuario.id:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    
    tarea.eliminar()
    return jsonify({'success': True, 'mensaje': 'Tarea eliminada'}), 200


@app.route('/api/tareas/<int:tarea_id>/completar', methods=['POST'])
@token_requerido
def completar_tarea(usuario, tarea_id):
    """POST /api/tareas/{id}/completar"""
    tarea = Tarea.obtener_por_id(tarea_id)
    
    if not tarea or tarea.usuario_id != usuario.id:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    
    tarea.marcar_completada()
    return jsonify({'success': True, 'mensaje': 'Tarea completada'}), 200


@app.route('/api/tareas/<int:tarea_id>/progreso', methods=['POST'])
@token_requerido
def actualizar_progreso(usuario, tarea_id):
    """POST /api/tareas/{id}/progreso"""
    tarea = Tarea.obtener_por_id(tarea_id)
    
    if not tarea or tarea.usuario_id != usuario.id:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    
    data = request.get_json()
    porcentaje = data.get('porcentaje')
    
    if porcentaje is None:
        return jsonify({'error': 'porcentaje requerido'}), 400
    
    tarea.actualizar_progreso(int(porcentaje))
    return jsonify({'success': True}), 200


# ========== ENDPOINTS DE RECOMENDACIONES ==========

@app.route('/api/recomendaciones', methods=['GET'])
@token_requerido
def obtener_recomendaciones(usuario):
    """GET /api/recomendaciones?limite=5"""
    limite = request.args.get('limite', 5, type=int)
    
    tareas = usuario.obtener_tareas(solo_pendientes=True)
    
    # Ordenar por fecha y tomar las primeras N
    tareas_ordenadas = sorted(tareas, key=lambda t: t.fecha_limite)[:limite]
    
    return jsonify({
        'recomendaciones': [{
            'id': t.id,
            'titulo': t.titulo,
            'curso': t.curso.nombre,
            'fecha_limite': t.fecha_limite.isoformat(),
            'dias_restantes': t.dias_restantes(),
            'horas_estimadas': t.horas_estimadas,
            'dificultad': t.dificultad
        } for t in tareas_ordenadas]
    })


@app.route('/api/recomendaciones/tareas-urgentes', methods=['GET'])
@token_requerido
def obtener_urgentes(usuario):
    """GET /api/recomendaciones/tareas-urgentes?dias=3"""
    dias = request.args.get('dias', 3, type=int)
    
    tareas = usuario.obtener_tareas(solo_pendientes=True)
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


@app.route('/api/estadisticas', methods=['GET'])
@token_requerido
def obtener_estadisticas(usuario):
    """GET /api/estadisticas"""
    stats = usuario.obtener_estadisticas()
    
    # Añadir datos ficticios para compatibilidad
    stats['horas_pendientes'] = stats['pendientes'] * 4
    
    return jsonify({
        'estadisticas': stats
    })


# ========== ENDPOINTS DE CALENDARIO ==========

@app.route('/api/calendario/eventos', methods=['GET'])
def obtener_eventos_calendario():
    """GET /api/calendario/eventos?semestre=2025-1"""
    semestre = request.args.get('semestre')
    
    if semestre:
        eventos = CalendarioInstitucional.obtener_por_semestre(semestre)
    else:
        eventos = CalendarioInstitucional.obtener_proximos(dias=90)
    
    return jsonify({
        'eventos': [{
            'id': e.id,
            'nombre_evento': e.nombre_evento,
            'descripcion': e.descripcion,
            'fecha_inicio': e.fecha_inicio.isoformat(),
            'fecha_fin': e.fecha_fin.isoformat() if e.fecha_fin else None,
            'tipo': e.tipo,
            'semestre': e.semestre,
            'icono': e.icono,
            'color': e.color
        } for e in eventos]
    })


# ========== HEALTH CHECK ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    """GET /api/health"""
    return jsonify({
        'status': 'ok',
        'mensaje': 'API funcionando correctamente',
        'version': '2.0.0 - Estructura Actualizada'
    })


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500


# ========== MAIN ==========

if __name__ == '__main__':
    print("🚀 Iniciando API REST - Sistema Académico Unipamplona")
    print("=" * 70)
    print("📡 Servidor corriendo en: http://localhost:5000")
    print("📚 Health Check: http://localhost:5000/api/health")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)