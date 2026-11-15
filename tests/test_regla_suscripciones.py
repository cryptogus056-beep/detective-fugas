from conftest import banco, citas, correr, de_tipo, equipo, licencias, rcv

TIPO = "suscripcion_duplicada_o_huerfana"
EQUIPO = equipo([("Carla Soto", "carla@x.cl", "Activo", ""), ("Bruno Vera", "bruno@x.cl", "Inactivo", "2026-07-31"),
                 ("Mati Reyes", "mati@x.cl", "Inactivo", "2026-05-31")])


def cobros(glosa, monto, dias, meses=(8, 9, 10)):
    return [(f"{d:02d}/{m:02d}/2026", glosa, -monto) for m in meses for d in dias]


def test_suscripcion_cobrada_dos_veces_al_mes_con_una_sola_licencia():
    res = correr({
        "banco.csv": banco(cobros("COMPRA TARJETA XXXX4321 DISENO* PRO", 12990, (3, 17))),
        "licencias.csv": licencias([("Diseno Pro", "carla@x.cl", 12990, "Activa")]),
    })
    [h] = de_tipo(res, TIPO)
    assert h.subtipo == "duplicada" and h.recurrente is True
    assert citas(h) == [("banco.csv", n) for n in range(4, 10)] + [("licencias.csv", 2)]   # un solo hallazgo con todo
    assert h.monto_clp == 12990 and h.impacto_mensual_clp == 12990 and h.impacto_clp == 38970
    assert h.evidencia[-1].fecha is None and h.evidencia[-1].monto_clp == 12990            # licencias no tiene fechas
    assert "los días 3 y 17" in h.descripcion


def test_senuelos_de_duplicadas():
    lic = [("Diseno Pro", "carla@x.cl", 12990, "Activa"), ("Nube Plus", "carla@x.cl", 12990, "Activa"),
           ("Correo Equipo", "carla@x.cl", 8600, "Activa"), ("Correo Equipo", "bruno2@x.cl", 8600, "Activa")]
    res = correr({
        "banco.csv": banco(
            cobros("COMPRA TARJETA DISENO* PRO", 12990, (3,))             # una vez al mes
            + cobros("COMPRA TARJETA NUBE*PLUS", 12990, (8,))             # otro servicio que cuesta lo mismo
            + cobros("COMPRA TARJETA CORREO*EQUIPO", 8600, (2, 2))        # dos cobros, pero hay dos licencias
            + cobros("COMISION TRANSFERENCIA", 300, (5, 12, 19))),        # no es un servicio con licencias
        "licencias.csv": licencias(lic),
    })
    assert not de_tipo(res, TIPO)


def test_doble_cobro_en_un_solo_mes_no_alcanza():
    res = correr({
        "banco.csv": banco(cobros("COMPRA DISENO PRO", 12990, (3, 17), meses=(9,)) + cobros("COMPRA DISENO PRO", 12990, (3,), meses=(8, 10))),
        "licencias.csv": licencias([("Diseno Pro", "carla@x.cl", 12990, "Activa")]),
    })
    assert not de_tipo(res, TIPO)


def test_licencia_activa_de_alguien_que_ya_se_fue():
    res = correr({
        "banco.csv": banco(cobros("COMPRA TARJETA CORREO*EQUIPO", 17200, (2,))),
        "licencias.csv": licencias([("Correo Equipo", "carla@x.cl", 8600, "Activa"), ("Correo Equipo", "bruno@x.cl", 8600, "Activa")]),
        "equipo.csv": EQUIPO,
    })
    [h] = de_tipo(res, TIPO)
    assert h.subtipo == "huerfana" and h.recurrente is True
    assert h.monto_clp == 8600 and h.impacto_mensual_clp == 8600 and h.impacto_clp == 25800      # 3 meses
    assert citas(h) == [("banco.csv", 4), ("banco.csv", 5), ("banco.csv", 6), ("licencias.csv", 3), ("equipo.csv", 3)]
    cobro, licencia, persona = h.evidencia[0], h.evidencia[3], h.evidencia[4]
    assert (cobro.fecha.isoformat(), cobro.monto_clp) == ("2026-08-02", 17200)       # completa: fecha y monto
    assert licencia.fecha is None and licencia.monto_clp == 8600
    assert persona.fecha.isoformat() == "2026-07-31" and persona.monto_clp is None
    assert "Bruno Vera dejó la empresa el 31/07/2026" in h.descripcion and h.verificado


def test_senuelos_de_huerfanas():
    res = correr({
        "banco.csv": banco(cobros("COMPRA TARJETA CORREO*EQUIPO", 8600, (2,))),
        "licencias.csv": licencias([("Correo Equipo", "carla@x.cl", 8600, "Activa"),          # persona activa
                                    ("Correo Equipo", "mati@x.cl", 8600, "Cancelada"),         # ya se dio de baja
                                    ("Correo Equipo", "externo@otro.cl", 8600, "Activa")]),    # no esta en el equipo
        "equipo.csv": EQUIPO,
    })
    assert not de_tipo(res, TIPO)


def test_quien_se_fue_a_mitad_del_periodo_solo_cuenta_los_meses_siguientes():
    res = correr({
        "banco.csv": banco(cobros("COMPRA CORREO EQUIPO", 8600, (2,))),
        "licencias.csv": licencias([("Correo Equipo", "ana@x.cl", 8600, "Activa")]),
        "equipo.csv": equipo([("Ana Paz", "ana@x.cl", "Inactivo", "2026-09-15")]),
    })
    [h] = de_tipo(res, TIPO)
    assert h.datos["meses"] == 1 and h.impacto_clp == 8600                  # solo octubre
    assert citas(h)[0] == ("banco.csv", 6)                                  # solo el cobro posterior a su salida


def test_huerfana_sin_cobro_en_el_banco_no_se_cuenta_pero_se_avisa():
    res = correr({
        "banco.csv": banco([("01/08/2026", "COMISION", -990)]),
        "licencias.csv": licencias([("Correo Equipo", "bruno@x.cl", 8600, "Activa")]),
        "equipo.csv": EQUIPO,
    })
    assert not res.hallazgos                                                 # regla de oro: sin fila con fecha y monto, no hay hallazgo
    assert any("no encontré el cobro de Correo Equipo" in a for a in res.avisos)


def test_sin_licencias_o_sin_equipo_se_avisa():
    res = correr({"banco.csv": banco(cobros("COMPRA DISENO PRO", 12990, (3, 17))), "rcv_ventas.csv": rcv([(39, "66.666.666-6", "CF", 1, "01/08/2026", 1000)])})
    assert not de_tipo(res, TIPO)
    assert any("No había archivo de licencias" in n for n in res.no_revisado)
    assert any("No había archivo del equipo" in n for n in res.no_revisado)
