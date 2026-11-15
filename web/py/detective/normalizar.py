"""Normalizacion de numeros, fechas, RUT, glosas y estados.

Todo lo que llega de un archivo es texto "sucio". Aqui se convierte a valores
comparables: montos enteros en pesos, fechas `date`, RUT con formato unico.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# --------------------------------------------------------------------------- texto


def sin_tildes(texto: str) -> str:
    """Quita tildes y dieresis; la letra enie queda como N."""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def clave_texto(texto) -> str:
    """Forma comparable de un texto: sin tildes, minusculas, espacios simples."""
    if texto is None:
        return ""
    limpio = sin_tildes(str(texto)).lower().replace("﻿", "")
    return re.sub(r"\s+", " ", limpio).strip()


# --------------------------------------------------------------------------- numeros

MODOS_NUMERO = ("chileno", "decimal_punto")


def redondear(valor) -> int:
    """Redondeo comercial (0,5 hacia arriba), no el redondeo "bancario" de Python."""
    d = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parsear_numero(valor, modo: str = "chileno"):
    """Convierte un texto de monto a entero en pesos. Devuelve None si no es un numero.

    Regla explicita para distinguir punto de miles de punto decimal:

    1. Si el texto trae punto Y coma, el separador que aparece al final es el decimal
       y el otro es de miles ("1.234,50" y "1,234.50" valen 1234,5).
    2. Si trae un solo tipo de separador y aparece mas de una vez, es de miles
       ("1.234.567").
    3. Si aparece una sola vez:
       - seguido de exactamente 3 digitos: es de MILES en modo "chileno" ("34.400" vale
         34400). En modo "decimal_punto" un punto es decimal ("34.400" vale 34,4) y una
         coma es de miles.
       - seguido de 1, 2 o mas de 3 digitos: es decimal ("65000.00" vale 65000),
         porque un grupo de miles siempre tiene 3 digitos.
    4. Se aceptan "$", espacios, signo menos adelante o atras y parentesis contables.
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        if valor != valor or valor in (float("inf"), float("-inf")):
            return None
        return redondear(valor)
    if isinstance(valor, Decimal):
        return redondear(valor)
    texto = str(valor).strip().replace(" ", " ")
    if not texto:
        return None
    negativo = False
    if texto.startswith("(") and texto.endswith(")"):
        negativo, texto = True, texto[1:-1]
    texto = re.sub(r"(?i)clp|\$|\s", "", texto)
    if texto.startswith("+"):
        texto = texto[1:]
    if texto.startswith("-"):
        negativo, texto = not negativo, texto[1:]
    elif texto.endswith("-"):
        negativo, texto = not negativo, texto[:-1]
    if not texto or not re.fullmatch(r"[\d.,]+", texto) or not re.search(r"\d", texto):
        return None

    n_punto, n_coma = texto.count("."), texto.count(",")
    if n_punto and n_coma:
        decimal = "." if texto.rfind(".") > texto.rfind(",") else ","
        miles = "," if decimal == "." else "."
        if texto.count(decimal) > 1:
            return None
        texto = texto.replace(miles, "").replace(decimal, ".")
    elif n_punto or n_coma:
        sep = "." if n_punto else ","
        partes = texto.split(sep)
        if len(partes) > 2:
            if any(len(p) != 3 for p in partes[1:]) or not partes[0]:
                return None
            texto = "".join(partes)
        else:
            es_decimal_por_modo = (sep == ".") == (modo == "decimal_punto")
            if len(partes[1]) == 3 and partes[0] and not es_decimal_por_modo:
                texto = "".join(partes)
            else:
                texto = (partes[0] or "0") + "." + partes[1]
    try:
        numero = redondear(Decimal(texto))
    except (InvalidOperation, ValueError):
        return None
    return -numero if negativo else numero


def formato_clp(monto) -> str:
    """12345 -> "$12.345"; negativos como "-$12.345"."""
    if monto is None:
        return ""
    n = int(monto)
    cuerpo = f"{abs(n):,}".replace(",", ".")
    return f"-${cuerpo}" if n < 0 else f"${cuerpo}"


def iva_de_neto(neto: int, tasa) -> int:
    """IVA de un neto, con redondeo comercial."""
    return redondear(Decimal(int(neto)) * Decimal(str(tasa)))


def neto_de_total(total: int, tasa) -> int:
    """Neto contenido en un total con IVA incluido."""
    return redondear(Decimal(int(total)) / (Decimal(1) + Decimal(str(tasa))))


# --------------------------------------------------------------------------- fechas

FORMATOS_FECHA = (
    "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%y", "%d-%m-%y",
)
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ]\d{2}:\d{2}")
_EXCEL_BASE = dt.date(1899, 12, 30)


