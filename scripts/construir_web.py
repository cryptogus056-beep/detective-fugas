#!/usr/bin/env python3
"""Arma la carpeta web/ con una copia del codigo probado, las plantillas y la demo.

    python scripts/construir_web.py              # copia todo y recalcula la demo
    python scripts/construir_web.py --comprobar  # no escribe: avisa si web/ quedo desactualizada

La pagina corre el MISMO paquete detective/ dentro del navegador (con Pyodide), asi que
web/ necesita una copia. Corre este script cada vez que cambies detective/ o plantillas/,
y antes de publicar la web.

Que copia:
    detective/*.py          -> web/py/detective/   (sin llm.py: la web no llama a ninguna API)
    plantillas/*.json       -> web/py/plantillas/
    data/demo/ (1er nivel)  -> web/demo/datos/     (solo los archivos de entrada)
    informe de la demo      -> web/demo/           (ya calculado, para mostrarlo al abrir)
    openpyxl (lector Excel) -> web/vendor/openpyxl.zip
"""
import argparse
import filecmp
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from detective import __version__  # noqa: E402
from detective.auditoria import Entrada, auditar  # noqa: E402
from detective.informe import archivos_de_salida, cuerpo_html  # noqa: E402
from detective.plantillas import cargar_plantillas  # noqa: E402

NO_COPIAR = {"llm.py"}
DEMO = RAIZ / "data" / "demo"
SALIDAS_DEMO = ("hallazgos.json", "informe.md", "mensajes_cobro.md", "informe.html")


