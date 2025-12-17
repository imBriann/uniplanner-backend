"""
Modulo de validaciones para UniPlanner.

Incluye funciones reutilizables para validar datos de entrada y normalizar texto.
"""

from datetime import datetime
from functools import wraps
import re
from typing import Any, List, Optional, Tuple

# ========== VALIDACIONES DE FORMATO ==========


def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de un correo electronico.

    Args:
        email: Direccion de correo a validar.

    Returns:
        Tupla (es_valido, mensaje_error).

    Example:
        >>> validar_email("usuario@unipamplona.edu.co")
        (True, None)
        >>> validar_email("correo_invalido")
        (False, 'Formato de email invalido')
    """
    if not isinstance(email, str) or not email.strip():
        return False, "El email no puede estar vacio"

    email = email.strip()
    patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(patron_email, email):
        return False, "Formato de email invalido"

    if len(email) > 255:
        return False, "Email demasiado largo (maximo 255 caracteres)"

    return True, None


def validar_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Valida la fortaleza de una contrasena.

    Reglas actuales:
    - Minimo 6 caracteres.
    - Al menos una letra.

    Args:
        password: Contrasena a validar.

    Returns:
        Tupla (es_valida, mensaje_error).

    Example:
        >>> validar_password("abc123")
        (True, None)
        >>> validar_password("123")
        (False, 'La contrasena debe tener al menos 6 caracteres')
    """
    if not isinstance(password, str) or not password:
        return False, "La contrasena no puede estar vacia"

    if len(password) < 6:
        return False, "La contrasena debe tener al menos 6 caracteres"

    if len(password) > 128:
        return False, "La contrasena es demasiado larga (maximo 128 caracteres)"

    if not re.search(r'[a-zA-Z]', password):
        return False, "La contrasena debe contener al menos una letra"

    return True, None


def validar_fecha(fecha_str: str, formato: str = '%Y-%m-%d') -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de una fecha.

    Args:
        fecha_str: Fecha en formato string.
        formato: Formato esperado (default: YYYY-MM-DD).

    Returns:
        Tupla (es_valida, mensaje_error).

    Example:
        >>> validar_fecha("2025-12-31")
        (True, None)
        >>> validar_fecha("31/12/2025", "%d/%m/%Y")
        (True, None)
    """
    if not isinstance(fecha_str, str) or not fecha_str.strip():
        return False, "La fecha no puede estar vacia"

    try:
        datetime.strptime(fecha_str, formato)
        return True, None
    except ValueError:
        return False, f"Formato de fecha invalido. Use: {formato}"


# ========== VALIDACIONES DE RANGO ==========


def validar_rango(
    valor: Any,
    minimo: Optional[Any] = None,
    maximo: Optional[Any] = None,
    nombre_campo: str = "valor"
) -> Tuple[bool, Optional[str]]:
    """
    Valida que un valor este dentro de un rango.

    Args:
        valor: Valor a validar.
        minimo: Valor minimo permitido (inclusive).
        maximo: Valor maximo permitido (inclusive).
        nombre_campo: Nombre del campo para mensajes de error.

    Returns:
        Tupla (es_valido, mensaje_error).

    Example:
        >>> validar_rango(5, 1, 10, "semestre")
        (True, None)
        >>> validar_rango(15, 1, 10, "semestre")
        (False, 'semestre debe ser menor o igual a 10')
    """
    if valor is None:
        return False, f"{nombre_campo} es requerido"

    try:
        if minimo is not None and valor < minimo:
            return False, f"{nombre_campo} debe ser mayor o igual a {minimo}"

        if maximo is not None and valor > maximo:
            return False, f"{nombre_campo} debe ser menor o igual a {maximo}"
    except TypeError:
        return False, f"{nombre_campo} debe ser comparable con el rango"

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
        texto: String a validar.
        minimo: Longitud minima.
        maximo: Longitud maxima.
        nombre_campo: Nombre del campo para mensajes.

    Returns:
        Tupla (es_valido, mensaje_error).
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
    Valida que un valor este dentro de las opciones permitidas.

    Args:
        valor: Valor a validar.
        opciones_validas: Lista de valores permitidos.
        nombre_campo: Nombre del campo.

    Returns:
        Tupla (es_valido, mensaje_error).

    Example:
        >>> validar_opcion("moderado", ["intensivo", "moderado", "leve"], "tipo_estudio")
        (True, None)
    """
    if valor not in opciones_validas:
        opciones_str = ", ".join(str(opcion) for opcion in opciones_validas)
        return False, f"{nombre_campo} debe ser uno de: {opciones_str}"

    return True, None


# ========== VALIDACIONES COMPUESTAS ==========