def parsear_fecha(valor, formatos=None):
    """Convierte un valor a `date`. Devuelve None si no es una fecha.

    Acepta dd/mm/aaaa, dd-mm-aaaa, aaaa-mm-dd, ISO con hora y zona (se queda con el dia
    tal como esta escrito, sin convertir de zona) y fechas nativas de Excel.
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, dt.datetime):
        return valor.date()
    if isinstance(valor, dt.date):
        return valor
    if isinstance(valor, (int, float)):
        # numero de serie de Excel (dias desde 1899-12-30); solo rangos razonables
        if 20000 <= valor <= 80000:
            return _EXCEL_BASE + dt.timedelta(days=int(valor))
        return None
    texto = str(valor).strip()
    if not texto or len(texto) < 6 or not texto[0].isdigit():
        return None
    for formato in tuple(formatos or ()) + FORMATOS_FECHA:
        try:
            return dt.datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    m = _ISO.match(texto)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def formato_fecha(fecha) -> str:
    """date -> dd/mm/aaaa (como se lee en Chile)."""
    return fecha.strftime("%d/%m/%Y") if fecha else ""


def meses_entre(desde: dt.date, hasta: dt.date) -> int:
    """Cantidad de meses calendario que toca un periodo (agosto a octubre son 3)."""
    if not desde or not hasta or hasta < desde:
        return 1
    return (hasta.year - desde.year) * 12 + (hasta.month - desde.month) + 1


# --------------------------------------------------------------------------- RUT

_RUT = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d{3}){2}|\d{7,8})\s?-\s?([\dkK])(?![\w])")
RUT_GENERICO = "66.666.666-6"  # "consumidor final": boletas sin RUT del cliente


def digito_verificador(numero: int) -> str:
    suma, factor = 0, 2
    for d in reversed(str(int(numero))):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return "0" if resto == 11 else "K" if resto == 10 else str(resto)


def normalizar_rut(texto):
    """Devuelve (rut con formato 12.345.678-9, es_valido). (None, False) si no es un RUT."""
    if texto is None:
        return None, False
    limpio = re.sub(r"[.\s]", "", str(texto)).upper()
    m = re.fullmatch(r"(\d{6,9})-?([\dK])", limpio)
    if not m:
        return None, False
    cuerpo, dv = int(m.group(1)), m.group(2)
    rut = f"{cuerpo:,}".replace(",", ".") + "-" + dv
    return rut, digito_verificador(cuerpo) == dv


def extraer_ruts(texto) -> list:
    """Todos los RUT que aparecen dentro de un texto (por ejemplo, una glosa del banco)."""
    encontrados = []
    for m in _RUT.finditer(str(texto or "")):
        rut, _ = normalizar_rut(m.group(1) + "-" + m.group(2))
        if rut and rut not in encontrados:
            encontrados.append(rut)
    return encontrados


# --------------------------------------------------------------------------- glosas


def normalizar_glosa(texto) -> str:
    """Nombre comparable de un comercio: mayusculas, sin tildes, sin numeros de tarjeta ni codigos.

    Se eliminan: tarjetas enmascaradas (XXXX1234, ****1234), numeros de 4 o mas digitos
    y codigos que mezclan letras y numeros de 6 o mas caracteres. Los numeros cortos se
    conservan porque suelen ser parte del nombre ("MICROSOFT 365").
    """
    t = sin_tildes(str(texto or "")).upper()
    t = re.sub(r"[X*]{2,}\s?\d{2,}", " ", t)          # tarjeta enmascarada
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    palabras = []
    for p in t.split():
        if p.isdigit() and len(p) >= 4:
            continue
        if len(p) >= 6 and re.search(r"\d", p) and re.search(r"[A-Z]", p) and sum(c.isdigit() for c in p) >= 3:
            continue
        palabras.append(p)
    return " ".join(palabras)


def contiene_palabras(glosa_normalizada: str, frase) -> bool:
    """True si todas las palabras de `frase` estan en la glosa (como palabras completas)."""
    palabras = set(glosa_normalizada.split())
    buscadas = normalizar_glosa(frase).split()
    return bool(buscadas) and all(b in palabras for b in buscadas)


# --------------------------------------------------------------------------- estados

ESTADOS_COTIZACION = {
    "aceptada": ["aceptada", "aceptado", "aprobada", "aprobado", "ok", "confirmada", "confirmado",
                 "adjudicada", "adjudicado", "ganada", "ganado", "cerrada ganada", "si"],
    "rechazada": ["rechazada", "rechazado", "perdida", "perdido", "anulada", "anulado", "cancelada",
                  "cancelado", "descartada", "no"],
    "pendiente": ["pendiente", "enviada", "enviado", "en espera", "borrador", "en revision", "por confirmar"],
}
ESTADOS_POS = {
    "aprobada": ["approved", "aprobada", "aprobado", "aprobadas", "ok", "pagada", "pagado", "exitosa",
                 "exitoso", "accredited", "acreditada", "acreditado", "autorizada", "autorizado"],
    "rechazada": ["rejected", "rechazada", "rechazado", "cancelled", "canceled", "cancelada", "anulada",
                  "anulado", "refunded", "devuelta", "reversada", "fallida", "pending", "pendiente",
                  "in_process", "charged_back"],
}
ESTADOS_ACTIVO = {
    "activo": ["activo", "activa", "vigente", "si", "alta"],
    "inactivo": ["inactivo", "inactiva", "desvinculado", "desvinculada", "baja", "cancelada", "cancelado",
                 "de baja", "no", "terminada", "terminado", "suspendida", "suspendido"],
}


def normalizar_estado(valor, tabla: dict, extra: dict = None, por_defecto: str = "otro") -> str:
    """Lleva un estado escrito de cualquier forma a una de las claves de `tabla`."""
    clave = clave_texto(valor)
    if not clave:
        return por_defecto
    for fuente in (extra or {}, tabla):
        for canonico, variantes in fuente.items():
            if clave == clave_texto(canonico) or clave in {clave_texto(v) for v in variantes}:
                return canonico
    return por_defecto
