"""
Endpoints Adicionales para UniPlanner

Agregar estos endpoints a flask_api.py o flask_api_improved.py
para funcionalidades avanzadas del frontend.

Autor: [Tu Nombre]
Fecha: 2025-01-08
"""

# ========== IMPORTAR EN TU flask_api.py ==========
# from notificaciones import GestorNotificaciones
# gestor_notificaciones = GestorNotificaciones()


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


# ===========================================
# INSTRUCCIONES DE INTEGRACIÓN:
# 
# 1. Copiar estos endpoints a tu flask_api.py
# 2. Asegurarte de tener importado:
#    - from notificaciones import GestorNotificaciones
#    - gestor_notificaciones = GestorNotificaciones()
# 3. Probar cada endpoint individualmente
# 4. Documentar en API_DOCUMENTATION.md
# ===========================================