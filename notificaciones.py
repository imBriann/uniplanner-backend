"""
Sistema de Notificaciones Inteligentes para UniPlanner

Genera notificaciones y recordatorios personalizados basados en:
- Tareas próximas a vencer
- Patrones de estudio del usuario
- Eventos del calendario académico

Paradigma: Programación Orientada a Objetos + Funcional
Autor: [Tu Nombre]
Fecha: 2025-01-08
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass


class TipoNotificacion(Enum):
    """
    Tipos de notificaciones disponibles en el sistema.
    
    Enum facilita el manejo consistente de tipos y previene errores.
    """
    TAREA_URGENTE = "tarea_urgente"
    TAREA_PROXIMA = "tarea_proxima"
    EVENTO_ACADEMICO = "evento_academico"
    RECORDATORIO_ESTUDIO = "recordatorio_estudio"
    LOGRO_DESBLOQUEADO = "logro_desbloqueado"
    SUGERENCIA_INSCRIPCION = "sugerencia_inscripcion"


class PrioridadNotificacion(Enum):
    """Niveles de prioridad para notificaciones."""
    CRITICA = "critica"      # Debe verse inmediatamente
    ALTA = "alta"            # Importante pero no crítica
    MEDIA = "media"          # Informativa
    BAJA = "baja"            # Opcional


@dataclass
class Notificacion:
    """
    Modelo de datos para notificaciones.
    
    Usa @dataclass para reducir boilerplate code y
    proporcionar métodos __init__, __repr__, etc. automáticamente.
    
    Attributes:
        id: Identificador único
        tipo: Tipo de notificación (enum)
        prioridad: Nivel de importancia
        titulo: Título breve de la notificación
        mensaje: Contenido detallado
        fecha_creacion: Timestamp de creación
        fecha_entrega: Cuándo mostrarla al usuario
        leida: Si fue vista por el usuario
        datos_extra: Información adicional en formato dict
    """
    id: str
    tipo: TipoNotificacion
    prioridad: PrioridadNotificacion
    titulo: str
    mensaje: str
    fecha_creacion: datetime
    fecha_entrega: datetime
    leida: bool = False
    datos_extra: Optional[Dict] = None
    
    def marcar_leida(self):
        """Marca la notificación como leída."""
        self.leida = True
    
    def to_dict(self) -> Dict:
        """
        Convierte la notificación a diccionario para JSON.
        
        Returns:
            Diccionario con todos los campos serializables
        """
        return {
            'id': self.id,
            'tipo': self.tipo.value,
            'prioridad': self.prioridad.value,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_entrega': self.fecha_entrega.isoformat(),
            'leida': self.leida,
            'datos_extra': self.datos_extra or {}
        }


class GeneradorNotificaciones:
    """
    Clase principal para generación de notificaciones.
    
    Implementa el patrón Strategy para diferentes tipos de notificaciones.
    """
    
    def __init__(self):
        """Inicializa el generador con configuración por defecto."""
        self.contador_ids = 0
    
    def _generar_id(self) -> str:
        """
        Genera ID único para notificación.
        
        Returns:
            String con formato "notif_TIMESTAMP_CONTADOR"
        """
        self.contador_ids += 1
        timestamp = int(datetime.now().timestamp())
        return f"notif_{timestamp}_{self.contador_ids}"
    
    def generar_notificacion_tarea_urgente(
        self,
        tarea,
        dias_restantes: int
    ) -> Notificacion:
        """
        Genera notificación para tarea urgente.
        
        Args:
            tarea: Objeto Tarea próxima a vencer
            dias_restantes: Días que quedan hasta la fecha límite
        
        Returns:
            Instancia de Notificacion configurada
        
        Example:
            >>> notif = generador.generar_notificacion_tarea_urgente(
            ...     tarea=mi_tarea,
            ...     dias_restantes=2
            ... )
        """
        # Determinar prioridad según días restantes
        if dias_restantes <= 1:
            prioridad = PrioridadNotificacion.CRITICA
            titulo = f"⚠️ URGENTE: {tarea.titulo} vence {('HOY' if dias_restantes == 0 else 'MAÑANA')}"
        elif dias_restantes <= 3:
            prioridad = PrioridadNotificacion.ALTA
            titulo = f"⏰ {tarea.titulo} vence en {dias_restantes} días"
        else:
            prioridad = PrioridadNotificacion.MEDIA
            titulo = f"📌 Recordatorio: {tarea.titulo}"
        
        # Construir mensaje personalizado
        mensaje = (
            f"La tarea '{tarea.titulo}' de {tarea.curso.nombre} "
            f"vence el {tarea.fecha_limite.strftime('%d/%m/%Y')}. "
            f"Tiempo estimado: {tarea.horas_estimadas}h."
        )
        
        return Notificacion(
            id=self._generar_id(),
            tipo=TipoNotificacion.TAREA_URGENTE,
            prioridad=prioridad,
            titulo=titulo,
            mensaje=mensaje,
            fecha_creacion=datetime.now(),
            fecha_entrega=datetime.now(),
            datos_extra={
                'tarea_id': tarea.id,
                'curso_codigo': tarea.curso_codigo,
                'dias_restantes': dias_restantes,
                'horas_estimadas': tarea.horas_estimadas
            }
        )
    
    def generar_notificacion_evento_academico(
        self,
        evento,
        dias_anticipacion: int = 3
    ) -> Notificacion:
        """
        Genera notificación para evento del calendario académico.
        
        Args:
            evento: Objeto CalendarioInstitucional
            dias_anticipacion: Días antes del evento para notificar
        
        Returns:
            Notificacion configurada
        """
        dias_hasta = (evento.fecha_inicio - datetime.now().date()).days
        
        if dias_hasta <= 1:
            titulo = f"📅 HOY: {evento.nombre_evento}"
            prioridad = PrioridadNotificacion.ALTA
        elif dias_hasta <= 3:
            titulo = f"📅 En {dias_hasta} días: {evento.nombre_evento}"
            prioridad = PrioridadNotificacion.MEDIA
        else:
            titulo = f"📅 Próximamente: {evento.nombre_evento}"
            prioridad = PrioridadNotificacion.BAJA
        
        mensaje = (
            f"{evento.nombre_evento} "
            f"{'comienza' if not evento.fecha_fin else 'es'} "
            f"el {evento.fecha_inicio.strftime('%d/%m/%Y')}"
        )
        
        return Notificacion(
            id=self._generar_id(),
            tipo=TipoNotificacion.EVENTO_ACADEMICO,
            prioridad=prioridad,
            titulo=titulo,
            mensaje=mensaje,
            fecha_creacion=datetime.now(),
            fecha_entrega=datetime.now(),
            datos_extra={
                'evento_id': evento.id,
                'tipo_evento': evento.tipo,
                'fecha_inicio': evento.fecha_inicio.isoformat()
            }
        )
    
    def generar_recordatorio_estudio(
        self,
        usuario,
        materias_pendientes: List
    ) -> Notificacion:
        """
        Genera recordatorio inteligente de estudio.
        
        Args:
            usuario: Objeto Usuario
            materias_pendientes: Lista de materias con tareas pendientes
        
        Returns:
            Notificacion con sugerencia de estudio
        """
        # Determinar mejor horario según tipo de estudio
        horarios = {
            'intensivo': '08:00',
            'moderado': '14:00',
            'leve': '18:00'
        }
        horario = horarios.get(usuario.tipo_estudio, '14:00')
        
        if len(materias_pendientes) == 1:
            titulo = f"📚 Hora de estudiar {materias_pendientes[0].nombre}"
            mensaje = f"Tienes tareas pendientes en {materias_pendientes[0].nombre}. ¡Es buen momento para avanzar!"
        else:
            titulo = f"📚 Tienes {len(materias_pendientes)} materias pendientes"
            mensaje = f"Materias: {', '.join(m.nombre for m in materias_pendientes[:3])}..."
        
        return Notificacion(
            id=self._generar_id(),
            tipo=TipoNotificacion.RECORDATORIO_ESTUDIO,
            prioridad=PrioridadNotificacion.MEDIA,
            titulo=titulo,
            mensaje=mensaje,
            fecha_creacion=datetime.now(),
            fecha_entrega=datetime.now().replace(
                hour=int(horario.split(':')[0]),
                minute=0
            ),
            datos_extra={
                'usuario_id': usuario.id,
                'tipo_estudio': usuario.tipo_estudio,
                'num_materias': len(materias_pendientes)
            }
        )
    
    def generar_notificacion_logro(
        self,
        tipo_logro: str,
        detalles: Dict
    ) -> Notificacion:
        """
        Genera notificación de logro desbloqueado (gamificación).
        
        Args:
            tipo_logro: Tipo de logro alcanzado
            detalles: Información adicional del logro
        
        Returns:
            Notificacion celebratoria
        """
        logros_config = {
            'primera_tarea': {
                'titulo': '🎉 ¡Primer paso!',
                'mensaje': '¡Completaste tu primera tarea! Sigue así.',
                'emoji': '🌟'
            },
            'racha_7_dias': {
                'titulo': '🔥 ¡Racha de 7 días!',
                'mensaje': 'Has usado UniPlanner 7 días seguidos. ¡Increíble dedicación!',
                'emoji': '🔥'
            },
            '10_tareas_completadas': {
                'titulo': '💪 ¡Productivo!',
                'mensaje': '¡Has completado 10 tareas! Tu organización es admirable.',
                'emoji': '⭐'
            },
            'semestre_sin_atrasos': {
                'titulo': '👑 ¡Maestro del tiempo!',
                'mensaje': 'No tienes tareas atrasadas este semestre. ¡Eres un ejemplo!',
                'emoji': '👑'
            }
        }
        
        config = logros_config.get(tipo_logro, {
            'titulo': '🎊 ¡Logro desbloqueado!',
            'mensaje': 'Has alcanzado un nuevo logro.',
            'emoji': '🏆'
        })
        
        return Notificacion(
            id=self._generar_id(),
            tipo=TipoNotificacion.LOGRO_DESBLOQUEADO,
            prioridad=PrioridadNotificacion.BAJA,
            titulo=config['titulo'],
            mensaje=config['mensaje'],
            fecha_creacion=datetime.now(),
            fecha_entrega=datetime.now(),
            datos_extra={
                'tipo_logro': tipo_logro,
                'emoji': config['emoji'],
                **detalles
            }
        )


class GestorNotificaciones:
    """
    Gestor central de notificaciones del usuario.
    
    Coordina la creación, almacenamiento y entrega de notificaciones.
    """
    
    def __init__(self):
        """Inicializa el gestor."""
        self.generador = GeneradorNotificaciones()
        self.notificaciones_cache = []
    
    def generar_notificaciones_usuario(self, usuario) -> List[Notificacion]:
        """
        Genera todas las notificaciones pendientes para un usuario.
        
        Esta función coordina diferentes tipos de notificaciones:
        1. Tareas urgentes
        2. Eventos académicos próximos
        3. Recordatorios de estudio
        4. Logros desbloqueados
        
        Args:
            usuario: Objeto Usuario
        
        Returns:
            Lista de notificaciones ordenadas por prioridad
        
        Example:
            >>> gestor = GestorNotificaciones()
            >>> notificaciones = gestor.generar_notificaciones_usuario(mi_usuario)
            >>> for notif in notificaciones:
            ...     print(notif.titulo)
        """
        notificaciones = []
        
        # 1. Verificar tareas urgentes
        tareas = usuario.obtener_tareas(solo_pendientes=True)
        for tarea in tareas:
            dias = tarea.dias_restantes()
            if dias <= 3:  # Solo notificar tareas con menos de 3 días
                notif = self.generador.generar_notificacion_tarea_urgente(
                    tarea, dias
                )
                notificaciones.append(notif)
        
        # 2. Verificar eventos académicos (implementar cuando se conecte)
        # eventos = CalendarioInstitucional.obtener_proximos(dias=7)
        # for evento in eventos:
        #     notif = self.generador.generar_notificacion_evento_academico(evento)
        #     notificaciones.append(notif)
        
        # 3. Generar recordatorio de estudio (una vez al día)
        materias_con_tareas = set(t.curso for t in tareas)
        if materias_con_tareas:
            notif = self.generador.generar_recordatorio_estudio(
                usuario, list(materias_con_tareas)
            )
            notificaciones.append(notif)
        
        # 4. Verificar logros
        stats = usuario.obtener_estadisticas()
        if stats['completadas'] == 1:
            notif = self.generador.generar_notificacion_logro(
                'primera_tarea',
                {'usuario_id': usuario.id}
            )
            notificaciones.append(notif)
        elif stats['completadas'] == 10:
            notif = self.generador.generar_notificacion_logro(
                '10_tareas_completadas',
                {'total': stats['completadas']}
            )
            notificaciones.append(notif)
        
        # Ordenar por prioridad (crítica primero)
        orden_prioridad = {
            PrioridadNotificacion.CRITICA: 0,
            PrioridadNotificacion.ALTA: 1,
            PrioridadNotificacion.MEDIA: 2,
            PrioridadNotificacion.BAJA: 3
        }
        
        notificaciones.sort(key=lambda n: orden_prioridad[n.prioridad])
        
        return notificaciones
    
    def filtrar_por_prioridad(
        self,
        notificaciones: List[Notificacion],
        prioridad_minima: PrioridadNotificacion
    ) -> List[Notificacion]:
        """
        Filtra notificaciones por nivel de prioridad mínimo.
        
        Args:
            notificaciones: Lista de notificaciones
            prioridad_minima: Prioridad mínima a incluir
        
        Returns:
            Lista filtrada de notificaciones
        """
        orden = {
            PrioridadNotificacion.CRITICA: 0,
            PrioridadNotificacion.ALTA: 1,
            PrioridadNotificacion.MEDIA: 2,
            PrioridadNotificacion.BAJA: 3
        }
        
        umbral = orden[prioridad_minima]
        
        return [
            n for n in notificaciones
            if orden[n.prioridad] <= umbral
        ]


if __name__ == '__main__':
    # Demostración del sistema de notificaciones
    print("🔔 Sistema de Notificaciones UniPlanner\n")
    print("=" * 60)
    
    # Simular generación de notificaciones
    generador = GeneradorNotificaciones()
    
    # Ejemplo 1: Notificación de tarea urgente
    from poo_models_postgres import Tarea, Curso
    
    print("\n📋 Ejemplos de Notificaciones:\n")
    
    # Simulación (en producción usarías objetos reales)
    class TareaEjemplo:
        id = 1
        titulo = "Parcial Final - Estructuras de Datos"
        curso = type('obj', (object,), {'nombre': 'Estructura de Datos', 'codigo': '167396'})()
        curso_codigo = '167396'
        fecha_limite = datetime.now() + timedelta(days=2)
        horas_estimadas = 6
    
    tarea_ejemplo = TareaEjemplo()
    
    notif1 = generador.generar_notificacion_tarea_urgente(tarea_ejemplo, 2)
    print(f"1. {notif1.titulo}")
    print(f"   Prioridad: {notif1.prioridad.value}")
    print(f"   Mensaje: {notif1.mensaje}\n")
    
    # Ejemplo 2: Notificación de logro
    notif2 = generador.generar_notificacion_logro(
        'racha_7_dias',
        {'dias': 7}
    )
    print(f"2. {notif2.titulo}")
    print(f"   Mensaje: {notif2.mensaje}\n")
    
    print("=" * 60)
    print("✅ Sistema de notificaciones funcionando correctamente")