# Archivo único: lógica del sistema, interfaz Tkinter y demostración.
# Ejecutar la interfaz: python Software_FJ_completo.py
# Ejecutar la demostración: python Software_FJ_completo.py --demo

import argparse
import logging
import math
import re
from abc import ABC, abstractmethod
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

LOGGER = logging.getLogger("software_fj")

def configurar_logs():
    ruta_log = Path("software_fj.log").resolve()
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == ruta_log
        for handler in LOGGER.handlers
    ):
        handler = logging.FileHandler(ruta_log, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        ))
        LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def registrar_evento(mensaje: str):
    configurar_logs()
    LOGGER.info(mensaje)


def registrar_error(error: Exception, contexto: str):
    configurar_logs()
    LOGGER.error("%s: %s", contexto, error, exc_info=True)


def _validar_texto(valor: str, etiqueta: str, error_type=None) -> str:
    if not isinstance(valor, str) or not valor.strip():
        exception_type = error_type or SoftwareFJError
        raise exception_type(f"{etiqueta} es obligatorio.")
    return valor.strip()


def _redondear_costo(costo: float) -> float:
    if not math.isfinite(costo):
        raise ErrorServicio("El cálculo produjo un costo fuera del rango permitido.")
    return round(costo, 2)


# 2. EXCEPCIONES PERSONALIZADAS Y ENCADENAMIENTO
class SoftwareFJError(Exception):
    """Excepción base personalizada para todos los errores del sistema Software FJ."""

    def __init__(self, mensaje: str):
        configurar_logs()
        LOGGER.error("%s: %s", type(self).__name__, mensaje)
        super().__init__(mensaje)

class ErrorCliente(SoftwareFJError):
    """Excepción lanzada ante fallos en los datos o validaciones de clientes."""
    pass

class ErrorServicio(SoftwareFJError):
    """Excepción lanzada ante parámetros inválidos o fallos en los servicios."""
    pass

class ErrorReserva(SoftwareFJError):
    """Excepción lanzada ante conflictos en la creación, confirmación o cancelación de reservas."""
    pass

# 3. CLASE ABSTRACTA BASE (Abstracción)

class EntidadBase(ABC):
    """
    Clase abstracta que representa una entidad general del sistema Software FJ.
    Establece un contrato para la representación en texto y validación de datos.
    """
    
    def __init__(self, id_entidad: str):
        self._id_entidad = _validar_texto(id_entidad, "El identificador")

    @property
    def id_entidad(self) -> str:
        """Getter encapsulado para el ID de la entidad."""
        return self._id_entidad

    @abstractmethod
    def validar(self) -> bool:
        """Método abstracto que obliga a las clases hijas a implementar sus propias reglas de validación."""
        pass

    @abstractmethod
    def obtener_informacion(self) -> dict:
        """Método abstracto para retornar un diccionario con los datos de la entidad."""
        pass

# 4. CLASE CLIENTE (Encapsulación y Validaciones)

class Cliente(EntidadBase):
    """
    Representa a un cliente de Software FJ con validaciones rigurosas y encapsulación estricta.
    """
    
    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str):
        super().__init__(id_cliente)
        # Asignación mediante setters para aplicar validaciones desde la instanciación
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str):
        if not isinstance(value, str) or len(value.strip()) < 3:
            raise ErrorCliente(f"Nombre de cliente inválido: '{value}'. Debe tener al menos 3 caracteres.")
        self._nombre = value.strip()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, value: str):
        if not isinstance(value, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()):
            raise ErrorCliente(f"Correo electrónico inválido: '{value}'. Formato requerido: user@domain.com")
        self._correo = value.strip()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, value: str):
        if not isinstance(value, str) or not value.strip().isdigit() or len(value.strip()) < 7:
            raise ErrorCliente(f"Teléfono inválido: '{value}'. Debe contener solo dígitos y al menos 7 caracteres.")
        self._telefono = value.strip()

    def validar(self) -> bool:
        """Valida que los datos del cliente cumplan con los criterios internos."""
        return bool(self._nombre and self._correo and self._telefono)

    def obtener_informacion(self) -> dict:
        return {
            "tipo": "Cliente",
            "id": self.id_entidad,
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono
        }

# 5. CLASE ABSTRACTA SERVICIO Y POLIMORFISMO

