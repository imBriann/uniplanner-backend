"""
Módulo de Validaciones para UniPlanner

Contiene funciones de validación reutilizables para datos de entrada,
previniendo errores y mejorando la seguridad de la aplicación.

"""

import re
from datetime import datetime
from typing import List, Tuple, Optional, Any
from functools import wraps


# ========== VALIDACIONES DE FORMATO ==========

def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida formato de correo electrónico.
    
    Verifica que el email cumpla con formato estándar RFC 5322 básico.
    
    Args:
        email: Dirección de correo a validar
    
    Returns:
        Tupla (es_valido, mensaje_error)
        - es_valido: True si el email es válido
        - mensaje_error: None si es válido, descripción del error si no
    
    Example:
        >>> validar_email("usuario@unipamplona.edu.co")
        (True, None)
        >>> validar_email("correo_invalido")
        (False, 'Formato de email inválido')
    """
    if not email or not isinstance(email, str):
        return False, "Email no puede estar vacío"
    
    # Patrón regex simplificado para validación de email
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(patron, email):
        return False, "Formato de email inválido"
    
    if len(email) > 255:
        return False, "Email demasiado largo (máximo 255 caracteres)"
    
    return True, None


def validar_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Valida fortaleza de contraseña.
    
    Requisitos:
    - Mínimo 6 caracteres
    - Al menos una letra
    - Al menos un número (opcional pero recomendado)
    
    Args:
        password: Contraseña a validar
    
    Returns:
        Tupla (es_valida, mensaje_error)
    
    Example:
        >>> validar_password("abc123")
        (True, None)
        >>> validar_password("123")
        (False, 'La contraseña debe tener al menos 6 caracteres')
    """
    if not password or not isinstance(password, str):
        return False, "La contraseña no puede estar vacía"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña es demasiado larga (máximo 128 caracteres)"
    
    # Validar que tenga al menos una letra
    if not re.search(r'[a-zA-Z]', password):
        return False, "La contraseña debe contener al menos una letra"
    
    return True, None


def validar_fecha(fecha_str: str, formato: str = '%Y-%m-%d') -> Tuple[bool, Optional[str]]:
    """
    Valida formato de fecha.
    
    Args:
        fecha_str: Fecha en formato string
        formato: Formato esperado (default: YYYY-MM-DD)
    
    Returns:
        Tupla (es_valida, mensaje_error)
    
    Example:
        >>> validar_fecha("2025-12-31")
        (True, None)
        >>> validar_fecha("31/12/2025", "%d/%m/%Y")
        (True, None)
    """
    if not fecha_str:
        return False, "La fecha no puede estar vacía"
    
    try:
        datetime.strptime(fecha_str, formato)
        return True, None
    except ValueError:
        return False, f"Formato de fecha inválido. Use: {formato}"


# ========== VALIDACIONES DE RANGO ==========

def validar_rango(
    valor: Any,
    minimo: Optional[Any] = None,
    maximo: Optional[Any] = None,
    nombre_campo: str = "valor"
) -> Tuple[bool, Optional[str]]:
    """
    Valida que un valor esté dentro de un rango.
    
    Args:
        valor: Valor a validar
        minimo: Valor mínimo permitido (inclusive)
        maximo: Valor máximo permitido (inclusive)
        nombre_campo: Nombre del campo para mensajes de error
    
    Returns:
        Tupla (es_valido, mensaje_error)
    
    Example:
        >>> validar_rango(5, 1, 10, "semestre")
        (True, None)
        >>> validar_rango(15, 1, 10, "semestre")
        (False, 'semestre debe estar entre 1 y 10')
    """
    if minimo is not None and valor < minimo:
        return False, f"{nombre_campo} debe ser mayor o igual a {minimo}"
    
    if maximo is not None and valor > maximo:
        return False, f"{nombre_campo} debe ser menor o igual a {maximo}"
    
    return True, None


