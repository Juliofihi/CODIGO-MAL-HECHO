
import sqlite3
import os


# ==========================================
# CONFIGURACION DE LA BASE DE DATOS
# ==========================================

CARPETA_BASE_DATOS = "base_datos"
RUTA_BASE_DATOS = os.path.join(
    CARPETA_BASE_DATOS,
    "reservaupn.db"
)


def conectar_base_datos():
    os.makedirs(CARPETA_BASE_DATOS, exist_ok=True)

    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion


# ==========================================
# CREACION DE TABLAS
# ==========================================

def crear_tablas():
    conexion = conectar_base_datos()
    cursor = conexion.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            codigo_estudiante TEXT PRIMARY KEY,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT,
            contrasena_hash TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Activo',
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS administradores (
            id_administrador INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT UNIQUE,
            telefono TEXT,
            contrasena_hash TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS categorias (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_categoria TEXT NOT NULL UNIQUE,
            descripcion TEXT
        );

        CREATE TABLE IF NOT EXISTS recursos (
            id_recurso INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_inventario TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            id_categoria INTEGER NOT NULL,
            descripcion TEXT,
            ubicacion TEXT,
            estado TEXT NOT NULL DEFAULT 'Disponible',

            FOREIGN KEY (id_categoria)
                REFERENCES categorias(id_categoria)
        );

        CREATE TABLE IF NOT EXISTS libros (
            id_recurso INTEGER PRIMARY KEY,
            autor TEXT,
            editorial TEXT,
            isbn TEXT,
            area TEXT,
            anio_publicacion INTEGER,

            FOREIGN KEY (id_recurso)
                REFERENCES recursos(id_recurso)
        );

        CREATE TABLE IF NOT EXISTS juegos (
            id_recurso INTEGER PRIMARY KEY,
            numero_jugadores INTEGER,
            descripcion_juego TEXT,

            FOREIGN KEY (id_recurso)
                REFERENCES recursos(id_recurso)
        );

        CREATE TABLE IF NOT EXISTS reservas (
            id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_estudiante TEXT NOT NULL,
            id_recurso INTEGER NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            hora_inicio TEXT,
            hora_fin TEXT,
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (codigo_estudiante)
                REFERENCES estudiantes(codigo_estudiante),

            FOREIGN KEY (id_recurso)
                REFERENCES recursos(id_recurso),

            CHECK (fecha_fin >= fecha_inicio)
        );

        CREATE TABLE IF NOT EXISTS historial (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_estudiante TEXT,
            accion TEXT NOT NULL,
            descripcion TEXT,
            fecha_operacion TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (codigo_estudiante)
                REFERENCES estudiantes(codigo_estudiante)
        );

        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS indice_reservas_recurso
        ON reservas(id_recurso, fecha_inicio, fecha_fin);

        CREATE INDEX IF NOT EXISTS indice_reservas_estudiante
        ON reservas(codigo_estudiante);
    """)

    # Agregar telefono si la tabla ya existia sin esa columna.
    for tabla in ("estudiantes", "administradores"):
        columnas = [
            fila[1]
            for fila in cursor.execute(
                f"PRAGMA table_info({tabla})"
            ).fetchall()
        ]

        if "telefono" not in columnas:
            cursor.execute(
                f"ALTER TABLE {tabla} ADD COLUMN telefono TEXT"
            )

    conexion.commit()
    conexion.close()


# ==========================================
# CATEGORIAS
# ==========================================

def registrar_categorias():
    conexion = conectar_base_datos()
    cursor = conexion.cursor()

    categorias = [
        ("Computadoras", "Equipos informaticos para estudiantes"),
        ("Salas", "Espacios de estudio y trabajo grupal"),
        ("Libros", "Material bibliografico"),
        ("Juegos", "Juegos de mesa educativos y recreativos")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO categorias
        (nombre_categoria, descripcion)
        VALUES (?, ?)
    """, categorias)

    conexion.commit()
    conexion.close()


# ==========================================
# INVENTARIO INICIAL
# Datos de demostracion, no inventario oficial UPN.
# ==========================================

