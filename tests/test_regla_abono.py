from conftest import ANA, BETO, SOCIA, banco, citas, correr, cotizaciones, de_tipo, pos, rcv

TIPO = "abono_sin_documento"
VENTAS = rcv([(39, ANA, "Ana", 1, "05/08/2026", 50000)])


def test_transferencia_sin_boleta_ni_factura():
    res = correr({"banco.csv": banco([("05/08/2026", f"TRANSF. DE {ANA} ANA", 59500),
                                      ("09/10/2026", f"TRANSF. DE {BETO} BETO SPA", 398650)]),
                  "rcv_ventas.csv": VENTAS})
    [h] = de_tipo(res, TIPO)
    assert citas(h) == [("banco.csv", 5)] and h.subtipo == "banco"
    e = h.evidencia[0]
    assert (e.fecha.isoformat(), e.monto_clp) == ("2026-10-09", 398650)
    assert e.fila_original == f"09/10/2026;TRANSF. DE {BETO} BETO SPA;;398.650"
    assert h.monto_clp == 398650 and h.impacto_clp == 398650 - 335000 == 63650      # el IVA en riesgo
    assert h.impacto_mensual_clp == 21217 and h.recurrente is False               # promedio de 3 meses
    assert "[sin verificar el monto de la multa]" in h.descripcion and h.verificado


def test_senuelos_del_banco_no_son_fuga():
    res = correr({"banco.csv": banco([
        ("03/08/2026", "TRANSF. MERCADO LIQUIDACION TARJETAS", 250000),        # liquidacion del POS
        ("02/09/2026", f"TRANSF. DE {SOCIA} CAMILA", 1500000),                 # RUT de la socia, excluido
        ("04/09/2026", "Aporte Socio capital", 700000),                        # palabra excluida, otra escritura
        ("03/10/2026", f"DEVOLUCIÓN {BETO} PROVEEDOR", 23800),                 # con tilde: igual se excluye
        ("02/08/2026", f"TRANSF. DE {ANA} ANA", 59500),                        # llega 3 dias antes de su boleta
        ("15/08/2026", "PAGO ARRIENDO", -650000),                              # un cargo nunca es un abono
    ]), "rcv_ventas.csv": VENTAS})
    assert not de_tipo(res, TIPO)
    assert any("Dejé fuera 4 abonos" in a for a in res.avisos)


def test_traspaso_desde_el_rut_de_la_propia_empresa_no_es_venta():
    archivos = {"banco.csv": banco([("10/09/2026", f"TRANSF. DE {BETO} MI OTRA CUENTA", 500000)]), "rcv_ventas.csv": VENTAS}
    assert len(de_tipo(correr(archivos), TIPO)) == 1
    assert not de_tipo(correr(archivos, {"rut_empresa": BETO}), TIPO)


def test_venta_con_tarjeta_aprobada_sin_boleta_y_sus_senuelos():
    res = correr({
        "banco.csv": banco([("01/08/2026", "COMISION", -990)]),
        "pos.csv": pos([("2026-09-18", "Mantencion", 73500, "approved"),        # fila 2: sin boleta -> fuga
                        ("2026-09-25", "Visita", 60000, "rejected"),            # fila 3: rechazada, no entro plata
                        ("2026-09-10", "Filtro", 23800, "approved"),            # fila 4: boleta el mismo dia
                        ("2026-09-11", "Control", 35700, "approved"),           # fila 5: boleta al dia siguiente
                        ("2026-09-12", "Limpieza", 47600, "approved")]),        # fila 6: boleta 2 dias despues -> fuga
        "rcv_ventas.csv": rcv([(39, "66.666.666-6", "Consumidor final", 1, "10/09/2026", 20000),
                               (39, "66.666.666-6", "Consumidor final", 2, "12/09/2026", 30000),
                               (39, "66.666.666-6", "Consumidor final", 3, "14/09/2026", 40000)]),
    })
    hallazgos = sorted(de_tipo(res, TIPO), key=lambda h: h.evidencia[0].fila)
    assert [citas(h) for h in hallazgos] == [[("pos.csv", 2)], [("pos.csv", 6)]]
    assert all(h.subtipo == "pos" for h in hallazgos)
    assert hallazgos[0].impacto_clp == 73500 - 61765


def test_abono_sin_rut_en_la_glosa_baja_la_confianza_y_queda_como_ambiguo():
    res = correr({"banco.csv": banco([("10/09/2026", "DEPOSITO EN EFECTIVO", 80000)]), "rcv_ventas.csv": VENTAS})
    [h] = de_tipo(res, TIPO)
    assert h.confianza == "media" and "no sé quién pagó" in h.descripcion
    assert [(a["archivo"], a["fila"]) for a in res.ambiguas] == [("banco.csv", 4)]


def test_clasificacion_solo_puede_quitar_hallazgos_ambiguos_nunca_agregar():
    archivos = {"banco.csv": banco([("10/09/2026", "DEPOSITO EN EFECTIVO", 80000),
                                    ("11/09/2026", f"TRANSF. DE {BETO} BETO", 90000)]), "rcv_ventas.csv": VENTAS}
    clasificaciones = [{"archivo": "banco.csv", "fila": 4, "categoria": "aporte_socio", "motivo": "depósito de la dueña"},
                       {"archivo": "banco.csv", "fila": 5, "categoria": "devolucion"},        # no era ambigua: se ignora
                       {"archivo": "banco.csv", "fila": 99, "categoria": "venta"}]            # fila inventada: se ignora
    res = correr(archivos, clasificaciones=clasificaciones)
    assert [citas(h) for h in de_tipo(res, TIPO)] == [[("banco.csv", 5)]]
    assert len(res.descartados) == 1 and "aporte_socio" in res.descartados[0]["motivo"]
    assert sum("no estaba marcada como ambigua" in a for a in res.avisos) == 2


def test_sin_registro_de_ventas_no_se_inventan_fugas_y_se_avisa():
    res = correr({"banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 59500)])})
    assert not res.hallazgos
    assert any("No había Registro de Ventas" in n for n in res.no_revisado)


def test_cotizacion_pagada_por_transferencia_pero_sin_factura_se_informa_una_sola_vez():
    res = correr({
        "banco.csv": banco([("20/09/2026", f"TRANSF. DE {ANA} ANA SPA", 119000)]),
        "rcv_ventas.csv": VENTAS,
        "cotizaciones.csv": cotizaciones([("C-1", "01/09/2026", "Ana SpA", ANA, 100000, "Aceptada", "02/09/2026")]),
    })
    assert not de_tipo(res, "cotizacion_sin_cobro")           # la plata SI entro: lo que falta es el documento
    [h] = de_tipo(res, TIPO)
    assert "C-1" in h.descripcion
