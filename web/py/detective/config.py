"""Configuracion de la auditoria: fecha de corte, umbrales y exclusiones.

Todo tiene un valor por defecto, asi que el detector funciona aunque no haya config.json.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

from .lectores import ErrorLectura, decodificar
from .normalizar import meses_entre, normalizar_rut, parsear_fecha

PALABRAS_EXCLUIDAS = ["APORTE SOCIO", "APORTE DE CAPITAL", "DEVOLUCION", "TRASPASO ENTRE CUENTAS",
                      "INTERESES", "LIQUIDACION", "ABONO TRANSBANK", "PRESTAMO", "CREDITO DE CONSUMO"]


@dataclass
class Config:
    empresa: str = "Tu empresa"
    rut_empresa: str = None
    fecha_corte: dt.date = None
    periodo_desde: dt.date = None
    periodo_hasta: dt.date = None
    tasa_iva: float = 0.19
    dias_pago_pendiente: int = 30
    dias_gracia_cotizacion: int = 15
    ventana_dias_abono_documento: int = 7
    dias_documento_antes_abono: int = 60
    tolerancia_clp: int = 2
    palabras_excluidas_abonos: list = field(default_factory=lambda: list(PALABRAS_EXCLUIDAS))
    ruts_excluidos_abonos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    desde_archivo: bool = False

    @property
    def meses(self) -> int:
        return meses_entre(self.periodo_desde, self.periodo_hasta)

    def completar_fechas(self, fechas: list) -> None:
        """Si la configuracion no trae fechas, se deducen de los datos (y se avisa)."""
        fechas = sorted(f for f in fechas if f)
        if self.periodo_hasta is None:
            self.periodo_hasta = self.fecha_corte or (fechas[-1] if fechas else dt.date.today())
        if self.fecha_corte is None:
            self.fecha_corte = self.periodo_hasta
            self.avisos.append(
                f"No había fecha de corte en la configuración: usé la última fecha de tus archivos "
                f"({self.fecha_corte.strftime('%d/%m/%Y')}).")
        if self.periodo_desde is None:
            self.periodo_desde = fechas[0] if fechas else self.periodo_hasta
        if self.periodo_desde > self.periodo_hasta:
            self.periodo_desde = self.periodo_hasta


_ENTEROS = ("dias_pago_pendiente", "dias_gracia_cotizacion", "ventana_dias_abono_documento",
            "dias_documento_antes_abono", "tolerancia_clp")
_FECHAS = ("fecha_corte", "periodo_desde", "periodo_hasta")


def config_desde_dict(datos: dict) -> Config:
    c = Config(desde_archivo=True)
    if not isinstance(datos, dict):
        raise ErrorLectura("config.json debe ser un objeto JSON con claves como \"fecha_corte\".")
    for clave in ("empresa", "rut_empresa"):
        if datos.get(clave):
            setattr(c, clave, str(datos[clave]))
    for clave in _FECHAS:
        if datos.get(clave):
            fecha = parsear_fecha(datos[clave])
            if fecha is None:
                raise ErrorLectura(f"config.json: no entiendo la fecha de \"{clave}\": {datos[clave]!r}. "
                                   "Usa el formato AAAA-MM-DD.")
            setattr(c, clave, fecha)
    for clave in _ENTEROS:
        if datos.get(clave) is not None:
            try:
                setattr(c, clave, int(datos[clave]))
            except (TypeError, ValueError):
                raise ErrorLectura(f"config.json: \"{clave}\" debe ser un número entero.") from None
    if datos.get("tasa_iva") is not None:
        try:
            c.tasa_iva = float(datos["tasa_iva"])
        except (TypeError, ValueError):
            raise ErrorLectura("config.json: \"tasa_iva\" debe ser un número, por ejemplo 0.19.") from None
    if isinstance(datos.get("palabras_excluidas_abonos"), list):
        c.palabras_excluidas_abonos = [str(p) for p in datos["palabras_excluidas_abonos"] if str(p).strip()]
    if isinstance(datos.get("ruts_excluidos_abonos"), list):
        for r in datos["ruts_excluidos_abonos"]:
            rut, _ = normalizar_rut(r)
            if rut:
                c.ruts_excluidos_abonos.append(rut)
            else:
                c.avisos.append(f"config.json: \"{r}\" no parece un RUT, lo ignoré en ruts_excluidos_abonos.")
    return c


def cargar_config(datos: bytes = None) -> Config:
    """Config desde el contenido de config.json; si no hay, valores por defecto."""
    if datos is None:
        c = Config()
        c.avisos.append("No había config.json: usé los valores por defecto (IVA 19%, 30 días para pagos "
                        "pendientes, 15 días de gracia para cotizaciones).")
        return c
    try:
        return config_desde_dict(json.loads(decodificar(datos)[0]))
    except json.JSONDecodeError as error:
        raise ErrorLectura(f"config.json no es un JSON válido: {error}") from error
