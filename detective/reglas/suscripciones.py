"""4.4 Pagas software de mas: suscripcion cobrada dos veces o licencia de alguien que ya se fue."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from ..normalizar import clave_texto, contiene_palabras, formato_clp, formato_fecha, meses_entre, normalizar_glosa
from . import Evidencia, Hallazgo, evidencia_de

TIPO = "suscripcion_duplicada_o_huerfana"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def cobros_por_servicio(ctx) -> dict:
    """servicio (tal como esta en licencias) -> cargos del banco de ese servicio.

    Un cargo es de un servicio si su glosa contiene todas las palabras del nombre del
    servicio. Si calza con dos servicios, gana el de nombre mas largo.
    """
    servicios = {}
    for lic in ctx.datos.licencias:
        servicios.setdefault(clave_texto(lic.servicio), lic.servicio)
    cobros = defaultdict(list)
    for m in ctx.datos.movimientos:
        if m.monto >= 0:
            continue
        glosa = normalizar_glosa(m.descripcion)
        calzan = [s for s in servicios.values() if contiene_palabras(glosa, s)]
        if calzan:
            cobros[max(calzan, key=lambda s: len(normalizar_glosa(s).split()))].append(m)
    return cobros


def _duplicadas(ctx, cobros: dict) -> list:
    config, hallazgos = ctx.config, []
    for servicio, cargos in sorted(cobros.items()):
        licencias = [l for l in ctx.datos.licencias if clave_texto(l.servicio) == clave_texto(servicio)]
        asientos = sum(1 for l in licencias if l.estado == "activo")
        por_monto = defaultdict(lambda: defaultdict(list))
        for m in cargos:
            por_monto[-m.monto][(m.fecha.year, m.fecha.month)].append(m)
        for monto, por_mes in sorted(por_monto.items()):
            repetidos = {mes: filas for mes, filas in por_mes.items() if len(filas) >= 2}
            if len(repetidos) < 2:
                continue
            cobros_al_mes = min(len(filas) for filas in repetidos.values())
            exceso = cobros_al_mes - asientos
            if exceso <= 0:
                continue
            impacto = sum(max(len(filas) - asientos, 0) * monto for filas in repetidos.values())
            filas = sorted((m for fs in repetidos.values() for m in fs), key=lambda m: (m.fecha, m.origen.fila))
            dias = sorted({m.fecha.day for m in filas})
            texto_dias = " y ".join([", ".join(str(d) for d in dias[:-1]), str(dias[-1])]) if len(dias) > 1 else str(dias[0])
            evidencia = [evidencia_de(m, m.fecha, -m.monto, m.descripcion) for m in filas]
            evidencia += [evidencia_de(l, None, l.costo_mensual, f"Licencia {l.servicio} de {l.usuario} ({l.plan})".replace(" ()", ""))
                          for l in licencias if l.estado == "activo"]
            veces = "dos veces" if cobros_al_mes == 2 else f"{cobros_al_mes} veces"
            licencia_txt = ("hay una sola licencia registrada" if asientos == 1 else "no hay ninguna licencia activa registrada"
                            if asientos == 0 else f"solo hay {asientos} licencias registradas")
            hallazgos.append(Hallazgo(
                tipo=TIPO, subtipo="duplicada", titulo=f"{servicio} se cobra {veces} al mes",
                descripcion=(f"{servicio} se cobra {veces} al mes por {formato_clp(monto)} (los días {texto_dias}) "
                             f"y {licencia_txt}. Pasó en {len(repetidos)} meses del periodo. "
                             f"Pagas {formato_clp(monto * exceso)} de más cada mes."),
                monto_clp=monto, impacto_clp=impacto, impacto_mensual_clp=monto * exceso, recurrente=True,
                evidencia=evidencia,
                accion_sugerida=f"Entra a la cuenta de {servicio}, revisa por qué hay más de un cobro y cancela el que sobra",
                datos={"servicio": servicio, "cobros_al_mes": cobros_al_mes, "asientos": asientos,
                       "meses": len(repetidos)}))
    return hallazgos


def _meses_despues_de(salida, config) -> int:
    """Meses del periodo en que la persona ya no estaba."""
    if salida is None or salida < config.periodo_desde:
        return config.meses
    siguiente = (salida.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    if siguiente > config.periodo_hasta:
        return 0
    return meses_entre(siguiente, config.periodo_hasta)


def _huerfanas(ctx, cobros: dict) -> list:
    config, hallazgos = ctx.config, []
    por_email = {clave_texto(p.email): p for p in ctx.datos.personas if p.email}
    por_nombre = {clave_texto(p.nombre): p for p in ctx.datos.personas if p.nombre}
    for lic in ctx.datos.licencias:
        if lic.estado != "activo":
            continue
        persona = por_email.get(clave_texto(lic.usuario)) or por_nombre.get(clave_texto(lic.usuario))
        if not persona or persona.estado != "inactivo":
            continue
        salida = persona.fecha_salida
        if salida and salida >= config.fecha_corte:
            continue
        meses = _meses_despues_de(salida, config)
        if meses <= 0:
            continue
        quien = persona.nombre or persona.email
        cargos = sorted((m for m in cobros.get(_nombre_servicio(lic, cobros), [])
                         if config.periodo_desde <= m.fecha <= config.periodo_hasta and (not salida or m.fecha > salida)),
                        key=lambda m: (m.fecha, m.origen.fila))
        if not cargos:
            ctx.avisos.append(
                f"La licencia de {lic.servicio} de {lic.usuario} sigue activa y {quien} ya no está en la empresa, "
                f"pero no encontré el cobro de {lic.servicio} en el banco. Sin una fila con fecha y monto no lo "
                "cuento como fuga: revísalo a mano.")
            continue
        costo = lic.costo_mensual
        if not costo:
            ctx.avisos.append(f"La licencia de {lic.servicio} de {lic.usuario} no trae costo mensual: "
                              "no pude calcular cuánto pierdes. Revísala a mano.")
            continue
        se_fue = f"dejó la empresa el {formato_fecha(salida)}" if salida else "figura como inactivo en tu equipo"
        evidencia = [evidencia_de(m, m.fecha, -m.monto, m.descripcion) for m in cargos]
        evidencia.append(evidencia_de(lic, None, costo, f"Licencia {lic.servicio} de {lic.usuario}, estado activa"))
        evidencia.append(Evidencia(persona.origen.archivo, persona.origen.fila, salida, None,
                                   f"{quien}, inactivo" + (f", salida {formato_fecha(salida)}" if salida else ""),
                                   persona.origen.crudo))
        hallazgos.append(Hallazgo(
            tipo=TIPO, subtipo="huerfana", titulo=f"Pagas la licencia de {lic.servicio} de alguien que ya se fue",
            descripcion=(f"La licencia de {lic.servicio} de {lic.usuario} sigue activa y cuesta "
                         f"{formato_clp(costo)} al mes, pero {quien} {se_fue}. En el periodo la pagaste "
                         f"{meses} {'mes' if meses == 1 else 'meses'} sin que nadie la use."),
            monto_clp=costo, impacto_clp=costo * meses, impacto_mensual_clp=costo, recurrente=True,
            evidencia=evidencia,
            accion_sugerida=f"Da de baja la licencia de {lic.usuario} en {lic.servicio}",
            datos={"servicio": lic.servicio, "usuario": lic.usuario, "persona": quien, "meses": meses,
                   "fecha_salida": salida.isoformat() if salida else None}))
    return hallazgos


def _nombre_servicio(lic, cobros: dict):
    for servicio in cobros:
        if clave_texto(servicio) == clave_texto(lic.servicio):
            return servicio
    return lic.servicio


def detectar(ctx) -> list:
    if "licencias" not in ctx.datos.roles or "banco" not in ctx.datos.roles:
        return []
    cobros = cobros_por_servicio(ctx)
    hallazgos = _duplicadas(ctx, cobros)
    if "equipo" in ctx.datos.roles:
        hallazgos += _huerfanas(ctx, cobros)
    return hallazgos
