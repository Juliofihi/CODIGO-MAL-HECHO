import tkinter as tk
from tkinter import messagebox, ttk

from estudiantes import iniciar_sesion
from reservas import consultar_reservas_estudiante


def iniciar_interfaz():

    ventana = tk.Tk()
    ventana.title("ReservaUPN")
    ventana.geometry("850x600")
    ventana.resizable(False, False)
    ventana.configure(bg="#F2F4F8")

    def limpiar_ventana():
        for elemento in ventana.winfo_children():
            elemento.destroy()

    def mostrar_inicio_sesion():

        limpiar_ventana()

        marco = tk.Frame(
            ventana,
            bg="white",
            padx=40,
            pady=35
        )
        marco.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            marco,
            text="ReservaUPN",
            font=("Arial", 25, "bold"),
            bg="white",
            fg="#17365D"
        ).pack(pady=10)

        tk.Label(
            marco,
            text="Sistema de reservas universitarias",
            font=("Arial", 11),
            bg="white"
        ).pack(pady=5)

        tk.Label(
            marco,
            text="Código de estudiante",
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(20, 5))

        entrada_codigo = tk.Entry(
            marco,
            width=35,
            font=("Arial", 12)
        )
        entrada_codigo.pack(ipady=7)

        tk.Label(
            marco,
            text="Contraseña",
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(15, 5))

        entrada_contrasena = tk.Entry(
            marco,
            width=35,
            font=("Arial", 12),
            show="*"
        )
        entrada_contrasena.pack(ipady=7)

        def acceder():

            codigo = entrada_codigo.get().strip()
            contrasena = entrada_contrasena.get()

            if not codigo or not contrasena:
                messagebox.showwarning(
                    "Datos incompletos",
                    "Ingresa tu código y contraseña."
                )
                return

            try:
                estudiante = iniciar_sesion(
                    codigo,
                    contrasena
                )

                if estudiante:
                    mostrar_panel_estudiante(estudiante)
                else:
                    messagebox.showerror(
                        "Acceso denegado",
                        "Código o contraseña incorrectos, "
                        "o cuenta inactiva."
                    )

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"No se pudo iniciar sesión:\n{error}"
                )

        tk.Button(
            marco,
            text="INICIAR SESIÓN",
            command=acceder,
            bg="#17365D",
            fg="white",
            font=("Arial", 11, "bold"),
            width=30,
            pady=10,
            cursor="hand2"
        ).pack(pady=25)

    def mostrar_panel_estudiante(estudiante):

        limpiar_ventana()

        encabezado = tk.Frame(
            ventana,
            bg="#17365D",
            height=100
        )
        encabezado.pack(fill="x")

        tk.Label(
            encabezado,
            text="ReservaUPN",
            font=("Arial", 23, "bold"),
            bg="#17365D",
            fg="white"
        ).pack(pady=25)

        contenido = tk.Frame(
            ventana,
            bg="white",
            padx=30,
            pady=20
        )
        contenido.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(
            contenido,
            text="Panel del estudiante",
            font=("Arial", 19, "bold"),
            bg="white",
            fg="#17365D"
        ).pack(anchor="w", pady=10)

        nombre = (
            estudiante.get("nombres", "")
            + " "
            + estudiante.get("apellidos", "")
        )

        informacion = (
            f"Estudiante: {nombre}\n"
            f"Código: {estudiante.get('codigo_estudiante', '')}\n"
            f"Correo: {estudiante.get('correo', '')}\n"
            f"Teléfono: {estudiante.get('telefono') or 'No registrado'}"
        )

        tk.Label(
            contenido,
            text=informacion,
            font=("Arial", 11),
            bg="white",
            justify="left"
        ).pack(anchor="w", pady=10)

        tk.Label(
            contenido,
            text="Mis reservas",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(15, 5))

        tabla = ttk.Treeview(
            contenido,
            columns=("recurso", "fecha", "horario", "estado"),
            show="headings",
            height=8
        )

        tabla.heading("recurso", text="Recurso")
        tabla.heading("fecha", text="Fecha")
        tabla.heading("horario", text="Horario")
        tabla.heading("estado", text="Estado")

        tabla.column("recurso", width=220)
        tabla.column("fecha", width=130)
        tabla.column("horario", width=130)
        tabla.column("estado", width=120)

        tabla.pack(fill="x", pady=10)

        try:
            reservas = consultar_reservas_estudiante(
                estudiante["codigo_estudiante"]
            )

            for reserva in reservas:
                recurso = (
                    reserva.get("nombre")
                    or reserva.get("recurso")
                    or "Recurso"
                )

                fecha = reserva.get("fecha_inicio", "")

                hora_inicio = reserva.get("hora_inicio") or ""
                hora_fin = reserva.get("hora_fin") or ""
                horario = (
                    f"{hora_inicio} - {hora_fin}"
                    if hora_inicio and hora_fin
                    else "Préstamo de 3 días"
                )

                estado = reserva.get("estado", "")

                tabla.insert(
                    "",
                    "end",
                    values=(recurso, fecha, horario, estado)
                )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar las reservas:\n{error}"
            )

        tk.Button(
            contenido,
            text="CERRAR SESIÓN",
            command=mostrar_inicio_sesion,
            bg="#17365D",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8
        ).pack(anchor="e", pady=15)

    mostrar_inicio_sesion()
    ventana.mainloop()
