"""
Modelos POO con PostgreSQL - Sistema Académico Unipamplona
Compatible con Render y ambientes de producción
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

# ========== CLASE BASE ==========

class DatabaseModel:
    """Clase base con utilidades comunes para PostgreSQL"""
    
    @staticmethod
    def get_connection():
        """Obtiene conexión a PostgreSQL desde variable de entorno"""
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError(
                "DATABASE_URL no está configurada. "
                "Configúrala como variable de entorno."
            )
        
        # Render usa postgresql:// pero psycopg2 necesita postgres://
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgres://', 1)
        
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    
    @staticmethod
    def encriptar_password(password: str) -> str:
        """Encripta contraseña con SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()


# ========== USUARIO ==========

class Usuario(DatabaseModel):
    """Modelo de Usuario"""
    
    def __init__(self, id=None, nombre=None, apellido=None, email=None,
                 carrera=None, semestre_actual=None, tipo_estudio=None):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.carrera = carrera
        self.semestre_actual = semestre_actual
        self.tipo_estudio = tipo_estudio
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    @classmethod
    def crear(cls, nombre: str, apellido: str, email: str, password: str,
              semestre_actual: int, tipo_estudio: str,
              materias_aprobadas: List[str] = None,
              materias_cursando: List[str] = None) -> 'Usuario':
        """Crea un nuevo usuario"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = cls.encriptar_password(password)
            
            cursor.execute('''
            INSERT INTO usuarios 
            (nombre, apellido, email, password_hash, semestre_actual, tipo_estudio, carrera)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            ''', (nombre, apellido, email, password_hash, semestre_actual, 
                  tipo_estudio, 'Ingeniería de Sistemas'))
            
            usuario_id = cursor.fetchone()['id']
            
            # Registrar materias aprobadas
            if materias_aprobadas:
                for codigo in materias_aprobadas:
                    cursor.execute('''
                    INSERT INTO historial_academico (usuario_id, curso_codigo, estado)
                    VALUES (%s, %s, 'aprobado')
                    ON CONFLICT (usuario_id, curso_codigo) DO NOTHING
                    ''', (usuario_id, codigo))
            
            # Registrar materias actuales
            if materias_cursando:
                for codigo in materias_cursando:
                    cursor.execute('''
                    INSERT INTO materias_actuales (usuario_id, curso_codigo)
                    VALUES (%s, %s)
                    ON CONFLICT (usuario_id, curso_codigo) DO NOTHING
                    ''', (usuario_id, codigo))
            
            conn.commit()
            return cls.obtener_por_id(usuario_id)
            
        except psycopg2.IntegrityError:
            conn.rollback()
            raise ValueError(f"El email '{email}' ya está registrado")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @classmethod
    def autenticar(cls, email: str, password: str) -> Optional['Usuario']:
        """Autentica un usuario"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        password_hash = cls.encriptar_password(password)
        
        cursor.execute('''
        SELECT * FROM usuarios 
        WHERE email = %s AND password_hash = %s AND activo = TRUE
        ''', (email, password_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row['id'],
                nombre=row['nombre'],
                apellido=row['apellido'],
                email=row['email'],
                carrera=row['carrera'],
                semestre_actual=row['semestre_actual'],
                tipo_estudio=row['tipo_estudio']
            )
        return None
    
    @classmethod
    def obtener_por_id(cls, usuario_id: int) -> Optional['Usuario']:
        """Obtiene usuario por ID"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (usuario_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row['id'],
                nombre=row['nombre'],
                apellido=row['apellido'],
                email=row['email'],
                carrera=row['carrera'],
                semestre_actual=row['semestre_actual'],
                tipo_estudio=row['tipo_estudio']
            )
        return None
    
    def obtener_materias_actuales(self) -> List['Curso']:
        """Obtiene las materias que está cursando"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.* FROM cursos c
        INNER JOIN materias_actuales ma ON c.codigo = ma.curso_codigo
        WHERE ma.usuario_id = %s AND ma.estado = 'activo'
        ORDER BY c.nombre
        ''', (self.id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Curso.from_row(row) for row in rows]
    
    def obtener_materias_aprobadas(self) -> List['Curso']:
        """Obtiene las materias que ya aprobó"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.* FROM cursos c
        INNER JOIN historial_academico ha ON c.codigo = ha.curso_codigo
        WHERE ha.usuario_id = %s AND ha.estado = 'aprobado'
        ORDER BY c.semestre, c.nombre
        ''', (self.id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Curso.from_row(row) for row in rows]
    
    def calcular_creditos_acumulados(self) -> int:
        """Calcula el total de créditos aprobados"""
        materias = self.obtener_materias_aprobadas()
        return sum(m.creditos for m in materias)
    
    def puede_inscribir_materia(self, codigo_materia: str) -> Tuple[bool, str]:
        """Verifica si puede inscribir una materia"""
        curso = Curso.obtener_por_codigo(codigo_materia)
        if not curso:
            return False, "Materia no encontrada"
        
        materias_aprobadas = [c.codigo for c in self.obtener_materias_aprobadas()]
        if codigo_materia in materias_aprobadas:
            return False, "Ya aprobaste esta materia"
        
        materias_actuales = [c.codigo for c in self.obtener_materias_actuales()]
        if codigo_materia in materias_actuales:
            return False, "Ya estás cursando esta materia"
        
        creditos_acumulados = self.calcular_creditos_acumulados()
        if curso.creditos_requisitos > creditos_acumulados:
            return False, f"Necesitas {curso.creditos_requisitos} créditos aprobados (tienes {creditos_acumulados})"
        
        if curso.requisitos:
            for req in curso.requisitos:
                if req not in materias_aprobadas:
                    req_nombre = Curso.obtener_por_codigo(req)
                    return False, f"Falta requisito: {req_nombre.nombre if req_nombre else req}"
        
        return True, "OK"
    
    def inscribir_materia(self, codigo_materia: str) -> bool:
        """Inscribe una materia"""
        puede, razon = self.puede_inscribir_materia(codigo_materia)
        if not puede:
            raise ValueError(razon)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO materias_actuales (usuario_id, curso_codigo)
            VALUES (%s, %s)
            ''', (self.id, codigo_materia))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def cancelar_materia(self, codigo_materia: str) -> bool:
        """Cancela una materia"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE materias_actuales 
        SET estado = 'cancelado'
        WHERE usuario_id = %s AND curso_codigo = %s AND estado = 'activo'
        ''', (self.id, codigo_materia))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def obtener_tareas(self, solo_pendientes: bool = False) -> List['Tarea']:
        """Obtiene todas las tareas del usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tareas WHERE usuario_id = %s'
        params = [self.id]
        
        if solo_pendientes:
            query += ' AND completada = FALSE'
        
        query += ' ORDER BY fecha_limite ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Tarea.from_row(row) for row in rows]
    
    def agregar_tarea(self, curso_codigo: str, titulo: str, tipo: str,
                     fecha_limite: str, horas_estimadas: float = 4,
                     dificultad: int = 3, descripcion: str = "",
                     hora_limite: str = None) -> 'Tarea':
        """Agrega una nueva tarea"""
        return Tarea.crear(
            usuario_id=self.id,
            curso_codigo=curso_codigo,
            titulo=titulo,
            descripcion=descripcion,
            tipo=tipo,
            fecha_limite=fecha_limite
        )
    
    def obtener_estadisticas(self) -> Dict:
        """Calcula estadísticas del usuario"""
        tareas = self.obtener_tareas()
        tareas_pendientes = [t for t in tareas if not t.completada]
        tareas_completadas = [t for t in tareas if t.completada]
        
        materias_actuales = self.obtener_materias_actuales()
        materias_aprobadas = self.obtener_materias_aprobadas()
        
        total_creditos_actuales = sum(m.creditos for m in materias_actuales)
        total_creditos_aprobados = sum(m.creditos for m in materias_aprobadas)
        
        return {
            'total_tareas': len(tareas),
            'pendientes': len(tareas_pendientes),
            'completadas': len(tareas_completadas),
            'materias_actuales': len(materias_actuales),
            'materias_aprobadas': len(materias_aprobadas),
            'creditos_actuales': total_creditos_actuales,
            'creditos_aprobados': total_creditos_aprobados,
            'porcentaje_completado': (len(tareas_completadas) / len(tareas) * 100) if tareas else 0
        }


# ========== CURSO ==========

class Curso(DatabaseModel):
    """Modelo de Curso"""
    
    def __init__(self, codigo: str, nombre: str, creditos: int,
                 semestre: int, ht: int = 0, hp: int = 0,
                 requisitos: List[str] = None, creditos_requisitos: int = 0):
        self.codigo = codigo
        self.nombre = nombre
        self.creditos = creditos
        self.semestre = semestre
        self.ht = ht
        self.hp = hp
        self.requisitos = requisitos or []
        self.creditos_requisitos = creditos_requisitos
        self.peso = creditos
    
    @classmethod
    def from_row(cls, row) -> 'Curso':
        requisitos = row['requisitos'] if isinstance(row['requisitos'], list) else []
        return cls(
            codigo=row['codigo'],
            nombre=row['nombre'],
            creditos=row['creditos'],
            semestre=row['semestre'],
            ht=row['ht'],
            hp=row['hp'],
            requisitos=requisitos,
            creditos_requisitos=row['creditos_requisitos']
        )
    
    @classmethod
    def obtener_por_codigo(cls, codigo: str) -> Optional['Curso']:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cursos WHERE codigo = %s', (codigo,))
        row = cursor.fetchone()
        conn.close()
        
        return cls.from_row(row) if row else None
    
    @classmethod
    def obtener_por_semestre(cls, semestre: int) -> List['Curso']:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM cursos WHERE semestre = %s ORDER BY nombre
        ''', (semestre,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def obtener_todos(cls) -> List['Curso']:
        """Obtiene todas las materias del pensum"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cursos ORDER BY semestre, nombre')
        rows = cursor.fetchall()
        conn.close()
        
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def buscar(cls, termino: str) -> List['Curso']:
        """Busca materias por nombre o código"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM cursos 
        WHERE codigo ILIKE %s OR nombre ILIKE %s
        ORDER BY semestre, nombre
        ''', (f'%{termino}%', f'%{termino}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [cls.from_row(row) for row in rows]


# ========== TAREA ==========

class Tarea(DatabaseModel):
    """Modelo de Tarea"""
    
    def __init__(self, id: int, usuario_id: int, curso_codigo: str,
                 titulo: str, descripcion: str, tipo: str,
                 fecha_limite: datetime, completada: bool):
        self.id = id
        self.usuario_id = usuario_id
        self.curso_codigo = curso_codigo
        self.titulo = titulo
        self.descripcion = descripcion
        self.tipo = tipo
        self.fecha_limite = fecha_limite
        self.completada = completada
        
        self.curso = Curso.obtener_por_codigo(curso_codigo)
        
        # Atributos ficticios para compatibilidad
        self.horas_estimadas = 4
        self.dificultad = 3
        self.prioridad = 0
        self.porcentaje_completado = 100 if completada else 0
    
    @classmethod
    def from_row(cls, row) -> 'Tarea':
        return cls(
            id=row['id'],
            usuario_id=row['usuario_id'],
            curso_codigo=row['curso_codigo'],
            titulo=row['titulo'],
            descripcion=row['descripcion'] or "",
            tipo=row['tipo'],
            fecha_limite=row['fecha_limite'],
            completada=bool(row['completada'])
        )
    
    @classmethod
    def crear(cls, usuario_id: int, curso_codigo: str, titulo: str,
              descripcion: str, tipo: str, fecha_limite: str) -> 'Tarea':
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        try:
            if ' ' not in fecha_limite:
                fecha_limite = f"{fecha_limite} 23:59:59"
            
            cursor.execute('''
            INSERT INTO tareas 
            (usuario_id, curso_codigo, titulo, descripcion, tipo, fecha_limite)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''', (usuario_id, curso_codigo, titulo, descripcion, tipo, fecha_limite))
            
            tarea_id = cursor.fetchone()['id']
            conn.commit()
            
            return cls.obtener_por_id(tarea_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @classmethod
    def obtener_por_id(cls, tarea_id: int) -> Optional['Tarea']:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tareas WHERE id = %s', (tarea_id,))
        row = cursor.fetchone()
        conn.close()
        
        return cls.from_row(row) if row else None
    
    def marcar_completada(self, porcentaje: int = 100):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE tareas SET completada = TRUE WHERE id = %s', (self.id,))
        conn.commit()
        conn.close()
        
        self.completada = True
    
    def actualizar_progreso(self, porcentaje: int):
        """Método dummy para compatibilidad"""
        pass
    
    def eliminar(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tareas WHERE id = %s', (self.id,))
        conn.commit()
        conn.close()
    
    def dias_restantes(self) -> int:
        delta = self.fecha_limite - datetime.now()
        return delta.days


# ========== CALENDARIO ==========

class CalendarioInstitucional(DatabaseModel):
    """Calendario académico institucional"""
    
    def __init__(self, id: int, nombre_evento: str,
                 fecha_inicio: datetime, fecha_fin: datetime,
                 tipo: str, semestre: str, color: str):
        self.id = id
        self.nombre_evento = nombre_evento
        self.descripcion = ""
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.tipo = tipo
        self.semestre = semestre
        self.icono = "📅"
        self.color = color
    
    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'],
            nombre_evento=row['nombre_evento'],
            fecha_inicio=row['fecha_inicio'],
            fecha_fin=row['fecha_fin'],
            tipo=row['tipo'],
            semestre=row['semestre'],
            color=row['color']
        )
    
    @classmethod
    def obtener_proximos(cls, dias: int = 60) -> List['CalendarioInstitucional']:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM calendario_institucional 
        WHERE fecha_inicio >= CURRENT_DATE 
        AND fecha_inicio <= CURRENT_DATE + INTERVAL '%s days'
        ORDER BY fecha_inicio ASC
        ''', (dias,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def obtener_por_semestre(cls, semestre: str) -> List['CalendarioInstitucional']:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM calendario_institucional 
        WHERE semestre = %s OR semestre IS NULL
        ORDER BY fecha_inicio ASC
        ''', (semestre,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [cls.from_row(row) for row in rows]