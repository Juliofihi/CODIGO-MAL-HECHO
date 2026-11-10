
import sqlite3
import os
import hashlib
import hmac


# Ubicacion de la base de datos
RUTA_BASE_DATOS = os.path.join(
    os.path.dirname(__file__),
    "base_datos",
    "reservaupn.db"
)


# Conectar con la base de datos
def conectar():
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


# Verificar la contraseña
def verificar_contrasena(contrasena, hash_guardado):
    try:
        algoritmo, iteraciones, sal, hash_original = hash_guardado.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        hash_nuevo = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            bytes.fromhex(sal),
            int(iteraciones)
        ).hex()

        return hmac.compare_digest(hash_nuevo, hash_original)

    except (ValueError, TypeError):
        return False


# Iniciar sesion del estudiante
def iniciar_sesion(codigo, contrasena):
    codigo = codigo.strip().upper()

    if not codigo or not contrasena:
        return None

    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo_estudiante = ?
            AND estado = 'Activo'
        """, (codigo,))

        estudiante = cursor.fetchone()
        conexion.close()

        if estudiante is None:
            return None

        if not verificar_contrasena(
            contrasena,
            estudiante["contrasena_hash"]
        ):
            return None

        return obtener_estudiante(codigo)

    except sqlite3.Error:
        return None


# Obtener los datos del estudiante
def obtener_estudiante(codigo):
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                codigo_estudiante,
                nombres,
                apellidos,
                correo,
                telefono,
                estado,
                fecha_registro
            FROM estudiantes
            WHERE codigo_estudiante = ?
        """, (codigo,))

        estudiante = cursor.fetchone()
        conexion.close()

        if estudiante is None:
            return None

        return dict(estudiante)

    except sqlite3.Error:
        return None


# Listar estudiantes (uso administrativo)
def listar_estudiantes():
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                codigo_estudiante,
                nombres,
                apellidos,
                correo,
                telefono,
                estado,
                fecha_registro
            FROM estudiantes
            ORDER BY apellidos, nombres
        """)

        estudiantes = [dict(fila) for fila in cursor.fetchall()]
        conexion.close()

        return estudiantes

    except sqlite3.Error:
        return []
