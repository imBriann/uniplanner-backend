"""
Módulo de Recomendaciones Inteligentes
Usa programación funcional pura (map, filter, reduce) para generar
recomendaciones personalizadas de tareas basadas en múltiples criterios
"""

from datetime import datetime, timedelta
from typing import List, Dict, Callable, Tuple
from functools import reduce
import operator

# ========== FUNCIONES DE CÁLCULO (PROGRAMACIÓN FUNCIONAL PURA) ==========

def calcular_urgencia(tarea, fecha_actual: datetime) -> float:
    """
    Calcula la urgencia de una tarea basado en días restantes
    
    Fórmula: Mientras más cerca la fecha, mayor urgencia (0-10)
    - 0 días = urgencia 10
    - 10+ días = urgencia 0
    """
    dias_restantes = (tarea.fecha_limite - fecha_actual).days
    return max(0, min(10, 10 - dias_restantes))


def calcular_peso_materia(tarea) -> float:
    """
    Calcula el peso de la materia según créditos
    
    Fórmula: peso = creditos * 2
    """
    return tarea.curso.creditos * 2


def calcular_factor_dificultad(tarea) -> float:
    """
    Calcula el factor de dificultad de la tarea
    
    Fórmula: dificultad * 1.5
    """
    return tarea.dificultad * 1.5


def calcular_factor_tiempo(tarea) -> float:
    """
    Calcula el factor de tiempo requerido
    
    Fórmula: Si requiere más de 8h, aumenta el peso
    """
    if tarea.horas_estimadas > 8:
        return tarea.horas_estimadas * 0.3
    return tarea.horas_estimadas * 0.2


def calcular_bonus_tipo(tarea) -> float:
    """
    Asigna bonus según el tipo de tarea
    
    parcial/final = +5 puntos
    proyecto = +3 puntos
    taller = +1 punto
    lectura = +0.5 puntos
    """
    bonus_map = {
        'parcial': 5.0,
        'final': 5.0,
        'proyecto': 3.0,
        'taller': 1.0,
        'exposicion': 2.0,
        'lectura': 0.5
    }
    return bonus_map.get(tarea.tipo.lower(), 0)


# ========== FUNCIÓN PRINCIPAL DE PUNTAJE ==========

def calcular_puntaje_prioridad(tarea, fecha_actual: datetime) -> float:
    """
    Calcula el puntaje de prioridad combinando todos los factores
    
    Puntaje = urgencia + peso_materia + dificultad + tiempo + bonus_tipo
    
    Esta es una función pura que no tiene efectos secundarios
    """
    urgencia = calcular_urgencia(tarea, fecha_actual)
    peso = calcular_peso_materia(tarea)
    dificultad = calcular_factor_dificultad(tarea)
    tiempo = calcular_factor_tiempo(tarea)
    bonus = calcular_bonus_tipo(tarea)
    
    return urgencia + peso + dificultad + tiempo + bonus


# ========== FUNCIONES DE ALTO ORDEN (FUNCTIONAL PROGRAMMING) ==========

def generar_recomendaciones(tareas: List, fecha_actual: datetime = None, 
                           limite: int = 5) -> List:
    """
    Genera recomendaciones usando programación funcional pura
    
    Pipeline funcional:
    1. Filter: Solo tareas pendientes
    2. Map: Calcular puntaje para cada tarea
    3. Sort: Ordenar por puntaje descendente
    4. Slice: Tomar las primeras N tareas
    
    Args:
        tareas: Lista de objetos Tarea
        fecha_actual: Fecha de referencia (default: hoy)
        limite: Número máximo de recomendaciones
    
    Returns:
        Lista de tareas ordenadas por prioridad
    """
    if fecha_actual is None:
        fecha_actual = datetime.now()
    
    # PARADIGMA FUNCIONAL: Filter + Map + Sort
    
    # 1. Filtrar solo tareas pendientes
    tareas_pendientes = list(filter(lambda t: not t.completada, tareas))
    
    # 2. Mapear cada tarea a una tupla (tarea, puntaje)
    tareas_con_puntaje = list(map(
        lambda t: (t, calcular_puntaje_prioridad(t, fecha_actual)),
        tareas_pendientes
    ))
    
    # 3. Ordenar por puntaje descendente
    tareas_ordenadas = sorted(
        tareas_con_puntaje,
        key=lambda x: x[1],  # Ordenar por puntaje
        reverse=True
    )
    
    # 4. Tomar solo las primeras N y extraer solo las tareas
    top_tareas = list(map(lambda x: x[0], tareas_ordenadas[:limite]))
    
    return top_tareas


