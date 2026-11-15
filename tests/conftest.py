"""Utilidades comunes de las pruebas."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from detective.plantillas import cargar_plantillas  # noqa: E402


@pytest.fixture(scope="session")
def raiz():
    return RAIZ


@pytest.fixture(scope="session")
def plantillas():
    return cargar_plantillas(RAIZ / "plantillas")


# --------------------------------------------------------------------------- mini datasets para probar reglas
from detective.auditoria import Entrada, auditar  # noqa: E402
from detective.normalizar import iva_de_neto  # noqa: E402

CONFIG_BASE = {"empresa": "Empresa de Prueba SpA", "fecha_corte": "2026-10-31", "periodo_desde": "2026-08-01",
               "periodo_hasta": "2026-10-31",
               "palabras_excluidas_abonos": ["APORTE SOCIO", "DEVOLUCION", "LIQUIDACION TARJETAS"],
               "ruts_excluidos_abonos": ["11.111.111-1"]}  # la socia


def rut_valido(numero: int) -> str:
    from detective.normalizar import digito_verificador
    return f"{numero:,}".replace(",", ".") + "-" + digito_verificador(numero)


ANA, BETO, PROVEEDOR, SOCIA = (rut_valido(n) for n in (76000001, 76000002, 76000003, 11111111))


def _miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def banco(filas) -> str:
    """filas: (dd/mm/aaaa, glosa, monto con signo). Con dos lineas de preambulo: los datos parten en la fila 4."""
    lineas = ["Banco de Prueba;;;", ";;;", "Fecha;Descripcion;Cargos ($);Abonos ($)"]
    for fecha, glosa, monto in filas:
        lineas.append(f"{fecha};{glosa};{_miles(-monto) if monto < 0 else ''};{_miles(monto) if monto > 0 else ''}")
    return "\n".join(lineas) + "\n"


def rcv(filas) -> str:
    """filas: (tipo, rut, razon, folio, dd/mm/aaaa, neto[, iva]). Los datos parten en la fila 2."""
    lineas = ["Nro;Tipo Doc;Tipo Venta;Rut cliente;Razon Social;Folio;Fecha Docto;Monto Exento;Monto Neto;Monto IVA;Monto total"]
    for n, fila in enumerate(filas, start=1):
        tipo, rut, razon, folio, fecha, neto = fila[:6]
        iva = fila[6] if len(fila) > 6 else iva_de_neto(neto, 0.19)
        lineas.append(f"{n};{tipo};Del Giro;{rut};{razon};{folio};{fecha};0;{neto};{iva};{neto + iva}")
    return "\n".join(lineas) + "\n"


def cotizaciones(filas) -> str:
    """filas: (numero, dd/mm/aaaa, cliente, rut, neto, estado, fecha de aceptacion). Datos desde la fila 3."""
    lineas = ["Mis cotizaciones", "N Cotizacion;Fecha;Cliente;RUT;Servicio;Neto;IVA;Total;Estado;Fecha aceptacion"]
    for numero, fecha, cliente, rut, neto, estado, aceptada in filas:
        iva = iva_de_neto(neto, 0.19)
        lineas.append(f"{numero};{fecha};{cliente};{rut};Servicio;{neto};{iva};{neto + iva};{estado};{aceptada}")
    return "\n".join(lineas) + "\n"


def pos(filas) -> str:
    """filas: (aaaa-mm-dd, descripcion, monto, estado). Datos desde la fila 2."""
    lineas = ["fecha_creacion,id_operacion,descripcion,monto_bruto,comision_mp,monto_neto,estado,medio_pago"]
    for n, (fecha, descripcion, monto, estado) in enumerate(filas, start=1):
        lineas.append(f"{fecha}T10:00:00-03:00,{9000 + n},{descripcion},{monto:.2f},0.00,{monto:.2f},{estado},qr")
    return "\n".join(lineas) + "\n"


def equipo(filas) -> str:
    """filas: (nombre, email, estado, fecha de salida aaaa-mm-dd o vacio)."""
    return "nombre,email,cargo,estado,fecha_ingreso,fecha_salida\n" + "".join(
        f"{nombre},{email},Cargo,{estado},2020-01-01,{salida}\n" for nombre, email, estado, salida in filas)


def licencias(filas) -> str:
    """filas: (servicio, usuario, costo, estado)."""
    return "servicio,usuario,plan,costo_mensual_clp,estado\n" + "".join(
        f"{servicio},{usuario},Plan,{costo},{estado}\n" for servicio, usuario, costo, estado in filas)


def correr(archivos: dict, config: dict = None, **opciones):
    """Audita archivos escritos como texto. `config=False` simula que no hay config.json."""
    import json
    entradas = [Entrada(nombre, texto.encode("utf-8") if isinstance(texto, str) else texto)
                for nombre, texto in archivos.items()]
    if config is not False:
        entradas.append(Entrada("config.json", json.dumps({**CONFIG_BASE, **(config or {})}).encode("utf-8")))
    return auditar(entradas, cargar_plantillas(RAIZ / "plantillas"), **opciones)


def de_tipo(res, tipo: str) -> list:
    return [h for h in res.hallazgos if h.tipo == tipo]


def citas(hallazgo) -> list:
    return [(e.archivo, e.fila) for e in hallazgo.evidencia]
