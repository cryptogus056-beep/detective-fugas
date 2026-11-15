"""Salidas de la auditoria: hallazgos.json (contrato 6.1 de la spec) y sus acompanantes."""
from __future__ import annotations

import json


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


def archivos_de_salida(res) -> dict:
    """nombre de archivo -> contenido en texto. Lo usan la CLI y la web."""
    return {
        "hallazgos.json": texto_json(a_json(res)),
        "descartados.json": texto_json(descartados_json(res)),
        "ambiguas.json": texto_json(res.ambiguas),
    }
