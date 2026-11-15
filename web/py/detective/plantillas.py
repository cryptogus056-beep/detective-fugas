"""Plantillas de mapeo: dicen como se llaman las columnas de cada banco o sistema.

El detector no tiene nombres de columna fijos. Cada plantilla (un JSON) declara
que encabezados la identifican y que columna corresponde a cada dato comun
(fecha, descripcion, monto...). Agregar un banco nuevo es agregar un JSON.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

from .lectores import (EXTENSIONES_CSV, SEPARADORES, ErrorLectura, Tabla, decodificar, extension, leer_tabla,
                       separadores_probables)
from .normalizar import clave_texto, parsear_fecha, parsear_numero

# Datos comunes de cada rol. "obligatorios": deben estar en la plantilla y en el archivo.
# "alguno_de": basta con que uno de los grupos este completo.
ROLES = {
    "banco": {
        "titulo": "Cartola o movimientos del banco",
        "campos": ["fecha", "descripcion", "cargo", "abono", "monto_con_signo", "documento", "saldo"],
        "obligatorios": ["fecha", "descripcion"],
        "alguno_de": [["monto_con_signo"], ["cargo", "abono"]],
    },
    "pos": {
        "titulo": "Ventas con tarjeta o link de pago",
        "campos": ["fecha", "descripcion", "monto", "estado", "id", "comision", "monto_neto"],
        "obligatorios": ["fecha", "monto"],
    },
    "rcv_ventas": {
        "titulo": "Registro de Ventas del SII",
        "campos": ["tipo", "folio", "fecha", "rut", "razon_social", "exento", "neto", "iva", "total"],
        "obligatorios": ["tipo", "folio", "fecha", "total"],
    },
    "rcv_compras": {
        "titulo": "Registro de Compras del SII",
        "campos": ["tipo", "folio", "fecha", "rut", "razon_social", "exento", "neto", "iva", "total"],
        "obligatorios": ["tipo", "folio", "fecha", "total"],
    },
    "cotizaciones": {
        "titulo": "Cotizaciones o presupuestos",
        "campos": ["numero", "fecha", "cliente", "rut", "servicio", "neto", "iva", "total", "estado",
                   "fecha_aceptacion"],
        "obligatorios": ["numero", "fecha", "estado"],
        "alguno_de": [["neto"], ["total"]],
    },
    "equipo": {
        "titulo": "Personas del equipo",
        "campos": ["nombre", "email", "cargo", "estado", "fecha_ingreso", "fecha_salida"],
        "obligatorios": ["estado"],
        "alguno_de": [["email"], ["nombre"]],
    },
    "licencias": {
        "titulo": "Licencias de software por usuario",
        "campos": ["servicio", "usuario", "plan", "costo_mensual", "estado"],
        "obligatorios": ["servicio", "usuario"],
    },
}
FILAS_DE_BUSQUEDA = 40  # el encabezado se busca en las primeras filas (puede haber preambulo)


class PlantillaNoEncontrada(ErrorLectura):
    """Ninguna plantilla calza con el archivo."""


@dataclass
class Plantilla:
    nombre: str
    rol: str
    descripcion: str = ""
    contiene: list = field(default_factory=list)
    no_contiene: list = field(default_factory=list)
    separador: str = None
    formato_fecha: list = field(default_factory=list)
    numeros: str = "chileno"
    columnas: dict = field(default_factory=dict)   # dato comun -> lista de encabezados posibles
    estados: dict = field(default_factory=dict)

    @classmethod
    def desde_dict(cls, d: dict) -> "Plantilla":
        rol = d.get("rol")
        if rol not in ROLES:
            raise ErrorLectura(f"La plantilla '{d.get('nombre')}' tiene un rol desconocido: '{rol}'. "
                               f"Roles válidos: {', '.join(ROLES)}.")
        columnas = {}
        for dato, encabezados in (d.get("columnas") or {}).items():
            if dato not in ROLES[rol]["campos"]:
                raise ErrorLectura(f"La plantilla '{d.get('nombre')}' usa el dato '{dato}', que no existe para "
                                   f"el rol '{rol}'. Datos válidos: {', '.join(ROLES[rol]['campos'])}.")
            columnas[dato] = [encabezados] if isinstance(encabezados, str) else list(encabezados)
        deteccion = d.get("deteccion") or {}
        fechas = d.get("formato_fecha") or []
        return cls(
            nombre=d.get("nombre") or "sin_nombre", rol=rol, descripcion=d.get("descripcion", ""),
            contiene=list(deteccion.get("encabezado_contiene") or []),
            no_contiene=list(deteccion.get("encabezado_no_contiene") or []),
            separador=d.get("separador") or None,
            formato_fecha=[fechas] if isinstance(fechas, str) else list(fechas),
            numeros=d.get("numeros") or "chileno", columnas=columnas, estados=d.get("estados") or {},
        )

    def faltantes(self) -> list:
        """Datos obligatorios del rol que la plantilla no declara."""
        esquema = ROLES[self.rol]
        faltan = [c for c in esquema["obligatorios"] if c not in self.columnas]
        grupos = esquema.get("alguno_de")
        if grupos and not any(all(c in self.columnas for c in g) for g in grupos):
            faltan.append(" o ".join("+".join(g) for g in grupos))
        return faltan


@dataclass
class Lectura:
    """Un archivo ya reconocido: su tabla, su plantilla y donde esta cada columna."""
    tabla: Tabla
    plantilla: Plantilla
    fila_encabezado: int          # numero de linea fisica del encabezado
    columnas: dict                # dato comun -> indice de columna
    encabezados: list

    @property
    def filas_de_datos(self) -> list:
        return [f for f in self.tabla.filas if f.numero > self.fila_encabezado]

    def valor(self, fila, dato):
        i = self.columnas.get(dato)
        if i is None or i >= len(fila.celdas):
            return None
        v = fila.celdas[i]
        return None if isinstance(v, str) and not v.strip() else v

    def texto(self, fila, dato) -> str:
        v = self.valor(fila, dato)
        return "" if v is None else str(v).strip()

    def numero(self, fila, dato):
        return parsear_numero(self.valor(fila, dato), self.plantilla.numeros)

    def fecha(self, fila, dato):
        return parsear_fecha(self.valor(fila, dato), self.plantilla.formato_fecha)


def cargar_plantillas(carpeta) -> list:
    """Lee todos los .json de la carpeta (los que empiezan con "_" son ejemplos y se saltan)."""
    plantillas = []
    for ruta in sorted(Path(carpeta).glob("*.json")):
        if ruta.name.startswith("_"):
            continue
        try:
            plantillas.append(Plantilla.desde_dict(json.loads(ruta.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as error:
            raise ErrorLectura(f"La plantilla {ruta.name} no es un JSON válido: {error}") from error
    if not plantillas:
        raise ErrorLectura(f"No encontré plantillas en {carpeta}.")
    return plantillas


def carpeta_por_defecto() -> Path:
    """Las plantillas viven junto al paquete: <raiz>/plantillas."""
    return Path(__file__).resolve().parent.parent / "plantillas"


def _calce(plantilla: Plantilla, celdas: list):
    """Si la fila es el encabezado de la plantilla, devuelve (puntaje, columnas). Si no, None."""
    claves = [clave_texto(c) for c in celdas]
    if sum(1 for c in claves if c) < 2:
        return None
    for termino in plantilla.contiene:
        if not any(clave_texto(termino) in c for c in claves):
            return None
    for termino in plantilla.no_contiene:
        if any(clave_texto(termino) in c for c in claves):
            return None
    columnas = {}
    for dato, encabezados in plantilla.columnas.items():
        for e in encabezados:
            if clave_texto(e) in claves:
                columnas[dato] = claves.index(clave_texto(e))
                break
    esquema = ROLES[plantilla.rol]
    if any(c not in columnas for c in esquema["obligatorios"]):
        return None
    grupos = esquema.get("alguno_de")
    if grupos and not any(all(c in columnas for c in g) for g in grupos):
        return None
    return len(plantilla.contiene) * 10 + len(columnas), columnas


def reconocer(tabla: Tabla, plantillas: list, rol: str = None):
    """Busca la plantilla y la fila de encabezado que mejor calzan con la tabla."""
    mejor = None
    for plantilla in plantillas:
        if rol and plantilla.rol != rol:
            continue
        if plantilla.separador and tabla.separador and plantilla.separador != tabla.separador:
            continue
        for fila in tabla.filas[:FILAS_DE_BUSQUEDA]:
            calce = _calce(plantilla, fila.celdas)
            if calce:
                if mejor is None or calce[0] > mejor[0]:
                    mejor = (calce[0], plantilla, fila, calce[1])
                break
    if mejor is None:
        return None
    _, plantilla, fila, columnas = mejor
    return Lectura(tabla, plantilla, fila.numero, columnas, [str(c) if c is not None else "" for c in fila.celdas])


def reconocer_archivo(nombre: str, datos: bytes, plantillas: list, rol: str = None) -> Lectura:
    """Lee el archivo y encuentra su plantilla. Si ninguna calza, explica como crear una."""
    separadores = [None]
    if extension(nombre) in EXTENSIONES_CSV:
        probables = separadores_probables(decodificar(datos)[0])
        separadores = probables + [s for s in SEPARADORES if s not in probables]
    primera = None
    for separador in separadores:
        tabla = leer_tabla(nombre, datos, separador)
        primera = primera or tabla
        lectura = reconocer(tabla, plantillas, rol)
        if lectura:
            return lectura
    raise PlantillaNoEncontrada(mensaje_sin_plantilla(primera, rol))


def fila_de_encabezado_probable(tabla: Tabla):
    """Adivina la fila de encabezado: la primera con varias celdas de texto y ninguna fecha ni numero."""
    mejor = None
    for fila in tabla.filas[:FILAS_DE_BUSQUEDA]:
        celdas = [c for c in fila.celdas if c is not None and str(c).strip()]
        if len(celdas) < 2:
            continue
        if any(not isinstance(c, str) or parsear_numero(c) is not None or parsear_fecha(c) for c in celdas):
            continue
        if mejor is None or len(celdas) > len(mejor.celdas) + 1:
            mejor = fila
            if len(celdas) >= 3:
                break
    return mejor


def mensaje_sin_plantilla(tabla: Tabla, rol: str = None) -> str:
    fila = fila_de_encabezado_probable(tabla)
    if fila:
        columnas = ", ".join(f'"{c}"' for c in fila.celdas if c is not None and str(c).strip())
        encontrado = f"En la fila {fila.numero} encontré estas columnas: {columnas}."
    else:
        encontrado = "No encontré una fila de encabezados con nombres de columna."
    de_rol = f" para el tipo '{rol}'" if rol else ""
    return (
        f"No tengo una plantilla{de_rol} que calce con '{tabla.nombre}'. {encontrado} "
        "Para crear una: copia plantillas/_ejemplo.json con otro nombre, escribe ahí los nombres de tus columnas "
        f"y vuelve a correr. Ayuda: python -m detective plantilla --archivo {tabla.nombre}"
    )


# Palabras que suelen aparecer en los encabezados de cada dato (para proponer una plantilla).
_PISTAS = {
    "banco": {
        "fecha": ["fecha"], "descripcion": ["descripcion", "glosa", "detalle", "movimiento", "concepto"],
        "cargo": ["cargo", "debito", "egreso", "giro"], "abono": ["abono", "credito", "deposito", "ingreso"],
        "monto_con_signo": ["monto", "importe", "valor"],
    },
    "pos": {"fecha": ["fecha"], "monto": ["monto bruto", "monto venta", "monto_bruto", "monto", "total"],
            "estado": ["estado", "status"], "descripcion": ["descripcion", "detalle", "glosa"],
            "id": ["id", "codigo", "operacion", "autorizacion"]},
    "rcv_ventas": {"tipo": ["tipo doc"], "folio": ["folio"], "fecha": ["fecha docto", "fecha"],
                   "rut": ["rut"], "razon_social": ["razon social"], "neto": ["neto"], "iva": ["iva"],
                   "total": ["total"], "exento": ["exento"]},
    "cotizaciones": {"numero": ["cotizacion", "presupuesto", "folio", "numero"], "fecha": ["fecha"],
                     "cliente": ["cliente", "razon social"], "rut": ["rut"], "neto": ["neto"], "iva": ["iva"],
                     "total": ["total"], "estado": ["estado"], "fecha_aceptacion": ["acepta", "aprob"],
                     "servicio": ["servicio", "detalle", "descripcion"]},
    "equipo": {"nombre": ["nombre"], "email": ["email", "correo"], "estado": ["estado"],
               "fecha_salida": ["salida", "termino", "egreso"], "fecha_ingreso": ["ingreso", "inicio"],
               "cargo": ["cargo", "puesto"]},
    "licencias": {"servicio": ["servicio", "software", "producto"], "usuario": ["usuario", "email", "correo"],
                  "plan": ["plan"], "costo_mensual": ["costo", "precio", "valor"], "estado": ["estado"]},
}


def proponer_plantilla(tabla: Tabla) -> dict:
    """Arma un borrador de plantilla a partir de los encabezados del archivo."""
    fila = fila_de_encabezado_probable(tabla)
    if not fila:
        raise ErrorLectura(f"No encontré una fila de encabezados en '{tabla.nombre}'.")
    encabezados = [str(c).strip() for c in fila.celdas if c is not None and str(c).strip()]
    claves = [clave_texto(e) for e in encabezados]
    mejor_rol, mejor_columnas, mejor_puntaje = "banco", {}, (False, 0)
    for rol, pistas in _PISTAS.items():
        columnas, usados = {}, set()
        for dato, palabras in pistas.items():
            for palabra in palabras:
                candidato = next((i for i, c in enumerate(claves) if palabra in c and i not in usados), None)
                if candidato is not None:
                    columnas[dato] = encabezados[candidato]
                    usados.add(candidato)
                    break
        if rol == "banco" and "cargo" in columnas and "abono" in columnas:
            columnas.pop("monto_con_signo", None)
        puntaje = (all(c in columnas for c in ROLES[rol]["obligatorios"]), len(columnas))
        if puntaje > mejor_puntaje:
            mejor_rol, mejor_columnas, mejor_puntaje = rol, columnas, puntaje
    datos = [f for f in tabla.filas if f.numero > fila.numero][:20]
    muestra_fechas = [str(f.celdas[i]) for f in datos for i in range(len(f.celdas))
                      if isinstance(f.celdas[i], str) and parsear_fecha(f.celdas[i])][:5]
    formato = "%d/%m/%Y"
    for candidato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        if muestra_fechas and all(_calza_formato(m, candidato) for m in muestra_fechas):
            formato = candidato
            break
    base = Path(tabla.nombre).stem.lower().replace(" ", "_")
    return {
        "nombre": f"mi_{base}",
        "rol": mejor_rol,
        "descripcion": f"Borrador generado desde {tabla.nombre}. Revisa que cada columna sea la correcta.",
        "deteccion": {"encabezado_contiene": list(mejor_columnas.values())[:4] or encabezados[:3]},
        "separador": tabla.separador,
        "formato_fecha": [formato],
        "numeros": "chileno",
        "columnas": mejor_columnas,
        "_encabezados_encontrados": encabezados,
        "_fila_encabezado": fila.numero,
    }


def _calza_formato(texto: str, formato: str) -> bool:
    try:
        dt.datetime.strptime(texto.strip()[:10], formato)
        return True
    except ValueError:
        return False
