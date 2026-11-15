from conftest import ANA, BETO, banco, citas, correr, cotizaciones, de_tipo, rcv

TIPO = "cotizacion_sin_cobro"
BANCO = banco([("01/08/2026", "COMISION", -990)])


def caso(cots, docs=()):
    return correr({"banco.csv": BANCO, "cotizaciones.csv": cotizaciones(cots),
                   "rcv_ventas.csv": rcv(list(docs) or [(39, "66.666.666-6", "Consumidor final", 900, "01/08/2026", 1000)])})


def test_aceptada_y_nunca_facturada():
    res = caso([("C-1", "30/08/2026", "Ana SpA", ANA, 1000000, "Aceptada", "03/09/2026")])
    [h] = de_tipo(res, TIPO)
    assert citas(h) == [("cotizaciones.csv", 3)]
    e = h.evidencia[0]
    assert (e.fecha.isoformat(), e.monto_clp) == ("2026-09-03", 1190000)       # fecha de aceptacion y total
    assert h.monto_clp == h.impacto_clp == 1190000 and h.impacto_mensual_clp == 396667
    assert "58 días" in h.descripcion and h.mensaje == "M01" and h.accion_sugerida.endswith("M01.")


def test_senuelos_rechazada_pendiente_y_recien_aceptada():
    res = caso([("C-1", "01/09/2026", "Ana SpA", ANA, 100000, "Rechazada", ""),
                ("C-2", "01/09/2026", "Ana SpA", ANA, 200000, "Pendiente", ""),
                ("C-3", "22/10/2026", "Ana SpA", ANA, 300000, "Aceptada", "24/10/2026")])    # 7 dias: en gracia
    assert not de_tipo(res, TIPO)


def test_dias_de_gracia_exactos():
    def n(aceptada):
        return len(de_tipo(caso([("C-1", "01/10/2026", "Ana SpA", ANA, 100000, "Aceptada", aceptada)]), TIPO))
    assert n("17/10/2026") == 0          # 14 dias antes del corte
    assert n("16/10/2026") == 1          # 15 dias: ya cuenta ("al menos 15 dias")


def test_formas_de_calzar_con_su_documento():
    cot = [("C-1", "01/09/2026", "Ana SpA", ANA, 100000, "OK", "02/09/2026")]
    assert not de_tipo(caso(cot, [(33, ANA, "Ana SpA", 1, "05/09/2026", 100000)]), TIPO)                 # mismo neto
    assert not de_tipo(caso(cot, [(39, ANA, "Ana SpA", 1, "05/09/2026", 99999, 19001)]), TIPO)           # mismo total
    assert not de_tipo(caso(cot, [(33, ANA, "Ana SpA", 1, "05/09/2026", 84034, 15966)]), TIPO)           # total = neto cotizado
    assert de_tipo(caso(cot, [(33, BETO, "Beto SpA", 1, "05/09/2026", 100000)]), TIPO)                   # otro RUT: no calza
    assert de_tipo(caso(cot, [(33, ANA, "Ana SpA", 1, "20/08/2026", 100000)]), TIPO)                     # anterior a la cotizacion
    assert de_tipo(caso(cot, [(33, ANA, "Ana SpA", 1, "05/09/2026", 150000)]), TIPO)                     # otro monto


def test_un_documento_no_cubre_dos_cotizaciones():
    res = caso([("C-1", "01/09/2026", "Ana SpA", ANA, 100000, "Aceptada", "02/09/2026"),
                ("C-2", "03/09/2026", "Ana SpA", ANA, 100000, "Aceptada", "04/09/2026")],
               [(33, ANA, "Ana SpA", 1, "05/09/2026", 100000)])
    assert len(de_tipo(res, TIPO)) == 1


def test_presupuesto_solo_con_neto_cita_el_neto_que_esta_en_la_fila():
    texto = ("Folio Presupuesto;Fecha Emision;Razon Social;RUT Cliente;Detalle;Valor Neto;Estado;Aceptado El\n"
             f"P-9;2026-09-01;Ana SpA;{ANA};Instalacion;200000;APROBADO;2026-09-02\n")
    res = correr({"banco.csv": BANCO, "presupuestos.csv": texto,
                  "rcv_ventas.csv": rcv([(39, "66.666.666-6", "Consumidor final", 900, "01/08/2026", 1000)])})
    [h] = de_tipo(res, TIPO)
    assert h.monto_clp == 238000                       # total calculado: neto + 19%
    assert h.evidencia[0].monto_clp == 200000          # pero la evidencia cita lo que dice la fila
    assert "solo el neto" in h.descripcion and h.verificado
