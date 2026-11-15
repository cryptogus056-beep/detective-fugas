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


COMPLETAR_PAGO = "[tu banco, tipo y número de cuenta, RUT y correo para el comprobante]"
COMPLETAR_CONTACTO = "[tu correo o teléfono]"
COMPLETAR_NOMBRE = "[Tu nombre]"


def _saludo(d: dict, usted: bool) -> str:
    quien = f"equipo de {d['cliente']}" if _es_empresa(d.get("rut")) else d["cliente"]
    return f"Buenos días, {quien}:" if usted else f"Hola, {quien}:"


def _cierre(empresa: str, usted: bool) -> str:
    if usted:
        return (f"Cualquier duda, escríbame a {COMPLETAR_CONTACTO}.\n\nSaludos cordiales,\n"
                f"{COMPLETAR_NOMBRE}\n{empresa}")
    return f"Cualquier duda, escríbeme a {COMPLETAR_CONTACTO}.\n\nSaludos,\n{COMPLETAR_NOMBRE}\n{empresa}"


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
            f"Al revisar nuestros registros notamos que quedó pendiente enviarle {doc} por ese trabajo. "
            f"Le pedimos disculpas por la demora: se la adjuntamos en este mensaje, por {total}.\n\n"
            f"Puede pagar por transferencia a: {COMPLETAR_PAGO}.\n\n"
            "Si ya pagó o ve algún error de nuestra parte, le agradecería avisarnos para corregirlo de inmediato.\n\n"
            f"{_cierre(empresa, usted)}")
    else:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Te escribo por la cotización {d['numero']}{servicio}, que aceptaste el {fecha} por {total} "
            f"(neto {neto} más IVA).\n\n"
            f"Al revisar nuestros registros notamos que quedó pendiente enviarte {doc} por ese trabajo. "
            f"Disculpa la demora: te la adjuntamos en este mensaje, por {total}.\n\n"
            f"Puedes pagar por transferencia a: {COMPLETAR_PAGO}.\n\n"
            "Si ya pagaste o ves algún error de nuestra parte, avísanos y lo corregimos de inmediato.\n\n"
            f"{_cierre(empresa, usted)}")
    return {"para": d["cliente"], "asunto": f"Cotización {d['numero']}: documento y pago pendientes ({total})",
            "cuerpo": cuerpo, "obligatorio": [d["numero"], total, fecha],
            "antes": [f"Emite {doc} por {total} y adjúntala al mensaje.",
                      "Completa lo que está entre corchetes: tus datos para el pago, tu contacto y tu nombre."]}


def _pago(h, empresa: str, usted: bool) -> dict:
    d = h.datos
    fecha, total = formato_fecha_iso(d["fecha"]), formato_clp(d["total"])
    if usted:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Junto con saludar, le escribo por la factura N° {d['folio']}, emitida el {fecha} por {total}, "
            "que en nuestros registros figura sin pago.\n\n"
            "¿Nos puede confirmar en qué fecha podrá pagarla? Si ya la pagó, le agradecería enviarnos el "
            "comprobante para dejarla al día.\n\n"
            f"Puede pagar por transferencia a: {COMPLETAR_PAGO}.\n\n"
            "Si hay algún problema con la factura o con el servicio, conversemos para resolverlo.\n\n"
            f"{_cierre(empresa, usted)}")
    else:
        cuerpo = (
            f"{_saludo(d, usted)}\n\n"
            f"Te escribo por la factura N° {d['folio']}, emitida el {fecha} por {total}, que en nuestros "
            "registros figura sin pago.\n\n"
            "¿Nos confirmas en qué fecha podrás pagarla? Si ya la pagaste, envíanos el comprobante para dejarla "
            "al día.\n\n"
            f"Puedes pagar por transferencia a: {COMPLETAR_PAGO}.\n\n"
            "Si hay algún problema con la factura o con el servicio, conversemos para resolverlo.\n\n"
            f"{_cierre(empresa, usted)}")
    return {"para": d["cliente"], "asunto": f"Factura N° {d['folio']} pendiente de pago ({total})",
            "cuerpo": cuerpo, "obligatorio": [str(d["folio"]), total, fecha],
            "antes": [f"Revisa en tu banco que el pago no haya llegado después del {formato_fecha_iso(d['corte'])} "
                      f"(a esa fecha llevaba {d['dias']} días sin pago).",
                      "Completa lo que está entre corchetes: tus datos para el pago, tu contacto y tu nombre."]}


def _nota(h) -> str:
    d, monto = h.datos, formato_clp(h.monto_clp)
    fecha = formato_fecha(h.evidencia[0].fecha) if h.evidencia and h.evidencia[0].fecha else ""
    if h.subtipo == "banco":
        relacion = (f" Parece ser el pago de la cotización {d['cotizacion']} de {d['cliente']}."
                    if d.get("cotizacion") else "")
        return (f"Confirma primero qué fue el abono del {fecha} por {monto} (\"{d.get('glosa', '')}\").{relacion} "
                "Si fue una venta y no tiene documento, emite la boleta o factura. Si no fue una venta (por ejemplo "
                "un préstamo, un aporte de un socio o una devolución), no emitas nada y avísale a tu contador; el "
                "README explica cómo anotar esos casos para que no vuelvan a aparecer.")
    if h.subtipo == "pos":
        return (f"Busca la boleta de la venta con tarjeta del {fecha} por {monto} ({d.get('glosa', '')}). "
                "Si existe con otra fecha u otro monto, revisa por qué no coinciden. Si no existe, emítela.")
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
    empresa = res.config.empresa
    lista = []
    for h in res.hallazgos:
        if h.tipo == "cotizacion_sin_cobro":
            b = {"clase": "mensaje", **_cotizacion(h, empresa, usted)}
        elif h.tipo == "pago_pendiente_30d":
            b = {"clase": "mensaje", **_pago(h, empresa, usted)}
        else:
            b = {"clase": "nota", "para": "", "asunto": h.titulo, "cuerpo": _nota(h), "obligatorio": [], "antes": []}
        if b["clase"] == "mensaje":      # lo que un texto pulido no puede perder
            b["obligatorio"] = b["obligatorio"] + [COMPLETAR_PAGO, COMPLETAR_CONTACTO, COMPLETAR_NOMBRE]
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
         "ajústalos a tu forma de hablar y envíalos tú desde tu correo o WhatsApp. Lo que está entre corchetes "
         "[así] lo completas tú.", ""]
    s += ["## Mensajes para clientes", ""]
    if not mensajes:
        s += ["No hay cobros pendientes a clientes en este informe.", ""]
    for b in mensajes:
        s += [f"### {b['codigo']} · {b['para']} ({b['hallazgo']})", "", f"- **Para:** {b['para']}",
              f"- **Asunto:** {b['asunto']}", f"- **Monto:** {b['monto']}",
              "- **Antes de enviarlo:** " + " ".join(b["antes"]), ""] + _cita(b["cuerpo"]) + [""]
    s += ["## Notas internas (no se envían a nadie)", ""]
    if not notas:
        s += ["No hay notas internas en este informe.", ""]
    for b in notas:
        s += [f"### {b['codigo']} · {b['asunto']} ({b['hallazgo']})", "", b["cuerpo"], ""]
    return "\n".join(s)
