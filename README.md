# 🎓 UniPlanner - Sistema de Gestión Académica Inteligente

**Sistema integral de planificación académica para estudiantes de Ingeniería de Sistemas de la Universidad de Pamplona**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Tabla de Contenidos

1. [Descripción del Problema](#-descripción-del-problema)
2. [Solución Propuesta](#-solución-propuesta)
3. [Características Principales](#-características-principales)
4. [Arquitectura del Sistema](#-arquitectura-del-sistema)
5. [Requisitos de Instalación](#-requisitos-de-instalación)
6. [Guía de Instalación](#-guía-de-instalación)
7. [Uso del Sistema](#-uso-del-sistema)
8. [Estructura del Proyecto](#-estructura-del-proyecto)
9. [API REST Endpoints](#-api-rest-endpoints)
10. [Paradigmas de Programación](#-paradigmas-de-programación)
11. [Mantenimiento y Extensión](#-mantenimiento-y-extensión)
12. [Autores](#-autores)

---

## 🎯 Descripción del Problema

### Problemática Identificada

Los estudiantes de Ingeniería de Sistemas de la Universidad de Pamplona enfrentan múltiples desafíos en la gestión de su carga académica:

1. **Desorganización de Tareas**: Dificultad para gestionar múltiples entregas, parciales y proyectos simultáneos
2. **Planificación Ineficiente**: Falta de herramientas para distribuir tiempo de estudio según prioridades reales
3. **Seguimiento Manual**: Ausencia de un sistema centralizado para monitorear progreso académico
4. **Inscripción de Materias**: Confusión con requisitos, prerrequisitos y créditos acumulados

### A Quién Afecta

- **Estudiantes activos** (primaria): Afecta especialmente a estudiantes de semestres intermedios (3°-7°) con alta carga académica
- **Estudiantes nuevos**: Dificulta la adaptación al sistema universitario
- **Estudiantes próximos a graduarse**: Complica la planificación de materias finales

### Importancia de la Solución

La gestión académica eficiente es crucial para:
- ✅ Reducir el estrés académico
- ✅ Mejorar el rendimiento estudiantil
- ✅ Optimizar el tiempo de estudio
- ✅ Prevenir reprobación de materias por mala planificación
- ✅ Facilitar el cumplimiento de plazos académicos

---

## 💡 Solución Propuesta

**UniPlanner** es un sistema web de gestión académica que integra:

### Componentes Principales

1. **Backend REST API** (Flask + PostgreSQL)
   - Autenticación segura con JWT
   - Gestión completa de datos académicos
   - Sistema de recomendaciones inteligentes

2. **Sistema de Recomendaciones**
   - Priorización automática de tareas
   - Distribución inteligente de carga de estudio
   - Alertas de tareas urgentes

3. **Gestión de Pensum**
   - Validación automática de requisitos
   - Cálculo de créditos acumulados
   - Sugerencias de materias a inscribir

---

## ✨ Características Principales

### Gestión de Usuario
- 🔐 Registro y autenticación segura
- 👤 Perfil personalizado con configuración de estudio
- 📊 Dashboard con estadísticas en tiempo real

### Gestión de Tareas
- ✏️ Crear, editar y eliminar tareas
- 📅 Asignación por materia con fechas límite
- ✅ Marcado de progreso y completado
- 🎯 Priorización automática por urgencia

### Sistema de Recomendaciones
- 🤖 Algoritmo de priorización inteligente
- ⏰ Detección de tareas urgentes
- 📈 Cálculo de carga de trabajo semanal
- 📝 Plan de estudio automatizado

### Gestión Académica
- 📚 Catálogo completo del pensum
- ✔️ Validación de requisitos y prerrequisitos
- 🎓 Seguimiento de materias aprobadas y actuales
- 📊 Cálculo automático de créditos

### Calendario Institucional
- 📆 Fechas importantes del semestre
- 🔔 Recordatorios de eventos académicos
- 📅 Plazos de inscripción y cancelación

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React Native)               │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Login   │  │Dashboard │  │  Tareas  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
                     │
┌────────────────────▼────────────────────────────────────┐
│              BACKEND (Flask REST API)                   │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Auth      │  │   Tareas    │  │  Cursos     │    │
│  │ (JWT)       │  │  Endpoints  │  │  Endpoints  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │      Sistema de Recomendaciones              │      │
│  │  (Programación Funcional - map/filter/reduce)│      │
│  └──────────────────────────────────────────────┘      │
└────────────────────┬────────────────────────────────────┘
                     │ SQL
                     │
┌────────────────────▼────────────────────────────────────┐
│              BASE DE DATOS (PostgreSQL)                 │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ usuarios │  │  cursos  │  │  tareas  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Capas de la Aplicación

1. **Capa de Presentación**: Frontend React Native (en desarrollo)
2. **Capa de API**: Flask REST con endpoints documentados
3. **Capa de Lógica de Negocio**: Modelos POO + Sistema de Recomendaciones
4. **Capa de Datos**: PostgreSQL con diseño normalizado

---

## 📋 Requisitos de Instalación

### Requisitos del Sistema

- **Sistema Operativo**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 o superior
- **PostgreSQL**: 12.0 o superior
- **RAM**: Mínimo 2GB (recomendado 4GB)
- **Espacio en Disco**: 500MB

### Dependencias de Python

Ver `requirements.txt` para lista completa:

```
Flask==3.0.0
Flask-CORS==4.0.0
PyJWT==2.8.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-dotenv==1.0.0
```

---

## 🚀 Guía de Instalación

### Opción 1: Instalación Local (Desarrollo)

#### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/uniplanner.git
cd uniplanner
```

#### Paso 2: Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### Paso 4: Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost:5432/uniplanner

# Seguridad
SECRET_KEY=tu-clave-secreta-super-segura-cambiala

# Ambiente
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

#### Paso 5: Inicializar Base de Datos

```bash
# Crear base de datos en PostgreSQL
createdb uniplanner

# Ejecutar script de inicialización
python init_db.py
```

#### Paso 6: Ejecutar el Servidor

```bash
python flask_api.py
```

El servidor estará disponible en `http://localhost:5000`

### Opción 2: Despliegue en Producción (Render/Heroku)

Ver [DEPLOYMENT.md](docs/DEPLOYMENT.md) para instrucciones detalladas.

---

## 📱 Uso del Sistema

### 1. Registro de Usuario

**Endpoint**: `POST /api/auth/registro`

```bash
curl -X POST http://localhost:5000/api/auth/registro \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan.perez@unipamplona.edu.co",
    "password": "Pass123",
    "semestre_actual": 5,
    "tipo_estudio": "moderado"
  }'
```

### 2. Inicio de Sesión

**Endpoint**: `POST /api/auth/login`

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan.perez@unipamplona.edu.co",
    "password": "Pass123"
  }'
```

Respuesta:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan.perez@unipamplona.edu.co"
  }
}
```

### 3. Crear Tarea

**Endpoint**: `POST /api/tareas`

```bash
curl -X POST http://localhost:5000/api/tareas \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "curso_codigo": "167396",
    "titulo": "Parcial 2 - Árboles Binarios",
    "tipo": "parcial",
    "fecha_limite": "2025-05-15",
    "descripcion": "Estudiar capítulos 4-6"
  }'
```

### 4. Obtener Recomendaciones

**Endpoint**: `GET /api/recomendaciones`

```bash
curl -X GET http://localhost:5000/api/recomendaciones?limite=5 \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## 📁 Estructura del Proyecto

```
uniplanner/
│
├── config.py                    # Configuración centralizada
├── logger.py                    # Sistema de logging
├── validators.py                # Validaciones de entrada
│
├── database_manager_postgres.py # Gestor de base de datos
├── poo_models_postgres.py      # Modelos POO (Usuario, Curso, Tarea)
├── recomendaciones_funcional.py # Sistema de recomendaciones
│
├── flask_api.py                 # API REST principal
├── init_db.py                   # Script de inicialización de BD
├── deleterBD.py                 # Script para resetear BD (desarrollo)
│
├── requirements.txt             # Dependencias Python
├── Procfile                     # Configuración para Heroku/Render
├── .gitignore                   # Archivos ignorados por Git
├── .env                         # Variables de entorno (NO commitear)
│
├── logs/                        # Logs del sistema
│   └── uniplanner_20250108.log
│
├── docs/                        # Documentación adicional
│   ├── MANUAL_TECNICO.pdf       # Manual técnico completo
│   ├── ARQUITECTURA.md          # Diagramas detallados
│   └── API_DOCUMENTATION.md     # Documentación de endpoints
│
└── README.md                    # Este archivo
```

---

## 🔌 API REST Endpoints

### Autenticación

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/registro` | Registrar nuevo usuario | No |
| POST | `/api/auth/login` | Iniciar sesión | No |

### Usuario

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/usuario/perfil` | Obtener perfil y estadísticas | Sí |
| GET | `/api/usuario/materias/actuales` | Materias inscritas | Sí |
| GET | `/api/usuario/materias/aprobadas` | Materias aprobadas | Sí |
| POST | `/api/usuario/materias/inscribir` | Inscribir materia | Sí |
| POST | `/api/usuario/materias/cancelar` | Cancelar materia | Sí |

### Tareas

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/tareas` | Listar todas las tareas | Sí |
| POST | `/api/tareas` | Crear nueva tarea | Sí |
| DELETE | `/api/tareas/{id}` | Eliminar tarea | Sí |
| POST | `/api/tareas/{id}/completar` | Marcar como completada | Sí |

### Recomendaciones

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/recomendaciones` | Top N tareas prioritarias | Sí |
| GET | `/api/recomendaciones/tareas-urgentes` | Tareas con vencimiento cercano | Sí |
| GET | `/api/estadisticas` | Estadísticas del usuario | Sí |

### Cursos

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/cursos` | Listar todos los cursos | No |
| GET | `/api/cursos/{codigo}` | Detalle de un curso | No |
| GET | `/api/cursos/buscar?q={termino}` | Buscar cursos | No |

---

## 🎨 Paradigmas de Programación

Este proyecto implementa **múltiples paradigmas de programación**:

### 1. Programación Orientada a Objetos (POO)

**Archivos**: `poo_models_postgres.py`

- **Clases**: `Usuario`, `Curso`, `Tarea`, `CalendarioInstitucional`
- **Encapsulación**: Atributos privados y métodos públicos
- **Herencia**: `DatabaseModel` como clase base
- **Polimorfismo**: Métodos `from_row()` en cada modelo

```python
class Usuario(DatabaseModel):
    def __init__(self, id, nombre, apellido, email, ...):
        self.id = id
        self.nombre = nombre
        # ...
    
    def inscribir_materia(self, codigo_materia):
        # Lógica de inscripción
        pass
```

### 2. Programación Funcional

**Archivos**: `recomendaciones_funcional.py`

- **Funciones Puras**: Sin efectos secundarios
- **Map/Filter/Reduce**: Transformación de datos
- **Composición de Funciones**: `compose()`
- **Inmutabilidad**: Datos no modificados

```python
# Ejemplo de pipeline funcional
recomendaciones = compose(
    tomar_primeros_5,
    ordenar_por_fecha,
    list,
    filtrar_pendientes
)(tareas)
```

### 3. Programación Imperativa

**Archivos**: `flask_api.py`, `database_manager_postgres.py`

- **Secuencias de Instrucciones**: Flujo de control explícito
- **Variables Mutables**: Estado modificable
- **Bucles**: for, while

---

## 🛠️ Mantenimiento y Extensión

### Agregar Nuevo Endpoint

1. Definir función en `flask_api.py`:

```python
@app.route('/api/nuevo-endpoint', methods=['POST'])
@token_requerido
def nuevo_endpoint(usuario):
    """
    Descripción del endpoint.
    
    Args:
        usuario: Usuario autenticado
    
    Returns:
        JSON con resultado
    """
    data = request.get_json()
    # Lógica del endpoint
    return jsonify({'success': True})
```

2. Agregar validación en `validators.py` si es necesario
3. Documentar en `docs/API_DOCUMENTATION.md`

### Agregar Nueva Funcionalidad al Modelo

1. Agregar método en clase correspondiente (`poo_models_postgres.py`):

```python
def nueva_funcionalidad(self, parametro):
    """
    Descripción de la funcionalidad.
    
    Args:
        parametro: Descripción del parámetro
    
    Returns:
        Resultado de la operación
    """
    # Implementación
    pass
```

2. Agregar pruebas
3. Actualizar documentación

### Modificar Base de Datos

1. Editar `database_manager_postgres.py`
2. Ejecutar `python deleterBD.py` (¡CUIDADO: borra todos los datos!)
3. Ejecutar `python init_db.py`

---

## 👥 Autores

**Equipo de Desarrollo**

- **[Tu Nombre]** - Líder de Proyecto y Backend
  - Email: tu.email@unipamplona.edu.co
  - GitHub: [@tu-usuario](https://github.com/tu-usuario)

- **[Nombre Compañero]** - Frontend y Diseño
  - Email: compañero@unipamplona.edu.co
  - GitHub: [@compañero](https://github.com/compañero)

**Institución**: Universidad de Pamplona  
**Programa**: Ingeniería de Sistemas  
**Curso**: Paradigmas de Programación  
**Año**: 2025

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🙏 Agradecimientos

- Universidad de Pamplona - Programa de Ingeniería de Sistemas
- Profesor [Nombre del Profesor] - Paradigmas de Programación
- Comunidad de estudiantes por feedback y sugerencias

---

## 📞 Soporte

¿Encontraste un bug o tienes una sugerencia?

- 🐛 Reportar en [Issues](https://github.com/tu-usuario/uniplanner/issues)
- 📧 Email: soporte.uniplanner@unipamplona.edu.co
- 💬 Slack: #uniplanner-support

---

**¡Gracias por usar UniPlanner! 🎓✨**