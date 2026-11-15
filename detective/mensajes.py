"""Borradores de mensajes de cobro y notas internas (seccion 6.3 de la spec).

Aqui NUNCA se envia nada: solo se escriben textos para que el dueno de la pyme los
revise, los copie y los mande por su cuenta. El modo por defecto son plantillas fijas
en codigo; pulir los textos con un modelo de lenguaje es opcional (ver llm.py).
"""
from __future__ import annotations

import re

from .informe import formato_fecha_iso
from .normalizar import formato_clp, formato_fecha

ENCABEZADO = "BORRADORES. Nada de esto se ha enviado. Revísalo antes de usarlo."
TRATAMIENTOS = ("usted", "tu")


def _es_empresa(rut) -> bool:
    """Los RUT de empresas en Chile parten desde los 50 millones (regla practica)."""
    numero = re.sub(r"\D", "", str(rut or "").split("-")[0])
    return bool(numero) and int(numero) >= 50_000_000


def _documento(rut) -> str:
    return "la factura" if _es_empresa(rut) else "la boleta o factura"


def _saludo(d: dict, usted: bool) -> str:
    if _es_empresa(d.get("rut")):
        return f"Estimado equipo de {d['cliente']}:" if usted else f"Hola, equipo de {d['cliente']}:"
    return f"Buenos días, {d['cliente']}:" if usted else f"Hola, {d['cliente']}:"


def _cotizacion(h, empresa: str, usted: bool) -> dict:
    d = h.datos
    fecha, total, neto = formato_fecha_iso(d["fecha"]), formato_clp(d["total"]), formato_clp(d["neto"])
    servicio = f" ({d['servicio']})" if d.get("servicio") else ""
    doc = _documento(d.get("rut"))
    if usted:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Junto con saludar, le escribo por la cotización {d['numero']}{servicio}, que usted aceptó el {fecha} "
            f"por {total} (neto {neto} más IVA).\n\n"
            f"Al revisar nuestros registros vimos que todavía no emitimos {doc} por ese trabajo ni tenemos "
            f"registrado su pago. Para dejarlo al día, le enviaremos {doc} por {total} esta semana.\n\n"
            "¿Nos puede confirmar sus datos de facturación y la fecha en que podría hacer el pago? Si ya pagó o "
            "hay algún error de nuestra parte, le agradecería avisarnos para corregirlo de inmediato.\n\n"
            f"Quedamos atentos a su respuesta.\n\nSaludos cordiales,\n{empresa}")
    else:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Te escribo por la cotización {d['numero']}{servicio}, que aceptaste el {fecha} por {total} "
            f"(neto {neto} más IVA).\n\n"
            f"Al revisar nuestros registros vimos que todavía no emitimos {doc} por ese trabajo ni tenemos "
            f"registrado tu pago. Para dejarlo al día, te enviaremos {doc} por {total} esta semana.\n\n"
            "¿Nos confirmas tus datos de facturación y la fecha en que podrías hacer el pago? Si ya pagaste o "
            "hay algún error de nuestra parte, avísanos y lo corregimos de inmediato.\n\n"
            f"Quedamos atentos a tu respuesta.\n\nSaludos,\n{empresa}")
    return {"para": d["cliente"], "asunto": f"Cotización {d['numero']}: documento y pago pendientes ({total})",
            "cuerpo": cuerpo, "obligatorio": [d["numero"], total, fecha]}


def _pago(h, empresa: str, usted: bool, corte: str) -> dict:
    d = h.datos
    fecha, total = formato_fecha_iso(d["fecha"]), formato_clp(d["total"])
    if usted:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Junto con saludar, le escribo por la factura N° {d['folio']}, emitida el {fecha} por {total}.\n\n"
            f"Según nuestros registros, al {corte} lleva {d['dias']} días sin pago. ¿Nos puede indicar en qué "
            "fecha hará la transferencia?\n\n"
            "Si ya la pagó, le agradecería enviarnos el comprobante para dejarla al día. Y si hay algún problema "
            "con la factura o con el servicio, conversemos para resolverlo.\n\n"
            f"Quedamos atentos a su respuesta.\n\nSaludos cordiales,\n{empresa}")
    else:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Te escribo por la factura N° {d['folio']}, emitida el {fecha} por {total}.\n\n"
            f"Según nuestros registros, al {corte} lleva {d['dias']} días sin pago. ¿Nos cuentas en qué fecha "
            "harás la transferencia?\n\n"
            "Si ya la pagaste, envíanos el comprobante para dejarla al día. Y si hay algún problema con la factura "
            "o con el servicio, conversemos para resolverlo.\n\n"
            f"Quedamos atentos a tu respuesta.\n\nSaludos,\n{empresa}")
    return {"para": d["cliente"], "asunto": f"Factura N° {d['folio']} pendiente de pago ({total})",
            "cuerpo": cuerpo, "obligatorio": [str(d["folio"]), total, fecha]}


