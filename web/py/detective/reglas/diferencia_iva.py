"""4.5 El IVA salio de tu bolsillo: IVA mal calculado o neto cobrado como total."""
from __future__ import annotations

from ..emparejar import TIPOS_VENTA, clave
from ..normalizar import formato_clp, formato_fecha, iva_de_neto
from . import Hallazgo, evidencia_de, mensual_puntual

TIPO = "diferencia_iva"


def _porcentaje(valor: float) -> str:
    texto = f"{valor:.1f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + "%"


def detectar(ctx) -> list:
    config, emp, hallazgos = ctx.config, ctx.emp, []
    if "rcv_ventas" not in ctx.datos.roles:
        return hallazgos
    tol = config.tolerancia_clp
    ya_informados = set()

    # Neto cobrado como total: la cotizacion decia N + IVA y el documento salio por N en total.
    for cot in ctx.datos.cotizaciones:
        calce = emp.doc_de_cot.get(clave(cot))
        if not calce or calce[1] != "neto_como_total":
            continue
        doc = calce[0]
        diferencia = cot.total - doc.total
        if diferencia <= tol:
            continue
        ya_informados.add(clave(doc))
        cliente = cot.cliente or doc.razon_social or "el cliente"
        evidencia = [
            evidencia_de(doc, doc.fecha, doc.total,
                         f"Documento folio {doc.folio}: neto {formato_clp(doc.neto)}, IVA {formato_clp(doc.iva)}, "
                         f"total {formato_clp(doc.total)}"),
            evidencia_de(cot, cot.fecha_aceptacion or cot.fecha, cot.neto if cot.neto_en_archivo else cot.total,
                         f"{cot.numero} {cot.estado_original}: neto {formato_clp(cot.neto)} más IVA"),
        ]
        pago = emp.pago_de_doc.get(clave(doc))
        if pago is not None:
            evidencia.append(evidencia_de(pago, pago.fecha, pago.monto, f"Pago recibido: {pago.descripcion}"))
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="neto_como_total", titulo="Cobraste el neto como si fuera el total",
            descripcion=(f"{cot.numero} cotizó a {cliente} {formato_clp(cot.neto)} más IVA "
                         f"(total {formato_clp(cot.total)}), pero el documento folio {doc.folio} del "
                         f"{formato_fecha(doc.fecha)} se emitió por {formato_clp(doc.total)} en total. "
                         f"El IVA ({formato_clp(diferencia)}) salió de tu bolsillo."),
            monto_clp=doc.total, impacto_clp=diferencia, impacto_mensual_clp=mensual_puntual(diferencia, config),
            recurrente=False, evidencia=evidencia,
            accion_sugerida="Revisa con tu contador cómo corregir el documento y cobra la diferencia al cliente",
            datos={"cliente": cliente, "rut": doc.rut, "folio": doc.folio, "numero": cot.numero,
                   "diferencia": diferencia, "fecha": doc.fecha.isoformat()}))

    # IVA mal calculado: el IVA del documento no es neto x tasa.
    for doc in ctx.datos.documentos:
        if doc.tipo not in TIPOS_VENTA or clave(doc) in ya_informados or clave(doc) in emp.anulados:
            continue
        if doc.neto is None or doc.iva is None or doc.neto <= 0:
            continue
        esperado = iva_de_neto(doc.neto, config.tasa_iva)
        diferencia = esperado - doc.iva
        if abs(diferencia) <= tol:
            continue
        cliente = doc.razon_social or doc.rut or "el cliente"
        aplicado, correcto = _porcentaje(doc.iva * 100 / doc.neto), _porcentaje(config.tasa_iva * 100)
        if diferencia > 0:
            consecuencia = (f"Cobraste {formato_clp(diferencia)} de menos y esa parte del IVA la terminas "
                            "poniendo tú.")
            accion = "Revisa con tu contador si corresponde una nota de débito y cobra la diferencia"
        else:
            consecuencia = f"Cobraste {formato_clp(-diferencia)} de más de IVA al cliente."
            accion = "Revisa con tu contador si corresponde una nota de crédito por la diferencia"
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="iva_mal_calculado", titulo="Documento con el IVA mal calculado",
            descripcion=(f"El documento folio {doc.folio} a {cliente}, del {formato_fecha(doc.fecha)}, tiene neto "
                         f"{formato_clp(doc.neto)} con IVA {formato_clp(doc.iva)} ({aplicado}) en vez de "
                         f"{formato_clp(esperado)} ({correcto}). {consecuencia}"),
            monto_clp=doc.total, impacto_clp=abs(diferencia),
            impacto_mensual_clp=mensual_puntual(abs(diferencia), config), recurrente=False,
            evidencia=[evidencia_de(doc, doc.fecha, doc.total,
                                    f"Documento folio {doc.folio}: neto {formato_clp(doc.neto)}, "
                                    f"IVA {formato_clp(doc.iva)}, total {formato_clp(doc.total)}")],
            accion_sugerida=accion,
            datos={"cliente": cliente, "rut": doc.rut, "folio": doc.folio, "diferencia": diferencia,
                   "fecha": doc.fecha.isoformat()}))
    return hallazgos
