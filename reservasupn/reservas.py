
import sqlite3
from datetime import datetime, timedelta

from database import conectar_base_datos


# ==========================================
# CONFIGURACION
# ==========================================

DURACIONES_PERMITIDAS = [1, 1.5, 2]
HORA_APERTURA = "09:00"
HORA_CIERRE = "21:00"
DIAS_PRESTAMO_LIBROS = 3


# ==========================================
# REGISTRAR UNA RESERVA
# ==========================================

def crear_reserva(
    codigo_estudiante,
    codigo_recurso,
    fecha_inicio,
    hora_inicio=None,
    duracion_horas=None
):
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        # Comprobar que el estudiante exista y este activo
        cursor.execute("""
            SELECT codigo_estudiante
            FROM estudiantes
            WHERE codigo_estudiante = ?
            AND estado = 'Activo'
        """, (codigo_estudiante,))

        estudiante = cursor.fetchone()

        if estudiante is None:
            return False, "El estudiante no existe o esta inactivo."

        # Buscar el recurso y su categoria
        cursor.execute("""
            SELECT
                r.id_recurso,
                r.codigo_inventario,
                r.nombre,
                r.estado,
                c.nombre_categoria
            FROM recursos r
            INNER JOIN categorias c
                ON r.id_categoria = c.id_categoria
            WHERE r.codigo_inventario = ?
        """, (codigo_recurso,))

        recurso = cursor.fetchone()

        if recurso is None:
            return False, "El recurso no existe."

        id_recurso = recurso[0]
        estado_recurso = recurso[3]
        categoria = recurso[4]

        if estado_recurso != "Disponible":
            return False, "El recurso no esta disponible para reservar."

        # Validar fecha
        try:
            fecha = datetime.strptime(
                fecha_inicio, "%Y-%m-%d"
            ).date()
        except ValueError:
            return False, "La fecha debe tener formato AAAA-MM-DD."

        if fecha < datetime.now().date():
            return False, "No puedes reservar en una fecha pasada."

        # ======================================
        # PRESTAMO DE LIBROS
        # ======================================

        if categoria == "Libros":

            fecha_fin = fecha + timedelta(
                days=DIAS_PRESTAMO_LIBROS
            )

            cursor.execute("""
                SELECT id_reserva
                FROM reservas
                WHERE id_recurso = ?
                AND estado NOT IN (
                    'Cancelada',
                    'Cancelado',
                    'Rechazada'
                )
                AND fecha_inicio <= ?
                AND fecha_fin >= ?
            """, (
                id_recurso,
                fecha_fin.isoformat(),
                fecha.isoformat()
            ))

            if cursor.fetchone():
                return False, "El libro ya esta prestado en esas fechas."

            hora_inicio = None
            hora_fin = None

        # ======================================
        # RESERVAS POR HORAS
        # ======================================

        else:

            if duracion_horas not in DURACIONES_PERMITIDAS:
                return False, "La duracion debe ser 1, 1.5 o 2 horas."

            if not hora_inicio:
                return False, "Debes indicar la hora de inicio."

            try:
                inicio = datetime.strptime(
                    hora_inicio, "%H:%M"
                )

            except ValueError:
                return False, "La hora debe tener formato HH:MM."

            hora_fin_datetime = inicio + timedelta(
                hours=duracion_horas
            )

            hora_fin = hora_fin_datetime.strftime("%H:%M")

            if hora_inicio < HORA_APERTURA:
                return False, "La atencion comienza a las 09:00."

            if hora_fin > HORA_CIERRE:
                return False, "La reserva no puede terminar despues de las 21:00."

            # Comprobar que no exista otra reserva
            # del mismo recurso en ese horario
            cursor.execute("""
                SELECT id_reserva
                FROM reservas
                WHERE id_recurso = ?
                AND fecha_inicio = ?
                AND estado NOT IN (
                    'Cancelada',
                    'Cancelado',
                    'Rechazada'
                )
                AND hora_inicio < ?
                AND hora_fin > ?
            """, (
                id_recurso,
                fecha.isoformat(),
                hora_fin,
                hora_inicio
            ))

            if cursor.fetchone():
                return False, "El recurso ya esta reservado en ese horario."

            fecha_fin = fecha

        # ======================================
        # GUARDAR RESERVA
        # ======================================

        cursor.execute("""
            INSERT INTO reservas (
                codigo_estudiante,
                id_recurso,
                fecha_inicio,
                fecha_fin,
                hora_inicio,
                hora_fin,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?, 'Pendiente')
        """, (
            codigo_estudiante,
            id_recurso,
            fecha.isoformat(),
            fecha_fin.isoformat(),
            hora_inicio,
            hora_fin
        ))

        id_reserva = cursor.lastrowid

        # Registrar operacion en el historial
        cursor.execute("""
            INSERT INTO historial (
                codigo_estudiante,
                accion,
                descripcion
            )
            VALUES (?, ?, ?)
        """, (
            codigo_estudiante,
            "Reserva creada",
            f"Reserva {id_reserva} - {recurso[2]}"
        ))

        conexion.commit()

        return True, f"Reserva registrada correctamente. Codigo: {id_reserva}"

    except sqlite3.Error as error:
        conexion.rollback()
        return False, f"Error en la base de datos: {error}"

    finally:
        conexion.close()


