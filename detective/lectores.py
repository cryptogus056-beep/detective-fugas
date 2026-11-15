"""Lectura de archivos CSV y XLSX tal como los exporta un banco o un sistema.

Devuelve una `Tabla` con TODAS las filas (incluido el preambulo) y, para cada una, su
numero de linea fisica: la primera linea del archivo es la 1. En XLSX es el numero de
fila de Excel. Ese numero es el que se cita como evidencia.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
from dataclasses import dataclass, field

SEPARADORES = (";", ",", "\t", "|")
EXTENSIONES_CSV = (".csv", ".txt", ".tsv")
EXTENSIONES_XLSX = (".xlsx", ".xlsm")


class ErrorLectura(Exception):
    """Un archivo no se pudo leer. El mensaje esta pensado para mostrarse al usuario."""


@dataclass
class Fila:
    numero: int      # linea fisica (CSV) o fila de Excel (XLSX); la primera es 1
    celdas: list     # textos en CSV; valores con tipo (fecha, numero, texto) en XLSX
    crudo: str       # la fila original, copiada tal cual


@dataclass
class Tabla:
    nombre: str
    formato: str                  # "csv" o "xlsx"
    filas: list
    separador: str = None
    codificacion: str = None
    _indice: dict = field(default_factory=dict, repr=False)

    def fila(self, numero: int):
        if not self._indice:
            self._indice = {f.numero: f for f in self.filas}
        return self._indice.get(int(numero))


def extension(nombre: str) -> str:
    nombre = str(nombre).lower()
    return nombre[nombre.rfind("."):] if "." in nombre else ""


def es_tabla(nombre: str) -> bool:
    return extension(nombre) in EXTENSIONES_CSV + EXTENSIONES_XLSX


def decodificar(datos: bytes):
    """Texto y codificacion. Prueba UTF-8 (con o sin BOM) y, si falla, Latin-1."""
    if datos.startswith(b"\xef\xbb\xbf"):
        try:
            return datos.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError:
            pass
    if datos.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return datos.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            pass
    try:
        return datos.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return datos.decode("latin-1"), "latin-1"


def _contar_fuera_de_comillas(linea: str, separador: str) -> int:
    total, dentro = 0, False
    for c in linea:
        if c == '"':
            dentro = not dentro
        elif c == separador and not dentro:
            total += 1
    return total


def separadores_probables(texto: str) -> list:
    """Separadores ordenados del mas probable al menos probable.

    Gana el que aparece la misma cantidad de veces en mas lineas (un separador de
    columnas es regular; una coma decimal o una coma dentro de un nombre, no).
    """
    lineas = [l for l in texto.splitlines()[:80] if l.strip()]
    puntajes = []
    for orden, sep in enumerate(SEPARADORES):
        cuentas = [_contar_fuera_de_comillas(l, sep) for l in lineas]
        positivas = [c for c in cuentas if c > 0]
        if not positivas:
            continue
        moda = max(set(positivas), key=lambda c: (positivas.count(c), c))
        regularidad = positivas.count(moda) / len(lineas)
        puntajes.append((-regularidad, -moda, orden, sep))
    return [p[3] for p in sorted(puntajes)] or [";"]


def leer_csv(nombre: str, datos: bytes, separador: str = None) -> Tabla:
    texto, codificacion = decodificar(datos)
    if "\x00" in texto[:2000]:
        raise ErrorLectura(f"'{nombre}' no parece un archivo de texto. Expórtalo como CSV o XLSX.")
    separador = separador or separadores_probables(texto)[0]
    lineas = list(io.StringIO(texto, newline=""))
    lector = csv.reader(iter(lineas), delimiter=separador)
    filas, inicio = [], 1
    while True:
        try:
            celdas = next(lector)
        except StopIteration:
            break
        except csv.Error as error:
            raise ErrorLectura(f"'{nombre}', línea {inicio}: no pude leer la fila ({error}).") from error
        fin = lector.line_num
        if any(str(c).strip() for c in celdas):
            crudo = "".join(lineas[inicio - 1:fin]).rstrip("\r\n")
            filas.append(Fila(inicio, [c.strip() for c in celdas], crudo))
        inicio = fin + 1
    return Tabla(nombre, "csv", filas, separador=separador, codificacion=codificacion)


def _celda_a_texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, dt.datetime):
        if (valor.hour, valor.minute, valor.second) == (0, 0, 0):
            return valor.strftime("%d/%m/%Y")
        return valor.strftime("%d/%m/%Y %H:%M:%S")
    if isinstance(valor, dt.date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, float) and valor == int(valor):
        return str(int(valor))
    return str(valor)


def leer_xlsx(nombre: str, datos: bytes) -> Tabla:
    try:
        import openpyxl
    except ImportError as error:
        raise ErrorLectura(
            f"No puedo leer '{nombre}' porque falta el lector de Excel. "
            "Guarda la planilla como CSV (Archivo, Guardar como, CSV) y vuelve a intentarlo."
        ) from error
    try:
        libro = openpyxl.load_workbook(io.BytesIO(datos), data_only=True)
    except Exception as error:  # openpyxl lanza errores muy distintos segun el dano del archivo
        raise ErrorLectura(f"No pude abrir '{nombre}' como Excel ({type(error).__name__}). "
                           "Prueba guardarlo de nuevo como .xlsx o como CSV.") from error
    hoja = libro.active
    filas = []
    for numero, valores in enumerate(hoja.iter_rows(values_only=True), start=1):
        celdas = list(valores)
        while celdas and (celdas[-1] is None or str(celdas[-1]).strip() == ""):
            celdas.pop()
        if not celdas:
            continue
        celdas = [c.strip() if isinstance(c, str) else c for c in celdas]
        filas.append(Fila(numero, celdas, " | ".join(_celda_a_texto(c) for c in celdas)))
    return Tabla(nombre, "xlsx", filas)


def leer_tabla(nombre: str, datos: bytes, separador: str = None) -> Tabla:
    """Lee un CSV o XLSX completo, sin interpretar columnas."""
    ext = extension(nombre)
    if ext in EXTENSIONES_XLSX:
        return leer_xlsx(nombre, datos)
    if ext in EXTENSIONES_CSV:
        return leer_csv(nombre, datos, separador)
    if ext == ".xls":
        raise ErrorLectura(f"'{nombre}' es un Excel antiguo (.xls). Ábrelo y guárdalo como .xlsx o como CSV.")
    raise ErrorLectura(f"No sé leer '{nombre}'. Acepto archivos .csv y .xlsx.")
