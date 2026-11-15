"""Reglas de deteccion: un modulo por tipo de fuga.

Cada regla recibe un `Contexto` (datos, configuracion y emparejamiento) y devuelve una
lista de `Hallazgo`. Ninguna regla lee archivos: solo trabaja con registros ya cargados.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..normalizar import redondear

TIPOS = ("abono_sin_documento", "cotizacion_sin_cobro", "pago_pendiente_30d",
         "suscripcion_duplicada_o_huerfana", "diferencia_iva")
TIPOS_DE_COBRO = ("cotizacion_sin_cobro", "pago_pendiente_30d")
NOMBRE_SIMPLE = {
    "abono_sin_documento": "Plata que entró sin boleta ni factura",
    "cotizacion_sin_cobro": "Trabajo aceptado que nunca se facturó",
    "pago_pendiente_30d": "Factura que no te han pagado",
    "suscripcion_duplicada_o_huerfana": "Software que pagas de más",
    "diferencia_iva": "IVA que salió de tu bolsillo",
}


@dataclass
class Evidencia:
    archivo: str
    fila: int
    fecha: object            # date o None (hay archivos sin fechas, como el de licencias)
    monto_clp: object        # int o None (hay archivos sin montos, como el del equipo)
    detalle: str
    fila_original: str = ""

    @property
    def completa(self) -> bool:
        return self.fecha is not None and self.monto_clp is not None

    def a_dict(self) -> dict:
        return {"archivo": self.archivo, "fila": self.fila,
                "fecha": self.fecha.isoformat() if self.fecha else None,
                "monto_clp": self.monto_clp, "detalle": self.detalle, "fila_original": self.fila_original}


@dataclass
class Hallazgo:
    tipo: str
    subtipo: str
    titulo: str
    descripcion: str
    monto_clp: int
    impacto_clp: int
    impacto_mensual_clp: int
    recurrente: bool
    evidencia: list
    accion_sugerida: str
    confianza: str = "alta"
    datos: dict = field(default_factory=dict)     # cliente, folio, etc. para los mensajes
    id: str = ""
    mensaje: str = ""                             # codigo del borrador asociado (M01, N01...)
    verificado: bool = False

    def a_dict(self) -> dict:
        return {
            "id": self.id, "tipo": self.tipo, "subtipo": self.subtipo, "titulo": self.titulo,
            "descripcion": self.descripcion, "monto_clp": self.monto_clp, "impacto_clp": self.impacto_clp,
            "impacto_mensual_clp": self.impacto_mensual_clp, "recurrente": self.recurrente,
            "confianza": self.confianza, "evidencia": [e.a_dict() for e in self.evidencia],
            "accion_sugerida": self.accion_sugerida, "mensaje": self.mensaje, "verificado": self.verificado,
            "datos": self.datos,
        }


@dataclass
class Contexto:
    datos: object
    config: object
    emp: object
    avisos: list = field(default_factory=list)    # cosas que la regla quiere contarle al usuario


def evidencia_de(registro, fecha, monto, detalle: str) -> Evidencia:
    o = registro.origen
    return Evidencia(o.archivo, o.fila, fecha, monto, detalle, o.crudo)


def mensual_puntual(impacto: int, config) -> int:
    """Fuga de una sola vez: promedio mensual del periodo."""
    return redondear(impacto / max(config.meses, 1))


def todas():
    from . import abono_sin_documento, cotizacion_sin_cobro, diferencia_iva, pago_pendiente, suscripciones
    return (abono_sin_documento, cotizacion_sin_cobro, pago_pendiente, suscripciones, diferencia_iva)