class Servicio(ABC):
    """
    Clase abstracta que define la estructura común para los servicios ofrecidos por Software FJ.
    Implementa polimorfismo mediante métodos abstractos sobrescritos por las subclases.
    """
    
    def __init__(self, codigo: str, nombre_servicio: str, tarifa_base: float):
        self._codigo = _validar_texto(codigo, "El código del servicio", ErrorServicio)
        self._nombre_servicio = _validar_texto(
            nombre_servicio, "El nombre del servicio", ErrorServicio
        )
        self.tarifa_base = tarifa_base  # Usa propiedad setter
        self.disponible = True

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nombre_servicio(self) -> str:
        return self._nombre_servicio

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, valor: bool):
        if not isinstance(valor, bool):
            raise ErrorServicio("La disponibilidad debe ser un valor booleano.")
        self._disponible = valor

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, value: float):
        if isinstance(value, bool):
            raise ErrorServicio("La tarifa base debe ser numérica.")
        try:
            tarifa = float(value)
        except (TypeError, ValueError) as error:
            raise ErrorServicio(f"La tarifa base debe ser numérica: {value}") from error
        if not math.isfinite(tarifa) or tarifa < 0:
            raise ErrorServicio("La tarifa base debe ser un número finito no negativo.")
        self._tarifa_base = tarifa

    @abstractmethod
    def calcular_costo(self, *args, **kwargs) -> float:
        """Método polimórfico abstracto para calcular costos según las reglas de cada servicio."""
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        """Método abstracto para obtener la descripción detallada del servicio."""
        pass

    @abstractmethod
    def validar_parametros(self, *args, **kwargs) -> bool:
        """Valida los parámetros específicos de cada tipo de servicio."""
        pass

# 6. CLASES DERIVADAS DE SERVICIOS (Herencia)

class ReservaSala(Servicio):
    """Servicio especializado 1: Reserva de salas físicas o virtuales para reuniones."""
    
    def __init__(self, codigo: str, nombre: str, tarifa_base: float, capacidad: int):
        super().__init__(codigo, nombre, tarifa_base)
        self.capacidad = capacidad

    @property
    def capacidad(self) -> int:
        return self._capacidad

    @capacidad.setter
    def capacidad(self, value: int):
        if isinstance(value, bool):
            raise ErrorServicio("La capacidad de la sala debe ser un número entero.")
        try:
            capacidad = int(value)
        except (TypeError, ValueError) as error:
            raise ErrorServicio("La capacidad de la sala debe ser un número entero.") from error
        if isinstance(value, float) and not value.is_integer():
            raise ErrorServicio("La capacidad de la sala debe ser un número entero.")
        if capacidad <= 0:
            raise ErrorServicio("La capacidad de la sala debe ser mayor a 0.")
        self._capacidad = capacidad

    def validar_parametros(self, horas: int = 0, *args, **kwargs) -> bool:
        if not isinstance(horas, int) or isinstance(horas, bool) or horas <= 0:
            raise ErrorServicio(f"Cantidad de horas inválida ({horas}) para reserva de sala.")
        return True

    def calcular_costo(self, horas: int = 1, incluir_proyector: bool = False, descuento_porcentaje: float = 0.0) -> float:
        """
        Método sobrecargado mediante argumentos opcionales y predeterminados.
        Calcula el costo considerando horas, cargos adicionales por proyector y descuentos.
        """
        self.validar_parametros(horas=horas)
        if not isinstance(incluir_proyector, bool):
            raise ErrorServicio("La opción de proyector debe ser verdadera o falsa.")
        if isinstance(descuento_porcentaje, bool):
            raise ErrorServicio("El descuento debe ser numérico.")
        try:
            descuento = float(descuento_porcentaje)
        except (TypeError, ValueError) as error:
            raise ErrorServicio("El descuento debe ser numérico.") from error
        if not math.isfinite(descuento) or not 0 <= descuento <= 100:
            raise ErrorServicio("El descuento debe estar entre 0 y 100 por ciento.")
        costo = self.tarifa_base * horas
        if incluir_proyector:
            costo += 50.0  # Cargo fijo por proyector
        if descuento > 0:
            costo -= costo * (descuento / 100.0)
        return _redondear_costo(costo)

    def describir_servicio(self) -> str:
        return f"Reserva de Sala: '{self.nombre_servicio}' (Capacidad: {self.capacidad} personas, Tarifa base: ${self.tarifa_base}/hr)"

