"""Salidas de la auditoria: hallazgos.json (contrato 6.1), informe.md e informe.html (6.2).

El informe se arma una sola vez como estructura (`construir`) y despues se escribe
en Markdown y en HTML, para que ambos digan exactamente lo mismo.
"""
from __future__ import annotations

import html
import json

from .normalizar import formato_clp, formato_fecha
from .plantillas import ROLES
from .reglas import NOMBRE_SIMPLE, TIPOS, TIPOS_DE_COBRO

PIE = "Este informe no reemplaza a tu contador. Montos en CLP."
CUENTA = {  # (singular, plural) para el resumen
    "abono_sin_documento": ("ingreso sin boleta ni factura", "ingresos sin boleta ni factura"),
    "cotizacion_sin_cobro": ("cotización aceptada sin facturar", "cotizaciones aceptadas sin facturar"),
    "pago_pendiente_30d": ("factura impaga", "facturas impagas"),
    "suscripcion_duplicada_o_huerfana": ("pago de software de más", "pagos de software de más"),
    "diferencia_iva": ("diferencia de IVA", "diferencias de IVA"),
}


# --------------------------------------------------------------------------- JSON

def a_json(res) -> dict:
    """El contrato de hallazgos.json. Lo lee scripts/evaluar.py."""
    c = res.config
    return {
        "empresa": c.empresa,
        "fecha_corte": c.fecha_corte.isoformat(),
        "periodo_desde": c.periodo_desde.isoformat(),
        "periodo_hasta": c.periodo_hasta.isoformat(),
        "meses_del_periodo": c.meses,
        "generado_en": res.generado_en,
        "version_detector": res.version,
        "archivos_leidos": res.archivos_leidos,
        "hallazgos": [h.a_dict() for h in res.hallazgos],
        "no_revisado": res.no_revisado,
        "avisos": res.avisos,
    }


def descartados_json(res) -> list:
    return [{"motivo": d["motivo"], "hallazgo": d["hallazgo"].a_dict()} for d in res.descartados]


def texto_json(objeto) -> str:
    return json.dumps(objeto, ensure_ascii=False, indent=2) + "\n"


# --------------------------------------------------------------------------- estructura del informe

def _lista(partes: list) -> str:
    partes = [p for p in partes if p]
    if len(partes) <= 1:
        return "".join(partes)
    return ", ".join(partes[:-1]) + " y " + partes[-1]


def _corto(texto: str, largo: int = 48) -> str:
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= largo else texto[:largo - 3].rstrip() + "..."


def referencia(h) -> str:
    """Una frase corta que identifica el hallazgo (para la tabla y el resumen)."""
    d, fecha = h.datos, formato_fecha(h.evidencia[0].fecha) if h.evidencia and h.evidencia[0].fecha else ""
    if h.tipo == "cotizacion_sin_cobro":
        return f"{d['numero']}: {d['cliente']} la aceptó el {formato_fecha_iso(d['fecha'])} y nunca se facturó"
    if h.tipo == "pago_pendiente_30d":
        return f"Factura folio {d['folio']} a {d['cliente']}: {d['dias']} días sin pago"
    if h.subtipo == "banco":
        return f"Abono del {fecha} sin boleta ni factura ({_corto(d.get('glosa', ''))})"
    if h.subtipo == "pos":
        return f"Venta con tarjeta del {fecha} sin boleta ({_corto(d.get('glosa', ''))})"
    if h.subtipo == "duplicada":
        licencias = "1 licencia" if d["asientos"] == 1 else f"{d['asientos']} licencias"
        return f"{d['servicio']}: {d['cobros_al_mes']} cobros al mes con {licencias}"
    if h.subtipo == "huerfana":
        return f"Licencia de {d['servicio']} de {d['persona']}, que ya no trabaja contigo"
    if h.subtipo == "neto_como_total":
        return f"{d['numero']} de {d['cliente']}: se facturó el neto como si fuera el total (folio {d['folio']})"
    if h.subtipo == "iva_mal_calculado":
        return f"Documento folio {d['folio']} a {d['cliente']}: IVA mal calculado"
    return h.titulo


