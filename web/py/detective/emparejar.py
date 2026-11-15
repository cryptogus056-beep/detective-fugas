"""Emparejamiento: que pago corresponde a que documento, y que cotizacion a que documento.

Se calcula UNA sola vez y lo usan todas las reglas. Asi una misma fuga no aparece dos
veces con nombres distintos. Todo emparejamiento es uno a uno: un documento respalda
un solo pago.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field

from .normalizar import RUT_GENERICO, normalizar_glosa, normalizar_rut, sin_tildes

TIPOS_FACTURA = {30, 32, 33, 34}
TIPOS_BOLETA = {35, 38, 39, 41}
TIPOS_NOTA_CREDITO = {60, 61}
TIPOS_VENTA = TIPOS_FACTURA | TIPOS_BOLETA


def clave(registro) -> tuple:
    return (registro.origen.archivo, registro.origen.fila)


@dataclass
class Datos:
    """Todo lo leido, ya convertido a registros comunes."""
    movimientos: list = field(default_factory=list)
    ventas_pos: list = field(default_factory=list)
    documentos: list = field(default_factory=list)     # rcv_ventas
    compras: list = field(default_factory=list)        # rcv_compras
    cotizaciones: list = field(default_factory=list)
    personas: list = field(default_factory=list)
    licencias: list = field(default_factory=list)
    roles: set = field(default_factory=set)            # roles para los que llego un archivo


@dataclass
class Emparejamiento:
    doc_de_abono: dict = field(default_factory=dict)       # clave(movimiento) -> Documento
    doc_de_venta: dict = field(default_factory=dict)       # clave(venta POS) -> Documento
    pago_de_doc: dict = field(default_factory=dict)        # clave(documento) -> Movimiento o VentaPos
    doc_de_cot: dict = field(default_factory=dict)         # clave(cotizacion) -> (Documento, tipo de calce)
    cot_de_doc: dict = field(default_factory=dict)         # clave(documento) -> (Cotizacion, tipo de calce)
    excluidos: dict = field(default_factory=dict)          # clave(movimiento) -> motivo de exclusion
    anulados: dict = field(default_factory=dict)           # clave(documento) -> nota de credito que lo anula


def asignar(pares: list) -> dict:
    """Asignacion uno a uno a partir de (puntaje, i, j); puntaje menor es mejor.

    Primero toma los mejores pares en orden. Despues, para los `i` que quedaron solos,
    busca reacomodos (caminos de aumento) para no dejar sin pareja a alguien que podia
    tenerla. Asi nunca se informa una fuga solo por haber elegido mal el orden.
    """
    pares = sorted(pares)
    par, inverso = {}, {}
    vecinos = defaultdict(list)
    for _, i, j in pares:
        vecinos[i].append(j)
        if i not in par and j not in inverso:
            par[i], inverso[j] = j, i

    def reacomodar(i, vistos) -> bool:
        for j in vecinos[i]:
            if j in vistos:
                continue
            vistos.add(j)
            if j not in inverso or reacomodar(inverso[j], vistos):
                par[i], inverso[j] = j, i
                return True
        return False

    for i in list(vecinos):
        if i not in par:
            reacomodar(i, set())
    return par


def texto_plano(texto) -> str:
    """Mayusculas, sin tildes y sin signos: para buscar frases dentro de una glosa."""
    limpio = "".join(c if c.isalnum() else " " for c in sin_tildes(str(texto or "")).upper())
    return " ".join(limpio.split())


def motivo_exclusion(movimiento, config, ruts_proveedores: set, ruts_clientes: set):
    """Por que un abono NO es una venta (aporte, devolucion, liquidacion...). None si puede serlo."""
    plano = f" {texto_plano(movimiento.descripcion)} "
    for palabra in config.palabras_excluidas_abonos:
        if f" {texto_plano(palabra)} " in plano:
            return f"contiene \"{palabra}\" (excluido en la configuración)"
    for rut in movimiento.ruts:
        if rut in config.ruts_excluidos_abonos:
            return f"viene del RUT {rut} (excluido en la configuración)"
        if config.rut_empresa and rut == normalizar_rut(config.rut_empresa)[0]:
            return "viene del RUT de tu propia empresa (traspaso entre cuentas)"
    for rut in movimiento.ruts:
        if rut in ruts_proveedores and rut not in ruts_clientes:
            return f"viene del RUT {rut}, que es un proveedor tuyo (probable devolución)"
    return None


def _rut_real(rut) -> bool:
    return bool(rut) and rut != RUT_GENERICO


def _candidatos_por_monto(documentos: list, tolerancia: int) -> dict:
    """Indice total -> documentos, para no comparar todo contra todo."""
    indice = defaultdict(list)
    for d in documentos:
        indice[d.total].append(d)
    return indice


def _pares(pagos: list, documentos: list, config, dias_antes: int, dias_despues: int, ruts_de_pago) -> list:
    """Pares posibles (pago, documento): mismo monto y documento dentro de la ventana de fechas."""
    tol = config.tolerancia_clp
    indice = _candidatos_por_monto(documentos, tol)
    orden_doc = {clave(d): n for n, d in enumerate(documentos)}
    pares = []
    for i, pago in enumerate(pagos):
        ruts = ruts_de_pago(pago)
        for delta in range(-tol, tol + 1):
            for doc in indice.get(pago.monto + delta, ()):
                dias = (doc.fecha - pago.fecha).days       # negativo: el documento es anterior al pago
                if not (-dias_antes <= dias <= dias_despues):
                    continue
                if ruts and _rut_real(doc.rut):
                    penal_rut = 0 if doc.rut in ruts else 2
                else:
                    penal_rut = 1
                pares.append(((penal_rut, abs(dias), abs(delta), i, orden_doc[clave(doc)]), i, orden_doc[clave(doc)]))
    return pares


def _emparejar_pagos(pagos, documentos, config, dias_antes, dias_despues, ruts_de_pago) -> list:
    asignados = asignar(_pares(pagos, documentos, config, dias_antes, dias_despues, ruts_de_pago))
    return [(pagos[i], documentos[j]) for i, j in asignados.items()]


def _anular_con_notas_de_credito(documentos, config, emp: Emparejamiento) -> None:
    tol = config.tolerancia_clp
    for nota in (d for d in documentos if d.tipo in TIPOS_NOTA_CREDITO):
        for doc in documentos:
            if (doc.tipo in TIPOS_VENTA and clave(doc) not in emp.anulados and doc.rut == nota.rut
                    and abs(abs(doc.total) - abs(nota.total)) <= tol and doc.fecha <= nota.fecha):
                emp.anulados[clave(doc)] = nota
                break


def _calce_cotizacion(cot, doc, tol: int):
    """Tipo de calce entre una cotizacion y un documento, o None."""
    if doc.fecha < cot.fecha:
        return None
    if _rut_real(cot.rut) and _rut_real(doc.rut) and cot.rut != doc.rut:
        return None
    if doc.neto is not None and abs(doc.neto - cot.neto) <= tol and doc.neto > 0:
        return "neto"
    if abs(doc.total - cot.total) <= tol:
        return "total"
    if abs(doc.total - cot.neto) <= tol:
        return "neto_como_total"
    return None


def emparejar(datos: Datos, config) -> Emparejamiento:
    emp = Emparejamiento()
    _anular_con_notas_de_credito(datos.documentos, config, emp)
    vigentes = [d for d in datos.documentos if d.tipo in TIPOS_VENTA and clave(d) not in emp.anulados]
    libres = {clave(d) for d in vigentes}

    def registrar(pares, destino):
        for pago, doc in pares:
            destino[clave(pago)] = doc
            emp.pago_de_doc[clave(doc)] = pago
            libres.discard(clave(doc))

    # 1. Ventas con tarjeta aprobadas con su boleta del mismo dia o del dia siguiente.
    ventas = [v for v in datos.ventas_pos if v.aprobada]
    boletas = [d for d in vigentes if d.tipo in TIPOS_BOLETA]
    registrar(_emparejar_pagos(ventas, boletas, config, 0, 1, lambda v: []), emp.doc_de_venta)

    # 2. Ventas con tarjeta que pagaron una factura (mejora sobre la spec: evita falsos positivos).
    ventas = [v for v in ventas if clave(v) not in emp.doc_de_venta]
    facturas = [d for d in vigentes if d.tipo in TIPOS_FACTURA and clave(d) in libres]
    registrar(_emparejar_pagos(ventas, facturas, config, config.dias_documento_antes_abono,
                               config.ventana_dias_abono_documento, lambda v: []), emp.doc_de_venta)

    # 3. Abonos del banco con facturas y boletas que sigan libres.
    ruts_proveedores = {d.rut for d in datos.compras if _rut_real(d.rut)}
    ruts_clientes = ({d.rut for d in datos.documentos if _rut_real(d.rut)}
                     | {c.rut for c in datos.cotizaciones if _rut_real(c.rut)})
    abonos = []
    for m in datos.movimientos:
        if m.monto <= 0:
            continue
        motivo = motivo_exclusion(m, config, ruts_proveedores, ruts_clientes)
        if motivo:
            emp.excluidos[clave(m)] = motivo
        else:
            abonos.append(m)
    disponibles = [d for d in vigentes if clave(d) in libres]
    registrar(_emparejar_pagos(abonos, disponibles, config, config.dias_documento_antes_abono,
                               config.ventana_dias_abono_documento, lambda m: m.ruts), emp.doc_de_abono)

    # 4. Cotizaciones aceptadas con su documento.
    aceptadas = [c for c in datos.cotizaciones if c.estado == "aceptada"]
    rango = {"neto": 0, "total": 0, "neto_como_total": 1}
    pares, tipos = [], {}
    for i, cot in enumerate(aceptadas):
        for j, doc in enumerate(vigentes):
            tipo = _calce_cotizacion(cot, doc, config.tolerancia_clp)
            if tipo:
                sin_rut = 0 if (_rut_real(cot.rut) and _rut_real(doc.rut)) else 1
                pares.append(((sin_rut, rango[tipo], (doc.fecha - cot.fecha).days, i, j), i, j))
                tipos[(i, j)] = tipo
    for i, j in asignar(pares).items():
        emp.doc_de_cot[clave(aceptadas[i])] = (vigentes[j], tipos[(i, j)])
        emp.cot_de_doc[clave(vigentes[j])] = (aceptadas[i], tipos[(i, j)])
    return emp


def nombre_comercio(descripcion: str) -> str:
    """Glosa normalizada: el "nombre" de un comercio para agrupar cobros."""
    return normalizar_glosa(descripcion)


def primer_dia(fecha: dt.date) -> dt.date:
    return fecha.replace(day=1)