def calcular_carga_semanal(tareas: List) -> Dict[str, float]:
    """
    Calcula la carga de trabajo semanal por materia usando reduce
    
    Usa REDUCE para acumular horas por materia
    
    Args:
        tareas: Lista de tareas pendientes
    
    Returns:
        Diccionario {nombre_materia: total_horas}
    """
    # Filtrar solo tareas pendientes
    tareas_pendientes = filter(lambda t: not t.completada, tareas)
    
    # Usar reduce para acumular horas por materia
    def acumular_horas(acumulador: Dict, tarea) -> Dict:
        materia = tarea.curso.nombre
        acumulador[materia] = acumulador.get(materia, 0) + tarea.horas_estimadas
        return acumulador
    
    carga = reduce(acumular_horas, tareas_pendientes, {})
    
    # Ordenar por carga descendente
    return dict(sorted(carga.items(), key=lambda x: x[1], reverse=True))


def agrupar_tareas_por_tipo(tareas: List) -> Dict[str, List]:
    """
    Agrupa tareas por tipo usando programación funcional
    
    Returns:
        Diccionario {tipo: [lista_de_tareas]}
    """
    # Obtener todos los tipos únicos
    tipos_unicos = set(map(lambda t: t.tipo, tareas))
    
    # Para cada tipo, filtrar tareas de ese tipo
    return {
        tipo: list(filter(lambda t: t.tipo == tipo, tareas))
        for tipo in tipos_unicos
    }


def obtener_tareas_urgentes(tareas: List, dias_umbral: int = 3) -> List:
    """
    Filtra tareas que vencen en los próximos N días
    
    Args:
        tareas: Lista de tareas
        dias_umbral: Días de anticipación
    
    Returns:
        Lista de tareas urgentes
    """
    fecha_limite = datetime.now() + timedelta(days=dias_umbral)
    
    return list(filter(
        lambda t: not t.completada and t.fecha_limite <= fecha_limite,
        tareas
    ))


def calcular_estadisticas_funcionales(tareas: List) -> Dict:
    """
    Calcula estadísticas usando solo programación funcional
    
    Usa map, filter y reduce para calcular todo
    """
    # Total de tareas
    total = len(tareas)
    
    # Tareas completadas (filter + len)
    completadas = len(list(filter(lambda t: t.completada, tareas)))
    
    # Tareas pendientes
    pendientes = total - completadas
    
    # Total horas pendientes (filter + map + reduce)
    horas_pendientes = reduce(
        operator.add,
        map(lambda t: t.horas_estimadas, 
            filter(lambda t: not t.completada, tareas)),
        0
    )
    
    # Promedio de dificultad (map + reduce + división)
    if pendientes > 0:
        suma_dificultad = reduce(
            operator.add,
            map(lambda t: t.dificultad,
                filter(lambda t: not t.completada, tareas)),
            0
        )
        dificultad_promedio = suma_dificultad / pendientes
    else:
        dificultad_promedio = 0
    
    # Tarea más urgente (max con key)
    tarea_mas_urgente = None
    if pendientes > 0:
        tareas_pendientes = list(filter(lambda t: not t.completada, tareas))
        tarea_mas_urgente = min(
            tareas_pendientes,
            key=lambda t: t.fecha_limite
        )
    
    return {
        'total_tareas': total,
        'completadas': completadas,
        'pendientes': pendientes,
        'horas_pendientes': round(horas_pendientes, 1),
        'dificultad_promedio': round(dificultad_promedio, 2),
        'tarea_mas_urgente': tarea_mas_urgente.titulo if tarea_mas_urgente else None
    }


def generar_plan_estudio(tareas: List, horas_disponibles_diarias: float = 4) -> List[Dict]:
    """
    Genera un plan de estudio distribuyendo tareas en los próximos días
    
    Esta función combina múltiples técnicas funcionales:
    - Filter para tareas pendientes
    - Map para calcular prioridades
    - Reduce para distribuir en días
    
    Args:
        tareas: Lista de todas las tareas
        horas_disponibles_diarias: Horas que el estudiante puede estudiar por día
    
    Returns:
        Lista de diccionarios con el plan por día
    """
    # 1. Obtener tareas recomendadas
    tareas_prioritarias = generar_recomendaciones(tareas, limite=10)
    
    # 2. Distribuir en días
    plan = []
    dia_actual = datetime.now()
    horas_restantes_hoy = horas_disponibles_diarias
    tareas_del_dia = []
    
    for tarea in tareas_prioritarias:
        if tarea.horas_estimadas <= horas_restantes_hoy:
            # Cabe en el día actual
            tareas_del_dia.append(tarea)
            horas_restantes_hoy -= tarea.horas_estimadas
        else:
            # Guardar el día actual y empezar nuevo día
            if tareas_del_dia:
                plan.append({
                    'fecha': dia_actual.date(),
                    'tareas': tareas_del_dia,
                    'horas_totales': horas_disponibles_diarias - horas_restantes_hoy
                })
            
            # Nuevo día
            dia_actual += timedelta(days=1)
            horas_restantes_hoy = horas_disponibles_diarias
            tareas_del_dia = [tarea]
            horas_restantes_hoy -= tarea.horas_estimadas
    
    # Agregar último día si tiene tareas
    if tareas_del_dia:
        plan.append({
            'fecha': dia_actual.date(),
            'tareas': tareas_del_dia,
            'horas_totales': horas_disponibles_diarias - horas_restantes_hoy
        })
    
    return plan


