"""informe.md e informe.html cumplen la seccion 6.2 de la spec."""
import re

import pytest
from conftest import ANA, banco, correr, cotizaciones, rcv

from detective.auditoria import Entrada, auditar
from detective.informe import PIE, archivos_de_salida, construir, informe_html, informe_md

SECCIONES = ["# Informe de fugas:", "## Resumen en 5 líneas", "## Fugas encontradas", "## Detalle de cada fuga",
             "## Cómo verificar este informe", "## Lo que no pude revisar", PIE]


@pytest.fixture(scope="module", params=["data/demo", "data/demo_b"])
def demo(request, raiz, plantillas):
    entradas = [Entrada(p.name, p.read_bytes()) for p in sorted((raiz / request.param).iterdir()) if p.is_file()]
    return auditar(entradas, plantillas)


def seccion(texto: str, titulo: str) -> str:
    inicio = texto.index(titulo) + len(titulo)
    fin = texto.find("\n## ", inicio)
    return texto[inicio:fin if fin != -1 else len(texto)]


def test_las_siete_partes_en_orden(demo):
    md = informe_md(demo)
    posiciones = [md.index(s) for s in SECCIONES]
    assert posiciones == sorted(posiciones)
    assert md.startswith("# Informe de fugas: Climatizacion Austral Ficticia SpA\n")
    assert "Periodo revisado: 01/08/2026 al 31/10/2026 (3 meses)" in md
    assert md.rstrip().endswith("Este informe no reemplaza a tu contador. Montos en CLP.")


def test_el_resumen_tiene_exactamente_cinco_lineas(demo):
    lineas = [l for l in seccion(informe_md(demo), "## Resumen en 5 líneas").splitlines() if l.strip()]
    assert len(lineas) == 5
    assert [l[:3] for l in lineas] == ["1. ", "2. ", "3. ", "4. ", "5. "]
    total = sum(h.impacto_clp for h in demo.hallazgos)
    assert f"${total:,}".replace(",", ".") in lineas[0]                         # total en juego
    assert "12 fugas" in lineas[1] and "3 cotizaciones aceptadas sin facturar" in lineas[1]
    assert demo.hallazgos[0].id in lineas[2]                                    # la mas grande
    assert "esta semana" in lineas[3] and "M01" in lineas[3]                    # que hacer primero
    cobrable = sum(h.impacto_clp for h in demo.hallazgos if h.tipo in ("cotizacion_sin_cobro", "pago_pendiente_30d"))
    assert f"recuperas ${cobrable:,}".replace(",", ".") in lineas[4]            # cuanto se recupera


def test_la_tabla_esta_ordenada_por_impacto_mensual_y_trae_evidencia(demo):
    filas = [l for l in seccion(informe_md(demo), "## Fugas encontradas").splitlines() if re.match(r"\| \d+ \|", l)]
    assert len(filas) == len(demo.hallazgos) == 12
    mensual = []
    for n, (fila, h) in enumerate(zip(filas, demo.hallazgos), start=1):
        celdas = [c.strip() for c in fila.strip("|").split(" | ")]
        assert len(celdas) == 7 and celdas[0] == str(n)
        mensual.append(int(re.sub(r"\D", "", celdas[4].split(" ")[0])))
        assert re.search(r"`[^`]+` fila \d+, \d{2}/\d{2}/\d{4}, \$[\d.]+", celdas[5]), celdas[5]
        assert celdas[6] == h.accion_sugerida
    assert mensual == sorted(mensual, reverse=True)
    assert mensual == [h.impacto_mensual_clp for h in demo.hallazgos]


def test_el_detalle_copia_la_fila_original_tal_cual(demo, raiz):
    md = informe_md(demo)
    for h in demo.hallazgos:
        assert f"### {h.id} · {h.titulo}" in md
        for e in h.evidencia:
            assert e.fila_original and f"    {e.fila_original}" in md
    cartola = next(e for h in demo.hallazgos for e in h.evidencia if e.archivo.endswith(".csv") and "cuenta" in e.archivo or e.archivo.startswith("cartola"))
    carpeta = "data/demo" if cartola.archivo.startswith("cartola") else "data/demo_b"
    lineas = (raiz / carpeta / cartola.archivo).read_text(encoding="utf-8-sig").splitlines()
    assert lineas[cartola.fila - 1] == cartola.fila_original          # la fila citada es la linea fisica del archivo


def test_formato_de_montos_y_fechas(demo):
    md = informe_md(demo)
    assert not re.search(r"\$\d{4,}", md), "hay un monto sin punto de miles"
    assert not re.search(r"\$ \d", md)
    cuerpo = re.sub(r"```text.*?```", "", md, flags=re.S)             # fuera de las filas originales copiadas
    assert not re.search(r"\b20\d\d-\d\d-\d\d\b", cuerpo), "hay una fecha en formato aaaa-mm-dd"


def test_html_dice_lo_mismo_y_no_usa_recursos_externos(demo):
    pagina = informe_html(demo)
    assert pagina.startswith("<!DOCTYPE html>") and '<html lang="es">' in pagina
    assert not re.search(r"https?://", pagina) and "<script" not in pagina and "<link" not in pagina
    modelo = construir(demo)
    assert pagina.count('<section class="fuga"') == 12 and pagina.count("<tr>") == 13
    for etiqueta, _ in modelo["resumen"]:
        assert f"<strong>{etiqueta}:</strong>" in pagina
    assert PIE in pagina and "viewport" in pagina


def test_html_escapa_texto_peligroso():
    res = correr({"banco.csv": banco([("10/09/2026", "TRANSF <script>alert(1)</script> & CIA", 80000)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    pagina = informe_html(res)
    assert "<script>" not in pagina and "&lt;script&gt;" in pagina and "&amp; CIA" in pagina


def test_lo_que_no_pude_revisar_aparece_en_el_informe():
    res = correr({"banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 80000)]),
                  "raro.csv": "Dia|Concepto|Importe\n01/02/2026|Algo|100\n"})
    no_revisado = seccion(informe_md(res), "## Lo que no pude revisar")
    assert "No había Registro de Ventas del SII" in no_revisado and "raro.csv" in no_revisado
    assert "No había archivo de licencias" in no_revisado


def test_informe_sin_fugas_sigue_teniendo_cinco_lineas_y_no_inventa_nada():
    res = correr({"banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 59500)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "10/09/2026", 50000)])})
    md = informe_md(res)
    assert not res.hallazgos
    assert len([l for l in seccion(md, "## Resumen en 5 líneas").splitlines() if l.strip()]) == 5
    assert "No encontré fugas con evidencia" in md and "$0" in md


def test_una_barra_vertical_en_un_texto_no_rompe_la_tabla():
    res = correr({"banco.csv": banco([("10/09/2026", "DEPOSITO | SUCURSAL 3", 80000)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    fila = next(l for l in informe_md(res).splitlines() if l.startswith("| 1 |"))
    assert "DEPOSITO \\| SUCURSAL 3" in fila


def test_salidas_completas(demo):
    salidas = archivos_de_salida(demo)
    assert set(salidas) == {"hallazgos.json", "informe.md", "mensajes_cobro.md", "informe.html", "descartados.json",
                            "ambiguas.json"}
    assert all(isinstance(v, str) and v.endswith("\n") for v in salidas.values())
