import datetime as dt

from conftest import ANA, banco, correr, rcv

from detective.reglas import Evidencia, Hallazgo
from detective.verificador import Fuente, revisar_evidencia, verificar

CARTOLA = banco([("09/10/2026", f"TRANSF. DE {ANA} ANA", 398650), ("10/10/2026", "PAGO LUZ", -45000)])


def fuentes():
    return {"banco.csv": Fuente("banco.csv", CARTOLA.encode(), ";", ["%d/%m/%Y"], "chileno", fila_encabezado=3)}


def hallazgo(*evidencias):
    return Hallazgo(tipo="abono_sin_documento", subtipo="banco", titulo="t", descripcion="d", monto_clp=1,
                    impacto_clp=1, impacto_mensual_clp=1, recurrente=False, evidencia=list(evidencias),
                    accion_sugerida="a")


def test_cita_correcta_se_confirma():
    buena = Evidencia("banco.csv", 4, dt.date(2026, 10, 9), 398650, "x")
    assert revisar_evidencia(buena, fuentes(), 2) is None
    cargo = Evidencia("banco.csv", 5, dt.date(2026, 10, 10), 45000, "un cargo se cita en positivo")
    assert revisar_evidencia(cargo, fuentes(), 2) is None
    confirmados, descartados = verificar([hallazgo(buena)], fuentes())
    assert len(confirmados) == 1 and confirmados[0].verificado and not descartados


def test_descarta_una_cita_falsa_y_dice_por_que():
    """Criterio de aceptacion: el verificador descarta una cita falsa."""
    casos = {
        "fila equivocada": (Evidencia("banco.csv", 5, dt.date(2026, 10, 9), 398650, "x"), "no tiene la fecha 09/10/2026"),
        "monto con digitos cambiados": (Evidencia("banco.csv", 4, dt.date(2026, 10, 9), 389650, "x"), "no tiene el monto $389.650"),
        "fecha equivocada": (Evidencia("banco.csv", 4, dt.date(2026, 10, 8), 398650, "x"), "no tiene la fecha 08/10/2026"),
        "fila que no existe": (Evidencia("banco.csv", 40, dt.date(2026, 10, 9), 398650, "x"), "no existe"),
        "archivo que no se leyo": (Evidencia("otro.csv", 4, dt.date(2026, 10, 9), 398650, "x"), "no está entre los archivos"),
    }
    for nombre, (evidencia, esperado) in casos.items():
        confirmados, descartados = verificar([hallazgo(evidencia)], fuentes())
        assert not confirmados, nombre
        assert esperado in descartados[0]["motivo"], nombre
        assert descartados[0]["hallazgo"].verificado is False
    encabezado = Evidencia("banco.csv", 3, None, None, "el encabezado no es un dato")
    assert "encabezado" in revisar_evidencia(encabezado, fuentes(), 2)


def test_un_hallazgo_necesita_al_menos_una_evidencia_completa():
    sin_fecha = Evidencia("banco.csv", 4, None, 398650, "x")
    assert not verificar([hallazgo(sin_fecha)], fuentes())[0]
    assert not verificar([hallazgo()], fuentes())[0]
    completa = Evidencia("banco.csv", 4, dt.date(2026, 10, 9), 398650, "x")
    assert verificar([hallazgo(sin_fecha, completa)], fuentes())[0]
    mala = Evidencia("banco.csv", 5, dt.date(2026, 1, 1), 5, "x")
    assert not verificar([hallazgo(completa, mala)], fuentes())[0]          # una sola cita mala bota el hallazgo


def test_el_verificador_corre_siempre_dentro_de_la_auditoria(monkeypatch):
    """Si una regla citara mal una fila, el hallazgo no llega al informe: queda en descartados."""
    from detective.reglas import abono_sin_documento as regla
    original = regla.detectar

    def con_trampa(ctx):
        hallazgos = original(ctx)
        hallazgos[0].evidencia[0].fila += 1            # la regla "se equivoca" de fila
        return hallazgos

    monkeypatch.setattr(regla, "detectar", con_trampa)
    res = correr({"banco.csv": CARTOLA, "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    assert not res.hallazgos
    assert len(res.descartados) == 1 and "Evidencia no verificada" in res.descartados[0]["motivo"]
