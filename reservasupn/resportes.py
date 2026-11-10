import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from database import conectar_base_datos


def obtener_reservas():
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                r.id_reserva,
                r.codigo_estudiante,
                e.nombres || ' ' || e.apellidos,
                re.codigo_inventario,
                re.nombre,
                c.nombre_categoria,
                r.fecha_inicio,
                r.fecha_fin,
                r.hora_inicio,
                r.hora_fin,
                r.estado,
                r.fecha_registro
            FROM reservas r
            INNER JOIN estudiantes e
                ON r.codigo_estudiante = e.codigo_estudiante
            INNER JOIN recursos re
                ON r.id_recurso = re.id_recurso
            INNER JOIN categorias c
                ON re.id_categoria = c.id_categoria
            ORDER BY r.fecha_registro DESC
        """)

        return cursor.fetchall()

    finally:
        conexion.close()


def obtener_inventario():
    conexion = conectar_base_datos()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                re.codigo_inventario,
                re.nombre,
                c.nombre_categoria,
                re.descripcion,
                re.ubicacion,
                re.estado
            FROM recursos re
            INNER JOIN categorias c
                ON re.id_categoria = c.id_categoria
            ORDER BY c.nombre_categoria, re.nombre
        """)

        return cursor.fetchall()

    finally:
        conexion.close()


def obtener_estudiantes():
    conexion = conectar_base_datos()

    try:
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

        return cursor.fetchall()

    finally:
        conexion.close()


def preparar_hoja(hoja, encabezados, datos):
    hoja.append(encabezados)

    for fila in datos:
        hoja.append(fila)

    color_encabezado = PatternFill(
        fill_type="solid",
        fgColor="17365D"
    )

    for celda in hoja[1]:
        celda.font = Font(
            bold=True,
            color="FFFFFF"
        )
        celda.fill = color_encabezado
        celda.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions

    for columna in hoja.columns:
        longitud = 0
        letra = get_column_letter(columna[0].column)

        for celda in columna:
            if celda.value is not None:
                longitud = max(
                    longitud,
                    len(str(celda.value))
                )

        hoja.column_dimensions[letra].width = min(
            longitud + 3,
            40
        )


def exportar_reporte_completo(ruta_archivo=None):

    try:
        carpeta_reportes = os.path.join(
            os.path.dirname(__file__),
            "reportes"
        )

        os.makedirs(carpeta_reportes, exist_ok=True)

        if ruta_archivo is None:
            fecha = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            nombre_archivo = f"Reporte_ReservaUPN_{fecha}.xlsx"

            ruta_archivo = os.path.join(
                carpeta_reportes,
                nombre_archivo
            )

        libro = Workbook()

        hoja_reservas = libro.active
        hoja_reservas.title = "Reservas"

        preparar_hoja(
            hoja_reservas,
            [
                "ID reserva",
                "Código estudiante",
                "Estudiante",
                "Código recurso",
                "Recurso",
                "Categoría",
                "Fecha inicio",
                "Fecha fin",
                "Hora inicio",
                "Hora fin",
                "Estado",
                "Fecha de registro"
            ],
            obtener_reservas()
        )

        hoja_inventario = libro.create_sheet(
            "Inventario"
        )

        preparar_hoja(
            hoja_inventario,
            [
                "Código",
                "Nombre",
                "Categoría",
                "Descripción",
                "Ubicación",
                "Estado"
            ],
            obtener_inventario()
        )

        hoja_estudiantes = libro.create_sheet(
            "Estudiantes"
        )

        preparar_hoja(
            hoja_estudiantes,
            [
                "Código",
                "Nombres",
                "Apellidos",
                "Correo",
                "Teléfono",
                "Estado",
                "Fecha de registro"
            ],
            obtener_estudiantes()
        )

        libro.save(ruta_archivo)

        return True, f"Reporte exportado correctamente: {ruta_archivo}"

    except Exception as error:
        return False, f"No se pudo exportar el reporte: {error}"