# ========== COMPOSICIÓN DE FUNCIONES ==========

def compose(*functions: Callable) -> Callable:
    """
    Compone múltiples funciones en una sola
    
    compose(f, g, h)(x) = f(g(h(x)))
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


# Ejemplo de composición
filtrar_pendientes = lambda tareas: filter(lambda t: not t.completada, tareas)
ordenar_por_fecha = lambda tareas: sorted(tareas, key=lambda t: t.fecha_limite)
tomar_primeros_5 = lambda tareas: list(tareas)[:5]

# Función compuesta
obtener_proximas_5_pendientes = compose(
    tomar_primeros_5,
    ordenar_por_fecha,
    list,
    filtrar_pendientes
)


# ========== EJEMPLO DE USO ==========

if __name__ == "__main__":
    # Este código requiere que hayas ejecutado primero el script de base de datos
    from poo_models_sqlite import Usuario
    
    print("🎯 Sistema de Recomendaciones Inteligentes\n")
    print("=" * 60)
    
    # 1. Cargar usuario
    usuario = Usuario.autenticar('estudiante', '1234')
    if not usuario:
        print("❌ Usuario no encontrado. Ejecuta primero el script de BD.")
        exit()
    
    tareas = usuario.obtener_tareas()
    
    # 2. Generar recomendaciones
    print("\n📌 TOP 5 RECOMENDACIONES PARA HOY:")
    print("-" * 60)
    recomendaciones = generar_recomendaciones(tareas, limite=5)
    
    for i, tarea in enumerate(recomendaciones, 1):
        puntaje = calcular_puntaje_prioridad(tarea, datetime.now())
        dias = tarea.dias_restantes()
        print(f"{i}. {tarea.titulo}")
        print(f"   Materia: {tarea.curso.nombre}")
        print(f"   Vence en: {dias} días | Dificultad: {tarea.dificultad}/5")
        print(f"   Horas estimadas: {tarea.horas_estimadas}h | Puntaje: {puntaje:.1f}")
        print()
    
    # 3. Carga semanal
    print("\n📊 CARGA DE TRABAJO POR MATERIA:")
    print("-" * 60)
    carga = calcular_carga_semanal(tareas)
    for materia, horas in list(carga.items())[:5]:
        barra = "█" * int(horas / 2)
        print(f"{materia[:40]:40} {barra} {horas:.1f}h")
    
    # 4. Estadísticas
    print("\n📈 ESTADÍSTICAS GENERALES:")
    print("-" * 60)
    stats = calcular_estadisticas_funcionales(tareas)
    print(f"Total de tareas: {stats['total_tareas']}")
    print(f"Completadas: {stats['completadas']}")
    print(f"Pendientes: {stats['pendientes']}")
    print(f"Horas pendientes: {stats['horas_pendientes']}h")
    print(f"Dificultad promedio: {stats['dificultad_promedio']}/5")
    print(f"Más urgente: {stats['tarea_mas_urgente']}")
    
    # 5. Tareas urgentes
    print("\n⚠️  TAREAS URGENTES (próximos 3 días):")
    print("-" * 60)
    urgentes = obtener_tareas_urgentes(tareas, dias_umbral=3)
    if urgentes:
        for tarea in urgentes:
            print(f"• {tarea.titulo} ({tarea.curso.nombre})")
            print(f"  └─ Vence: {tarea.fecha_limite.date()}")
    else:
        print("✓ No hay tareas urgentes")
    
    # 6. Plan de estudio
    print("\n📅 PLAN DE ESTUDIO (4 horas/día):")
    print("-" * 60)
    plan = generar_plan_estudio(tareas, horas_disponibles_diarias=4)
    for dia in plan[:3]:  # Mostrar solo 3 días
        print(f"\n{dia['fecha']} ({dia['horas_totales']:.1f}h totales):")
        for tarea in dia['tareas']:
            print(f"  • {tarea.titulo} - {tarea.horas_estimadas}h")
    
    print("\n" + "=" * 60)
    print("✨ Recomendaciones generadas usando programación funcional pura")

    