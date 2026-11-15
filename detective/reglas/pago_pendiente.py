"""4.3 Facturaste y no te pagaron (mas de N dias)."""
from __future__ import annotations

from ..emparejar import TIPOS_FACTURA, clave
from ..normalizar import formato_clp, formato_fecha
from . import Hallazgo, evidencia_de, mensual_puntual

TIPO = "pago_pendiente_30d"


def detectar(ctx) -> list:
    config, hallazgos = ctx.config, []
    if "rcv_ventas" not in ctx.datos.roles or "banco" not in ctx.datos.roles:
        return hallazgos
    for doc in ctx.datos.documentos:
        if doc.tipo not in TIPOS_FACTURA or clave(doc) in ctx.emp.pago_de_doc or clave(doc) in ctx.emp.anulados:
            continue
        dias = (config.fecha_corte - doc.fecha).days
        if dias <= config.dias_pago_pendiente or doc.total <= 0:
            continue
        cliente = doc.razon_social or doc.rut or "el cliente"
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="factura_impaga", titulo="Factura emitida que no te han pagado",
            descripcion=(f"La factura folio {doc.folio} a {cliente}, del {formato_fecha(doc.fecha)}, por "
                         f"{formato_clp(doc.total)}, no tiene pago en tu banco. Lleva {dias} días al "
                         f"{formato_fecha(config.fecha_corte)} ({dias - config.dias_pago_pendiente} sobre el plazo "
                         f"de {config.dias_pago_pendiente} días)."),
            monto_clp=doc.total, impacto_clp=doc.total, impacto_mensual_clp=mensual_puntual(doc.total, config),
            recurrente=False,
            evidencia=[evidencia_de(doc, doc.fecha, doc.total, f"Factura folio {doc.folio} a {cliente}")],
            accion_sugerida="Llama al cliente y envía el mensaje de cobro",
            datos={"cliente": cliente, "rut": doc.rut, "folio": doc.folio, "fecha": doc.fecha.isoformat(),
                   "dias": dias, "total": doc.total, "corte": config.fecha_corte.isoformat()}))
    return hallazgos
