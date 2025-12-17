"""
Usa programacion funcional (map, filter, reduce) para generar
recomendaciones personalizadas de tareas basadas en multiples criterios.
"""

from datetime import datetime, timedelta
from functools import reduce
import operator
from typing import Callable, Dict, List, Tuple

# ========== FUNCIONES DE CALCULO (PROGRAMACION FUNCIONAL PURA) ==========


def calcular_urgencia(tarea, fecha_actual: datetime) -> float:
    """
    Calcula un puntaje de urgencia segun los dias restantes.

    Args:
        tarea: Objeto con fecha_limite.
        fecha_actual: Fecha de referencia.

    Returns:
        Puntaje entre 0 y 10.
    """
    dias_restantes = (tarea.fecha_limite - fecha_actual).days
    return max(0, min(10, 10 - dias_restantes))


def calcular_peso_materia(tarea) -> float:
    """
    Calcula el peso base de la materia segun sus creditos.

    Args:
        tarea: Objeto con curso.creditos.

    Returns:
        Puntaje ponderado por creditos.
    """
    return tarea.curso.creditos * 2


def calcular_factor_dificultad(tarea) -> float:
    """
    Calcula el aporte de dificultad a la prioridad.

    Args:
        tarea: Objeto con dificultad.

    Returns:
        Puntaje ponderado por dificultad.
    """
    return tarea.dificultad * 1.5


def calcular_factor_tiempo(tarea) -> float:
    """
    Calcula un factor segun horas estimadas.

    Args:
        tarea: Objeto con horas_estimadas.

    Returns:
        Puntaje proporcional al tiempo estimado.
    """
    if tarea.horas_estimadas > 8:
        return tarea.horas_estimadas * 0.3
    return tarea.horas_estimadas * 0.2


def calcular_bonus_tipo(tarea) -> float:
    """
    Asigna un bono segun el tipo de tarea.

    Args:
        tarea: Objeto con tipo.

    Returns:
        Bono asociado al tipo (puede ser 0).
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


# ========== FUNCION PRINCIPAL DE PUNTAJE ==========


def calcular_puntaje_prioridad(tarea, fecha_actual: datetime) -> float:
    """
    Calcula el puntaje total de prioridad de una tarea.

    Args:
        tarea: Objeto Tarea.
        fecha_actual: Fecha usada como referencia.

    Returns:
        Puntaje combinado de urgencia, peso, dificultad y tiempo.
    """
    urgencia = calcular_urgencia(tarea, fecha_actual)
    peso = calcular_peso_materia(tarea)
    dificultad = calcular_factor_dificultad(tarea)
    tiempo = calcular_factor_tiempo(tarea)
    bonus = calcular_bonus_tipo(tarea)

    return urgencia + peso + dificultad + tiempo + bonus


# ========== FUNCIONES DE ALTO ORDEN ==========


def generar_recomendaciones(
    tareas: List,
    fecha_actual: datetime = None,
    limite: int = 5
) -> List:
    """
    Genera recomendaciones usando programacion funcional.

    Pipeline:
    1. Filter: Solo tareas pendientes.
    2. Map: Calcular puntaje para cada tarea.
    3. Sort: Ordenar por puntaje descendente.
    4. Slice: Tomar las primeras N tareas.

    Args:
        tareas: Lista de objetos Tarea.
        fecha_actual: Fecha de referencia (default: ahora).
        limite: Numero maximo de recomendaciones.

    Returns:
        Lista de tareas ordenadas por prioridad.
    """
    if fecha_actual is None:
        fecha_actual = datetime.now()

    tareas_pendientes = list(filter(lambda t: not t.completada, tareas))

    tareas_con_puntaje = list(map(
        lambda t: (t, calcular_puntaje_prioridad(t, fecha_actual)),
        tareas_pendientes
    ))

    tareas_ordenadas = sorted(
        tareas_con_puntaje,
        key=lambda x: x[1],
        reverse=True
    )

    top_tareas = list(map(lambda x: x[0], tareas_ordenadas[:limite]))

    return top_tareas


def calcular_carga_semanal(tareas: List) -> Dict[str, float]:
    """
    Calcula la carga semanal por materia usando reduce.

    Args:
        tareas: Lista de tareas pendientes.

    Returns:
        Diccionario {nombre_materia: total_horas}.
    """
    tareas_pendientes = filter(lambda t: not t.completada, tareas)

    def acumular_horas(acumulador: Dict, tarea) -> Dict:
        materia = tarea.curso.nombre
        acumulador[materia] = acumulador.get(materia, 0) + tarea.horas_estimadas
        return acumulador

    carga = reduce(acumular_horas, tareas_pendientes, {})

    return dict(sorted(carga.items(), key=lambda x: x[1], reverse=True))


def agrupar_tareas_por_tipo(tareas: List) -> Dict[str, List]:
    """
    Agrupa tareas por tipo usando programacion funcional.

    Returns:
        Diccionario {tipo: [lista_de_tareas]}.
    """
    tipos_unicos = set(map(lambda t: t.tipo, tareas))

    return {
        tipo: list(filter(lambda t: t.tipo == tipo, tareas))
        for tipo in tipos_unicos
    }


def obtener_tareas_urgentes(tareas: List, dias_umbral: int = 3) -> List:
    """
    Filtra tareas que vencen en los proximos N dias.

    Args:
        tareas: Lista de tareas.
        dias_umbral: Dias de anticipacion.

    Returns:
        Lista de tareas urgentes.
    """
    fecha_limite = datetime.now() + timedelta(days=dias_umbral)

    return list(filter(
        lambda t: not t.completada and t.fecha_limite <= fecha_limite,
        tareas
    ))


def calcular_estadisticas_funcionales(tareas: List) -> Dict:
    """
    Calcula estadisticas usando solo programacion funcional.

    Usa map, filter y reduce para calcular el resumen de tareas.
    """
    total = len(tareas)

    completadas = len(list(filter(lambda t: t.completada, tareas)))
    pendientes = total - completadas

    horas_pendientes = reduce(
        operator.add,
        map(lambda t: t.horas_estimadas,
            filter(lambda t: not t.completada, tareas)),
        0
    )

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


def generar_plan_estudio(
    tareas: List,
    horas_disponibles_diarias: float = 4
) -> List[Dict]:
    """
    Genera un plan de estudio distribuyendo tareas en los proximos dias.

    Esta funcion combina varias tecnicas funcionales:
    - Filter para tareas pendientes.
    - Map para calcular prioridades.
    - Reduce para distribuir en dias.

    Args:
        tareas: Lista de todas las tareas.
        horas_disponibles_diarias: Horas disponibles por dia.

    Returns:
        Lista de diccionarios con el plan por dia.
    """
    tareas_prioritarias = generar_recomendaciones(tareas, limite=10)

    plan = []
    dia_actual = datetime.now()
    horas_restantes_hoy = horas_disponibles_diarias
    tareas_del_dia = []

    for tarea in tareas_prioritarias:
        if tarea.horas_estimadas <= horas_restantes_hoy:
            tareas_del_dia.append(tarea)
            horas_restantes_hoy -= tarea.horas_estimadas
        else:
            if tareas_del_dia:
                plan.append({
                    'fecha': dia_actual.date(),
                    'tareas': tareas_del_dia,
                    'horas_totales': horas_disponibles_diarias - horas_restantes_hoy
                })

            dia_actual += timedelta(days=1)
            horas_restantes_hoy = horas_disponibles_diarias
            tareas_del_dia = [tarea]
            horas_restantes_hoy -= tarea.horas_estimadas

    if tareas_del_dia:
        plan.append({
            'fecha': dia_actual.date(),
            'tareas': tareas_del_dia,
            'horas_totales': horas_disponibles_diarias - horas_restantes_hoy
        })

    return plan


# ========== COMPOSICION DE FUNCIONES ==========


def compose(*functions: Callable) -> Callable:
    """
    Compone multiples funciones en una sola.

    compose(f, g, h)(x) = f(g(h(x)))
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