def formato_fecha_iso(texto) -> str:
    """'2026-09-03' -> '03/09/2026'."""
    partes = str(texto or "").split("-")
    return f"{partes[2]}/{partes[1]}/{partes[0]}" if len(partes) == 3 else str(texto or "")


def cita(e) -> str:
    """`archivo` fila N, fecha, monto (solo lo que la fila tiene)."""
    partes = [f"`{e.archivo}` fila {e.fila}"]
    if e.fecha:
        partes.append(formato_fecha(e.fecha))
    if e.monto_clp is not None:
        partes.append(formato_clp(e.monto_clp))
    return ", ".join(partes)


def _impacto_mensual(h) -> str:
    return f"{formato_clp(h.impacto_mensual_clp)} {'cada mes' if h.recurrente else '(promedio mensual)'}"


SEGURIDAD = {"alta": "Alta", "media": "Media: confirma antes", "baja": "Baja: confirma antes"}
COLUMNAS = [("n", "N°"), ("tipo", "Tipo"), ("que", "Qué pasó"), ("monto", "Monto del documento o movimiento"),
            ("en_juego", "Plata en juego"), ("mensual", "Impacto mensual"), ("seguridad", "Qué tan seguro"),
            ("evidencia", "Evidencia"), ("accion", "Acción")]
NOTA_TABLA = ("\"Monto del documento o movimiento\" es el total de la factura, cotización, cobro o abono. "
              "\"Plata en juego\" es la parte que pierdes, te deben o arriesgas: a veces es todo el monto y a veces "
              "solo el IVA. \"Promedio mensual\" quiere decir que la fuga pasó una vez y la repartí entre los meses "
              "del periodo para poder ordenar la tabla; \"cada mes\" quiere decir que se repite hasta que la arregles.")
GLOSARIO = ("Palabras que uso: **neto** es el precio sin IVA; **folio** es el número de la factura o boleta; "
            "**fecha de corte** es el último día que cubren tus archivos; una **nota de crédito o de débito** es un "
            "documento que corrige una factura ya emitida (te la emite tu contador o tu sistema de facturación).")


