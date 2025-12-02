"""
Sistema de Gestión Académica Unipamplona
Base de datos PostgreSQL para producción en Render
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import json
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

class DatabaseManager:
    """Gestor de base de datos PostgreSQL"""
    
    def __init__(self, database_url=None):
        # Leer URL de conexión desde variable de entorno o argumento
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError(
                "No se encontró DATABASE_URL. "
                "Configúrala como variable de entorno o pásala como argumento."
            )
        
        # Render usa postgresql:// pero psycopg2 necesita postgres://
        if self.database_url.startswith('postgresql://'):
            self.database_url = self.database_url.replace('postgresql://', 'postgres://', 1)
        
        self.conn = None
    
    def connect(self):
        """Establece conexión con PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            print("✅ Conexión exitosa a PostgreSQL")
            return self.conn
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def close(self):
        """Cierra la conexión"""
        if self.conn:
            self.conn.close()
            print("🔌 Conexión cerrada")
    
    def crear_tablas(self):
        """Crea todas las tablas del sistema"""
        cursor = self.conn.cursor()
        
        # Tabla usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            carrera VARCHAR(255) DEFAULT 'Ingeniería de Sistemas',
            semestre_actual INTEGER NOT NULL,
            tipo_estudio VARCHAR(20) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT TRUE
        )
        ''')
        
        # Tabla cursos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            codigo VARCHAR(20) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            creditos INTEGER NOT NULL,
            semestre INTEGER NOT NULL,
            ht INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 0,
            htp INTEGER DEFAULT 0,
            requisitos JSONB DEFAULT '[]'::jsonb,
            creditos_requisitos INTEGER DEFAULT 0
        )
        ''')
        
        # Tabla historial_academico
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_academico (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            curso_codigo VARCHAR(20) NOT NULL REFERENCES cursos(codigo),
            semestre_cursado INTEGER,
            nota_final DECIMAL(3,2),
            estado VARCHAR(20) DEFAULT 'aprobado',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, curso_codigo)
        )
        ''')
        
        # Tabla materias_actuales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS materias_actuales (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            curso_codigo VARCHAR(20) NOT NULL REFERENCES cursos(codigo),
            estado VARCHAR(20) DEFAULT 'activo',
            UNIQUE(usuario_id, curso_codigo)
        )
        ''')
        
        # Tabla tareas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            curso_codigo VARCHAR(20) NOT NULL REFERENCES cursos(codigo),
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            tipo VARCHAR(50) NOT NULL,
            fecha_limite TIMESTAMP NOT NULL,
            completada BOOLEAN DEFAULT FALSE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabla calendario_institucional
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendario_institucional (
            id SERIAL PRIMARY KEY,
            nombre_evento VARCHAR(255) NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE,
            tipo VARCHAR(50),
            semestre VARCHAR(10),
            color VARCHAR(7) DEFAULT '#3B82F6'
        )
        ''')
        
        # Crear índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tareas_usuario ON tareas(usuario_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tareas_fecha ON tareas(fecha_limite)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_usuario ON historial_academico(usuario_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_materias_usuario ON materias_actuales(usuario_id)')
        
        self.conn.commit()
        print("✅ Tablas creadas exitosamente")
    
    def insertar_pensum_sistemas(self):
        """Inserta el pensum completo de Ingeniería de Sistemas"""
        cursor = self.conn.cursor()
        
        pensum = [
            # SEMESTRE 1
            {"codigo": "171342", "nombre": "ACTIVIDAD DEPORTIVA, RECREATIVA Y CULTURAL", "creditos": 1, "semestre": 1, "ht": 0, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "153002", "nombre": "CÁTEDRA FARIA", "creditos": 2, "semestre": 1, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "167389", "nombre": "INFORMÁTICA BÁSICA", "creditos": 1, "semestre": 1, "ht": 0, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "162274", "nombre": "INGLÉS NIVEL I", "creditos": 2, "semestre": 1, "ht": 1, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "157408", "nombre": "ÁLGEBRA LINEAL", "creditos": 2, "semestre": 1, "ht": 1, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "167391", "nombre": "INTRODUCCIÓN A LA INGENIERÍA DE SISTEMAS", "creditos": 2, "semestre": 1, "ht": 4, "hp": 0, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "167390", "nombre": "PENSAMIENTO COMPUTACIONAL", "creditos": 3, "semestre": 1, "ht": 2, "hp": 4, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "162003", "nombre": "HABILIDADES COMUNICATIVAS", "creditos": 2, "semestre": 1, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},

            # SEMESTRE 2
            {"codigo": "1673961", "nombre": "CRÉDITOS DE LIBRE ELECCIÓN", "creditos": 3, "semestre": 2, "ht": 0, "hp": 0, "requisitos": [], "creditos_requisitos": 15},
            {"codigo": "164374", "nombre": "FORMACIÓN CIUDADANA Y CULTURA DE LA PAZ", "creditos": 1, "semestre": 2, "ht": 0, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "162275", "nombre": "INGLÉS NIVEL II", "creditos": 2, "semestre": 2, "ht": 1, "hp": 3, "requisitos": ["162274"], "creditos_requisitos": 0},
            {"codigo": "157400", "nombre": "CÁLCULO DIFERENCIAL", "creditos": 3, "semestre": 2, "ht": 2, "hp": 3, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "167392", "nombre": "FUNDAMENTOS DE PROGRAMACIÓN", "creditos": 3, "semestre": 2, "ht": 2, "hp": 4, "requisitos": ["167390"], "creditos_requisitos": 0},
            {"codigo": "167393", "nombre": "GESTIÓN DE PROYECTOS", "creditos": 3, "semestre": 2, "ht": 2, "hp": 2, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "164004", "nombre": "EDUCACIÓN AMBIENTAL", "creditos": 2, "semestre": 2, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "150001", "nombre": "ELECTIVA SOCIOHUMANÍSTICA I", "creditos": 2, "semestre": 2, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},

            # SEMESTRE 3
            {"codigo": "162276", "nombre": "INGLÉS NIVEL III", "creditos": 2, "semestre": 3, "ht": 1, "hp": 3, "requisitos": ["162275"], "creditos_requisitos": 0},
            {"codigo": "157401", "nombre": "CÁLCULO INTEGRAL", "creditos": 3, "semestre": 3, "ht": 2, "hp": 3, "requisitos": ["157400"], "creditos_requisitos": 0},
            {"codigo": "167395", "nombre": "ESTADÍSTICA Y PROBABILIDAD", "creditos": 4, "semestre": 3, "ht": 2, "hp": 4, "requisitos": [], "creditos_requisitos": 0},
            {"codigo": "157405", "nombre": "MECÁNICA", "creditos": 3, "semestre": 3, "ht": 2, "hp": 3, "requisitos": ["157400"], "creditos_requisitos": 0},
            {"codigo": "167394", "nombre": "PROGRAMACIÓN ORIENTADA A OBJETOS", "creditos": 3, "semestre": 3, "ht": 2, "hp": 4, "requisitos": ["167392"], "creditos_requisitos": 0},
            {"codigo": "150002", "nombre": "ELECTIVA SOCIOHUMANÍSTICA II", "creditos": 2, "semestre": 3, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},

            # SEMESTRE 4
            {"codigo": "157402", "nombre": "CÁLCULO MULTIVARIABLE", "creditos": 3, "semestre": 4, "ht": 2, "hp": 3, "requisitos": ["157401"], "creditos_requisitos": 0},
            {"codigo": "157406", "nombre": "ELECTROMAGNETISMO", "creditos": 3, "semestre": 4, "ht": 2, "hp": 3, "requisitos": ["157405"], "creditos_requisitos": 0},
            {"codigo": "167396", "nombre": "ESTRUCTURA DE DATOS Y ANÁLISIS DE ALGORITMOS", "creditos": 4, "semestre": 4, "ht": 2, "hp": 4, "requisitos": ["167394"], "creditos_requisitos": 0},
            {"codigo": "167397", "nombre": "SISTEMAS DE INFORMACIÓN", "creditos": 4, "semestre": 4, "ht": 4, "hp": 2, "requisitos": ["167393"], "creditos_requisitos": 0},
            {"codigo": "164010", "nombre": "ÉTICA", "creditos": 2, "semestre": 4, "ht": 2, "hp": 0, "requisitos": [], "creditos_requisitos": 0},

            # SEMESTRE 5
            {"codigo": "157403", "nombre": "ECUACIONES DIFERENCIALES", "creditos": 3, "semestre": 5, "ht": 2, "hp": 3, "requisitos": ["157402"], "creditos_requisitos": 0},
            {"codigo": "167402", "nombre": "ARQUITECTURAS EMPRESARIALES", "creditos": 4, "semestre": 5, "ht": 2, "hp": 4, "requisitos": ["167397"], "creditos_requisitos": 0},
            {"codigo": "167401", "nombre": "BASE DE DATOS I", "creditos": 3, "semestre": 5, "ht": 2, "hp": 4, "requisitos": ["167394"], "creditos_requisitos": 0},
            {"codigo": "167399", "nombre": "ESTRUCTURAS COMPUTACIONALES DISCRETAS", "creditos": 3, "semestre": 5, "ht": 2, "hp": 4, "requisitos": ["167396"], "creditos_requisitos": 0},
            {"codigo": "167398", "nombre": "PLATAFORMAS TECNOLÓGICAS", "creditos": 3, "semestre": 5, "ht": 2, "hp": 2, "requisitos": ["167396"], "creditos_requisitos": 0},
            {"codigo": "167400", "nombre": "INVESTIGACIÓN EN INGENIERÍA DE SISTEMAS", "creditos": 2, "semestre": 5, "ht": 2, "hp": 2, "requisitos": [], "creditos_requisitos": 64},

            # SEMESTRE 6
            {"codigo": "167403", "nombre": "ALGORITMOS NUMÉRICOS PARA INGENIERÍA", "creditos": 3, "semestre": 6, "ht": 2, "hp": 2, "requisitos": ["157403"], "creditos_requisitos": 0},
            {"codigo": "167406", "nombre": "BASE DE DATOS II", "creditos": 3, "semestre": 6, "ht": 2, "hp": 4, "requisitos": ["167401"], "creditos_requisitos": 0},
            {"codigo": "167404", "nombre": "DESARROLLO ORIENTADO A PLATAFORMAS", "creditos": 3, "semestre": 6, "ht": 2, "hp": 3, "requisitos": ["167401"], "creditos_requisitos": 0},
            {"codigo": "167405", "nombre": "LÓGICA Y REPRESENTACIÓN DEL CONOCIMIENTO", "creditos": 3, "semestre": 6, "ht": 2, "hp": 2, "requisitos": ["167399"], "creditos_requisitos": 0},

            # SEMESTRE 7
            {"codigo": "167409", "nombre": "PARADIGMAS DE PROGRAMACIÓN", "creditos": 3, "semestre": 7, "ht": 2, "hp": 2, "requisitos": ["167405"], "creditos_requisitos": 0},
            {"codigo": "167407", "nombre": "REDES", "creditos": 4, "semestre": 7, "ht": 2, "hp": 4, "requisitos": ["167398"], "creditos_requisitos": 0},
            {"codigo": "167408", "nombre": "TEORÍA DE LA COMPUTACIÓN", "creditos": 3, "semestre": 7, "ht": 2, "hp": 2, "requisitos": ["167399"], "creditos_requisitos": 0},
            {"codigo": "167410", "nombre": "PROYECTO INTEGRADOR", "creditos": 2, "semestre": 7, "ht": 0, "hp": 2, "requisitos": [], "creditos_requisitos": 99},

            # SEMESTRE 8
            {"codigo": "167411", "nombre": "FUNDAMENTOS DE COMPUTACIÓN PARALELA Y DISTRIBUIDA", "creditos": 3, "semestre": 8, "ht": 2, "hp": 4, "requisitos": ["167398"], "creditos_requisitos": 0},
            {"codigo": "167412", "nombre": "INGENIERÍA DEL SOFTWARE I", "creditos": 4, "semestre": 8, "ht": 2, "hp": 2, "requisitos": ["167397", "157401"], "creditos_requisitos": 0},
            {"codigo": "167414", "nombre": "MODELADO Y SIMULACIÓN DE SISTEMAS CONTINUOS", "creditos": 3, "semestre": 8, "ht": 2, "hp": 4, "requisitos": ["167406", "167403"], "creditos_requisitos": 0},
            {"codigo": "167413", "nombre": "SISTEMAS INTELIGENTES", "creditos": 4, "semestre": 8, "ht": 2, "hp": 4, "requisitos": ["167399", "167395"], "creditos_requisitos": 0},

            # SEMESTRE 9
            {"codigo": "167417", "nombre": "CIENCIA DE DATOS", "creditos": 3, "semestre": 9, "ht": 2, "hp": 2, "requisitos": ["167413"], "creditos_requisitos": 0},
            {"codigo": "167415", "nombre": "INGENIERÍA DEL SOFTWARE II", "creditos": 4, "semestre": 9, "ht": 2, "hp": 2, "requisitos": ["167412"], "creditos_requisitos": 0},
            {"codigo": "167416", "nombre": "LEGISLACIÓN INFORMÁTICA Y ASUNTOS SOCIALES", "creditos": 2, "semestre": 9, "ht": 4, "hp": 0, "requisitos": [], "creditos_requisitos": 120},
            {"codigo": "167418", "nombre": "MODELADO Y SIMULACIÓN DE SISTEMAS DISCRETOS", "creditos": 3, "semestre": 9, "ht": 2, "hp": 2, "requisitos": ["167399", "167395"], "creditos_requisitos": 0},

            # SEMESTRE 10
            {"codigo": "167420", "nombre": "INGENIERÍA DEL SOFTWARE III", "creditos": 4, "semestre": 10, "ht": 2, "hp": 2, "requisitos": ["167415"], "creditos_requisitos": 0},
            {"codigo": "167421", "nombre": "SEGURIDAD INFORMÁTICA", "creditos": 3, "semestre": 10, "ht": 2, "hp": 2, "requisitos": ["167407"], "creditos_requisitos": 0},
            {"codigo": "167419", "nombre": "TRABAJO DE GRADO", "creditos": 6, "semestre": 10, "ht": 0, "hp": 2, "requisitos": [], "creditos_requisitos": 150}
        ]
        
        insertadas = 0
        for materia in pensum:
            try:
                cursor.execute('''
                INSERT INTO cursos 
                (codigo, nombre, creditos, semestre, ht, hp, htp, requisitos, creditos_requisitos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    creditos = EXCLUDED.creditos,
                    semestre = EXCLUDED.semestre,
                    ht = EXCLUDED.ht,
                    hp = EXCLUDED.hp,
                    htp = EXCLUDED.htp,
                    requisitos = EXCLUDED.requisitos,
                    creditos_requisitos = EXCLUDED.creditos_requisitos
                ''', (
                    materia["codigo"],
                    materia["nombre"],
                    materia["creditos"],
                    materia["semestre"],
                    materia.get("ht", 0),
                    materia.get("hp", 0),
                    materia.get("htp", 0),
                    json.dumps(materia.get("requisitos", [])),
                    materia.get("creditos_requisitos", 0)
                ))
                insertadas += 1
            except Exception as e:
                print(f"Error insertando {materia['codigo']}: {e}")
        
        self.conn.commit()
        print(f"✅ Pensum insertado: {insertadas} materias")
    
    def insertar_calendario_2025(self):
        """Inserta fechas del calendario académico 2025"""
        cursor = self.conn.cursor()
        
        eventos = [
            ("Inicio de Clases 2025-1", "2025-01-20", None, "inicio_clases", "2025-1", "#10B981"),
            ("Primer Parcial 2025-1", "2025-03-10", "2025-03-14", "parcial", "2025-1", "#F59E0B"),
            ("Segundo Parcial 2025-1", "2025-04-21", "2025-04-25", "parcial", "2025-1", "#F59E0B"),
            ("Cancelación Materias", "2025-04-25", None, "cancelacion", "2025-1", "#EF4444"),
            ("Examen Final 2025-1", "2025-05-19", "2025-05-23", "final", "2025-1", "#DC2626"),
            ("Inscripciones 2025-2", "2025-06-02", "2025-06-13", "inscripcion", "2025-2", "#3B82F6"),
            ("Inicio Clases 2025-2", "2025-07-28", None, "inicio_clases", "2025-2", "#10B981"),
            ("Primer Parcial 2025-2", "2025-09-22", "2025-09-26", "parcial", "2025-2", "#F59E0B"),
            ("Segundo Parcial 2025-2", "2025-10-27", "2025-10-31", "parcial", "2025-2", "#F59E0B"),
            ("Cancelación 2025-2", "2025-10-31", None, "cancelacion", "2025-2", "#EF4444"),
            ("Examen Final 2025-2", "2025-11-24", "2025-11-28", "final", "2025-2", "#DC2626")
        ]
        
        for evento in eventos:
            cursor.execute('''
            INSERT INTO calendario_institucional 
            (nombre_evento, fecha_inicio, fecha_fin, tipo, semestre, color)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            ''', evento)
        
        self.conn.commit()
        print(f"✅ Calendario actualizado: {len(eventos)} eventos")


def inicializar_base_datos(database_url=None):
    """Función principal de inicialización"""
    print("=" * 70)
    print("🚀 Inicializando Sistema Académico Unipamplona (PostgreSQL)")
    print("=" * 70)
    
    try:
        db = DatabaseManager(database_url)
        db.connect()
        
        db.crear_tablas()
        db.insertar_pensum_sistemas()
        db.insertar_calendario_2025()
        
        print("=" * 70)
        print("✅ Base de datos PostgreSQL inicializada correctamente")
        print("=" * 70)
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Ejecutar inicialización
    # La URL se lee desde la variable de entorno DATABASE_URL
    inicializar_base_datos()