def registrar_inventario_inicial():
    conexion = conectar_base_datos()
    cursor = conexion.cursor()

    categorias = {
        fila[1]: fila[0]
        for fila in cursor.execute(
            "SELECT id_categoria, nombre_categoria FROM categorias"
        ).fetchall()
    }

    recursos = []

    # 10 computadoras
    for numero in range(1, 11):
        recursos.append((
            f"PC-{numero:03}",
            f"Computadora {numero}",
            categorias["Computadoras"],
            "Equipo informatico para uso academico",
            "Laboratorio de computo"
        ))

    # 5 salas
    for numero in range(1, 6):
        recursos.append((
            f"SAL-{numero:03}",
            f"Sala de estudio {numero}",
            categorias["Salas"],
            "Espacio para estudio y trabajo grupal",
            f"Pabellon de estudio - Sala {numero}"
        ))

    # 15 libros de demostracion
    libros = [
        ("Introduccion a la programacion", "Autor por registrar", "Informatica"),
        ("Fundamentos de Python", "Autor por registrar", "Programacion"),
        ("Bases de datos", "Autor por registrar", "Informatica"),
        ("Logica matematica", "Autor por registrar", "Matematica"),
        ("Calculo diferencial", "Autor por registrar", "Matematica"),
        ("Algebra lineal", "Autor por registrar", "Matematica"),
        ("Comunicacion efectiva", "Autor por registrar", "Comunicacion"),
        ("Comprension lectora", "Autor por registrar", "Comunicacion"),
        ("Administracion general", "Autor por registrar", "Administracion"),
        ("Contabilidad basica", "Autor por registrar", "Contabilidad"),
        ("Marketing digital", "Autor por registrar", "Marketing"),
        ("Estadistica aplicada", "Autor por registrar", "Estadistica"),
        ("Redes informaticas", "Autor por registrar", "Tecnologia"),
        ("Seguridad informatica", "Autor por registrar", "Tecnologia"),
        ("Etica profesional", "Autor por registrar", "Humanidades")
    ]

    for numero, (titulo, autor, area) in enumerate(libros, 1):
        recursos.append((
            f"LIB-{numero:03}",
            titulo,
            categorias["Libros"],
            "Libro de demostracion",
            "Biblioteca"
        ))

    # 10 juegos de demostracion
    juegos = [
        ("Ajedrez", 2),
        ("Damas", 2),
        ("Domino", 4),
        ("Monopoly", 6),
        ("Scrabble", 4),
        ("Jenga", 4),
        ("Uno", 10),
        ("Rummikub", 4),
        ("Ludo", 4),
        ("Memoria", 4)
    ]

    for numero, (nombre, jugadores) in enumerate(juegos, 1):
        recursos.append((
            f"JUE-{numero:03}",
            nombre,
            categorias["Juegos"],
            "Juego de mesa de demostracion",
            "Area recreativa"
        ))

    cursor.executemany("""
        INSERT OR IGNORE INTO recursos
        (codigo_inventario, nombre, id_categoria, descripcion, ubicacion)
        VALUES (?, ?, ?, ?, ?)
    """, recursos)

    # Registrar detalles de los libros
    for numero, (titulo, autor, area) in enumerate(libros, 1):
        codigo = f"LIB-{numero:03}"

        fila = cursor.execute("""
            SELECT id_recurso FROM recursos
            WHERE codigo_inventario = ?
        """, (codigo,)).fetchone()

        cursor.execute("""
            INSERT OR IGNORE INTO libros
            (id_recurso, autor, area)
            VALUES (?, ?, ?)
        """, (fila[0], autor, area))

    # Registrar detalles de los juegos
    for numero, (nombre, jugadores) in enumerate(juegos, 1):
        codigo = f"JUE-{numero:03}"

        fila = cursor.execute("""
            SELECT id_recurso FROM recursos
            WHERE codigo_inventario = ?
        """, (codigo,)).fetchone()

        cursor.execute("""
            INSERT OR IGNORE INTO juegos
            (id_recurso, numero_jugadores, descripcion_juego)
            VALUES (?, ?, ?)
        """, (fila[0], jugadores, "Juego de mesa"))

    conexion.commit()
    conexion.close()


# ==========================================
# CONFIGURACION DEL SISTEMA
# ==========================================

def registrar_configuracion():
    conexion = conectar_base_datos()
    cursor = conexion.cursor()

    configuraciones = [
        ("hora_apertura", "09:00"),
        ("hora_cierre", "21:00"),
        ("duracion_maxima_reserva_horas", "2"),
        ("duracion_prestamo_libros_dias", "3"),
        ("duraciones_permitidas", "1,1.5,2")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO configuracion
        (clave, valor)
        VALUES (?, ?)
    """, configuraciones)

    conexion.commit()
    conexion.close()


# ==========================================
# CREAR BASE DE DATOS COMPLETA
# ==========================================

def crear_base_datos():
    crear_tablas()
    registrar_categorias()
    registrar_inventario_inicial()
    registrar_configuracion()

    print("Base de datos ReservaUPN creada correctamente.")
    print("Las tablas y el inventario inicial estan preparados.")


if __name__ == "__main__":
    crear_base_datos()
