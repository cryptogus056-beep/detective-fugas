"""Registros comunes: lo mismo sin importar de que banco o sistema venga el archivo.

Cada registro recuerda su `origen` (archivo, fila fisica y texto original) para poder
citarlo como evidencia.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .normalizar import (ESTADOS_ACTIVO, ESTADOS_COTIZACION, ESTADOS_POS, clave_texto, extraer_ruts,
                         iva_de_neto, neto_de_total, normalizar_estado, normalizar_rut)
from .plantillas import Lectura


@dataclass(frozen=True)
class Origen:
    archivo: str
    fila: int
    crudo: str


@dataclass
class Movimiento:            # banco
    origen: Origen
    fecha: dt.date
    descripcion: str
    monto: int               # positivo = abono (entra plata), negativo = cargo (sale plata)
    ruts: list = field(default_factory=list)


@dataclass
class VentaPos:              # tarjeta o link de pago
    origen: Origen
    fecha: dt.date
    descripcion: str
    monto: int               # monto bruto que pago el cliente
    aprobada: bool
    estado_original: str = ""
    identificador: str = ""


@dataclass
class Documento:             # factura, boleta o nota del SII
    origen: Origen
    tipo: int
    folio: str
    fecha: dt.date
    rut: str
    razon_social: str
    neto: int
    iva: int
    total: int
    exento: int = 0


@dataclass
class Cotizacion:
    origen: Origen
    numero: str
    fecha: dt.date
    cliente: str
    rut: str
    servicio: str
    neto: int
    iva: int
    total: int
    estado: str              # aceptada, rechazada, pendiente u otro
    estado_original: str
    fecha_aceptacion: dt.date
    total_en_archivo: bool   # False cuando el total se calculo desde el neto
    neto_en_archivo: bool = True


@dataclass
class Persona:
    origen: Origen
    nombre: str
    email: str
    estado: str              # activo, inactivo u otro
    fecha_salida: dt.date


@dataclass
class Licencia:
    origen: Origen
    servicio: str
    usuario: str
    plan: str
    costo_mensual: int
    estado: str              # activo, inactivo u otro


@dataclass
class Carga:
    """Resultado de convertir un archivo: registros utiles y filas que no se pudieron leer."""
    registros: list
    filas_saltadas: list     # [(numero_de_fila, motivo)]
    avisos: list = field(default_factory=list)


def _origen(lectura: Lectura, fila) -> Origen:
    return Origen(lectura.tabla.nombre, fila.numero, fila.crudo)


def _rut(texto, avisos_rut: set):
    rut, valido = normalizar_rut(texto)
    if rut and not valido:
        avisos_rut.add(rut)
    return rut or (str(texto).strip() if texto else None)


def _banco(lectura, config):
    registros, saltadas = [], []
    con_signo = "monto_con_signo" in lectura.columnas
    for fila in lectura.filas_de_datos:
        fecha = lectura.fecha(fila, "fecha")
        if con_signo:
            monto = lectura.numero(fila, "monto_con_signo")
        else:
            cargo, abono = lectura.numero(fila, "cargo"), lectura.numero(fila, "abono")
            monto = None if cargo is None and abono is None else abs(abono or 0) - abs(cargo or 0)
        if fecha is None or monto is None:
            saltadas.append((fila.numero, "sin fecha" if fecha is None else "sin monto"))
            continue
        if monto == 0:
            continue
        descripcion = lectura.texto(fila, "descripcion")
        registros.append(Movimiento(_origen(lectura, fila), fecha, descripcion, monto, extraer_ruts(descripcion)))
    return registros, saltadas


def _pos(lectura, config):
    registros, saltadas = [], []
    tiene_estado = "estado" in lectura.columnas
    for fila in lectura.filas_de_datos:
        fecha, monto = lectura.fecha(fila, "fecha"), lectura.numero(fila, "monto")
        if fecha is None or monto is None:
            saltadas.append((fila.numero, "sin fecha" if fecha is None else "sin monto"))
            continue
        original = lectura.texto(fila, "estado")
        estado = normalizar_estado(original, ESTADOS_POS, lectura.plantilla.estados) if tiene_estado else "aprobada"
        if tiene_estado and estado == "otro":
            saltadas.append((fila.numero, f"estado desconocido '{original}'"))
            continue
        registros.append(VentaPos(_origen(lectura, fila), fecha, lectura.texto(fila, "descripcion"), monto,
                                  estado == "aprobada", original, lectura.texto(fila, "id")))
    return registros, saltadas


def _documentos(lectura, config, avisos_rut):
    registros, saltadas = [], []
    for fila in lectura.filas_de_datos:
        tipo, fecha = lectura.numero(fila, "tipo"), lectura.fecha(fila, "fecha")
        total = lectura.numero(fila, "total")
        if tipo is None or fecha is None or total is None:
            motivo = "sin tipo de documento" if tipo is None else "sin fecha" if fecha is None else "sin monto total"
            saltadas.append((fila.numero, motivo))
            continue
        exento = lectura.numero(fila, "exento") or 0
        neto, iva = lectura.numero(fila, "neto"), lectura.numero(fila, "iva")
        registros.append(Documento(
            _origen(lectura, fila), tipo, lectura.texto(fila, "folio"), fecha,
            _rut(lectura.valor(fila, "rut"), avisos_rut), lectura.texto(fila, "razon_social"),
            neto if neto is not None else None, iva if iva is not None else None, total, exento))
    return registros, saltadas


def _cotizaciones(lectura, config, avisos_rut):
    registros, saltadas = [], []
    for fila in lectura.filas_de_datos:
        numero, fecha = lectura.texto(fila, "numero"), lectura.fecha(fila, "fecha")
        neto, total = lectura.numero(fila, "neto"), lectura.numero(fila, "total")
        if not numero or fecha is None or (neto is None and total is None):
            motivo = "sin número" if not numero else "sin fecha" if fecha is None else "sin monto"
            saltadas.append((fila.numero, motivo))
            continue
        total_en_archivo, neto_en_archivo = total is not None, neto is not None
        if neto is None:
            neto = neto_de_total(total, config.tasa_iva)
        if total is None:
            total = neto + iva_de_neto(neto, config.tasa_iva)
        iva = lectura.numero(fila, "iva")
        original = lectura.texto(fila, "estado")
        registros.append(Cotizacion(
            _origen(lectura, fila), numero, fecha, lectura.texto(fila, "cliente"),
            _rut(lectura.valor(fila, "rut"), avisos_rut), lectura.texto(fila, "servicio"), neto,
            iva if iva is not None else total - neto, total,
            normalizar_estado(original, ESTADOS_COTIZACION, lectura.plantilla.estados), original,
            lectura.fecha(fila, "fecha_aceptacion"), total_en_archivo, neto_en_archivo))
    return registros, saltadas


def _equipo(lectura, config):
    registros, saltadas = [], []
    for fila in lectura.filas_de_datos:
        nombre, email = lectura.texto(fila, "nombre"), lectura.texto(fila, "email")
        if not nombre and not email:
            saltadas.append((fila.numero, "sin nombre ni correo"))
            continue
        registros.append(Persona(
            _origen(lectura, fila), nombre, email,
            normalizar_estado(lectura.texto(fila, "estado"), ESTADOS_ACTIVO, lectura.plantilla.estados),
            lectura.fecha(fila, "fecha_salida")))
    return registros, saltadas


def _licencias(lectura, config):
    registros, saltadas = [], []
    tiene_estado = "estado" in lectura.columnas
    for fila in lectura.filas_de_datos:
        servicio, usuario = lectura.texto(fila, "servicio"), lectura.texto(fila, "usuario")
        if not servicio or not usuario:
            saltadas.append((fila.numero, "sin servicio o sin usuario"))
            continue
        estado = (normalizar_estado(lectura.texto(fila, "estado"), ESTADOS_ACTIVO, lectura.plantilla.estados)
                  if tiene_estado else "activo")
        registros.append(Licencia(_origen(lectura, fila), servicio, usuario, lectura.texto(fila, "plan"),
                                  lectura.numero(fila, "costo_mensual"), estado))
    return registros, saltadas


def cargar_registros(lectura: Lectura, config) -> Carga:
    """Convierte las filas de un archivo reconocido en registros comunes segun su rol."""
    rol, avisos_rut = lectura.plantilla.rol, set()
    if rol == "banco":
        registros, saltadas = _banco(lectura, config)
    elif rol == "pos":
        registros, saltadas = _pos(lectura, config)
    elif rol in ("rcv_ventas", "rcv_compras"):
        registros, saltadas = _documentos(lectura, config, avisos_rut)
    elif rol == "cotizaciones":
        registros, saltadas = _cotizaciones(lectura, config, avisos_rut)
    elif rol == "equipo":
        registros, saltadas = _equipo(lectura, config)
    elif rol == "licencias":
        registros, saltadas = _licencias(lectura, config)
    else:
        raise ValueError(f"rol desconocido: {rol}")
    avisos = []
    if avisos_rut:
        ejemplos = ", ".join(sorted(avisos_rut)[:3])
        avisos.append(f"{lectura.tabla.nombre}: {len(avisos_rut)} RUT no pasan la validación del dígito "
                      f"verificador (por ejemplo {ejemplos}). Los usé igual.")
    return Carga(registros, saltadas, avisos)


def huella(registro) -> tuple:
    """Contenido de un registro sin su origen: sirve para saber si dos archivos traen lo mismo."""
    valores = []
    for nombre, valor in sorted(vars(registro).items()):
        if nombre == "origen":
            continue
        valores.append(clave_texto(valor) if isinstance(valor, str) else str(valor))
    return tuple(valores)