def _resumen(res) -> list:
    c, hs = res.config, res.hallazgos
    periodo = f"los {c.meses} meses revisados" if c.meses > 1 else "el mes revisado"
    if not hs:
        return [
            ("En juego", f"{formato_clp(0)}: no encontré fugas con evidencia en {periodo}."),
            ("Qué encontré", "0 fugas en los tipos que pude revisar."),
            ("La más grande", "no hay ninguna que informar."),
            ("Qué hacer primero esta semana", "mira más abajo \"Lo que no pude revisar\": si faltó algún archivo, "
                                              "agrégalo y vuelve a correr la revisión."),
            ("Si cobras lo pendiente", "no hay cobros pendientes a clientes en lo que revisé."),
        ]
    total = sum(h.impacto_clp for h in hs)
    por_cobrar = sum(h.impacto_clp for h in hs if h.tipo in TIPOS_DE_COBRO)
    cada_mes = sum(h.impacto_mensual_clp for h in hs if h.recurrente)
    partes = []
    if por_cobrar:
        partes.append(f"{formato_clp(por_cobrar)} que te deben o no has facturado")
    if total - por_cobrar:
        partes.append(f"{formato_clp(total - por_cobrar)} entre IVA en riesgo o mal cobrado y software pagado de más")
    repite = (f" Casi todo pasó una sola vez; lo único que se repite cada mes son {formato_clp(cada_mes)} de software."
              if cada_mes else " Todo pasó una sola vez: no es un gasto de cada mes.")
    por_confirmar = sum(1 for h in hs if h.confianza != "alta")
    confirmar = (f" De ellas, {por_confirmar} {'es' if por_confirmar == 1 else 'son'} de seguridad media: "
                 
                 f"{'confírmala' if por_confirmar == 1 else 'confírmalas'} antes de actuar." if por_confirmar else "")
    cuenta = []
    for tipo in TIPOS:
        n = sum(1 for h in hs if h.tipo == tipo)
        if n:
            cuenta.append(f"{n} {CUENTA[tipo][0] if n == 1 else CUENTA[tipo][1]}")
    mayor = hs[0]
    cobros = [h for h in hs if h.tipo in TIPOS_DE_COBRO]
    if cobros:
        n_cot = sum(1 for h in cobros if h.tipo == "cotizacion_sin_cobro")
        n_fac = len(cobros) - n_cot
        detalle = _lista([f"{n_cot} {'cotización' if n_cot == 1 else 'cotizaciones'} sin facturar" if n_cot else "",
                          f"{n_fac} {'factura impaga' if n_fac == 1 else 'facturas impagas'}" if n_fac else ""])
        recupera = (f"recuperas {formato_clp(sum(h.impacto_clp for h in cobros))} ({detalle}). Los mensajes ya "
                    "están redactados en `mensajes_cobro.md`.")
    else:
        recupera = "no hay cobros pendientes a clientes; lo que encontré se arregla puertas adentro."
    return [
        ("En juego", f"{formato_clp(total)} en {periodo}: {_lista(partes)}.{repite}"),
        ("Qué encontré", f"{len(hs)} {'fuga' if len(hs) == 1 else 'fugas'}: {_lista(cuenta)}.{confirmar}"),
        ("La más grande", f"{referencia(mayor)} ({formato_clp(mayor.impacto_clp)}, {mayor.id})."),
        ("Qué hacer primero esta semana", f"{mayor.accion_sugerida} Después sigue con la tabla, de arriba hacia abajo."),
        ("Si cobras lo pendiente", recupera),
    ]


def construir(res) -> dict:
    """El informe como estructura, independiente del formato de salida."""
    c = res.config
    tabla, detalles = [], []
    for n, h in enumerate(res.hallazgos, start=1):
        principal = next((e for e in h.evidencia if e.completa), h.evidencia[0])
        otras = len(h.evidencia) - 1
        evidencia = cita(principal) + (f" (y {otras} {'fila' if otras == 1 else 'filas'} más en el detalle)" if otras else "")
        tabla.append({"n": str(n), "id": h.id, "tipo": NOMBRE_SIMPLE[h.tipo], "que": referencia(h),
                      "monto": formato_clp(h.monto_clp), "en_juego": formato_clp(h.impacto_clp),
                      "mensual": _impacto_mensual(h), "seguridad": SEGURIDAD.get(h.confianza, h.confianza),
                      "evidencia": evidencia, "accion": h.accion_sugerida})
        lineas = [("Qué pasó", h.descripcion), ("Monto del documento o movimiento", formato_clp(h.monto_clp)),
                  ("Plata en juego", formato_clp(h.impacto_clp)), ("Impacto mensual", _impacto_mensual(h)),
                  ("Qué tan seguro", "Alta: la evidencia es directa." if h.confianza == "alta"
                   else f"{h.confianza.capitalize()}: confírmalo antes de actuar."),
                  ("Qué hacer", h.accion_sugerida)]
        detalles.append({"id": h.id, "titulo": h.titulo, "tipo": NOMBRE_SIMPLE[h.tipo], "lineas": lineas,
                         "evidencias": [{"cita": cita(e), "detalle": e.detalle, "fila_original": e.fila_original}
                                        for e in h.evidencia]})
    archivos = []
    for a in res.archivos_leidos:
        nota = "" if a.get("usado", True) else " No lo usé porque repite a otro archivo."
        tipo = ROLES[a["rol"]]["titulo"].lower() if a.get("rol") in ROLES else a.get("rol", "")
        archivos.append(f"`{a['archivo']}`: {tipo}, {a['filas']} filas leídas.{nota}")
    notas = list(res.avisos)
    if res.descartados:
        n = len(res.descartados)
        notas.append(f"Dejé fuera {n} {'posible hallazgo' if n == 1 else 'posibles hallazgos'} porque no "
                     "pasaron la verificación o la clasificación. El detalle está en `descartados.json`.")
    return {
        "titulo": f"Informe de fugas: {c.empresa}",
        "periodo": (f"Periodo revisado: {formato_fecha(c.periodo_desde)} al {formato_fecha(c.periodo_hasta)} "
                    f"({c.meses} {'mes' if c.meses == 1 else 'meses'}). Último día que cubren tus archivos "
                    f"(fecha de corte): {formato_fecha(c.fecha_corte)}."),
        "resumen": _resumen(res),
        "tabla": tabla,
        "detalles": detalles,
        "verificar": [
            "Elige cualquier hallazgo y mira su evidencia: dice el archivo, la fila, la fecha y el monto.",
            "Abre ese archivo en Excel o en cualquier editor y ve a esa fila. La fila 1 es la primera línea del "
            "archivo, así que los títulos y encabezados también cuentan: es el mismo número que muestra Excel a la izquierda.",
            "Compara la fecha y el monto de la fila con los del informe. Deben ser iguales.",
            "En el detalle de cada hallazgo está copiada la fila original, para que la reconozcas sin buscar.",
            "El detector hizo esta misma comprobación antes de escribir el informe: lo que no calzó no aparece aquí.",
        ],
        "archivos": archivos,
        "no_revisado": list(res.no_revisado),
        "notas": notas,
        "pie": PIE,
    }


