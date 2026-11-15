"""Capa opcional: pulir los borradores de cobro con un modelo de lenguaje.

Solo se usa si pides `--llm` Y existe la variable de entorno ANTHROPIC_API_KEY. Usarla
cuesta dinero (se cobra por uso de la API), por eso esta apagada por defecto. Nunca
envia mensajes a clientes: solo reescribe el texto del borrador.

Regla de oro tambien aqui: si el texto pulido pierde un dato (monto, fecha, folio o
numero de cotizacion), se descarta y queda la plantilla original.

Este modulo no se copia a la web: la pagina no hace llamadas de red con tus datos.
"""
from __future__ import annotations

import os

MODELO = "claude-haiku-5-5"       # modelo economico: la tarea es solo mejorar la redaccion
VARIABLE = "ANTHROPIC_API_KEY"
GUION_LARGO = chr(0x2014)
INSTRUCCIONES = (
    "Eres redactor de una pyme chilena. Recibirás el borrador de un mensaje de cobro para un cliente. "
    "Mejora la redacción para que suene cordial, claro y firme, en español neutro latinoamericano. "
    "Reglas estrictas: (1) no cambies ni quites ningún dato: montos, fechas, números de factura o de "
    "cotización, nombres y firma deben quedar exactamente como están; (2) no agregues datos, plazos, "
    "amenazas, intereses ni descuentos que no estén en el borrador; (3) conserva el tratamiento (usted o tú) "
    "del borrador; (4) no uses el guion largo, usa comas, dos puntos o paréntesis; (5) responde solo con el "
    "texto final del mensaje, sin comentarios ni comillas."
)


def disponible(entorno=None):
    """(True, "") si se puede usar; si no, (False, motivo en palabras simples)."""
    entorno = os.environ if entorno is None else entorno
    if not entorno.get(VARIABLE):
        return False, (f"No encontré la variable {VARIABLE}: usé las plantillas fijas (funcionan igual y son gratis).")
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False, ("Falta la librería de Anthropic: instálala con \"pip install anthropic\" o sigue con las "
                       "plantillas fijas. Usé las plantillas.")
    return True, ""


def _texto(respuesta) -> str:
    return "".join(b.text for b in respuesta.content if getattr(b, "type", "") == "text").strip()


def _problema(original: dict, pulido: str):
    """Por que no se puede aceptar el texto pulido (None si esta bien)."""
    if not pulido:
        return "el modelo no devolvió texto"
    if GUION_LARGO in pulido:
        return "el texto pulido usa guion largo"
    faltan = [dato for dato in original["obligatorio"] if dato not in pulido]
    if faltan:
        return f"el texto pulido perdió datos ({', '.join(faltan)})"
    if len(pulido) > 3 * len(original["cuerpo"]):
        return "el texto pulido es mucho más largo que el borrador"
    return None


def pulir(borradores: list, cliente=None, modelo: str = MODELO):
    """Devuelve (borradores, avisos). Solo toca los mensajes a clientes, no las notas internas."""
    import anthropic
    cliente = cliente or anthropic.Anthropic()
    resultado, avisos, detenido = [], [], False
    for b in borradores:
        if b["clase"] != "mensaje" or detenido:
            resultado.append(b)
            continue
        try:
            respuesta = cliente.messages.create(
                model=modelo, max_tokens=16000, system=INSTRUCCIONES, output_config={"effort": "low"},
                messages=[{"role": "user", "content": b["cuerpo"]}])
        except anthropic.AuthenticationError:
            avisos.append(f"La clave de {VARIABLE} no es válida: usé las plantillas fijas.")
            detenido = True
            resultado.append(b)
            continue
        except anthropic.RateLimitError:
            avisos.append("La API pidió esperar (límite de uso): el resto de los mensajes quedó con la plantilla fija.")
            detenido = True
            resultado.append(b)
            continue
        except anthropic.APIStatusError as error:
            avisos.append(f"{b['codigo']}: la API respondió con error {error.status_code}; quedó la plantilla fija.")
            resultado.append(b)
            continue
        except anthropic.APIConnectionError:
            avisos.append("No hubo conexión con la API: usé las plantillas fijas.")
            detenido = True
            resultado.append(b)
            continue
        if respuesta.stop_reason != "end_turn":
            avisos.append(f"{b['codigo']}: el modelo no terminó el texto ({respuesta.stop_reason}); quedó la plantilla fija.")
            resultado.append(b)
            continue
        pulido = _texto(respuesta)
        problema = _problema(b, pulido)
        if problema:
            avisos.append(f"{b['codigo']}: {problema}; quedó la plantilla fija.")
            resultado.append(b)
        else:
            resultado.append({**b, "cuerpo": pulido, "pulido": True})
    return resultado, avisos
