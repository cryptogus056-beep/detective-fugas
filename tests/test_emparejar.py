from conftest import ANA, BETO, PROVEEDOR, banco, citas, correr, de_tipo, rcv

from detective.emparejar import asignar


def test_asignar_toma_el_mejor_par_y_reacomoda_para_no_dejar_a_nadie_solo():
    # i=0 prefiere j=0; i=1 SOLO puede ir con j=0. Si 0 se queda con j=0, 1 queda solo: hay que reacomodar.
    pares = [((0,), 0, 0), ((1,), 0, 1), ((2,), 1, 0)]
    assert asignar(pares) == {0: 1, 1: 0}
    assert asignar([((0,), 0, 0), ((1,), 1, 0)]) == {0: 0}          # uno a uno: j=0 se usa una sola vez
    assert asignar([]) == {}


def test_cada_documento_respalda_un_solo_abono():
    res = correr({
        "banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", 119000), ("12/09/2026", f"TRANSF. DE {ANA} ANA", 119000)]),
        "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "08/09/2026", 100000)]),
    })
    sin_doc = de_tipo(res, "abono_sin_documento")
    assert len(sin_doc) == 1
    assert citas(sin_doc[0]) == [("banco.csv", 5)]                   # el mas cercano a la factura se la queda


def test_si_la_glosa_trae_rut_se_prefiere_el_documento_de_ese_rut():
    res = correr({
        "banco.csv": banco([("20/08/2026", f"TRANSF. DE {BETO} BETO", 119000)]),
        "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1, "19/08/2026", 100000), (33, BETO, "Beto SpA", 2, "05/08/2026", 100000)]),
    })
    pendientes = de_tipo(res, "pago_pendiente_30d")
    assert len(pendientes) == 1 and pendientes[0].datos["cliente"] == "Ana SpA"   # la de Beto quedo pagada


def test_ventana_de_fechas_del_abono():
    """El documento puede ser hasta 60 dias anterior o hasta 7 dias posterior al abono."""
    def hallazgos(fecha_abono, fecha_doc):
        res = correr({"banco.csv": banco([(fecha_abono, f"TRANSF. DE {ANA} ANA", 59500)]),
                      "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, fecha_doc, 50000)])})
        return len(de_tipo(res, "abono_sin_documento"))
    assert hallazgos("10/09/2026", "13/09/2026") == 0        # senuelo: la boleta sale 3 dias despues
    assert hallazgos("10/09/2026", "17/09/2026") == 0        # dia 7: todavia calza
    assert hallazgos("10/09/2026", "18/09/2026") == 1        # dia 8: ya no
    assert hallazgos("10/10/2026", "11/08/2026") == 0        # 60 dias antes: calza
    assert hallazgos("10/10/2026", "10/08/2026") == 1        # 61 dias antes: no


def test_tolerancia_de_dos_pesos():
    def hallazgos(monto):
        res = correr({"banco.csv": banco([("10/09/2026", f"TRANSF. DE {ANA} ANA", monto)]),
                      "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "10/09/2026", 50000)])})
        return len(de_tipo(res, "abono_sin_documento"))
    assert hallazgos(59500) == hallazgos(59502) == hallazgos(59498) == 0
    assert hallazgos(59503) == 1


def test_devolucion_de_un_proveedor_reconocida_por_su_rut_aunque_la_glosa_no_lo_diga():
    compras = ("Nro;Tipo Doc;Tipo Compra;RUT Proveedor;Razon Social;Folio;Fecha Docto;Monto Exento;Monto Neto;"
               "Monto IVA Recuperable;Monto Total\n" f"1;33;Del Giro;{PROVEEDOR};Proveedor SpA;77;03/08/2026;0;20000;3800;23800\n")
    archivos = {"banco.csv": banco([("03/10/2026", f"TRANSF. DE {PROVEEDOR} PROVEEDOR SPA", 23800)]),
                "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 50000)])}
    assert len(de_tipo(correr(archivos), "abono_sin_documento")) == 1            # sin el registro de compras, es sospechoso
    con_compras = correr({**archivos, "rcv_compras.csv": compras})
    assert not de_tipo(con_compras, "abono_sin_documento")
    assert any("Dejé fuera 1 abono" in a for a in con_compras.avisos)
