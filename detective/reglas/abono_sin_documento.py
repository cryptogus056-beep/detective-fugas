"""4.1 Entro plata sin boleta ni factura (en el banco o en las ventas con tarjeta)."""
from __future__ import annotations

import datetime as dt

from ..emparejar import clave
from ..normalizar import formato_clp, formato_fecha, neto_de_total
from . import Hallazgo, evidencia_de, mensual_puntual

TIPO = "abono_sin_documento"
NOTA_MULTA = "Riesgo de multa del SII [sin verificar el monto de la multa]."


def _cotizacion_relacionada(movimiento, ctx):
    """Cotizacion aceptada y sin documento que este abono parece estar pagando."""
    tol = ctx.config.tolerancia_clp
    for cot in ctx.datos.cotizaciones:
        if cot.estado != "aceptada" or clave(cot) in ctx.emp.doc_de_cot:
            continue
        if abs(cot.total - movimiento.monto) > tol or movimiento.fecha < cot.fecha:
            continue
        if movimiento.ruts and cot.rut and cot.rut not in movimiento.ruts:
            continue
        return cot
    return None


def detectar(ctx) -> list:
    config, emp, hallazgos = ctx.config, ctx.emp, []
    if "rcv_ventas" not in ctx.datos.roles:
        return hallazgos

    for m in ctx.datos.movimientos:
        if m.monto <= 0 or clave(m) in emp.excluidos or clave(m) in emp.doc_de_abono:
            continue
        iva = m.monto - neto_de_total(m.monto, config.tasa_iva)
        cot = _cotizacion_relacionada(m, ctx)
        descripcion = (f"El {formato_fecha(m.fecha)} entraron {formato_clp(m.monto)} a tu cuenta "
                       f"(\"{m.descripcion}\") y no encontré boleta ni factura por ese monto. "
                       f"IVA en riesgo: {formato_clp(iva)}. {NOTA_MULTA}")
        datos = {"origen": "banco", "glosa": m.descripcion, "ruts": m.ruts, "iva_en_riesgo": iva}
        if cot:
            descripcion += (f" Parece ser el pago de {cot.numero} ({cot.cliente}), que está aceptada "
                            "y tampoco tiene factura.")
            datos.update(cotizacion=cot.numero, cliente=cot.cliente)
        confianza, primeros_dias = "alta", config.periodo_desde + dt.timedelta(days=config.dias_pago_pendiente)
        if not m.ruts:
            confianza = "media"
            descripcion += " La glosa no trae RUT, así que no sé quién pagó: revísalo antes de emitir el documento."
        elif m.fecha < primeros_dias:
            confianza = "media"
            descripcion += (" Ojo: llegó al comienzo del periodo, así que podría ser el pago de un documento "
                            "emitido antes de lo que cubren tus archivos.")
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="banco", titulo="Entró plata al banco sin boleta ni factura",
            descripcion=descripcion, monto_clp=m.monto, impacto_clp=iva,
            impacto_mensual_clp=mensual_puntual(iva, config), recurrente=False, confianza=confianza,
            evidencia=[evidencia_de(m, m.fecha, m.monto, m.descripcion)],
            accion_sugerida="Emite la boleta o factura que falta", datos=datos))

    for v in ctx.datos.ventas_pos:
        if not v.aprobada or clave(v) in emp.doc_de_venta:
            continue
        iva = v.monto - neto_de_total(v.monto, config.tasa_iva)
        detalle = ", ".join(p for p in (v.descripcion, f"operación {v.identificador}" if v.identificador else "") if p)
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="pos", titulo="Venta con tarjeta sin boleta",
            descripcion=(f"El {formato_fecha(v.fecha)} se aprobó una venta con tarjeta por {formato_clp(v.monto)} "
                         f"({detalle}) y no encontré su boleta de ese día ni del día siguiente. "
                         f"IVA en riesgo: {formato_clp(iva)}. {NOTA_MULTA}"),
            monto_clp=v.monto, impacto_clp=iva, impacto_mensual_clp=mensual_puntual(iva, config),
            recurrente=False, evidencia=[evidencia_de(v, v.fecha, v.monto, detalle or v.estado_original)],
            accion_sugerida="Emite la boleta que falta",
            datos={"origen": "pos", "glosa": detalle, "iva_en_riesgo": iva}))
    return hallazgos


def abonos_ambiguos(ctx) -> list:
    """Abonos sin documento cuya glosa no dice quien pago: candidatos para el clasificador."""
    return [m for m in ctx.datos.movimientos
            if m.monto > 0 and not m.ruts and clave(m) not in ctx.emp.excluidos
            and clave(m) not in ctx.emp.doc_de_abono]
