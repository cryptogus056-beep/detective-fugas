"""Linea de comandos del Detective de Fugas Pyme.

    python -m detective auditar --datos data/demo --salida salida/demo
    python -m detective plantilla --archivo mi_cartola.csv
    python -m detective version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .lectores import ErrorLectura, leer_tabla
from .plantillas import (ROLES, PlantillaNoEncontrada, cargar_plantillas, carpeta_por_defecto,
                         fila_de_encabezado_probable, proponer_plantilla, reconocer_archivo)


def _plantillas(args):
    return cargar_plantillas(args.plantillas or carpeta_por_defecto())


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
