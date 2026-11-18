import json

from conftest import ANA, CONFIG_BASE, banco, rcv

from detective.__main__ import main


def test_version(capsys):
    assert main(["version"]) == 0
    assert "Detective de Fugas Pyme 1." in capsys.readouterr().out


def test_sin_comando_muestra_la_ayuda(capsys):
    assert main([]) == 2
    assert "auditar" in capsys.readouterr().out


def test_plantilla_reconocida_y_desconocida(tmp_path, capsys):
    conocido = tmp_path / "cartola.csv"
    conocido.write_text(banco([("10/08/2026", "ALGO", -1000)]), encoding="utf-8")
    assert main(["plantilla", "--archivo", str(conocido)]) == 0
    salida = capsys.readouterr().out
    assert "banco_cargos_abonos_separados" in salida and "Encabezado en la fila 3" in salida

    raro = tmp_path / "mibanco.csv"
    raro.write_text("Fecha Operacion;Detalle Movimiento;Debitos;Creditos\n03/02/2026;LUZ;45.000;\n", encoding="utf-8")
    assert main(["plantilla", "--archivo", str(raro)]) == 0
    salida = capsys.readouterr().out
    assert "Ninguna plantilla calza" in salida and '"cargo": "Debitos"' in salida and "plantillas/mi_mibanco.json" in salida

    assert main(["plantilla", "--archivo", str(tmp_path / "no_existe.csv")]) == 2


def test_auditar_escribe_los_resultados(tmp_path, capsys):
    datos, salida = tmp_path / "datos", tmp_path / "salida"
    datos.mkdir()
    (datos / "banco.csv").write_text(banco([("09/10/2026", f"TRANSF. DE {ANA} ANA", 398650)]), encoding="utf-8")
    (datos / "rcv_ventas.csv").write_text(rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)]), encoding="utf-8")
    (datos / "config.json").write_text(json.dumps(CONFIG_BASE), encoding="utf-8")
    assert main(["auditar", "--datos", str(datos), "--salida", str(salida)]) == 0
    texto = capsys.readouterr().out
    assert "Hallazgos verificados: 1" in texto and "No revisado" in texto
    hallazgos = json.loads((salida / "hallazgos.json").read_text(encoding="utf-8"))
    assert hallazgos["empresa"] == "Empresa de Prueba SpA" and len(hallazgos["hallazgos"]) == 1
    assert (salida / "descartados.json").exists() and (salida / "ambiguas.json").exists()


def test_auditar_con_errores_explica_y_no_revienta(tmp_path, capsys):
    assert main(["auditar", "--datos", str(tmp_path / "nada")]) == 2
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    (vacia / "raro.csv").write_text("Dia|Concepto\n1|x\n", encoding="utf-8")
    assert main(["auditar", "--datos", str(vacia), "--salida", str(tmp_path / "s")]) == 2
    assert "No reconocí ningún archivo" in capsys.readouterr().out


def test_modo_agentico_clasificaciones_y_descartes_solo_pueden_quitar(tmp_path, capsys):
    datos, salida = tmp_path / "datos", tmp_path / "salida"
    datos.mkdir()
    (datos / "banco.csv").write_text(banco([("09/10/2026", f"TRANSF. DE {ANA} ANA", 398650),
                                            ("10/10/2026", "DEPOSITO EN EFECTIVO", 80000),
                                            ("11/10/2026", "DEPOSITO CHEQUE", 70000)]), encoding="utf-8")
    (datos / "rcv_ventas.csv").write_text(rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)]), encoding="utf-8")
    (datos / "config.json").write_text(json.dumps(CONFIG_BASE), encoding="utf-8")
    assert main(["auditar", "--datos", str(datos), "--salida", str(salida)]) == 0
    base = json.loads((salida / "hallazgos.json").read_text(encoding="utf-8"))["hallazgos"]
    ambiguas = json.loads((salida / "ambiguas.json").read_text(encoding="utf-8"))
    assert len(base) == 3 and [a["fila"] for a in ambiguas] == [5, 6]

    clasificaciones = tmp_path / "clasificaciones.json"
    clasificaciones.write_text(json.dumps([{"archivo": "banco.csv", "fila": 5, "categoria": "aporte_socio", "motivo": "x"},
                                           {"archivo": "banco.csv", "fila": 6, "categoria": "venta", "motivo": "y"}]), encoding="utf-8")
    descartes = tmp_path / "verificacion.json"
    descartes.write_text(json.dumps({"confirmados": ["H02"], "descartados": [{"id": "H01", "motivo": "prueba"},
                                                                             {"id": "H99", "motivo": "no existe"}]}), encoding="utf-8")
    assert main(["auditar", "--datos", str(datos), "--salida", str(salida), "--clasificaciones", str(clasificaciones),
                 "--descartes", str(descartes)]) == 0
    final = json.loads((salida / "hallazgos.json").read_text(encoding="utf-8"))
    citas = [(h["id"], h["evidencia"][0]["fila"]) for h in final["hallazgos"]]
    assert citas == [("H02", 6)]                                     # quedo solo el deposito clasificado como venta
    fuera = json.loads((salida / "descartados.json").read_text(encoding="utf-8"))
    assert sorted(d["motivo"].split(":")[0] for d in fuera) == ['Clasificado como "aporte_socio" (no es una venta)',
                                                                "Descartado por el verificador de segunda opinión"]
    assert any("H99" in a for a in final["avisos"])
    assert "| 1 |" in (salida / "informe.md").read_text(encoding="utf-8")


def test_volver_a_auditar_lo_mismo_no_deja_cambios_falsos(tmp_path, raiz):
    """Regresion: correr el detector reescribia hallazgos.json con la hora nueva y bloqueaba un git pull."""
    assert main(["auditar", "--datos", str(raiz / "data" / "demo"), "--salida", str(tmp_path)]) == 0
    antes = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    import time
    time.sleep(1.1)
    assert main(["auditar", "--datos", str(raiz / "data" / "demo"), "--salida", str(tmp_path)]) == 0
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == antes
