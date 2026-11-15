from conftest import ANA, BETO, banco, citas, correr, de_tipo, pos, rcv

TIPO = "pago_pendiente_30d"


def test_factura_sin_pago_hace_mas_de_30_dias():
    res = correr({"banco.csv": banco([("01/08/2026", "COMISION", -990)]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1203, "20/08/2026", 665000)])})
    [h] = de_tipo(res, TIPO)
    assert citas(h) == [("rcv_ventas.csv", 2)]
    assert (h.evidencia[0].fecha.isoformat(), h.evidencia[0].monto_clp) == ("2026-08-20", 791350)
    assert h.impacto_clp == 791350 and h.datos["dias"] == 72 and "72 días" in h.descripcion
    assert h.mensaje.startswith("M")


def test_limite_exacto_de_30_dias():
    def n(fecha):
        res = correr({"banco.csv": banco([("01/08/2026", "COMISION", -990)]),
                      "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, fecha, 100000)])})
        return len(de_tipo(res, TIPO))
    assert n("01/10/2026") == 0          # 30 dias justos: todavia no
    assert n("30/09/2026") == 1          # 31 dias


def test_senuelos_pagada_a_los_29_dias_boleta_y_factura_reciente():
    res = correr({
        "banco.csv": banco([("07/10/2026", f"TRANSF. DE {ANA} ANA SPA", 119000)]),
        "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "08/09/2026", 100000),         # pagada a los 29 dias
                               (39, BETO, "Beto", 2, "10/08/2026", 50000),            # boleta: no se cobra a plazo
                               (33, BETO, "Beto SpA", 3, "20/10/2026", 300000)]),     # 11 dias: reciente
    })
    assert not de_tipo(res, TIPO)


def test_factura_anulada_con_nota_de_credito_no_se_cobra():
    res = correr({"banco.csv": banco([("01/08/2026", "COMISION", -990)]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "10/08/2026", 100000),
                                         (61, ANA, "Ana SpA", 50, "12/08/2026", 100000)])})
    assert not de_tipo(res, TIPO)


def test_factura_pagada_con_tarjeta_no_queda_pendiente_ni_como_venta_sin_boleta():
    res = correr({"banco.csv": banco([("01/08/2026", "COMISION", -990)]),
                  "pos.csv": pos([("2026-08-15", "Pago factura", 119000, "approved")]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "10/08/2026", 100000)])})
    assert not res.hallazgos


def test_sin_banco_no_se_puede_saber_y_se_avisa():
    res = correr({"rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "10/08/2026", 100000)])})
    assert not de_tipo(res, TIPO)
    assert any("No había cartola del banco" in n for n in res.no_revisado)
