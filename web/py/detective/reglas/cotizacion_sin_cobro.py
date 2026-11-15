"""4.2 Cotizacion aceptada que nunca se facturo."""
from __future__ import annotations

from ..emparejar import clave
from ..normalizar import formato_clp, formato_fecha
from . import Hallazgo, evidencia_de, mensual_puntual

TIPO = "cotizacion_sin_cobro"


def _ya_la_pagaron(cot, ctx) -> bool:
    """True si hay un abono sin documento que calza con esta cotizacion.

    En ese caso la plata SI entro: lo que falta es el documento, y eso lo informa la
    regla de abonos sin documento. No se informa dos veces.
    """
    tol = ctx.config.tolerancia_clp
    for m in ctx.datos.movimientos:
        if m.monto <= 0 or clave(m) in ctx.emp.excluidos or clave(m) in ctx.emp.doc_de_abono:
            continue
        if abs(m.monto - cot.total) <= tol and m.fecha >= cot.fecha and (
                not m.ruts or not cot.rut or cot.rut in m.ruts):
            return True
    return False


def detectar(ctx) -> list:
    config, hallazgos = ctx.config, []
    if "rcv_ventas" not in ctx.datos.roles:
        return hallazgos
    for cot in ctx.datos.cotizaciones:
        if cot.estado != "aceptada" or clave(cot) in ctx.emp.doc_de_cot:
            continue
        aceptada = cot.fecha_aceptacion or cot.fecha
        dias = (config.fecha_corte - aceptada).days
        if dias < config.dias_gracia_cotizacion:
            continue
        if _ya_la_pagaron(cot, ctx):
            continue
        cliente = cot.cliente or cot.rut or "el cliente"
        if cot.total_en_archivo:
            montos = f"{formato_clp(cot.total)} (neto {formato_clp(cot.neto)} más IVA)"
            monto_fila = cot.total
        else:
            montos = (f"{formato_clp(cot.total)} (el archivo trae solo el neto, {formato_clp(cot.neto)}; "
                      f"le sumé el IVA)")
            monto_fila = cot.neto
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="sin_documento", titulo="Cotización aceptada que nunca se facturó",
            descripcion=(f"{cot.numero} fue aceptada por {cliente} el {formato_fecha(aceptada)} por {montos}. "
                         f"Pasaron {dias} días y no encontré factura, boleta ni pago por ese trabajo."),
            monto_clp=cot.total, impacto_clp=cot.total, impacto_mensual_clp=mensual_puntual(cot.total, config),
            recurrente=False,
            evidencia=[evidencia_de(cot, aceptada, monto_fila,
                                    f"{cot.numero} {cot.estado_original} {cliente}: {cot.servicio}".strip())],
            accion_sugerida="Emite la factura y envía el mensaje de cobro",
            datos={"cliente": cliente, "rut": cot.rut, "numero": cot.numero, "servicio": cot.servicio,
                   "fecha": aceptada.isoformat(), "dias": dias, "neto": cot.neto, "total": cot.total}))
    return hallazgos