# --------------------------------------------------------------------------- Markdown

def _celda(texto: str) -> str:
    return " ".join(str(texto).split()).replace("|", "\\|")


def informe_md(res) -> str:
    m = construir(res)
    s = [f"# {m['titulo']}", "", m["periodo"], "", "## Resumen en 5 líneas", ""]
    s += [f"{n}. **{etiqueta}:** {texto}" for n, (etiqueta, texto) in enumerate(m["resumen"], start=1)]
    s += ["", "## Fugas encontradas, de mayor a menor impacto mensual", ""]
    if m["tabla"]:
        s += ["| " + " | ".join(titulo for _, titulo in COLUMNAS) + " |", "|" + "---|" * len(COLUMNAS)]
        s += ["| " + " | ".join(_celda(f[clave]) for clave, _ in COLUMNAS) + " |" for f in m["tabla"]]
        s += ["", NOTA_TABLA, "", GLOSARIO]
    else:
        s.append("No encontré fugas con evidencia en los archivos que revisé.")
    s += ["", "## Detalle de cada fuga", ""]
    if not m["detalles"]:
        s += ["No hay fugas que detallar.", ""]
    for d in m["detalles"]:
        s += [f"### {d['id']} · {d['titulo']}", ""]
        s += [f"- **{etiqueta}:** {texto}" for etiqueta, texto in d["lineas"]]
        s += ["- **Evidencia:**", ""]
        for e in d["evidencias"]:
            s += [f"  - {e['cita']}. {e['detalle']}", "", "    ```text"]
            s += [f"    {linea}" for linea in (e["fila_original"] or "").splitlines() or [""]]
            s += ["    ```", ""]
    s += ["## Cómo verificar este informe", ""]
    s += [f"{n}. {paso}" for n, paso in enumerate(m["verificar"], start=1)]
    s += ["", "Archivos que leí:", ""] + [f"- {a}" for a in m["archivos"]]
    s += ["", "## Lo que no pude revisar", ""]
    s += [f"- {linea}" for linea in m["no_revisado"]] or ["Revisé todos los tipos de fuga: no faltó ningún archivo."]
    if m["notas"]:
        s += ["", "Ten en cuenta:", ""] + [f"- {nota}" for nota in m["notas"]]
    s += ["", "---", "", m["pie"], ""]
    return "\n".join(s)


# --------------------------------------------------------------------------- HTML

