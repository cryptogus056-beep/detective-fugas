"""Verificador: la regla de oro en codigo.

Vuelve a abrir cada archivo citado, va a la fila indicada y comprueba que la fecha y el
monto que dice el hallazgo esten escritos ahi. No confia en lo que cargaron las reglas:
lee el archivo de nuevo, desde los bytes. Lo que no calza se descarta con su motivo.
"""
from __future__ import annotations

from .lectores import ErrorLectura, leer_tabla
from .normalizar import formato_clp, formato_fecha, parsear_fecha, parsear_numero


class Fuente:
    """Un archivo de entrada tal como lo necesita el verificador."""

    def __init__(self, nombre: str, datos: bytes, separador=None, formatos_fecha=(), numeros="chileno",
                 fila_encabezado: int = 0):
        self.nombre, self.datos, self.separador = nombre, datos, separador
        self.formatos_fecha, self.numeros, self.fila_encabezado = list(formatos_fecha), numeros, fila_encabezado
        self._tabla = None

    def tabla(self):
        if self._tabla is None:
            self._tabla = leer_tabla(self.nombre, self.datos, self.separador)
        return self._tabla


def revisar_evidencia(evidencia, fuentes: dict, tolerancia: int):
    """None si la cita es correcta; si no, el motivo en palabras simples."""
    fuente = fuentes.get(evidencia.archivo)
    if fuente is None:
        return f"cita el archivo '{evidencia.archivo}', que no está entre los archivos leídos"
    try:
        fila = fuente.tabla().fila(evidencia.fila)
    except (ErrorLectura, TypeError, ValueError):
        return f"no pude volver a abrir '{evidencia.archivo}'"
    if fila is None:
        return f"la fila {evidencia.fila} de '{evidencia.archivo}' no existe o está vacía"
    if fila.numero <= fuente.fila_encabezado:
        return f"la fila {evidencia.fila} de '{evidencia.archivo}' es parte del encabezado, no un dato"
    if evidencia.fecha is not None:
        fechas = [parsear_fecha(c, fuente.formatos_fecha) for c in fila.celdas]
        if evidencia.fecha not in fechas:
            return (f"la fila {evidencia.fila} de '{evidencia.archivo}' no tiene la fecha "
                    f"{formato_fecha(evidencia.fecha)}")
    if evidencia.monto_clp is not None:
        montos = [parsear_numero(c, fuente.numeros) for c in fila.celdas]
        if not any(m is not None and abs(abs(m) - abs(evidencia.monto_clp)) <= tolerancia for m in montos):
            return (f"la fila {evidencia.fila} de '{evidencia.archivo}' no tiene el monto "
                    f"{formato_clp(evidencia.monto_clp)}")
    return None


def verificar(hallazgos: list, fuentes: dict, tolerancia: int = 2):
    """Separa los hallazgos en confirmados y descartados (con motivo)."""
    confirmados, descartados = [], []
    for h in hallazgos:
        motivo = None
        if not h.evidencia:
            motivo = "no trae evidencia"
        elif not any(e.completa for e in h.evidencia):
            motivo = "ninguna evidencia tiene archivo, fila, fecha y monto a la vez"
        else:
            for e in h.evidencia:
                motivo = revisar_evidencia(e, fuentes, tolerancia)
                if motivo:
                    break
        if motivo:
            h.verificado = False
            descartados.append({"motivo": f"Evidencia no verificada: {motivo}.", "hallazgo": h})
        else:
            h.verificado = True
            confirmados.append(h)
    return confirmados, descartados
