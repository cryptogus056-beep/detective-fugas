"""Recorrido completo de una auditoria: leer, emparejar, detectar, verificar.

Trabaja con archivos en memoria (nombre y bytes), sin tocar el disco. Por eso lo usan
igual la linea de comandos y la pagina web.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass, field

from . import __version__, reglas
from .config import cargar_config
from .emparejar import Datos, emparejar
from .lectores import ErrorLectura, es_tabla, extension
from .modelo import cargar_registros, huella
from .plantillas import ROLES, PlantillaNoEncontrada, reconocer_archivo
from .reglas import TIPOS_DE_COBRO, Contexto
from .reglas.abono_sin_documento import abonos_ambiguos
from .verificador import Fuente, verificar

NOMBRE_CONFIG = "config.json"
IGNORAR = "ignorar"
CATEGORIAS_QUE_NO_SON_VENTA = {"aporte_socio", "devolucion", "prestamo", "reembolso", "pago_proveedor",
                               "suscripcion", "remuneraciones", "impuestos", "traspaso"}
DESTINO = {"banco": "movimientos", "pos": "ventas_pos", "rcv_ventas": "documentos", "rcv_compras": "compras",
           "cotizaciones": "cotizaciones", "equipo": "personas", "licencias": "licencias"}
SIN_ARCHIVO = {
    "rcv_ventas": "No había Registro de Ventas del SII: no revisé abonos sin documento, cotizaciones sin cobro, "
                  "pagos pendientes ni diferencias de IVA.",
    "banco": "No había cartola del banco: no revisé abonos sin documento en el banco, pagos pendientes ni "
             "suscripciones.",
    "pos": "No había archivo de ventas con tarjeta: no revisé ventas con tarjeta sin boleta.",
    "cotizaciones": "No había planilla de cotizaciones: no revisé cotizaciones sin cobro ni netos cobrados como total.",
    "licencias": "No había archivo de licencias: no revisé suscripciones duplicadas ni huérfanas.",
    "equipo": "No había archivo del equipo: no revisé licencias de personas que ya salieron.",
    "rcv_compras": "No había Registro de Compras del SII: no pude reconocer devoluciones de proveedores por su RUT "
                   "(solo por las palabras de la configuración).",
}


@dataclass
class Entrada:
    nombre: str
    datos: bytes


@dataclass
class Resultado:
    config: object
    hallazgos: list = field(default_factory=list)
    descartados: list = field(default_factory=list)       # [{"motivo": str, "hallazgo": Hallazgo}]
    archivos_leidos: list = field(default_factory=list)
    no_revisado: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    ambiguas: list = field(default_factory=list)
    generado_en: str = ""
    version: str = __version__
    datos: object = None
    emp: object = None


def _ahora() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _quitar_repetidos(cargados: list, avisos: list) -> list:
    """Si dos archivos del mismo rol traen exactamente lo mismo, se usa uno solo (primero el XLSX)."""
    usados = []
    for lectura, carga in sorted(cargados, key=lambda lc: (extension(lc[0].tabla.nombre) != ".xlsx", lc[0].tabla.nombre)):
        contenido = Counter(huella(r) for r in carga.registros)
        gemelo = next((l for l, c in usados if l.plantilla.rol == lectura.plantilla.rol
                       and Counter(huella(r) for r in c.registros) == contenido), None)
        if gemelo is not None and carga.registros:
            avisos.append(f"`{gemelo.tabla.nombre}` y `{lectura.tabla.nombre}` traen las mismas filas: usé solo "
                          f"`{gemelo.tabla.nombre}` para no contar nada dos veces.")
            continue
        usados.append((lectura, carga))
    return usados


def _aplicar_clasificaciones(hallazgos: list, ambiguas: list, clasificaciones, avisos: list):
    """Quita hallazgos de abonos ambiguos que el clasificador marco como "no es venta".

    Una clasificacion nunca agrega un hallazgo ni puede tocar uno que no era ambiguo.
    """
    if not clasificaciones:
        return hallazgos, []
    permitidas = {(a["archivo"], a["fila"]) for a in ambiguas}
    decision = {}
    for c in clasificaciones:
        try:
            llave = (str(c["archivo"]), int(c["fila"]))
            categoria = str(c.get("categoria", "")).strip().lower()
        except (KeyError, TypeError, ValueError):
            avisos.append(f"Ignoré una clasificación mal formada: {c!r}.")
            continue
        if llave not in permitidas:
            avisos.append(f"Ignoré la clasificación de {llave[0]} fila {llave[1]}: esa fila no estaba marcada "
                          "como ambigua.")
            continue
        decision[llave] = (categoria, str(c.get("motivo", "")).strip())
    quedan, fuera = [], []
    for h in hallazgos:
        llave = (h.evidencia[0].archivo, h.evidencia[0].fila) if h.evidencia else None
        categoria, motivo = decision.get(llave, ("", ""))
        if h.tipo == "abono_sin_documento" and h.subtipo == "banco" and categoria in CATEGORIAS_QUE_NO_SON_VENTA:
            fuera.append({"motivo": f"Clasificado como \"{categoria}\" (no es una venta)"
                                    + (f": {motivo}" if motivo else "") + ".", "hallazgo": h})
        else:
            if categoria:
                h.datos["clasificacion"] = categoria
            quedan.append(h)
    return quedan, fuera


def _aplicar_descartes(confirmados: list, descartes, avisos: list):
    """Segunda opinion (modo agentico): saca del informe los hallazgos que un verificador externo descarto.

    Solo puede quitar. Los que quedan conservan su numero, para que el informe siga calzando.
    """
    if not descartes:
        return confirmados, []
    motivos = {}
    for d in descartes:
        if isinstance(d, dict) and d.get("id"):
            motivos[str(d["id"])] = str(d.get("motivo", "")).strip()
        else:
            avisos.append(f"Ignoré un descarte mal formado: {d!r}.")
    existentes = {h.id for h in confirmados}
    for desconocido in sorted(set(motivos) - existentes):
        avisos.append(f"Ignoré el descarte de {desconocido}: ese hallazgo no existe.")
    quedan, fuera = [], []
    for h in confirmados:
        if h.id in motivos:
            h.verificado = False
            fuera.append({"motivo": "Descartado por el verificador de segunda opinión"
                                    + (f": {motivos[h.id]}" if motivos[h.id] else "") + ".", "hallazgo": h})
        else:
            quedan.append(h)
    return quedan, fuera


def auditar(entradas: list, plantillas: list, roles_forzados: dict = None, clasificaciones: list = None,
            ahora: str = None, descartes: list = None) -> Resultado:
    """Audita un conjunto de archivos. `roles_forzados`: {nombre_de_archivo: rol o "ignorar"}."""
    roles_forzados = roles_forzados or {}
    crudo_config = next((e.datos for e in entradas if e.nombre.lower() == NOMBRE_CONFIG), None)
    config = cargar_config(crudo_config)
    res = Resultado(config=config, generado_en=ahora or _ahora())
    res.avisos.extend(config.avisos)

    cargados, fuentes = [], {}
    for e in sorted(entradas, key=lambda x: x.nombre):
        if not es_tabla(e.nombre) or roles_forzados.get(e.nombre) == IGNORAR:
            continue
        rol = roles_forzados.get(e.nombre)
        if rol is not None and rol not in ROLES:
            res.no_revisado.append(f"No usé '{e.nombre}': el tipo \"{rol}\" no existe.")
            continue
        try:
            lectura = reconocer_archivo(e.nombre, e.datos, plantillas, rol)
            carga = cargar_registros(lectura, config)
        except PlantillaNoEncontrada as error:
            res.no_revisado.append(f"No pude usar '{e.nombre}'. {error}")
            continue
        except ErrorLectura as error:
            res.no_revisado.append(f"No pude leer '{e.nombre}': {error}")
            continue
        cargados.append((lectura, carga))
        p = lectura.plantilla
        fuentes[e.nombre] = Fuente(e.nombre, e.datos, lectura.tabla.separador, p.formato_fecha, p.numeros,
                                   lectura.fila_encabezado)
        res.avisos.extend(carga.avisos)
        if carga.filas_saltadas:
            filas = ", ".join(f"{n} ({motivo})" for n, motivo in carga.filas_saltadas[:8])
            mas = f" y {len(carga.filas_saltadas) - 8} más" if len(carga.filas_saltadas) > 8 else ""
            res.no_revisado.append(f"En '{e.nombre}' no pude interpretar {len(carga.filas_saltadas)} "
                                   f"{'fila' if len(carga.filas_saltadas) == 1 else 'filas'}: {filas}{mas}.")

    usados = _quitar_repetidos(cargados, res.avisos)
    nombres_usados = {l.tabla.nombre for l, _ in usados}
    datos = Datos()
    for lectura, carga in usados:
        datos.roles.add(lectura.plantilla.rol)
        getattr(datos, DESTINO[lectura.plantilla.rol]).extend(carga.registros)
    for lectura, carga in sorted(cargados, key=lambda lc: lc[0].tabla.nombre):
        res.archivos_leidos.append({"archivo": lectura.tabla.nombre, "rol": lectura.plantilla.rol,
                                    "plantilla": lectura.plantilla.nombre, "filas": len(carga.registros),
                                    "usado": lectura.tabla.nombre in nombres_usados})
    if not cargados:
        raise ErrorLectura("No reconocí ningún archivo. Necesito al menos la cartola del banco en CSV o XLSX. "
                           + " ".join(res.no_revisado))

    fechas = [m.fecha for m in datos.movimientos] or [d.fecha for d in datos.documentos] or \
             [v.fecha for v in datos.ventas_pos] or [c.fecha for c in datos.cotizaciones]
    config.completar_fechas(fechas)
    res.avisos = config.avisos + [a for a in res.avisos if a not in config.avisos]
    for rol, mensaje in SIN_ARCHIVO.items():
        if rol not in datos.roles:
            res.no_revisado.append(mensaje)

    emp = emparejar(datos, config)
    ctx = Contexto(datos, config, emp)
    hallazgos = []
    for regla in reglas.todas():
        hallazgos.extend(regla.detectar(ctx))
    res.avisos.extend(ctx.avisos)
    res.ambiguas = [{"archivo": m.origen.archivo, "fila": m.origen.fila, "fecha": m.fecha.isoformat(),
                     "monto_clp": m.monto, "texto": m.origen.crudo,
                     "motivo": "abono sin documento cuya descripción no trae RUT: no se sabe quién pagó"}
                    for m in abonos_ambiguos(ctx)] if "rcv_ventas" in datos.roles else []
    hallazgos, por_clasificacion = _aplicar_clasificaciones(hallazgos, res.ambiguas, clasificaciones, res.avisos)

    confirmados, descartados = verificar(hallazgos, fuentes, config.tolerancia_clp)
    res.descartados = por_clasificacion + descartados
    confirmados.sort(key=lambda h: (-h.impacto_mensual_clp, -h.impacto_clp, h.tipo,
                                    h.evidencia[0].archivo, h.evidencia[0].fila))
    n_cobro = n_nota = 0
    for n, h in enumerate(confirmados, start=1):
        h.id = f"H{n:02d}"
        if h.tipo in TIPOS_DE_COBRO:
            n_cobro += 1
            h.mensaje = f"M{n_cobro:02d}"
            h.accion_sugerida = f"{h.accion_sugerida} {h.mensaje}."
        else:
            n_nota += 1
            h.mensaje = f"N{n_nota:02d}"
            h.accion_sugerida = f"{h.accion_sugerida} (nota interna {h.mensaje})."
    confirmados, por_segunda_opinion = _aplicar_descartes(confirmados, descartes, res.avisos)
    res.descartados.extend(por_segunda_opinion)
    excluidos = len(emp.excluidos)
    if excluidos:
        res.avisos.append(f"Dejé fuera {excluidos} {'abono' if excluidos == 1 else 'abonos'} que no son ventas "
                          "(aportes de socios, devoluciones, liquidaciones de tarjetas), según tu configuración.")
    res.hallazgos, res.datos, res.emp = confirmados, datos, emp
    return res