ESTILO = """
.informe{--tinta:#1c2733;--suave:#5b6875;--linea:#dfe5ea;--fondo:#ffffff;--papel:#f5f7f9;--acento:#0b6e4f;--alerta:#9a3412;
  color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.informe h1{font-size:1.6rem;line-height:1.25;margin:0 0 .3rem}
.informe h2{font-size:1.2rem;margin:2rem 0 .7rem;padding-top:1rem;border-top:1px solid var(--linea)}
.informe h3{font-size:1.02rem;margin:0 0 .5rem}
.informe .periodo{color:var(--suave);margin:0}
.informe .resumen{background:var(--papel);border-left:4px solid var(--acento);border-radius:6px;margin:0;padding:.9rem 1rem .9rem 2.2rem}
.informe .resumen li{margin:.3rem 0}
.informe table{border-collapse:collapse;width:100%;font-size:.92rem}
.informe th,.informe td{border-bottom:1px solid var(--linea);padding:.55rem .5rem;text-align:left;vertical-align:top}
.informe th{background:var(--papel);font-weight:600}
.informe td.monto{white-space:nowrap;font-variant-numeric:tabular-nums}
.informe .nota{color:var(--suave);font-size:.9rem}
.informe .fuga{border:1px solid var(--linea);border-radius:8px;margin:0 0 1rem;padding:1rem}
.informe .fuga .tipo{color:var(--acento);font-size:.8rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase}
.informe .fuga dl{display:grid;grid-template-columns:11rem 1fr;gap:.35rem .8rem;margin:.4rem 0}
.informe .fuga dt{color:var(--suave)}
.informe .fuga dd{margin:0}
.informe .evidencia{margin:.6rem 0 0;padding:0;list-style:none}
.informe .evidencia li{margin:.6rem 0}
.informe pre{background:var(--papel);border:1px solid var(--linea);border-radius:6px;font:.82rem/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  margin:.3rem 0 0;overflow-x:auto;padding:.55rem .7rem;white-space:pre-wrap;word-break:break-word}
.informe code{background:var(--papel);border-radius:4px;font:.88em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;padding:.05rem .3rem}
.informe .pie{border-top:1px solid var(--linea);color:var(--suave);margin-top:2rem;padding-top:1rem}
@media (max-width:760px){
  .informe table,.informe tbody,.informe tr,.informe td{display:block;width:auto}
  .informe thead{display:none}
  .informe tr{border:1px solid var(--linea);border-radius:8px;margin:0 0 .8rem;padding:.4rem .7rem}
  .informe td{border:0;padding:.25rem 0}
  .informe td::before{color:var(--suave);content:attr(data-etiqueta) ": ";font-size:.85rem}
  .informe td.monto{white-space:normal}
  .informe .fuga dl{grid-template-columns:1fr}
  .informe .fuga dt{margin-top:.4rem}
}
@media print{.informe .fuga,.informe tr{break-inside:avoid}}
"""


def _marcas(texto: str) -> str:
    """Escapa HTML y convierte `codigo` en <code>."""
    partes = html.escape(str(texto)).split("`")
    unido = "".join(p if i % 2 == 0 else f"<code>{p}</code>" for i, p in enumerate(partes))
    negritas = unido.split("**")
    if len(negritas) % 2 == 0:
        return unido
    return "".join(p if i % 2 == 0 else f"<strong>{p}</strong>" for i, p in enumerate(negritas))


