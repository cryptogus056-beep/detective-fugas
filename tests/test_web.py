"""La web: archivos al dia, privacidad (no envia datos) y, si hay navegador, prueba real de punta a punta."""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile

import pytest

CDN_PERMITIDO = "https://cdn.jsdelivr.net/pyodide/"
URL = re.compile(r"""(?:https?:)?//[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\s"'<>)]*""")
ENVIO_DE_DATOS = ["XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "<form", "method:", "body:",
                  "FormData", "postMessage", "<iframe", "<img", "document.cookie", "localStorage"]


@pytest.fixture(scope="module")
def web(raiz):
    carpeta = raiz / "web"
    assert (carpeta / "index.html").exists(), "falta web/: corre python scripts/construir_web.py"
    return carpeta


def test_la_web_esta_al_dia_con_el_codigo_probado(raiz, web):
    sys.path.insert(0, str(raiz / "scripts"))
    try:
        import construir_web
    finally:
        sys.path.pop(0)
    problemas = construir_web.comprobar(web)
    assert not problemas, f"{problemas}. Corre: python scripts/construir_web.py"


def test_archivos_necesarios_y_ninguno_de_mas(web):
    for nombre in ("index.html", "estilo.css", "app.js", "puente.py", "py/manifiesto.json", "py/detective/auditoria.py",
                   "py/detective/reglas/diferencia_iva.py", "py/plantillas/banco_monto_con_signo.json",
                   "demo/informe_cuerpo.html", "demo/hallazgos.json", "demo/informe.md", "demo/mensajes_cobro.md",
                   "demo/plan_cuerpo.html", "demo/borradores.json", "llenar/cotizaciones.csv", "llenar/equipo.csv",
                   "llenar/licencias.csv",
                   "demo/datos/cartola_banco.csv", "demo/datos/cotizaciones.xlsx", "demo/datos/config.json"):
        assert (web / nombre).is_file(), f"falta web/{nombre}"
    assert not (web / "py" / "detective" / "llm.py").exists(), "la web no debe llevar el módulo que llama a una API"
    assert not [p for p in web.rglob("*") if p.is_dir() and p.name.startswith("_")], "se copió una carpeta privada"
    manifiesto = json.loads((web / "py" / "manifiesto.json").read_text(encoding="utf-8"))
    assert all((web / "py" / ruta).is_file() for ruta in manifiesto["codigo"])
    assert sorted(manifiesto["demo"]) == sorted(p.name for p in (web / "demo" / "datos").iterdir())
    if manifiesto["xlsx"]:
        nombres = zipfile.ZipFile(web / "vendor" / "openpyxl.zip").namelist()
        assert "openpyxl/__init__.py" in nombres and "et_xmlfile/__init__.py" in nombres
        assert any(n.startswith("licencias/") for n in nombres), "falta la licencia de la librería incluida"


def test_textos_obligatorios_de_la_pagina(web):
    pagina = (web / "index.html").read_text(encoding="utf-8")
    assert '<html lang="es">' in pagina and "viewport" in pagina
    for texto in ("Detective de Fugas Pyme", "La plata que se pierde no hace ruido: hay que contarla fila por fila.",
                  "Datos 100% ficticios", "Tus archivos no salen de tu computador", "Usar mis archivos",
                  "Cómo se usa, en 3 pasos", "¿Qué hago aquí?", "¿Qué hago ahora?", "Preguntas frecuentes",
                  "Paso 1: junta y sube tus archivos", "Paso 2: revisa", "Paso 3: tu informe"):
        assert texto in pagina, texto
    demo = (web / "demo" / "informe_cuerpo.html").read_text(encoding="utf-8")
    assert demo.count('<section class="fuga"') == 12 and "Resumen en 5 líneas" in demo
    assert demo.count("Este informe no reemplaza a tu contador") == 1


