import datetime as dt

import pytest

from detective.normalizar import (contiene_palabras, digito_verificador, extraer_ruts, formato_clp, iva_de_neto,
                                  meses_entre, neto_de_total, normalizar_estado, normalizar_glosa, normalizar_rut,
                                  parsear_fecha, parsear_numero, ESTADOS_COTIZACION, ESTADOS_POS)


@pytest.mark.parametrize("texto, esperado", [
    ("1.234.567", 1234567),
    ("$ 1.234.567", 1234567),
    ("-34400", -34400),
    ("65000.00", 65000),            # dos decimales: el punto es decimal
    ("34.400", 34400),              # tres digitos despues del punto: es de miles
    ("12.990", 12990),
    ("1.234,50", 1235),             # punto de miles y coma decimal
    ("1,234.50", 1235),             # formato de Estados Unidos
    ("820", 820),
    ("0", 0),
    ("(1.500)", -1500),             # parentesis contables
    ("1.500-", -1500),
    ("$-2.000", -2000),
    (8600, 8600),
    (65000.0, 65000),
])
def test_numeros_chilenos(texto, esperado):
    assert parsear_numero(texto) == esperado


@pytest.mark.parametrize("texto", ["", "   ", None, "abc", "12/08/2026", "76.123.456-7", "1.2.3", "N/A", True])
def test_lo_que_no_es_numero(texto):
    assert parsear_numero(texto) is None


def test_modo_decimal_punto_trata_el_punto_como_decimal():
    assert parsear_numero("322500.00", "decimal_punto") == 322500
    assert parsear_numero("34.400", "decimal_punto") == 34       # 34,4 redondeado
    assert parsear_numero("1,234", "decimal_punto") == 1234      # la coma pasa a ser de miles
    assert parsear_numero("34.400", "chileno") == 34400


def test_redondeo_comercial_no_bancario():
    assert parsear_numero("2,5") == 3 and parsear_numero("3,5") == 4
    assert iva_de_neto(100000, 0.19) == 19000
    assert iva_de_neto(271008, 0.19) == 51492
    assert neto_de_total(322500, 0.19) == 271008


@pytest.mark.parametrize("texto, esperado", [
    ("31/10/2026", dt.date(2026, 10, 31)),
    ("31-10-2026", dt.date(2026, 10, 31)),
    ("2026-10-31", dt.date(2026, 10, 31)),
    ("2026-08-03T11:39:00-03:00", dt.date(2026, 8, 3)),
    ("2026-08-03T23:59:00Z", dt.date(2026, 8, 3)),      # se respeta el dia escrito, no se cambia de zona
    ("02/08/2026 12:00:00", dt.date(2026, 8, 2)),
    (dt.datetime(2026, 9, 1, 10, 30), dt.date(2026, 9, 1)),   # fecha nativa de Excel
    (dt.date(2026, 9, 1), dt.date(2026, 9, 1)),
    (46266, dt.date(2026, 9, 1)),                             # numero de serie de Excel
])
def test_fechas(texto, esperado):
    assert parsear_fecha(texto) == esperado


@pytest.mark.parametrize("texto", ["", None, "hola", "32/13/2026", "1234567", "COT-0101", 12, "12.990"])
def test_lo_que_no_es_fecha(texto):
    assert parsear_fecha(texto) is None


def test_formato_de_fecha_de_la_plantilla_tiene_prioridad():
    assert parsear_fecha("03/04/2026", ["%m/%d/%Y"]) == dt.date(2026, 3, 4)
    assert parsear_fecha("03/04/2026") == dt.date(2026, 4, 3)


def test_rut_se_normaliza_y_se_valida():
    assert normalizar_rut("77111357-5") == ("77.111.357-5", True)
    assert normalizar_rut("77.111.357-5") == ("77.111.357-5", True)
    assert normalizar_rut("20680243-k") == ("20.680.243-K", True)
    assert normalizar_rut(" 20.680.243 - K ") == ("20.680.243-K", True)
    rut, valido = normalizar_rut("77.111.357-9")            # digito verificador malo: se usa, pero se avisa
    assert rut == "77.111.357-9" and valido is False
    assert normalizar_rut("no es rut") == (None, False)
    assert digito_verificador(66666666) == "6"


def test_extraer_rut_de_una_glosa():
    assert extraer_ruts("TRANSF. DE 20.680.243-K KAREN FICTICIO MUNOZ") == ["20.680.243-K"]
    assert extraer_ruts("TRANSF. DE 77111357-5 EMPRESA") == ["77.111.357-5"]
    assert extraer_ruts("COMPRA TARJETA MICROSOFT*365") == []
    assert extraer_ruts("PAGO 00-123-45678-09") == []


def test_glosa_sin_tarjeta_ni_codigos_pero_con_nombre_completo():
    assert normalizar_glosa("Compra Tarjeta CANVA* PRO") == "COMPRA TARJETA CANVA PRO"
    assert normalizar_glosa("COMPRA TARJETA MICROSOFT*365") == "COMPRA TARJETA MICROSOFT 365"   # el 365 se queda
    assert normalizar_glosa("COMPRA XXXX1234 SPOTIFY 20260803 REF AB12CD34") == "COMPRA SPOTIFY REF"
    assert normalizar_glosa("Suscripción Diseño ****9876") == "SUSCRIPCION DISENO"
    assert contiene_palabras(normalizar_glosa("COMPRA TARJETA CANVA* PRO"), "Canva Pro")
    assert not contiene_palabras(normalizar_glosa("COMPRA TARJETA DROPBOX*PLUS"), "Canva Pro")
    assert not contiene_palabras(normalizar_glosa("COMPRA TARJETA CANVAS"), "Canva")       # palabra completa


def test_estados_escritos_de_distintas_formas():
    for texto in ("Aceptada", "APROBADO", "Aprobada", "OK", " aceptado "):
        assert normalizar_estado(texto, ESTADOS_COTIZACION) == "aceptada"
    assert normalizar_estado("RECHAZADO", ESTADOS_COTIZACION) == "rechazada"
    assert normalizar_estado("ENVIADO", ESTADOS_COTIZACION) == "pendiente"
    assert normalizar_estado("???", ESTADOS_COTIZACION) == "otro"
    assert normalizar_estado("approved", ESTADOS_POS) == "aprobada"
    assert normalizar_estado("Rechazada", ESTADOS_POS) == "rechazada"
    assert normalizar_estado("Lista", ESTADOS_COTIZACION, {"aceptada": ["lista"]}) == "aceptada"


def test_formato_de_montos_y_meses():
    assert formato_clp(1234567) == "$1.234.567"
    assert formato_clp(-500) == "-$500"
    assert formato_clp(0) == "$0"
    assert meses_entre(dt.date(2026, 8, 1), dt.date(2026, 10, 31)) == 3
    assert meses_entre(dt.date(2026, 12, 15), dt.date(2027, 1, 10)) == 2
    assert meses_entre(dt.date(2026, 8, 1), dt.date(2026, 8, 1)) == 1