# ==========================================
# CONSULTAR RESERVAS DE UN ESTUDIANTE
# ==========================================

def consultar_reservas_estudiante(codigo_estudiante):
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                r.id_reserva,
                r.codigo_estudiante,
                re.codigo_inventario,
                re.nombre,
                c.nombre_categoria,
                r.fecha_inicio,
                r.fecha_fin,
                r.hora_inicio,
                r.hora_fin,
                r.estado
            FROM reservas r
            INNER JOIN recursos re
                ON r.id_recurso = re.id_recurso
            INNER JOIN categorias c
                ON re.id_categoria = c.id_categoria
            WHERE r.codigo_estudiante = ?
            ORDER BY r.fecha_registro DESC
        """, (codigo_estudiante,))

        columnas = [
            descripcion[0]
            for descripcion in cursor.description
        ]

        return [
            dict(zip(columnas, fila))
            for fila in cursor.fetchall()
        ]

    except sqlite3.Error as error:
        print("Error al consultar reservas:", error)
        return []

    finally:
        conexion.close()


# ==========================================
# CONSULTAR TODAS LAS RESERVAS
# ==========================================

def consultar_todas_las_reservas():
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                r.id_reserva,
                r.codigo_estudiante,
                e.nombres,
                e.apellidos,
                re.codigo_inventario,
                re.nombre AS recurso,
                c.nombre_categoria,
                r.fecha_inicio,
                r.fecha_fin,
                r.hora_inicio,
                r.hora_fin,
                r.estado
            FROM reservas r
            INNER JOIN estudiantes e
                ON r.codigo_estudiante = e.codigo_estudiante
            INNER JOIN recursos re
                ON r.id_recurso = re.id_recurso
            INNER JOIN categorias c
                ON re.id_categoria = c.id_categoria
            ORDER BY r.fecha_registro DESC
        """)

        columnas = [
            descripcion[0]
            for descripcion in cursor.description
        ]

        return [
            dict(zip(columnas, fila))
            for fila in cursor.fetchall()
        ]

    except sqlite3.Error as error:
        print("Error al consultar todas las reservas:", error)
        return []

    finally:
        conexion.close()


# ==========================================
# CANCELAR UNA RESERVA
# ==========================================

def cancelar_reserva(id_reserva, codigo_estudiante):
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_reserva
            FROM reservas
            WHERE id_reserva = ?
            AND codigo_estudiante = ?
            AND estado NOT IN (
                'Cancelada',
                'Cancelado',
                'Rechazada'
            )
        """, (id_reserva, codigo_estudiante))

        reserva = cursor.fetchone()

        if reserva is None:
            return False, "No se encontro una reserva activa con esos datos."

        cursor.execute("""
            UPDATE reservas
            SET estado = 'Cancelada'
            WHERE id_reserva = ?
        """, (id_reserva,))

        cursor.execute("""
            INSERT INTO historial (
                codigo_estudiante,
                accion,
                descripcion
            )
            VALUES (?, ?, ?)
        """, (
            codigo_estudiante,
            "Reserva cancelada",
            f"Se cancelo la reserva {id_reserva}"
        ))

        conexion.commit()

        return True, "Reserva cancelada correctamente."

    except sqlite3.Error as error:
        conexion.rollback()
        return False, f"Error al cancelar: {error}"

    finally:
        conexion.close()


def consultar_reservas_estudiante(codigo_estudiante):
    conexion = conectar_base_datos()
    conexion.row_factory = sqlite3.Row

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                r.id_reserva,
                r.codigo_estudiante,
                re.codigo_inventario,
                re.nombre,
                c.nombre_categoria,
                r.fecha_inicio,
                r.fecha_fin,
                r.hora_inicio,
                r.hora_fin,
                r.estado
            FROM reservas r
            INNER JOIN recursos re ON r.id_recurso = re.id_recurso
            INNER JOIN categorias c ON re.id_categoria = c.id_categoria
            WHERE r.codigo_estudiante = ?
            ORDER BY r.fecha_registro DESC
        """, (codigo_estudiante,))

        return [dict(fila) for fila in cursor.fetchall()]

    except sqlite3.Error as error:
        print(f"Error al consultar reservas: {error}")
        return []

    finally:
        conexion.close()