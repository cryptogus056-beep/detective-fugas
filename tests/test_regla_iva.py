from conftest import ANA, banco, citas, correr, cotizaciones, de_tipo, rcv

TIPO = "diferencia_iva"
BANCO = banco([("01/08/2026", "COMISION", -990)])


def test_iva_mal_calculado():
    res = correr({"banco.csv": banco([("15/10/2026", f"TRANSF. DE {ANA} ANA", 500500)]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1222, "06/10/2026", 455000, 45500)])})   # IVA al 10%
    [h] = de_tipo(res, TIPO)
    assert h.subtipo == "iva_mal_calculado" and citas(h) == [("rcv_ventas.csv", 2)]
    assert h.impacto_clp == 86450 - 45500 == 40950 and h.monto_clp == 500500
    assert "(10%)" in h.descripcion and "(19%)" in h.descripcion and "de menos" in h.descripcion
    assert len(res.hallazgos) == 1                              # esta pagada y no es otra cosa


def test_senuelo_redondeo_de_un_peso_en_boletas():
    res = correr({"banco.csv": BANCO, "rcv_ventas.csv": rcv([
        (39, ANA, "Ana", 1, "05/10/2026", 271008, 51492),       # exacto
        (39, ANA, "Ana", 2, "05/10/2026", 267227, 50774),       # +1 peso
        (39, ANA, "Ana", 3, "05/10/2026", 24790, 4708),         # -2 pesos: todavia dentro de la tolerancia
        (34, ANA, "Ana", 4, "05/10/2026", 0, 0)])})             # exenta: sin neto afecto
    assert not de_tipo(res, TIPO)


def test_tres_pesos_de_diferencia_ya_se_informa_y_tambien_el_iva_de_mas():
    res = correr({"banco.csv": BANCO, "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "25/10/2026", 100000, 19003),
                                                             (39, ANA, "Ana", 2, "25/10/2026", 100000, 18997)])})
    hallazgos = de_tipo(res, TIPO)
    assert sorted(h.impacto_clp for h in hallazgos) == [3, 3]
    assert sum("de más" in h.descripcion for h in hallazgos) == 1


def test_neto_cobrado_como_total():
    res = correr({
        "banco.csv": banco([("22/09/2026", f"TRANSF. DE {ANA} ANA SPA", 835000)]),
        "cotizaciones.csv": cotizaciones([("C-21", "02/09/2026", "Ana SpA", ANA, 835000, "Aceptada", "04/09/2026")]),
        "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1212, "10/09/2026", 701681, 133319)]),      # total 835.000
    })
    [h] = res.hallazgos                                           # ni "cotizacion sin cobro" ni "IVA mal calculado"
    assert h.tipo == TIPO and h.subtipo == "neto_como_total"
    assert citas(h) == [("rcv_ventas.csv", 2), ("cotizaciones.csv", 3), ("banco.csv", 4)]
    assert h.monto_clp == 835000 and h.impacto_clp == 993650 - 835000 == 158650
    assert "salió de tu bolsillo" in h.descripcion


def test_cotizacion_facturada_correctamente_no_es_diferencia():
    res = correr({"banco.csv": banco([("22/09/2026", f"TRANSF. DE {ANA} ANA SPA", 993650)]),
                  "cotizaciones.csv": cotizaciones([("C-21", "02/09/2026", "Ana SpA", ANA, 835000, "Aceptada", "04/09/2026")]),
                  "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1212, "10/09/2026", 835000)])})
    assert not res.hallazgos