def test_privacidad_la_web_no_llama_a_ningun_dominio_fuera_del_cdn_de_pyodide(web):
    revisados = 0
    for ruta in sorted(web.rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in {".html", ".js", ".css", ".py", ".json", ".md"}:
            continue
        revisados += 1
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        for url in URL.findall(texto):
            assert url.startswith(CDN_PERMITIDO), f"{ruta.relative_to(web)} apunta a {url}"
    assert revisados > 30
    codigo = (web / "app.js").read_text(encoding="utf-8") + (web / "index.html").read_text(encoding="utf-8")
    for peligro in ENVIO_DE_DATOS:
        assert peligro not in codigo, f"la página usa {peligro}"
    assert re.findall(r"fetch\(([^,)]*)", codigo) == ["ruta", "ruta"], "solo se descargan archivos propios, con GET"
    for ruta in sorted((web / "py").rglob("*.py")) + [web / "puente.py"]:
        texto = ruta.read_text(encoding="utf-8")
        for peligro in ("urllib", "requests", "socket", "http.client", "smtplib", "pyodide.http", "pyfetch"):
            assert peligro not in texto, f"{ruta.relative_to(web)} usa {peligro}"
        assert not re.search(r"^\s*(import js\b|from js\b)", texto, flags=re.M), f"{ruta.relative_to(web)} usa el puente a JavaScript"


def test_politica_de_seguridad_del_navegador_impide_enviar_datos_a_otros_sitios(web):
    pagina = (web / "index.html").read_text(encoding="utf-8")
    politica = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', pagina).group(1)
    reglas = dict(parte.strip().split(" ", 1) for parte in politica.split(";") if " " in parte.strip())
    assert reglas["default-src"] == "'self'"
    assert reglas["connect-src"] == f"'self' {CDN_PERMITIDO}"
    assert reglas["form-action"] == "'none'"
    assert "unsafe-eval'" not in reglas["script-src"].replace("'wasm-unsafe-eval'", "")


# --------------------------------------------------------------------------- navegador real (opcional)

def _hay_playwright() -> bool:
    if not shutil.which("node") or os.environ.get("DETECTIVE_SIN_NAVEGADOR"):
        return False
    return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode == 0


def _hay_cdn() -> bool:
    try:
        with urllib.request.urlopen(CDN_PERMITIDO.replace("/pyodide/", "/npm/pyodide/package.json"), timeout=8):
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def navegador(raiz, web):
    if not _hay_playwright():
        pytest.skip("sin Node o Playwright: se salta la prueba con navegador real")
    if not _hay_cdn():
        pytest.skip("sin acceso al CDN de Pyodide: se salta la prueba con navegador real")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    servidor = subprocess.Popen([sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1", "-d", str(web)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", puerto), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        corrida = subprocess.run(["node", str(raiz / "tests" / "navegador" / "prueba_web.cjs"),
                                  f"http://127.0.0.1:{puerto}/", str(raiz / "data" / "demo_b")],
                                 capture_output=True, text=True, timeout=240)
        assert corrida.returncode == 0, corrida.stderr[-2000:]
        yield json.loads(corrida.stdout)
    finally:
        servidor.terminate()


def test_navegador_la_demo_se_ve_sin_errores_y_sin_cargar_nada_externo(navegador):
    assert navegador["titulo"] == "Detective de Fugas Pyme"
    assert "Tus archivos no salen de tu computador" in navegador["cabecera"]
    assert "Datos 100% ficticios" in navegador["aviso_demo"] and "12 de 12" in navegador["aviso_demo"]
    assert "todavía no se ha probado con archivos reales" in navegador["aviso_demo"]
    assert navegador["fugas_demo"] == 12 and navegador["titulo_informe"].startswith("Informe de fugas:")
    assert navegador["dominios_solo_demo"] == ["127.0.0.1"], "ver la demo no debe descargar nada de otros sitios"
    assert navegador["errores"] == [] and navegador["fallidas"] == []


def test_navegador_subir_demo_b_da_el_mismo_resultado_que_la_cli(navegador, raiz, tmp_path):
    cli = subprocess.run([sys.executable, "-m", "detective", "auditar", "--datos", "data/demo_b", "--salida", str(tmp_path)],
                         cwd=raiz, capture_output=True, text=True)
    assert cli.returncode == 0, cli.stdout
    esperado = json.loads((tmp_path / "hallazgos.json").read_text(encoding="utf-8"))
    obtenido = json.loads(navegador["hallazgos_json"])
    esperado.pop("generado_en"), obtenido.pop("generado_en")
    assert obtenido == esperado
    assert navegador["informe_md"] == (tmp_path / "informe.md").read_text(encoding="utf-8")
    assert navegador["mensajes_md"] == (tmp_path / "mensajes_cobro.md").read_text(encoding="utf-8")
    roles = {nombre: rol for nombre, rol, _ in navegador["roles"]}
    assert roles == {"config.json": "config", "equipo.csv": "equipo", "licencias.csv": "licencias",
                     "movimientos_cuenta.csv": "banco", "presupuestos.csv": "cotizaciones",
                     "rcv_compras.csv": "rcv_compras", "rcv_ventas.csv": "rcv_ventas", "ventas_transbank.csv": "pos"}
    assert navegador["descargas"] == ["informe.html", "mensajes_cobro.md", "informe.md", "hallazgos.json"]


def test_navegador_la_guia_acompana_todo_el_proceso(navegador):
    assert navegador["plan_demo_grupos"] == 4 and navegador["mensajes_demo"] == 5         # el ejemplo trae plan y mensajes
    assert navegador["cobertura"] == "Qué puedo revisar con lo que subiste: 5 de 5 tipos de fuga"
    assert navegador["tarjetas_listas"] == 7                                               # cada tipo de archivo se marca
    assert navegador["plan_grupos"] == 4 and navegador["mensajes_tarjetas"] == 5
    assert navegador["etapas"] == ["hecho", "hecho", "actual"]                             # el indicador avanza al paso 3
    assert navegador["plan_lleva_al_detalle"] is True


def test_navegador_sin_archivo_de_empresa_la_pagina_pregunta_los_datos(navegador):
    assert navegador["formulario_oculto_con_config"] is True and navegador["formulario_visible_sin_config"] is True
    assert navegador["titulo_sin_config"] == "Informe de fugas: Mi Pyme de Prueba SpA"
    assert "31/10/2026" in navegador["periodo_sin_config"]


def test_navegador_la_tabla_no_se_sale_de_su_recuadro_en_ningun_ancho(navegador):
    """Regresion: con 9 columnas la tabla quedo mas ancha que el recuadro en pantallas de escritorio."""
    assert navegador["desbordes"] == []


def test_navegador_no_envia_datos_y_lee_excel(navegador):
    assert navegador["metodos"] == ["GET"], "la página solo debe descargar, nunca enviar"
    assert set(navegador["dominios"]) <= {"127.0.0.1", "cdn.jsdelivr.net"}
    assert navegador["xlsx"] is True
    assert navegador["estado_demo"].startswith("Listo: recalculado en tu navegador. 12 fugas")   # usa el XLSX de la demo
    assert navegador["fugas_demo_recalculada"] == 12