def cuerpo_html(res) -> str:
    """El informe como fragmento HTML con su estilo (lo incrusta la web)."""
    m = construir(res)
    s = [f"<style>{ESTILO}</style>", '<article class="informe">', f"<h1>{_marcas(m['titulo'])}</h1>",
         f'<p class="periodo">{_marcas(m["periodo"])}</p>', "<h2>Resumen en 5 líneas</h2>", '<ol class="resumen">']
    s += [f"<li><strong>{_marcas(etiqueta)}:</strong> {_marcas(texto)}</li>" for etiqueta, texto in m["resumen"]]
    s += ["</ol>", "<h2>Fugas encontradas, de mayor a menor impacto mensual</h2>"]
    if m["tabla"]:
        columnas = COLUMNAS
        s += ["<table>", "<thead><tr>" + "".join(f"<th>{t}</th>" for _, t in columnas) + "</tr></thead>", "<tbody>"]
        for f in m["tabla"]:
            celdas = "".join(
                f'<td data-etiqueta="{t}"{" class=monto" if k in ("monto", "en_juego", "mensual") else ""}>{_marcas(f[k])}</td>'
                for k, t in columnas)
            s.append(f"<tr>{celdas}</tr>")
        s += ["</tbody>", "</table>",
              f'<p class="nota">{_marcas(NOTA_TABLA)}</p>', f'<p class="nota">{_marcas(GLOSARIO)}</p>']
    else:
        s.append("<p>No encontré fugas con evidencia en los archivos que revisé.</p>")
    s.append("<h2>Detalle de cada fuga</h2>")
    if not m["detalles"]:
        s.append("<p>No hay fugas que detallar.</p>")
    for d in m["detalles"]:
        s += [f'<section class="fuga" id="{d["id"]}">', f'<div class="tipo">{_marcas(d["tipo"])}</div>',
              f"<h3>{d['id']} · {_marcas(d['titulo'])}</h3>", "<dl>"]
        s += [f"<dt>{_marcas(etiqueta)}</dt><dd>{_marcas(texto)}</dd>" for etiqueta, texto in d["lineas"]]
        s += ["</dl>", "<strong>Evidencia</strong>", '<ul class="evidencia">']
        for e in d["evidencias"]:
            s.append(f"<li>{_marcas(e['cita'])}. {_marcas(e['detalle'])}<pre>{html.escape(e['fila_original'] or '')}</pre></li>")
        s += ["</ul>", "</section>"]
    s += ["<h2>Cómo verificar este informe</h2>", "<ol>"] + [f"<li>{_marcas(p)}</li>" for p in m["verificar"]] + ["</ol>"]
    s += ["<p>Archivos que leí:</p>", "<ul>"] + [f"<li>{_marcas(a)}</li>" for a in m["archivos"]] + ["</ul>"]
    s.append("<h2>Lo que no pude revisar</h2>")
    if m["no_revisado"]:
        s += ["<ul>"] + [f"<li>{_marcas(l)}</li>" for l in m["no_revisado"]] + ["</ul>"]
    else:
        s.append("<p>Revisé todos los tipos de fuga: no faltó ningún archivo.</p>")
    if m["notas"]:
        s += ["<p>Ten en cuenta:</p>", "<ul>"] + [f"<li>{_marcas(n)}</li>" for n in m["notas"]] + ["</ul>"]
    s += [f'<p class="pie">{_marcas(m["pie"])}</p>', "</article>"]
    return "\n".join(s) + "\n"


def informe_html(res) -> str:
    """Pagina completa, en un solo archivo y sin recursos externos: sirve para imprimir o compartir."""
    titulo = html.escape(construir(res)["titulo"])
    return ("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{titulo}</title>\n"
            "<style>body{background:#fff;margin:0 auto;max-width:1040px;padding:1.5rem 1rem 3rem}</style>\n"
            f"</head>\n<body>\n{cuerpo_html(res)}</body>\n</html>\n")


# --------------------------------------------------------------------------- todo junto

def archivos_de_salida(res, borradores: list = None, tratamiento: str = "usted") -> dict:
    """nombre de archivo -> contenido en texto. Lo usan la CLI y la web."""
    from . import mensajes
    borradores = borradores if borradores is not None else mensajes.borradores(res, tratamiento)
    return {
        "hallazgos.json": texto_json(a_json(res)),
        "informe.md": informe_md(res),
        "mensajes_cobro.md": mensajes.mensajes_md(res, borradores),
        "informe.html": informe_html(res),
        "descartados.json": texto_json(descartados_json(res)),
        "ambiguas.json": texto_json(res.ambiguas),
    }