def validar_longitud(
    texto: str,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
    nombre_campo: str = "texto"
) -> Tuple[bool, Optional[str]]:
    """
    Valida la longitud de un string.
    
    Args:
        texto: String a validar
        minimo: Longitud mínima
        maximo: Longitud máxima
        nombre_campo: Nombre del campo para mensajes
    
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not isinstance(texto, str):
        return False, f"{nombre_campo} debe ser texto"
    
    longitud = len(texto)
    
    if minimo is not None and longitud < minimo:
        return False, f"{nombre_campo} debe tener al menos {minimo} caracteres"
    
    if maximo is not None and longitud > maximo:
        return False, f"{nombre_campo} no puede exceder {maximo} caracteres"
    
    return True, None


# ========== VALIDACIONES DE OPCIONES ==========

def validar_opcion(
    valor: Any,
    opciones_validas: List[Any],
    nombre_campo: str = "valor"
) -> Tuple[bool, Optional[str]]:
    """
    Valida que un valor esté dentro de opciones permitidas.
    
    Args:
        valor: Valor a validar
        opciones_validas: Lista de valores permitidos
        nombre_campo: Nombre del campo
    
    Returns:
        Tupla (es_valido, mensaje_error)
    
    Example:
        >>> validar_opcion("moderado", ["intensivo", "moderado", "leve"], "tipo_estudio")
        (True, None)
    """
    if valor not in opciones_validas:
        opciones_str = ", ".join(str(o) for o in opciones_validas)
        return False, f"{nombre_campo} debe ser uno de: {opciones_str}"
    
    return True, None


# ========== VALIDACIONES COMPUESTAS ==========

def validar_datos_registro(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida todos los datos necesarios para registro de usuario.
    
    Combina múltiples validaciones en una función conveniente.
    
    Args:
        data: Diccionario con datos del usuario
    
    Returns:
        Tupla (es_valido, mensaje_error)
    
    Example:
        >>> datos = {
        ...     'nombre': 'Juan',
        ...     'apellido': 'Pérez',
        ...     'email': 'juan@example.com',
        ...     'password': 'Pass123',
        ...     'semestre_actual': 5,
        ...     'tipo_estudio': 'moderado'
        ... }
        >>> validar_datos_registro(datos)
        (True, None)
    """
    # Campos requeridos
    campos_requeridos = ['nombre', 'apellido', 'email', 'password', 
                        'semestre_actual', 'tipo_estudio']
    
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido: {campo}"
    
    # Validar email
    valido, error = validar_email(data['email'])
    if not valido:
        return False, error
    
    # Validar password
    valido, error = validar_password(data['password'])
    if not valido:
        return False, error
    
    # Validar nombre y apellido
    valido, error = validar_longitud(data['nombre'], 2, 100, "nombre")
    if not valido:
        return False, error
    
    valido, error = validar_longitud(data['apellido'], 2, 100, "apellido")
    if not valido:
        return False, error
    
    # Validar semestre
    try:
        semestre = int(data['semestre_actual'])
        valido, error = validar_rango(semestre, 1, 12, "semestre_actual")
        if not valido:
            return False, error
    except (ValueError, TypeError):
        return False, "semestre_actual debe ser un número"
    
    # Validar tipo de estudio
    valido, error = validar_opcion(
        data['tipo_estudio'],
        ['intensivo', 'moderado', 'leve'],
        'tipo_estudio'
    )
    if not valido:
        return False, error
    
    return True, None


def validar_datos_tarea(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida datos para creación de tarea.
    
    Args:
        data: Diccionario con datos de la tarea
    
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    # Campos requeridos
    campos_requeridos = ['curso_codigo', 'titulo', 'tipo', 'fecha_limite']
    
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido: {campo}"
    
    # Validar título
    valido, error = validar_longitud(data['titulo'], 3, 255, "titulo")
    if not valido:
        return False, error
    
    # Validar tipo de tarea
    tipos_validos = ['parcial', 'final', 'proyecto', 'taller', 
                     'exposicion', 'lectura', 'laboratorio']
    valido, error = validar_opcion(data['tipo'], tipos_validos, 'tipo')
    if not valido:
        return False, error
    
    # Validar fecha límite
    valido, error = validar_fecha(data['fecha_limite'].split()[0])  # Solo fecha
    if not valido:
        return False, error
    
    return True, None


# ========== DECORADOR DE VALIDACIÓN ==========

def validar_entrada(funcion_validacion):
    """
    Decorador que aplica validación automática a endpoints.
    
    Args:
        funcion_validacion: Función que valida los datos
    
    Returns:
        Decorador aplicable a funciones de Flask
    
    Example:
        @app.route('/api/registro', methods=['POST'])
        @validar_entrada(validar_datos_registro)
        def registro():
            data = request.get_json()
            # data ya está validado aquí
            ...
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No se recibieron datos'}), 400
            
            es_valido, mensaje_error = funcion_validacion(data)
            if not es_valido:
                return jsonify({'error': mensaje_error}), 400
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorador


# ========== SANITIZACIÓN ==========

def sanitizar_texto(texto: str, max_length: int = 1000) -> str:
    """
    Limpia y sanitiza texto de entrada.
    
    Previene inyección de código malicioso y normaliza espacios.
    
    Args:
        texto: Texto a sanitizar
        max_length: Longitud máxima permitida
    
    Returns:
        Texto sanitizado
    
    Example:
        >>> sanitizar_texto("  Hola   Mundo  ")
        'Hola Mundo'
    """
    if not texto:
        return ""
    
    # Convertir a string si no lo es
    texto = str(texto)
    
    # Truncar si es muy largo
    texto = texto[:max_length]
    
    # Remover espacios múltiples
    texto = ' '.join(texto.split())
    
    # Remover caracteres de control
    texto = ''.join(char for char in texto if ord(char) >= 32 or char == '\n')
    
    return texto.strip()


if __name__ == '__main__':
    # Pruebas del módulo de validación
    print("Probando módulo de validaciones\n")
    
    # Probar validación de email
    print("Validación de emails:")
    emails = ["usuario@example.com", "invalido@", "correo_sin_arroba.com"]
    for email in emails:
        valido, error = validar_email(email)
        print(f"  {email}: {'✓' if valido else '✗'} {error or ''}")
    
    # Probar validación de contraseña
    print("\nValidación de contraseñas:")
    passwords = ["Pass123", "123", "contraseña_larga_válida"]
    for pwd in passwords:
        valido, error = validar_password(pwd)
        print(f"  {pwd}: {'✓' if valido else '✗'} {error or ''}")
    
    # Probar validación de registro completo
    print("\nValidación de datos de registro:")
    datos_usuario = {
        'nombre': 'Juan',
        'apellido': 'Pérez',
        'email': 'juan@unipamplona.edu.co',
        'password': 'Pass123',
        'semestre_actual': 5,
        'tipo_estudio': 'moderado'
    }
    valido, error = validar_datos_registro(datos_usuario)
    print(f"  Datos válidos: {'✓' if valido else '✗'} {error or ''}")
    
    print("\nTodas las pruebas completadas")