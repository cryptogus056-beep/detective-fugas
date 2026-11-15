"""Puente entre la pagina y el paquete detective/ cuando corre dentro del navegador (Pyodide).

Todo ocurre en la memoria del navegador: los archivos del usuario se escriben en una
carpeta virtual (/entrada) y nunca se envian a ningun servidor.
"""
import json
from pathlib import Path

from detective import __version__, mensajes
from detective.auditoria import NOMBRE_CONFIG, Entrada, auditar
from detective.informe import archivos_de_salida, cuerpo_html
from detective.lectores import ErrorLectura, es_tabla
from detective.modelo import cargar_registros
from detective.config import cargar_config
from detective.plantillas import ROLES, cargar_plantillas, reconocer_archivo

ENTRADA = Path("/entrada")
_PLANTILLAS = None


def _plantillas():
    global _PLANTILLAS
    if _PLANTILLAS is None:
        _PLANTILLAS = cargar_plantillas("/app/plantillas")
    return _PLANTILLAS


def _entradas():
    return [Entrada(p.name, p.read_bytes()) for p in sorted(ENTRADA.iterdir()) if p.is_file()]


def roles() -> str:
    """Tipos de archivo que la pagina ofrece en el selector."""
    return json.dumps([{"rol": rol, "titulo": datos["titulo"]} for rol, datos in ROLES.items()], ensure_ascii=False)


def reconocer() -> str:
    """Dice, para cada archivo subido, que tipo de archivo parece ser."""
    resultado = []
    for e in _entradas():
        if e.nombre.lower() == NOMBRE_CONFIG:
            try:
                cargar_config(e.datos)
                resultado.append({"nombre": e.nombre, "rol": "config", "titulo": "Configuración", "filas": None, "error": ""})
            except ErrorLectura as error:
                resultado.append({"nombre": e.nombre, "rol": "", "titulo": "", "filas": None, "error": str(error)})
            continue
        if not es_tabla(e.nombre):
            resultado.append({"nombre": e.nombre, "rol": "", "titulo": "", "filas": None,
                              "error": "No es un archivo CSV ni XLSX: no lo voy a usar."})
            continue
        try:
            lectura = reconocer_archivo(e.nombre, e.datos, _plantillas())
            filas = len(cargar_registros(lectura, cargar_config(None)).registros)
            resultado.append({"nombre": e.nombre, "rol": lectura.plantilla.rol,
                              "titulo": ROLES[lectura.plantilla.rol]["titulo"], "filas": filas, "error": ""})
        except ErrorLectura as error:
            resultado.append({"nombre": e.nombre, "rol": "", "titulo": "", "filas": None, "error": str(error)})
    return json.dumps(resultado, ensure_ascii=False)


def auditar_entrada(roles_json: str = "{}", tratamiento: str = "usted") -> str:
    """Corre la auditoria completa sobre /entrada y devuelve el informe y los archivos para descargar."""
    try:
        res = auditar(_entradas(), _plantillas(), roles_forzados=json.loads(roles_json or "{}"))
    except ErrorLectura as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
    borradores = mensajes.borradores(res, tratamiento)
    salidas = archivos_de_salida(res, borradores)
    return json.dumps({
        "error": "",
        "cuerpo_html": cuerpo_html(res),
        "archivos": {n: salidas[n] for n in ("informe.md", "hallazgos.json", "mensajes_cobro.md", "informe.html")},
        "hallazgos": len(res.hallazgos),
        "total_clp": sum(h.impacto_clp for h in res.hallazgos),
        "version": __version__,
    }, ensure_ascii=False)