class AlquilerEquipos(Servicio):
    """Servicio especializado 2: Alquiler temporal de equipos tecnológicos."""
    
    def __init__(self, codigo: str, nombre: str, tarifa_base: float, tipo_equipo: str):
        super().__init__(codigo, nombre, tarifa_base)
        self.tipo_equipo = _validar_texto(
            tipo_equipo, "El tipo de equipo", ErrorServicio
        )

    def validar_parametros(self, dias: int = 0, *args, **kwargs) -> bool:
        if not isinstance(dias, int) or isinstance(dias, bool) or dias <= 0:
            raise ErrorServicio(f"Cantidad de días inválida ({dias}) para alquiler de equipos.")
        return True

    def calcular_costo(self, dias: int = 1, seguro_incluido: bool = False) -> float:
        """Calcula el costo por días de alquiler, sumando seguro opcional si se requiere."""
        self.validar_parametros(dias=dias)
        if not isinstance(seguro_incluido, bool):
            raise ErrorServicio("La opción de seguro debe ser verdadera o falsa.")
        costo = self.tarifa_base * dias
        if seguro_incluido:
            costo += 30.0 * dias  # Costo diario de seguro
        return _redondear_costo(costo)

    def describir_servicio(self) -> str:
        return f"Alquiler de Equipo: '{self.nombre_servicio}' [Tipo: {self.tipo_equipo}, Tarifa base: ${self.tarifa_base}/día]"


class AsesoriaEspecializada(Servicio):
    """Servicio especializado 3: Asesorías técnicas o de arquitectura de software especializadas."""
    
    def __init__(self, codigo: str, nombre: str, tarifa_base: float, nivel_experto: str):
        super().__init__(codigo, nombre, tarifa_base)
        self.nivel_experto = _validar_texto(
            nivel_experto, "El nivel de experto", ErrorServicio
        )

    def validar_parametros(self, sesiones: int = 0, *args, **kwargs) -> bool:
        if not isinstance(sesiones, int) or isinstance(sesiones, bool) or sesiones <= 0:
            raise ErrorServicio(f"Número de sesiones inválido ({sesiones}) para asesoría especializada.")
        return True

    def calcular_costo(self, sesiones: int = 1, impuestos: float = 19.0) -> float:
        """Calcula el costo de las asesorías aplicando impuestos configurables."""
        self.validar_parametros(sesiones=sesiones)
        if isinstance(impuestos, bool):
            raise ErrorServicio("Los impuestos deben ser numéricos.")
        try:
            porcentaje_impuestos = float(impuestos)
        except (TypeError, ValueError) as error:
            raise ErrorServicio("Los impuestos deben ser numéricos.") from error
        if not math.isfinite(porcentaje_impuestos) or porcentaje_impuestos < 0:
            raise ErrorServicio("Los impuestos no pueden ser negativos.")
        costo_base = self.tarifa_base * sesiones
        costo_total = costo_base + (costo_base * (porcentaje_impuestos / 100.0))
        return _redondear_costo(costo_total)

    def describir_servicio(self) -> str:
        return f"Asesoría Especializada: '{self.nombre_servicio}' (Nivel: {self.nivel_experto}, Tarifa base: ${self.tarifa_base}/sesión)"


