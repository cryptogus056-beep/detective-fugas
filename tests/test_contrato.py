"""Contrato de hallazgos.json (seccion 6.1 de la spec) y reglas generales de la auditoria."""
import datetime as dt
import io
import json

import pytest
from conftest import ANA, banco, correr, cotizaciones, rcv

from detective.auditoria import Entrada, auditar
from detective.informe import a_json, archivos_de_salida
from detective.lectores import ErrorLectura
from detective.reglas import TIPOS

CAMPOS = {"id", "tipo", "titulo", "descripcion", "monto_clp", "impacto_clp", "impacto_mensual_clp", "recurrente",
          "confianza", "evidencia", "accion_sugerida", "verificado"}


def demo(raiz, plantillas, carpeta):
    entradas = [Entrada(p.name, p.read_bytes()) for p in sorted((raiz / carpeta).iterdir()) if p.is_file()]
    return auditar(entradas, plantillas)


@pytest.mark.parametrize("carpeta", ["data/demo", "data/demo_b"])
def test_contrato_de_hallazgos_json(raiz, plantillas, carpeta):
    datos = json.loads(archivos_de_salida(demo(raiz, plantillas, carpeta))["hallazgos.json"])
    assert {"empresa", "fecha_corte", "generado_en", "version_detector", "archivos_leidos", "hallazgos",
            "no_revisado"} <= set(datos)
    assert datos["empresa"] == "Climatizacion Austral Ficticia SpA" and datos["fecha_corte"] == "2026-10-31"
    dt.datetime.fromisoformat(datos["generado_en"])
    for a in datos["archivos_leidos"]:
        assert {"archivo", "rol", "plantilla", "filas"} <= set(a) and isinstance(a["filas"], int)
    hallazgos = datos["hallazgos"]
    assert hallazgos and [h["id"] for h in hallazgos] == [f"H{n:02d}" for n in range(1, len(hallazgos) + 1)]
    mensual = [h["impacto_mensual_clp"] for h in hallazgos]
    assert mensual == sorted(mensual, reverse=True)                       # ordenado por impacto mensual
    for h in hallazgos:
        assert CAMPOS <= set(h), h["id"]
        assert h["tipo"] in TIPOS and h["confianza"] in ("alta", "media", "baja") and h["verificado"] is True
        assert all(isinstance(h[c], int) and h[c] > 0 for c in ("monto_clp", "impacto_clp", "impacto_mensual_clp"))
        assert isinstance(h["recurrente"], bool) and h["accion_sugerida"].endswith(".")
        assert h["evidencia"], "regla de oro: todo hallazgo trae evidencia"
        completas = 0
        for e in h["evidencia"]:
            assert {"archivo", "fila", "fecha", "monto_clp", "detalle"} <= set(e)
            assert isinstance(e["archivo"], str) and isinstance(e["fila"], int) and e["fila"] >= 2 and e["detalle"]
            if e["fecha"] is not None:
                dt.date.fromisoformat(e["fecha"])
            completas += e["fecha"] is not None and isinstance(e["monto_clp"], int)
        assert completas >= 1


@pytest.mark.parametrize("carpeta", ["data/demo", "data/demo_b"])
def test_ninguna_fila_respalda_dos_hallazgos_del_mismo_tipo(raiz, plantillas, carpeta):
    vistas = set()
    for h in demo(raiz, plantillas, carpeta).hallazgos:
        for e in h.evidencia:
            llave = (h.tipo, e.archivo, e.fila)
            assert llave not in vistas, f"{llave} repetida: una fuga se estaria contando dos veces"
            vistas.add(llave)


def test_mismo_contenido_en_xlsx_y_csv_se_usa_una_sola_vez_y_se_prefiere_el_xlsx(raiz, plantillas):
    res = demo(raiz, plantillas, "data/demo")
    usados = {a["archivo"]: a["usado"] for a in res.archivos_leidos}
    assert usados["cotizaciones.xlsx"] is True and usados["cotizaciones.csv"] is False
    assert any("traen las mismas filas" in a for a in res.avisos)
    assert not any(e.archivo == "cotizaciones.csv" for h in res.hallazgos for e in h.evidencia)


def test_dos_cartolas_distintas_del_mismo_rol_se_suman():
    res = correr({"agosto.csv": banco([("10/08/2026", f"TRANSF. DE {ANA} ANA", 59500)]),
                  "septiembre.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 71400)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    assert sorted(h.evidencia[0].archivo for h in res.hallazgos) == ["agosto.csv", "septiembre.csv"]


def test_archivo_que_no_calza_con_ninguna_plantilla_no_bota_la_auditoria_pero_se_informa():
    res = correr({"banco.csv": banco([("10/08/2026", f"TRANSF. DE {ANA} ANA", 59500)]),
                  "raro.csv": "Dia|Concepto|Importe\n01/02/2026|Algo|100\n", "notas.txt": "hola"})
    assert [a["archivo"] for a in res.archivos_leidos] == ["banco.csv"]
    assert any("raro.csv" in n and "plantillas/_ejemplo.json" in n for n in res.no_revisado)
    assert any("notas.txt" in n for n in res.no_revisado)


def test_sin_ningun_archivo_reconocible_el_error_es_claro():
    with pytest.raises(ErrorLectura, match="No reconocí ningún archivo"):
        correr({"raro.csv": "Dia|Concepto|Importe\n01/02/2026|Algo|100\n"})


def test_sin_config_usa_valores_por_defecto_y_deduce_el_periodo():
    res = correr({"banco.csv": banco([("03/08/2026", "COMISION", -990), ("20/10/2026", "COMISION", -990)]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "10/08/2026", 100000)])}, config=False)
    c = res.config
    assert (c.periodo_desde.isoformat(), c.fecha_corte.isoformat(), c.meses) == ("2026-08-03", "2026-10-20", 3)
    assert any("No había config.json" in a for a in res.avisos) and any("fecha de corte" in a for a in res.avisos)
    assert [h.tipo for h in res.hallazgos] == ["pago_pendiente_30d"]


def test_el_usuario_puede_forzar_o_ignorar_el_rol_de_un_archivo():
    archivos = {"banco.csv": banco([("10/08/2026", f"TRANSF. DE {ANA} ANA", 59500)]),
                "cot.csv": cotizaciones([("C-1", "01/08/2026", "Ana", ANA, 100000, "Aceptada", "02/08/2026")]),
                "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])}
    assert len(correr(archivos).hallazgos) == 2
    sin_cot = correr(archivos, roles_forzados={"cot.csv": "ignorar"})
    assert [h.tipo for h in sin_cot.hallazgos] == ["abono_sin_documento"]
    mal = correr(archivos, roles_forzados={"cot.csv": "banco"})
    assert any("cot.csv" in n and "para el tipo 'banco'" in n for n in mal.no_revisado)


def test_filas_ilegibles_aparecen_en_lo_que_no_pude_revisar():
    texto = banco([("10/08/2026", f"TRANSF. DE {ANA} ANA", 59500)]) + "TOTAL;;;59.500\n"
    res = correr({"banco.csv": texto})
    assert any("no pude interpretar 1 fila" in n and "5 (sin fecha)" in n for n in res.no_revisado)
