"""El detector no puede conocer las respuestas ni estar hecho a la medida de la demo."""
import re

from detective.__main__ import leer_carpeta

CARPETAS = ["detective", "web", "plantillas"]
PROHIBIDO = ["_respuestas", "respuestas.json"]
# Nombres propios de los datasets de ejemplo: si aparecen en el codigo, hay una regla hecha a la medida.
PROPIO_DE_LA_DEMO = ["demo_b", "data/demo", "climatizacion", "cartola_banco", "movimientos_cuenta", "canva",
                     "workspace", "dropbox", r"cot-\d", r"pre-\d", "ficticia", "ficticio"]


def _archivos(raiz, carpeta, extensiones):
    base = raiz / carpeta
    if not base.exists():
        return []
    return [p for p in sorted(base.rglob("*")) if p.is_file() and p.suffix.lower() in extensiones]


def test_nada_del_detector_ni_de_la_web_menciona_la_llave(raiz):
    revisados = 0
    for carpeta in CARPETAS:
        for ruta in _archivos(raiz, carpeta, {".py", ".json", ".js", ".mjs", ".html", ".css", ".md", ".txt", ".csv"}):
            texto = ruta.read_text(encoding="utf-8", errors="replace")
            for cadena in PROHIBIDO:
                assert cadena not in texto, f"{ruta.relative_to(raiz)} menciona {cadena}"
            revisados += 1
    assert revisados > 20


def test_no_hay_carpeta_de_respuestas_copiada_en_la_web(raiz):
    assert not [p for p in (raiz / "web").rglob("*") if "respuestas" in p.name.lower()] if (raiz / "web").exists() else True


def test_el_codigo_y_las_plantillas_no_nombran_nada_propio_de_la_demo(raiz):
    for ruta in _archivos(raiz, "detective", {".py"}) + _archivos(raiz, "plantillas", {".json"}):
        texto = ruta.read_text(encoding="utf-8").lower()
        for patron in PROPIO_DE_LA_DEMO:
            assert not re.search(patron, texto), f"{ruta.relative_to(raiz)} contiene '{patron}': ¿regla a la medida?"


def test_la_cli_solo_lee_el_primer_nivel_de_la_carpeta(tmp_path):
    (tmp_path / "banco.csv").write_text("a;b\n1;2\n", encoding="utf-8")
    (tmp_path / ".oculto.csv").write_text("x", encoding="utf-8")
    interna = tmp_path / "carpeta_interna"
    interna.mkdir()
    (interna / "secreto.json").write_text("{}", encoding="utf-8")
    assert [e.nombre for e in leer_carpeta(tmp_path)] == ["banco.csv"]
