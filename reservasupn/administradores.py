
import sqlite3
import os


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
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# Listar todas las categorias
def listar_categorias():
    try:
        with conectar() as conexion:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT id, nombre, descripcion
                FROM categorias
                ORDER BY nombre
            """)

            return [dict(fila) for fila in cursor.fetchall()]

    except sqlite3.Error:
        return []


# Listar recursos disponibles de una categoria
def listar_recursos(categoria):
    try:
        with conectar() as conexion:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT
                    r.id,
                    r.codigo,
                    r.nombre,
                    r.descripcion,
                    r.estado,
                    c.nombre AS categoria
                FROM recursos r
                INNER JOIN categorias c
                    ON r.categoria_id = c.id
                WHERE c.nombre = ?
                ORDER BY r.codigo
            """, (categoria,))

            return [dict(fila) for fila in cursor.fetchall()]

    except sqlite3.Error:
        return []


# Consultar un recurso por su codigo
def obtener_recurso(codigo):
    try:
        with conectar() as conexion:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT
                    r.id,
                    r.codigo,
                    r.nombre,
                    r.descripcion,
                    r.estado,
                    c.nombre AS categoria
                FROM recursos r
                INNER JOIN categorias c
                    ON r.categoria_id = c.id
                WHERE r.codigo = ?
            """, (codigo,))

            recurso = cursor.fetchone()

            return dict(recurso) if recurso else None

    except sqlite3.Error:
        return None


# Agregar un recurso nuevo
def agregar_recurso(
    categoria_id,
    codigo,
    nombre,
    descripcion=""
):
    if not codigo.strip() or not nombre.strip():
        return False, "El codigo y el nombre son obligatorios."

    try:
        with conectar() as conexion:
            conexion.execute("""
                INSERT INTO recursos (
                    categoria_id,
                    codigo,
                    nombre,
                    descripcion,
                    estado
                )
                VALUES (?, ?, ?, ?, 'Disponible')
            """, (
                categoria_id,
                codigo.strip().upper(),
                nombre.strip(),
                descripcion.strip()
            ))

        return True, "Recurso agregado correctamente."

    except sqlite3.IntegrityError:
        return False, "El codigo ya existe o la categoria no es valida."

    except sqlite3.Error as error:
        return False, f"Error de base de datos: {error}"


# Cambiar el estado de un recurso
def cambiar_estado_recurso(codigo, nuevo_estado):
    estados_validos = [
        "Disponible",
        "Mantenimiento",
        "Inactivo"
    ]

    if nuevo_estado not in estados_validos:
        return False, "El estado indicado no es valido."

    try:
        with conectar() as conexion:
            cursor = conexion.cursor()

            cursor.execute("""
                UPDATE recursos
                SET estado = ?
                WHERE codigo = ?
            """, (nuevo_estado, codigo))

            if cursor.rowcount == 0:
                return False, "No se encontro el recurso."

        return True, "Estado actualizado correctamente."

    except sqlite3.Error as error:
        return False, f"Error de base de datos: {error}"


# Eliminar un recurso
def eliminar_recurso(codigo):
    try:
        with conectar() as conexion:
            cursor = conexion.cursor()

            cursor.execute("""
                DELETE FROM recursos
                WHERE codigo = ?
            """, (codigo,))

            if cursor.rowcount == 0:
                return False, "No se encontro el recurso."

        return True, "Recurso eliminado correctamente."

    except sqlite3.IntegrityError:
        return False, (
            "No se puede eliminar porque tiene reservas relacionadas."
        )

    except sqlite3.Error as error:
        return False, f"Error de base de datos: {error}"