class Reserva:
    """Reserva en memoria que relaciona un cliente con un servicio."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"

    def __init__(
        self, codigo: str, cliente: Cliente, servicio: Servicio, duracion: int
    ):
        self.codigo = _validar_texto(codigo, "El código de reserva", ErrorReserva)
        if not isinstance(cliente, Cliente) or not cliente.validar():
            raise ErrorReserva("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ErrorReserva("La reserva requiere un servicio válido.")
        if not isinstance(duracion, int) or isinstance(duracion, bool) or duracion <= 0:
            raise ErrorReserva("La duración debe ser un entero mayor que cero.")
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = self.PENDIENTE
        self.total = None

    def confirmar(self):
        if self.estado != self.PENDIENTE:
            raise ErrorReserva(
                f"No se puede confirmar una reserva en estado {self.estado}."
            )
        if not self.servicio.disponible:
            raise ErrorReserva(
                f"El servicio '{self.servicio.nombre_servicio}' no está disponible."
            )
        self.servicio.disponible = False
        self.estado = self.CONFIRMADA
        registrar_evento(f"Reserva {self.codigo} confirmada.")

    def cancelar(self):
        if self.estado not in (self.PENDIENTE, self.CONFIRMADA):
            raise ErrorReserva(
                f"No se puede cancelar una reserva en estado {self.estado}."
            )
        if self.estado == self.CONFIRMADA:
            self.servicio.disponible = True
        self.estado = self.CANCELADA
        registrar_evento(f"Reserva {self.codigo} cancelada.")

    def procesar(self, **opciones) -> float:
        if self.estado != self.CONFIRMADA:
            raise ErrorReserva(
                f"Solo se pueden procesar reservas confirmadas; estado actual: {self.estado}."
            )
        try:
            if isinstance(self.servicio, ReservaSala):
                total = self.servicio.calcular_costo(
                    horas=self.duracion, **opciones
                )
            elif isinstance(self.servicio, AlquilerEquipos):
                total = self.servicio.calcular_costo(
                    dias=self.duracion, **opciones
                )
            elif isinstance(self.servicio, AsesoriaEspecializada):
                total = self.servicio.calcular_costo(
                    sesiones=self.duracion, **opciones
                )
            else:
                raise ErrorServicio("Tipo de servicio no soportado por la reserva.")
        except (ErrorServicio, TypeError, ValueError) as error:
            raise ErrorReserva(
                f"No se pudo procesar la reserva {self.codigo}: {error}"
            ) from error
        else:
            self.total = total
            self.estado = self.PROCESADA
            self.servicio.disponible = True
            registrar_evento(
                f"Reserva {self.codigo} procesada; total ${self.total:.2f}."
            )
            return total
        finally:
            registrar_evento(f"Fin del intento de procesamiento {self.codigo}.")

    def obtener_informacion(self) -> dict:
        return {
            "codigo": self.codigo,
            "cliente": self.cliente.nombre,
            "servicio": self.servicio.nombre_servicio,
            "duracion": self.duracion,
            "estado": self.estado,
            "total": self.total,
        }


class SistemaReservas:
    """Gestiona clientes, servicios y reservas mediante listas en memoria."""

    def __init__(self):
        configurar_logs()
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    @staticmethod
    def _exigir_codigo_unico(elementos: list, codigo: str, etiqueta: str):
        if any(
            getattr(elemento, "codigo", getattr(elemento, "id_entidad", None))
            == codigo
            for elemento in elementos
        ):
            raise SoftwareFJError(f"Ya existe {etiqueta} con identificador '{codigo}'.")

    def registrar_cliente(self, cliente: Cliente):
        if not isinstance(cliente, Cliente) or not cliente.validar():
            raise ErrorCliente("Solo se pueden registrar clientes válidos.")
        self._exigir_codigo_unico(
            self.clientes, cliente.id_entidad, "un cliente"
        )
        self.clientes.append(cliente)
        registrar_evento(f"Cliente {cliente.id_entidad} registrado.")
        return cliente

    def registrar_servicio(self, servicio: Servicio):
        if not isinstance(servicio, Servicio):
            raise ErrorServicio("El objeto no es un servicio válido.")
        if any(actual.codigo == servicio.codigo for actual in self.servicios):
            raise ErrorServicio(f"Ya existe un servicio con código '{servicio.codigo}'.")
        self.servicios.append(servicio)
        registrar_evento(f"Servicio {servicio.codigo} registrado.")
        return servicio

    def crear_reserva(
        self,
        codigo: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: int,
    ) -> Reserva:
        if cliente not in self.clientes:
            raise ErrorReserva("El cliente debe estar registrado en el sistema.")
        if servicio not in self.servicios:
            raise ErrorReserva("El servicio debe estar registrado en el sistema.")
        self._exigir_codigo_unico(self.reservas, codigo, "una reserva")
        reserva = Reserva(codigo, cliente, servicio, duracion)
        self.reservas.append(reserva)
        registrar_evento(f"Reserva {codigo} creada.")
        return reserva


class InterfazServicios:
    def __init__(self, ventana: tk.Tk):
        self.ventana = ventana
        self.ventana.title("Software FJ - Cálculo de servicios")
        self.ventana.resizable(False, False)

        self.tipo_var = tk.StringVar(value="Reserva de sala")
        self.nombre_var = tk.StringVar()
        self.tarifa_var = tk.StringVar()
        self.cantidad_var = tk.StringVar(value="1")
        self.detalle_var = tk.StringVar()
        self.opcion_var = tk.BooleanVar(value=False)
        self.porcentaje_var = tk.StringVar(value="0")
        self.sistema = SistemaReservas()
        self.numero_reserva = 0

        formulario = ttk.Frame(ventana, padding=16)
        formulario.grid(sticky="nsew")
        formulario.columnconfigure(1, weight=1)

        ttk.Label(formulario, text="Tipo de servicio:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.tipo_combo = ttk.Combobox(
            formulario,
            textvariable=self.tipo_var,
            values=("Reserva de sala", "Alquiler de equipos", "Asesoría especializada"),
            state="readonly",
            width=28,
        )
        self.tipo_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.tipo_combo.bind("<<ComboboxSelected>>", self.actualizar_campos)

        ttk.Label(formulario, text="Nombre del cliente:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.cliente_nombre_var = tk.StringVar()
        ttk.Entry(formulario, textvariable=self.cliente_nombre_var).grid(
            row=1, column=1, sticky="ew", pady=5
        )

        ttk.Label(formulario, text="Correo del cliente:").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.cliente_correo_var = tk.StringVar()
        ttk.Entry(formulario, textvariable=self.cliente_correo_var).grid(
            row=2, column=1, sticky="ew", pady=5
        )

        ttk.Label(formulario, text="Teléfono del cliente:").grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.cliente_telefono_var = tk.StringVar()
        ttk.Entry(formulario, textvariable=self.cliente_telefono_var).grid(
            row=3, column=1, sticky="ew", pady=5
        )

        ttk.Label(formulario, text="Nombre del servicio:").grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=5
        )
        ttk.Entry(formulario, textvariable=self.nombre_var).grid(
            row=4, column=1, sticky="ew", pady=5
        )

        ttk.Label(formulario, text="Tarifa base ($):").grid(
            row=5, column=0, sticky="w", padx=(0, 10), pady=5
        )
        ttk.Entry(formulario, textvariable=self.tarifa_var).grid(
            row=5, column=1, sticky="ew", pady=5
        )

        self.cantidad_label = ttk.Label(formulario)
        self.cantidad_label.grid(row=6, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(formulario, textvariable=self.cantidad_var).grid(
            row=6, column=1, sticky="ew", pady=5
        )

        self.detalle_label = ttk.Label(formulario)
        self.detalle_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(formulario, textvariable=self.detalle_var).grid(
            row=7, column=1, sticky="ew", pady=5
        )

        self.opcion_check = ttk.Checkbutton(
            formulario, variable=self.opcion_var
        )
        self.opcion_check.grid(row=8, column=0, columnspan=2, sticky="w", pady=5)

        self.porcentaje_label = ttk.Label(formulario)
        self.porcentaje_label.grid(row=9, column=0, sticky="w", padx=(0, 10), pady=5)
        self.porcentaje_entry = ttk.Entry(
            formulario, textvariable=self.porcentaje_var
        )
        self.porcentaje_entry.grid(row=9, column=1, sticky="ew", pady=5)

        ttk.Button(
            formulario, text="Crear y procesar reserva", command=self.calcular
        ).grid(row=10, column=0, columnspan=2, pady=(12, 6))

        self.resultado = ttk.Label(
            formulario, text="Ingresa los datos para calcular.", wraplength=380
        )
        self.resultado.grid(row=11, column=0, columnspan=2, sticky="w", pady=5)
        self.historial = tk.Listbox(formulario, width=58, height=5)
        self.historial.grid(row=12, column=0, columnspan=2, sticky="ew", pady=5)

        self.actualizar_campos()

    def actualizar_campos(self, _evento=None):
        tipo = self.tipo_var.get()
        if tipo == "Reserva de sala":
            unidad = "Horas:"
            detalle = "Capacidad (personas):"
            opcion = "Incluir proyector ($50)"
            porcentaje = "Descuento (%):"
            valor_porcentaje = "0"
        elif tipo == "Alquiler de equipos":
            unidad = "Días:"
            detalle = "Tipo de equipo:"
            opcion = "Incluir seguro ($30 por día)"
            porcentaje = None
            valor_porcentaje = "0"
        else:
            unidad = "Sesiones:"
            detalle = "Nivel de experto:"
            opcion = None
            porcentaje = "Impuestos (%):"
            valor_porcentaje = "19"

        self.cantidad_label.config(text=unidad)
        self.detalle_label.config(text=detalle)
        self.opcion_check.config(text=opcion or "")
        self.opcion_check.grid()
        if opcion is None:
            self.opcion_check.grid_remove()
        self.opcion_var.set(False)

        if porcentaje is None:
            self.porcentaje_label.grid_remove()
            self.porcentaje_entry.grid_remove()
        else:
            self.porcentaje_label.config(text=porcentaje)
            self.porcentaje_label.grid()
            self.porcentaje_entry.grid()
            self.porcentaje_var.set(valor_porcentaje)

        self.resultado.config(text="Ingresa los datos para calcular.")

    def calcular(self):
        try:
            cliente_nombre = self.cliente_nombre_var.get().strip()
            cliente_correo = self.cliente_correo_var.get().strip()
            cliente_telefono = self.cliente_telefono_var.get().strip()
            nombre = self.nombre_var.get().strip()
            detalle = self.detalle_var.get().strip()
            if not all((
                cliente_nombre,
                cliente_correo,
                cliente_telefono,
                nombre,
                detalle,
            )):
                raise ValueError("Completa todos los campos antes de continuar.")

            tarifa = float(self.tarifa_var.get().strip().replace(",", "."))
            cantidad = int(self.cantidad_var.get().strip())
            tipo = self.tipo_var.get()
            numero = self.numero_reserva + 1
            cliente = Cliente(
                f"CLI-{numero}",
                cliente_nombre,
                cliente_correo,
                cliente_telefono,
            )

            if tipo == "Reserva de sala":
                servicio = ReservaSala(
                    f"SER-{numero}", nombre, tarifa, int(detalle)
                )
                porcentaje = float(
                    self.porcentaje_var.get().strip().replace(",", ".")
                )
                opciones = {
                    "incluir_proyector": self.opcion_var.get(),
                    "descuento_porcentaje": porcentaje,
                }
            elif tipo == "Alquiler de equipos":
                servicio = AlquilerEquipos(
                    f"SER-{numero}", nombre, tarifa, detalle
                )
                opciones = {"seguro_incluido": self.opcion_var.get()}
            else:
                servicio = AsesoriaEspecializada(
                    f"SER-{numero}", nombre, tarifa, detalle
                )
                porcentaje = float(
                    self.porcentaje_var.get().strip().replace(",", ".")
                )
                opciones = {"impuestos": porcentaje}

            if tipo == "Reserva de sala":
                servicio.calcular_costo(horas=cantidad, **opciones)
            elif tipo == "Alquiler de equipos":
                servicio.calcular_costo(dias=cantidad, **opciones)
            else:
                servicio.calcular_costo(sesiones=cantidad, **opciones)

            self.sistema.registrar_cliente(cliente)
            self.sistema.registrar_servicio(servicio)
            reserva = self.sistema.crear_reserva(
                f"RES-{numero}", cliente, servicio, cantidad
            )
            reserva.confirmar()
            total = reserva.procesar(**opciones)
            self.numero_reserva = numero

            self.resultado.config(
                text=f"Reserva {reserva.codigo} ({reserva.estado})\n"
                f"{servicio.describir_servicio()}\nTotal: ${total:.2f}"
            )
            self.historial.insert(
                tk.END, f"{reserva.codigo} — {cliente.nombre}: ${total:.2f}"
            )
        except (ValueError, ErrorCliente, ErrorReserva, ErrorServicio) as error:
            registrar_error(error, "Error al registrar o procesar desde Tkinter")
            messagebox.showerror("Datos inválidos", str(error), parent=self.ventana)


def main():
    configurar_logs()
    ventana = tk.Tk()
    InterfazServicios(ventana)
    ventana.mainloop()




def ejecutar_demostracion() -> tuple[int, int]:
    configurar_logs()
    sistema = SistemaReservas()
    resultados = {"correctas": 0, "fallidas": 0}
    datos = {}

    def operar(numero: int, nombre: str, accion, se_espera_error=False):
        try:
            accion()
        except Exception as error:
            registrar_error(error, f"Operación {numero}: {nombre}")
            if se_espera_error:
                resultados["correctas"] += 1
                print(f"{numero:02}. ERROR CONTROLADO — {nombre}: {error}")
            else:
                resultados["fallidas"] += 1
                print(f"{numero:02}. ERROR INESPERADO — {nombre}: {error}")
        else:
            if se_espera_error:
                resultados["fallidas"] += 1
                print(f"{numero:02}. FALLO — Se esperaba un error: {nombre}")
            else:
                resultados["correctas"] += 1
                print(f"{numero:02}. OK — {nombre}")
        finally:
            registrar_evento(f"Finalizada operación de demostración {numero}: {nombre}.")

    operar(
        1,
        "registrar cliente válido",
        lambda: datos.update(
            cliente=sistema.registrar_cliente(
                Cliente("CLI-001", "Ana Pérez", "ana@example.com", "3001234567")
            )
        ),
    )
    operar(
        2,
        "rechazar correo inválido",
        lambda: Cliente("CLI-002", "Luis Pérez", "correo-invalido", "3001234568"),
        se_espera_error=True,
    )
    operar(
        3,
        "registrar segundo cliente válido",
        lambda: datos.update(
            cliente2=sistema.registrar_cliente(
                Cliente("CLI-003", "Luis Pérez", "luis@example.com", "3001234568")
            )
        ),
    )
    operar(
        4,
        "crear servicio de sala",
        lambda: datos.update(
            sala=sistema.registrar_servicio(
                ReservaSala("SAL-001", "Sala Norte", 100000, 12)
            )
        ),
    )
    operar(
        5,
        "crear servicio de alquiler",
        lambda: datos.update(
            equipo=sistema.registrar_servicio(
                AlquilerEquipos("EQ-001", "Portátil", 50000, "Computador")
            )
        ),
    )
    operar(
        6,
        "crear servicio de asesoría",
        lambda: datos.update(
            asesoria=sistema.registrar_servicio(
                AsesoriaEspecializada("ASE-001", "Arquitectura", 80000, "Senior")
            )
        ),
    )
    operar(
        7,
        "rechazar tarifa de servicio inválida",
        lambda: ReservaSala("SAL-ERR", "Sala inválida", -10, 4),
        se_espera_error=True,
    )

    def crear_y_confirmar_sala():
        reserva = sistema.crear_reserva(
            "RES-001", datos["cliente"], datos["sala"], 2
        )
        reserva.confirmar()
        datos["reserva_sala"] = reserva

    operar(8, "crear y confirmar reserva de sala", crear_y_confirmar_sala)

    def intentar_servicio_no_disponible():
        reserva = sistema.crear_reserva(
            "RES-002", datos["cliente2"], datos["sala"], 1
        )
        datos["reserva_pendiente"] = reserva
        reserva.confirmar()

    operar(
        9,
        "rechazar reserva de un servicio ocupado",
        intentar_servicio_no_disponible,
        se_espera_error=True,
    )
    operar(
        10,
        "procesar sala con proyector y descuento",
        lambda: print(
            "    Total:",
            f"${datos['reserva_sala'].procesar(incluir_proyector=True, descuento_porcentaje=10):,.2f}",
        ),
    )
    operar(
        11,
        "cancelar reserva pendiente",
        lambda: datos["reserva_pendiente"].cancelar(),
    )

    def procesar_alquiler():
        reserva = sistema.crear_reserva(
            "RES-003", datos["cliente"], datos["equipo"], 3
        )
        reserva.confirmar()
        total = reserva.procesar(seguro_incluido=True)
        print(f"    Total: ${total:,.2f}")

    operar(12, "procesar alquiler con seguro", procesar_alquiler)

    def intentar_impuesto_invalido():
        reserva = sistema.crear_reserva(
            "RES-004", datos["cliente2"], datos["asesoria"], 2
        )
        reserva.confirmar()
        datos["reserva_asesoria"] = reserva
        reserva.procesar(impuestos=-1)

    operar(
        13,
        "capturar cálculo inválido con excepción encadenada",
        intentar_impuesto_invalido,
        se_espera_error=True,
    )
    operar(
        14,
        "reintentar asesoría con impuestos válidos",
        lambda: print(
            "    Total:",
            f"${datos['reserva_asesoria'].procesar(impuestos=19):,.2f}",
        ),
    )

    print(
        f"\nResumen: {resultados['correctas']} operaciones demostradas, "
        f"{resultados['fallidas']} fallos no esperados."
    )
    return resultados["correctas"], resultados["fallidas"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sistema de reservas Software FJ")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="ejecuta la demostración de operaciones válidas e inválidas",
    )
    argumentos = parser.parse_args()
    if argumentos.demo:
        ejecutar_demostracion()
    else:
        main()
