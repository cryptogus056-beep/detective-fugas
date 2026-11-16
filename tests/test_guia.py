"""La guía de uso: plan de acción y planillas para llenar."""
import json

import pytest
from conftest import ANA, banco, correr, rcv

from detective.auditoria import Entrada, auditar
from detective.config import cargar_config
from detective.informe import plan_de_accion, plan_html
from detective.modelo import cargar_registros
from detective.plantillas import reconocer_archivo


@pytest.fixture(scope="module")
def demo(raiz, plantillas):
    entradas = [Entrada(p.name, p.read_bytes()) for p in sorted((raiz / "data/demo").iterdir()) if p.is_file()]
    return auditar(entradas, plantillas)


def test_el_plan_agrupa_cada_fuga_una_sola_vez_y_en_orden_de_accion(demo):
    grupos = plan_de_accion(demo)
    assert [g["clave"] for g in grupos] == ["cobrar", "documentos", "software", "iva"]
    ids = [it["id"] for g in grupos for it in g["items"]]
    assert sorted(ids) == sorted(h.id for h in demo.hallazgos)                     # ninguna falta ni se repite
    assert sum(g["total"] for g in grupos) == sum(h.impacto_clp for h in demo.hallazgos)
    cobrar = grupos[0]
    assert cobrar["total"] == 3373650 and all("mensaje M" in " ".join(it["notas"]) for it in cobrar["items"])
    for g in grupos:
        montos = [it["monto"] for it in g["items"]]
        assert montos == sorted(montos, reverse=True)
    assert any(it["confirmar"] for it in grupos[1]["items"])                        # la de seguridad media se marca


def test_plan_html_enlaza_al_detalle_y_escapa_el_texto(demo):
    html = plan_html(demo)
    assert html.count('class="grupo ') == 4 and 'href="#H01" data-id="H01"' in html
    res = correr({"banco.csv": banco([("10/09/2026", "TRANSF <b>raro</b>", 80000)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    assert "<b>raro</b>" not in plan_html(res) and "&lt;b&gt;raro&lt;/b&gt;" in plan_html(res)


def test_sin_fugas_el_plan_lo_dice():
    res = correr({"banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 59500)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "10/09/2026", 50000)])})
    assert plan_de_accion(res) == [] and "No encontré fugas" in plan_html(res)


@pytest.mark.parametrize("nombre, rol, fila", [
    ("cotizaciones.csv", "cotizaciones", "C-1;01/09/2026;Cliente SpA;76.000.001-9;Mantención;100.000;;;Aceptada;02/09/2026"),
    ("licencias.csv", "licencias", "Canva Pro;ana@x.cl;Pro;$12.990;Activa"),
    ("equipo.csv", "equipo", "Ana Paz;ana@x.cl;Ventas;Inactivo;01/03/2024;31/07/2026"),
])
def test_las_planillas_para_llenar_se_reconocen_vacias_y_llenas(raiz, plantillas, nombre, rol, fila):
    vacia = (raiz / "plantillas_para_llenar" / nombre).read_bytes()
    assert vacia.startswith(b"\xef\xbb\xbf"), "con BOM para que Excel muestre bien las tildes"
    assert reconocer_archivo(nombre, vacia, plantillas).plantilla.rol == rol
    llena = vacia + (fila + "\r\n").encode("utf-8")
    registros = cargar_registros(reconocer_archivo(nombre, llena, plantillas), cargar_config(None)).registros
    assert len(registros) == 1
    if rol == "cotizaciones":
        assert (registros[0].neto, registros[0].total, registros[0].estado) == (100000, 119000, "aceptada")


def test_una_planilla_de_licencias_llena_encuentra_la_licencia_huerfana(raiz):
    cabeza = (raiz / "plantillas_para_llenar")
    res = correr({
        "banco.csv": banco([(f"02/{m:02d}/2026", "COMPRA TARJETA CANVA* PRO", -12990) for m in (8, 9, 10)]),
        "licencias.csv": (cabeza / "licencias.csv").read_bytes() + "Canva Pro;bruno@x.cl;Pro;12.990;Activa\r\n".encode(),
        "equipo.csv": (cabeza / "equipo.csv").read_bytes() + "Bruno Vera;bruno@x.cl;Técnico;Inactivo;01/02/2022;31/07/2026\r\n".encode(),
    })
    [h] = res.hallazgos
    assert h.subtipo == "huerfana" and h.impacto_clp == 3 * 12990