def _copiar_texto(origen: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(origen.read_bytes())


def _sin_hora(texto: str) -> str:
    return "\n".join(l for l in texto.splitlines() if '"generado_en"' not in l)


def _escribir_estable(ruta: Path, contenido: str) -> None:
    """Escribe el archivo salvo que solo cambie la hora de generacion (evita cambios falsos en git)."""
    if ruta.exists() and _sin_hora(ruta.read_text(encoding="utf-8")) == _sin_hora(contenido):
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")


def _limpiar(carpeta: Path, vigentes: set) -> None:
    """Borra archivos que ya no corresponden (por ejemplo, un modulo que se elimino)."""
    if not carpeta.exists():
        return
    for ruta in sorted(carpeta.rglob("*")):
        if ruta.is_file() and ruta not in vigentes:
            ruta.unlink()


def _zip_openpyxl(destino: Path) -> bool:
    """Empaqueta openpyxl y et_xmlfile (ambos Python puro, licencia MIT) para leer XLSX en el navegador."""
    try:
        import et_xmlfile
        import openpyxl
    except ImportError:
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for paquete in (openpyxl, et_xmlfile):
            base = Path(paquete.__file__).resolve().parent
            for ruta in sorted(base.rglob("*")):
                if ruta.is_file() and ruta.suffix in (".py", ".txt", ".rst", ".md") and "__pycache__" not in ruta.parts:
                    info = zipfile.ZipInfo(str(Path(base.name) / ruta.relative_to(base)), date_time=(2026, 11, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    z.writestr(info, ruta.read_bytes())
            for licencia in sorted(base.parent.glob(f"{base.name.replace('_', '?')}-*.dist-info/**/LICEN*")):
                info = zipfile.ZipInfo(f"licencias/{base.name}-{licencia.name}", date_time=(2026, 11, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, licencia.read_bytes())
    return True


def _puntaje(carpeta_hallazgos: Path):
    """Puntaje de la demo segun el evaluador oficial (solo se mira su resultado)."""
    corrida = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "evaluar.py"), "--dataset", "data/demo", "--hallazgos",
         str(carpeta_hallazgos / "hallazgos.json"), "--json"], cwd=RAIZ, capture_output=True, text=True)
    try:
        r = json.loads(corrida.stdout)
        return {"encontradas": r["encontradas"], "total": r["total_fugas"], "falsos": r["falsos_positivos"],
                "aprobado": r["aprobado"]}
    except (ValueError, KeyError):
        return None


def construir(web: Path, con_vendor: bool = True, web_real: Path = None) -> dict:
    vigentes = set()
    codigo = []
    for ruta in sorted((RAIZ / "detective").rglob("*.py")):
        if ruta.name in NO_COPIAR or "__pycache__" in ruta.parts:
            continue
        relativo = ruta.relative_to(RAIZ)
        _copiar_texto(ruta, web / "py" / relativo)
        vigentes.add(web / "py" / relativo)
        codigo.append(str(relativo).replace("\\", "/"))
    for ruta in sorted((RAIZ / "plantillas").glob("*.json")):
        relativo = ruta.relative_to(RAIZ)
        _copiar_texto(ruta, web / "py" / relativo)
        vigentes.add(web / "py" / relativo)
        codigo.append(str(relativo).replace("\\", "/"))

    datos_demo = []
    for ruta in sorted(DEMO.iterdir()):          # solo el primer nivel: nunca entra a subcarpetas
        if ruta.is_file() and ruta.suffix.lower() in (".csv", ".xlsx", ".json"):
            _copiar_texto(ruta, web / "demo" / "datos" / ruta.name)
            vigentes.add(web / "demo" / "datos" / ruta.name)
            datos_demo.append(ruta.name)

    entradas = [Entrada(n, (DEMO / n).read_bytes()) for n in datos_demo]
    res = auditar(entradas, cargar_plantillas(RAIZ / "plantillas"))
    salidas = archivos_de_salida(res)
    for nombre in SALIDAS_DEMO:
        _escribir_estable(web / "demo" / nombre, salidas[nombre])
        vigentes.add(web / "demo" / nombre)
    _escribir_estable(web / "demo" / "informe_cuerpo.html", cuerpo_html(res))
    vigentes.add(web / "demo" / "informe_cuerpo.html")
    puntaje = _puntaje(web / "demo")
    if puntaje:
        _escribir_estable(web / "demo" / "puntaje.json", json.dumps(puntaje, ensure_ascii=False) + "\n")
        vigentes.add(web / "demo" / "puntaje.json")

    xlsx = ((web_real or web) / "vendor" / "openpyxl.zip").exists()
    if con_vendor:
        xlsx = _zip_openpyxl(web / "vendor" / "openpyxl.zip")
    manifiesto = {"version": __version__, "codigo": codigo, "demo": datos_demo, "xlsx": xlsx,
                  "empresa_demo": res.config.empresa, "hallazgos_demo": len(res.hallazgos)}
    _escribir_estable(web / "py" / "manifiesto.json", json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n")
    vigentes.add(web / "py" / "manifiesto.json")
    _limpiar(web / "py", vigentes)
    _limpiar(web / "demo", vigentes)
    return manifiesto


def _diferencias(esperado: Path, real: Path) -> list:
    """Archivos de py/ y demo/ que faltan, sobran o cambiaron (sin contar la hora de generacion)."""
    problemas = []
    for sub in ("py", "demo"):
        nombres = {p.relative_to(esperado) for p in (esperado / sub).rglob("*") if p.is_file()}
        nombres |= {p.relative_to(real) for p in (real / sub).rglob("*") if p.is_file()}
        for nombre in sorted(nombres):
            a, b = esperado / nombre, real / nombre
            if not b.exists():
                problemas.append(f"falta web/{nombre}")
            elif not a.exists():
                problemas.append(f"sobra web/{nombre}")
            elif not filecmp.cmp(a, b, shallow=False):
                if a.suffix in (".json", ".md", ".html") and _sin_hora(a.read_text(encoding="utf-8")) == _sin_hora(
                        b.read_text(encoding="utf-8")):
                    continue
                problemas.append(f"web/{nombre} está desactualizado")
    return problemas


def comprobar(web: Path) -> list:
    with tempfile.TemporaryDirectory() as tmp:
        construir(Path(tmp), con_vendor=False, web_real=web)
        return _diferencias(Path(tmp), web)


def main() -> int:
    ap = argparse.ArgumentParser(description="Arma web/ con el código probado, las plantillas y la demo")
    ap.add_argument("--comprobar", action="store_true", help="no escribe: solo avisa si web/ está desactualizada")
    a = ap.parse_args()
    web = RAIZ / "web"
    if a.comprobar:
        problemas = comprobar(web)
        for p in problemas:
            print(p)
        print("web/ está al día." if not problemas else "Corre: python scripts/construir_web.py")
        return 1 if problemas else 0
    m = construir(web)
    print(f"web/ lista: {len(m['codigo'])} archivos de código y plantillas, {len(m['demo'])} archivos de la demo, "
          f"{m['hallazgos_demo']} hallazgos precalculados. Lector de Excel en la web: {'sí' if m['xlsx'] else 'no (solo CSV)'}.")
    print("Para verla: python -m http.server -d web 8000  y abre http://localhost:8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
