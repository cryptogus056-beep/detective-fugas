"""Linea de comandos del Detective de Fugas Pyme.

    python -m detective auditar --datos <carpeta con tus archivos> --salida <carpeta de resultados>
    python -m detective plantilla --archivo mi_cartola.csv
    python -m detective version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, mensajes
from .auditoria import Entrada, auditar
from .informe import archivos_de_salida
from .lectores import ErrorLectura, leer_tabla
from .normalizar import formato_clp
from .plantillas import (ROLES, PlantillaNoEncontrada, cargar_plantillas, carpeta_por_defecto,
                         fila_de_encabezado_probable, proponer_plantilla, reconocer_archivo)


def _plantillas(args):
    return cargar_plantillas(args.plantillas or carpeta_por_defecto())


def _sin_hora(texto: str) -> str:
    return "\n".join(l for l in texto.splitlines() if '"generado_en"' not in l)


def escribir_si_cambio(ruta: Path, contenido: str) -> None:
    """No reescribe un resultado si lo unico distinto es la hora en que se genero.

    Asi, volver a correr la auditoria sobre los mismos archivos no deja cambios falsos en git.
    """
    if ruta.exists() and _sin_hora(ruta.read_text(encoding="utf-8")) == _sin_hora(contenido):
        return
    ruta.write_text(contenido, encoding="utf-8")


def leer_carpeta(carpeta: Path) -> list:
    """Archivos del primer nivel de la carpeta (no entra a subcarpetas)."""
    return [Entrada(ruta.name, ruta.read_bytes()) for ruta in sorted(carpeta.iterdir())
            if ruta.is_file() and not ruta.name.startswith((".", "~$"))]


def cmd_auditar(args) -> int:
    carpeta = Path(args.datos)
    if not carpeta.is_dir():
        print(f"No encuentro la carpeta {carpeta}.")
        return 2
    clasificaciones = None
    if args.clasificaciones:
        clasificaciones = json.loads(Path(args.clasificaciones).read_text(encoding="utf-8"))
    descartes = None
    if args.descartes:
        descartes = json.loads(Path(args.descartes).read_text(encoding="utf-8"))
        descartes = descartes.get("descartados", []) if isinstance(descartes, dict) else descartes
    res = auditar(leer_carpeta(carpeta), _plantillas(args), clasificaciones=clasificaciones, descartes=descartes)
    borradores = mensajes.borradores(res, args.tratamiento)
    if args.llm:
        from . import llm
        se_puede, motivo = llm.disponible()
        if se_puede:
            borradores, avisos = llm.pulir(borradores)
            pulidos = sum(1 for b in borradores if b["pulido"])
            print(f"Mensajes pulidos con {llm.MODELO}: {pulidos}. Nada se envió: siguen siendo borradores.")
            for aviso in avisos:
                print(f"  Aviso: {aviso}")
        else:
            print(motivo)
    salida = Path(args.salida) if args.salida else Path("salida") / carpeta.resolve().name
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in archivos_de_salida(res, borradores).items():
        escribir_si_cambio(salida / nombre, contenido)
    print(f"Empresa: {res.config.empresa}. Corte: {res.config.fecha_corte.strftime('%d/%m/%Y')}.")
    for a in res.archivos_leidos:
        nota = "" if a["usado"] else " (repetido, no se usó)"
        print(f"  leí {a['archivo']}: {a['filas']} filas, plantilla {a['plantilla']}{nota}")
    print(f"Hallazgos verificados: {len(res.hallazgos)}. Descartados: {len(res.descartados)}.")
    for linea in res.no_revisado:
        print(f"  No revisado: {linea}")
    total = sum(h.impacto_clp for h in res.hallazgos)
    print(f"En juego: {formato_clp(total)}. Abre {salida / 'informe.md'} para ver el detalle.")
    return 0


def cmd_version(args) -> int:
    print(f"Detective de Fugas Pyme {__version__}")
    return 0


def cmd_plantilla(args) -> int:
    ruta = Path(args.archivo)
    if not ruta.is_file():
        print(f"No encuentro el archivo {ruta}.")
        return 2
    datos = ruta.read_bytes()
    try:
        lectura = reconocer_archivo(ruta.name, datos, _plantillas(args))
    except PlantillaNoEncontrada:
        lectura = None
    if lectura:
        print(f"'{ruta.name}' ya calza con la plantilla '{lectura.plantilla.nombre}' "
              f"({ROLES[lectura.plantilla.rol]['titulo']}).")
        print(f"Encabezado en la fila {lectura.fila_encabezado}: {', '.join(e for e in lectura.encabezados if e)}")
        print("Columnas reconocidas:")
        for dato, indice in lectura.columnas.items():
            print(f"  {dato:18} <- \"{lectura.encabezados[indice]}\"")
        print(f"Filas de datos: {len(lectura.filas_de_datos)}. No necesitas crear una plantilla nueva.")
        return 0
    tabla = leer_tabla(ruta.name, datos)
    fila = fila_de_encabezado_probable(tabla)
    if not fila:
        print(f"No encontré una fila de encabezados en '{ruta.name}'. Revisa que el archivo tenga nombres de columna.")
        return 1
    propuesta = proponer_plantilla(tabla)
    encabezados = propuesta.pop("_encabezados_encontrados")
    n_fila = propuesta.pop("_fila_encabezado")
    print(f"Ninguna plantilla calza con '{ruta.name}'.")
    print(f"Encabezados encontrados en la fila {n_fila}: {', '.join(encabezados)}")
    print(f"Me parece que es: {ROLES[propuesta['rol']]['titulo']} (rol \"{propuesta['rol']}\").")
    print(f"\nBorrador de plantilla. Guárdalo como plantillas/{propuesta['nombre']}.json y revisa cada columna:\n")
    print(json.dumps(propuesta, ensure_ascii=False, indent=2))
    faltan = [c for c in ROLES[propuesta["rol"]]["obligatorios"] if c not in propuesta["columnas"]]
    if faltan:
        print(f"\nOjo: no pude adivinar estas columnas obligatorias: {', '.join(faltan)}. "
              "Agrégalas a mano en \"columnas\".")
    print("\nDatos que puedes mapear para ese rol: " + ", ".join(ROLES[propuesta["rol"]]["campos"]))
    return 0


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m detective",
                                 description="Detective de Fugas Pyme: encuentra plata que tu pyme pierde sin darse cuenta.")
    sub = ap.add_subparsers(dest="comando")

    p = sub.add_parser("auditar", help="audita una carpeta de archivos y escribe el informe")
    p.add_argument("--datos", required=True, help="carpeta con tus archivos (CSV, XLSX y config.json)")
    p.add_argument("--salida", default=None, help="carpeta de resultados (por defecto salida/<nombre de la carpeta>)")
    p.add_argument("--plantillas", default=None, help="carpeta de plantillas (por defecto, plantillas/)")
    p.add_argument("--tratamiento", choices=["usted", "tu"], default="usted",
                   help="cómo tratar al cliente en los mensajes de cobro (por defecto, usted)")
    p.add_argument("--llm", action="store_true",
                   help="pule los mensajes con un modelo de lenguaje si existe ANTHROPIC_API_KEY (tiene costo)")
    p.add_argument("--clasificaciones", default=None,
                   help="JSON con clasificaciones de filas ambiguas (lo genera el modo agéntico)")
    p.add_argument("--descartes", default=None,
                   help="JSON del verificador de segunda opinión con los hallazgos a sacar (modo agéntico)")
    p.set_defaults(funcion=cmd_auditar)

    p = sub.add_parser("plantilla", help="muestra los encabezados de un archivo y propone una plantilla")
    p.add_argument("--archivo", required=True)
    p.add_argument("--plantillas", default=None, help="carpeta de plantillas (por defecto, plantillas/)")
    p.set_defaults(funcion=cmd_plantilla)

    p = sub.add_parser("version", help="muestra la versión")
    p.set_defaults(funcion=cmd_version)
    return ap


def main(argv=None) -> int:
    ap = construir_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "funcion", None):
        ap.print_help()
        return 2
    try:
        return args.funcion(args)
    except ErrorLectura as error:
        print(f"No pude continuar: {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
