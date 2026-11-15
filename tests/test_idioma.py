"""Idioma: nada de guion largo en textos para personas (ni en lo que genera el detector)."""
GUION_LARGO = "\u2014"
SALTAR = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "vendor"}
EXTENSIONES = {".md", ".html", ".js", ".mjs", ".css", ".py", ".json", ".txt"}


def test_ningun_texto_tiene_guion_largo(raiz):
    con_guion, revisados = [], 0
    for ruta in sorted(raiz.rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES or SALTAR & set(ruta.relative_to(raiz).parts):
            continue
        revisados += 1
        if GUION_LARGO in ruta.read_text(encoding="utf-8", errors="replace"):
            con_guion.append(str(ruta.relative_to(raiz)))
    assert revisados > 40
    assert not con_guion, f"archivos con guion largo: {con_guion}"