# Ejemplo de composicion
filtrar_pendientes = lambda tareas: filter(lambda t: not t.completada, tareas)
ordenar_por_fecha = lambda tareas: sorted(tareas, key=lambda t: t.fecha_limite)
tomar_primeros_5 = lambda tareas: list(tareas)[:5]

obtener_proximas_5_pendientes = compose(
    tomar_primeros_5,
    ordenar_por_fecha,
    list,
    filtrar_pendientes
)


# ========== EJEMPLO DE USO ==========

if __name__ == "__main__":
    from poo_models_postgres import Usuario

    print("Sistema de recomendaciones inteligentes\n")
    print("=" * 60)

    usuario = Usuario.autenticar('estudiante', '1234')
    if not usuario:
        print("Usuario no encontrado. Ejecuta primero el script de BD.")
        raise SystemExit(1)

    tareas = usuario.obtener_tareas()

    print("\nTOP 5 RECOMENDACIONES PARA HOY:")
    print("-" * 60)
    recomendaciones = generar_recomendaciones(tareas, limite=5)

    for i, tarea in enumerate(recomendaciones, 1):
        puntaje = calcular_puntaje_prioridad(tarea, datetime.now())
        dias = tarea.dias_restantes()
        print(f"{i}. {tarea.titulo}")
        print(f"   Materia: {tarea.curso.nombre}")
        print(f"   Vence en: {dias} dias | Dificultad: {tarea.dificultad}/5")
        print(f"   Horas estimadas: {tarea.horas_estimadas}h | Puntaje: {puntaje:.1f}")
        print()

    print("\nCARGA DE TRABAJO POR MATERIA:")
    print("-" * 60)
    carga = calcular_carga_semanal(tareas)
    for materia, horas in list(carga.items())[:5]:
        barra = "-" * int(horas / 2)
        print(f"{materia[:40]:40} {barra} {horas:.1f}h")

    print("\nESTADISTICAS GENERALES:")
    print("-" * 60)
    stats = calcular_estadisticas_funcionales(tareas)
    print(f"Total de tareas: {stats['total_tareas']}")
    print(f"Completadas: {stats['completadas']}")
    print(f"Pendientes: {stats['pendientes']}")
    print(f"Horas pendientes: {stats['horas_pendientes']}h")
    print(f"Dificultad promedio: {stats['dificultad_promedio']}/5")
    print(f"Mas urgente: {stats['tarea_mas_urgente']}")

    print("\nTAREAS URGENTES (proximos 3 dias):")
    print("-" * 60)
    urgentes = obtener_tareas_urgentes(tareas, dias_umbral=3)
    if urgentes:
        for tarea in urgentes:
            print(f"* {tarea.titulo} ({tarea.curso.nombre})")
            print(f"  Vence: {tarea.fecha_limite.date()}")
    else:
        print("No hay tareas urgentes")

    print("\nPLAN DE ESTUDIO (4 horas/dia):")
    print("-" * 60)
    plan = generar_plan_estudio(tareas, horas_disponibles_diarias=4)
    for dia in plan[:3]:
        print(f"\n{dia['fecha']} ({dia['horas_totales']:.1f}h totales):")
        for tarea in dia['tareas']:
            print(f"  * {tarea.titulo} - {tarea.horas_estimadas}h")

    print("\n" + "=" * 60)
    print("Recomendaciones generadas usando programacion funcional pura")