def _nota(h) -> str:
    d, monto = h.datos, formato_clp(h.monto_clp)
    fecha = formato_fecha(h.evidencia[0].fecha) if h.evidencia and h.evidencia[0].fecha else ""
    if h.subtipo == "banco":
        relacion = (f" Parece ser el pago de la cotización {d['cotizacion']} de {d['cliente']}."
                    if d.get("cotizacion") else "")
        return (f"Emite la boleta o factura por {monto} del abono del {fecha} (\"{d.get('glosa', '')}\").{relacion} "
                "Si no era una venta (un préstamo, un aporte, una devolución), agrega una palabra de esa descripción a "
                "\"palabras_excluidas_abonos\" en tu config.json y no volverá a aparecer.")
    if h.subtipo == "pos":
        return (f"Emite la boleta por {monto} de la venta con tarjeta del {fecha} ({d.get('glosa', '')}). "
                "Si la boleta existe con otra fecha u otro monto, revisa por qué no coinciden.")
    if h.subtipo == "duplicada":
        return (f"Entra a la cuenta de {d['servicio']} y revisa por qué hay {d['cobros_al_mes']} cobros al mes de "
                f"{monto} si tienes {d['asientos']} {'licencia' if d['asientos'] == 1 else 'licencias'}. Cancela la "
                f"suscripción que sobra y pide el reembolso de lo cobrado de más ({formato_clp(h.impacto_clp)} en el periodo).")
    if h.subtipo == "huerfana":
        return (f"Da de baja la licencia de {d['servicio']} de {d['usuario']}: {d['persona']} ya no trabaja contigo. "
                f"Ahorras {monto} cada mes. Antes de borrarla, respalda sus archivos y correos si los necesitas.")
    if h.subtipo == "neto_como_total":
        return (f"Revisa con tu contador el documento folio {d['folio']} de {d['cliente']}: se emitió por el neto "
                f"cotizado en {d['numero']} como si fuera el total. La diferencia es {formato_clp(d['diferencia'])}. "
                "Decidan si corresponde corregir el documento y cobrar esa diferencia al cliente.")
    if h.subtipo == "iva_mal_calculado":
        return (f"Revisa con tu contador el documento folio {d['folio']} de {d['cliente']}: el IVA no es el 19% del "
                f"neto. La diferencia es {formato_clp(abs(d['diferencia']))}. Decidan si corresponde una nota de "
                "débito o de crédito.")
    return h.accion_sugerida


def borradores(res, tratamiento: str = "usted") -> list:
    """Un borrador por hallazgo: mensaje al cliente si hay que cobrar, nota interna si no."""
    usted = tratamiento != "tu"
    empresa, corte = res.config.empresa, formato_fecha(res.config.fecha_corte)
    lista = []
    for h in res.hallazgos:
        if h.tipo == "cotizacion_sin_cobro":
            b = {"clase": "mensaje", **_cotizacion(h, empresa, usted)}
        elif h.tipo == "pago_pendiente_30d":
            b = {"clase": "mensaje", **_pago(h, empresa, usted, corte)}
        else:
            b = {"clase": "nota", "para": "", "asunto": h.titulo, "cuerpo": _nota(h), "obligatorio": []}
        b.update(codigo=h.mensaje, hallazgo=h.id, monto=formato_clp(h.monto_clp), pulido=False)
        lista.append(b)
    return lista


def _cita(texto: str) -> list:
    return [f"> {linea}" if linea else ">" for linea in texto.split("\n")]


def mensajes_md(res, lista: list = None) -> str:
    lista = lista if lista is not None else borradores(res)
    mensajes = [b for b in lista if b["clase"] == "mensaje"]
    notas = [b for b in lista if b["clase"] == "nota"]
    s = [f"# Mensajes de cobro: {res.config.empresa}", "", f"> **{ENCABEZADO}**", "",
         "Estos textos los escribió el Detective de Fugas a partir del informe. Nadie los ha mandado: cópialos, "
         "ajústalos a tu forma de hablar y envíalos tú desde tu correo o WhatsApp.", ""]
    s += ["## Mensajes para clientes", ""]
    if not mensajes:
        s += ["No hay cobros pendientes a clientes en este informe.", ""]
    for b in mensajes:
        s += [f"### {b['codigo']} · {b['para']} ({b['hallazgo']})", "", f"- **Para:** {b['para']}",
              f"- **Asunto:** {b['asunto']}", f"- **Monto:** {b['monto']}", ""] + _cita(b["cuerpo"]) + [""]
    s += ["## Notas internas (no se envían a nadie)", ""]
    if not notas:
        s += ["No hay notas internas en este informe.", ""]
    for b in notas:
        s += [f"### {b['codigo']} · {b['asunto']} ({b['hallazgo']})", "", b["cuerpo"], ""]
    return "\n".join(s)