def validar_datos_registro(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida los datos necesarios para registrar un usuario.

    Combina varias validaciones para asegurar coherencia en el registro.

    Args:
        data: Diccionario con datos del usuario.

    Returns:
        Tupla (es_valido, mensaje_error).
    """
    if not isinstance(data, dict):
        return False, "Datos de registro invalidos"

    campos_requeridos = [
        'nombre',
        'apellido',
        'email',
        'password',
        'semestre_actual',
        'tipo_estudio',
    ]

    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido: {campo}"

    valido, error = validar_email(data['email'])
    if not valido:
        return False, error

    valido, error = validar_password(data['password'])
    if not valido:
        return False, error

    valido, error = validar_longitud(data['nombre'], 2, 100, "nombre")
    if not valido:
        return False, error

    valido, error = validar_longitud(data['apellido'], 2, 100, "apellido")
    if not valido:
        return False, error

    try:
        semestre = int(data['semestre_actual'])
        valido, error = validar_rango(semestre, 1, 12, "semestre_actual")
        if not valido:
            return False, error
    except (ValueError, TypeError):
        return False, "semestre_actual debe ser un numero"

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
    Valida los datos necesarios para crear una tarea.

    Args:
        data: Diccionario con datos de la tarea.

    Returns:
        Tupla (es_valido, mensaje_error).
    """
    if not isinstance(data, dict):
        return False, "Datos de tarea invalidos"

    campos_requeridos = ['curso_codigo', 'titulo', 'tipo', 'fecha_limite']

    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido: {campo}"

    valido, error = validar_longitud(data['titulo'], 3, 255, "titulo")
    if not valido:
        return False, error

    tipos_validos = [
        'parcial',
        'final',
        'proyecto',
        'taller',
        'exposicion',
        'lectura',
        'laboratorio',
        'quiz',
    ]
    valido, error = validar_opcion(data['tipo'], tipos_validos, 'tipo')
    if not valido:
        return False, error

    fecha_limite = data['fecha_limite']
    if not isinstance(fecha_limite, str):
        return False, "fecha_limite debe ser texto"

    fecha_sola = fecha_limite.split()[0]
    valido, error = validar_fecha(fecha_sola)
    if not valido:
        return False, error

    if 'horas_estimadas' in data and data['horas_estimadas'] is not None:
        try:
            horas = float(data['horas_estimadas'])
        except (TypeError, ValueError):
            return False, "horas_estimadas debe ser un numero"
        if horas < 0.5 or horas > 24:
            return False, "horas_estimadas debe estar entre 0.5 y 24"

    if 'dificultad' in data and data['dificultad'] is not None:
        try:
            dificultad = int(data['dificultad'])
        except (TypeError, ValueError):
            return False, "dificultad debe ser un numero"
        if dificultad < 1 or dificultad > 5:
            return False, "dificultad debe estar entre 1 y 5"

    return True, None


# ========== DECORADOR DE VALIDACION ==========


def validar_entrada(funcion_validacion):
    """
    Aplica validacion automatica a endpoints de Flask.

    Args:
        funcion_validacion: Funcion que valida los datos de entrada.

    Returns:
        Decorador aplicable a funciones de Flask.
    """
    def decorador(funcion):
        """Envuelve el endpoint para validar datos de entrada."""
        @wraps(funcion)
        def wrapper(*args, **kwargs):
            """Valida el JSON de entrada antes de ejecutar el endpoint."""
            from flask import jsonify, request

            data = request.get_json()
            if not data:
                return jsonify({'error': 'No se recibieron datos'}), 400

            es_valido, mensaje_error = funcion_validacion(data)
            if not es_valido:
                return jsonify({'error': mensaje_error}), 400

            return funcion(*args, **kwargs)

        return wrapper
    return decorador


# ========== SANITIZACION ==========


def sanitizar_texto(texto: str, max_length: int = 1000) -> str:
    """
    Limpia y sanitiza texto de entrada.

    Elimina espacios repetidos y caracteres de control, y limita la longitud.

    Args:
        texto: Texto a sanitizar.
        max_length: Longitud maxima permitida.

    Returns:
        Texto sanitizado.

    Example:
        >>> sanitizar_texto("  Hola   Mundo  ")
        'Hola Mundo'
    """
    if not texto:
        return ""

    texto = str(texto)
    texto = texto[:max_length]
    texto = ' '.join(texto.split())
    texto = ''.join(char for char in texto if ord(char) >= 32 or char == '\n')

    return texto.strip()


if __name__ == '__main__':
    print("Pruebas basicas del modulo de validaciones\n")

    print("Validacion de emails:")
    emails = ["usuario@example.com", "invalido@", "correo_sin_arroba.com"]
    for email in emails:
        valido, error = validar_email(email)
        estado = "OK" if valido else "ERROR"
        print(f"  {email}: {estado} {error or ''}")

    print("\nValidacion de contrasenas:")
    passwords = ["Pass123", "123", "contrasena_larga_valida"]
    for pwd in passwords:
        valido, error = validar_password(pwd)
        estado = "OK" if valido else "ERROR"
        print(f"  {pwd}: {estado} {error or ''}")

    print("\nValidacion de datos de registro:")
    datos_usuario = {
        'nombre': 'Juan',
        'apellido': 'Perez',
        'email': 'juan@unipamplona.edu.co',
        'password': 'Pass123',
        'semestre_actual': 5,
        'tipo_estudio': 'moderado'
    }
    valido, error = validar_datos_registro(datos_usuario)
    estado = "OK" if valido else "ERROR"
    print(f"  Datos validos: {estado} {error or ''}")

    print("\nTodas las pruebas completadas")
