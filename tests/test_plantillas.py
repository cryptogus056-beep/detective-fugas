import json

import pytest

from detective.config import cargar_config
from detective.lectores import ErrorLectura, leer_tabla
from detective.modelo import cargar_registros
from detective.plantillas import (ROLES, Plantilla, PlantillaNoEncontrada, cargar_plantillas, proponer_plantilla,
                                  reconocer_archivo)

ESPERADO = {
    "data/demo": {
        "cartola_banco.csv": ("banco", "banco_cargos_abonos_separados", 6, 86),
        "ventas_mercadopago.csv": ("pos", "mercadopago_ventas", 1, 47),
        "rcv_ventas.csv": ("rcv_ventas", "sii_rcv_ventas", 1, 78),
        "rcv_compras.csv": ("rcv_compras", "sii_rcv_compras", 1, 12),
        "cotizaciones.xlsx": ("cotizaciones", "cotizaciones_generica", 2, 49),
        "cotizaciones.csv": ("cotizaciones", "cotizaciones_generica", 2, 49),
        "equipo.csv": ("equipo", "equipo", 1, 5),
        "licencias.csv": ("licencias", "licencias", 1, 7),
    },
    "data/demo_b": {
        "movimientos_cuenta.csv": ("banco", "banco_monto_con_signo", 1, 85),
        "ventas_transbank.csv": ("pos", "transbank_ventas", 1, 48),
        "presupuestos.csv": ("cotizaciones", "presupuestos_generica", 1, 44),
        "rcv_ventas.csv": ("rcv_ventas", "sii_rcv_ventas", 1, 78),
        "rcv_compras.csv": ("rcv_compras", "sii_rcv_compras", 1, 12),
        "equipo.csv": ("equipo", "equipo", 1, 5),
        "licencias.csv": ("licencias", "licencias", 1, 7),
    },
}


@pytest.mark.parametrize("carpeta", sorted(ESPERADO))
def test_lee_todos_los_archivos_de_las_demos(raiz, plantillas, carpeta):
    """Checkpoint de la fase 1: 9 archivos en demo A y 8 en demo B (contando config.json)."""
    config = cargar_config((raiz / carpeta / "config.json").read_bytes())
    assert config.fecha_corte.isoformat() == "2026-10-31" and config.meses == 3
    archivos = sorted(p.name for p in (raiz / carpeta).iterdir() if p.is_file() and p.suffix in (".csv", ".xlsx"))
    assert archivos == sorted(ESPERADO[carpeta])
    for nombre, (rol, plantilla, fila_encabezado, registros) in ESPERADO[carpeta].items():
        lectura = reconocer_archivo(nombre, (raiz / carpeta / nombre).read_bytes(), plantillas)
        carga = cargar_registros(lectura, config)
        assert (lectura.plantilla.rol, lectura.plantilla.nombre) == (rol, plantilla), nombre
        assert lectura.fila_encabezado == fila_encabezado, nombre
        assert len(carga.registros) == registros and not carga.filas_saltadas, nombre


def test_incluye_las_plantillas_minimas_y_todas_estan_completas(plantillas):
    nombres = {p.nombre for p in plantillas}
    assert {"banco_cargos_abonos_separados", "banco_monto_con_signo", "mercadopago_ventas", "transbank_ventas",
            "sii_rcv_ventas", "sii_rcv_compras", "cotizaciones_generica", "presupuestos_generica", "equipo",
            "licencias"} <= nombres
    for p in plantillas:
        assert p.rol in ROLES and not p.faltantes(), p.nombre


def test_el_ejemplo_es_una_plantilla_valida_pero_no_se_carga_sola(raiz, plantillas):
    ejemplo = Plantilla.desde_dict(json.loads((raiz / "plantillas" / "_ejemplo.json").read_text(encoding="utf-8")))
    assert ejemplo.rol == "banco" and not ejemplo.faltantes()
    assert "mi_banco" not in {p.nombre for p in plantillas}


def test_banco_con_signo_y_banco_separado_dan_los_mismos_movimientos(plantillas):
    config = cargar_config(None)
    a = "Banco X;;;;\n;;;;\nFecha;Descripcion;Cargos ($);Abonos ($);Saldo ($)\n05/03/2026;ARRIENDO;650.000;;1.000\n06/03/2026;TRANSF. DE 12.345.678-5 ANA;;119.000;2.000\n"
    b = "﻿Fecha Movimiento,Glosa,Monto,Saldo Disponible\n2026-03-05,ARRIENDO,-650000,1000\n2026-03-06,TRANSF. DE 12.345.678-5 ANA,119000,2000\n"
    ra = cargar_registros(reconocer_archivo("a.csv", a.encode(), plantillas), config).registros
    rb = cargar_registros(reconocer_archivo("b.csv", b.encode("utf-8"), plantillas), config).registros
    assert [(m.fecha, m.descripcion, m.monto) for m in ra] == [(m.fecha, m.descripcion, m.monto) for m in rb]
    assert [m.monto for m in ra] == [-650000, 119000]
    assert ra[1].ruts == ["12.345.678-5"]
    assert [m.origen.fila for m in ra] == [4, 5] and [m.origen.fila for m in rb] == [2, 3]


def test_presupuesto_solo_con_neto_calcula_el_total(plantillas):
    texto = "Folio Presupuesto;Fecha Emision;Razon Social;RUT Cliente;Detalle;Valor Neto;Estado;Aceptado El\nP-1;2026-03-01;Cliente Uno;76.123.456-0;Servicio;100000;APROBADO;2026-03-02\n"
    lectura = reconocer_archivo("pres.csv", texto.encode(), plantillas)
    cot = cargar_registros(lectura, cargar_config(None)).registros[0]
    assert (cot.neto, cot.iva, cot.total, cot.estado) == (100000, 19000, 119000, "aceptada")
    assert cot.total_en_archivo is False


def test_filas_que_no_se_pueden_leer_se_informan_no_se_esconden(plantillas):
    texto = "Fecha;Descripcion;Cargos ($);Abonos ($)\n05/03/2026;BIEN;1.000;\nTOTAL;;1.000;\n06/03/2026;SIN MONTO;;\n"
    carga = cargar_registros(reconocer_archivo("c.csv", texto.encode(), plantillas), cargar_config(None))
    assert len(carga.registros) == 1
    assert carga.filas_saltadas == [(3, "sin fecha"), (4, "sin monto")]


def test_si_ninguna_plantilla_calza_el_error_dice_que_encontro_y_que_hacer(plantillas):
    texto = "Dia|Concepto|Importe\n01/02/2026|Algo|100\n02/02/2026|Otro|200\n"
    with pytest.raises(PlantillaNoEncontrada) as error:
        reconocer_archivo("raro.csv", texto.encode(), plantillas)
    mensaje = str(error.value)
    assert '"Dia"' in mensaje and '"Concepto"' in mensaje and '"Importe"' in mensaje
    assert "plantillas/_ejemplo.json" in mensaje and "python -m detective plantilla" in mensaje


def test_proponer_plantilla_para_un_banco_desconocido():
    texto = "Mi Banco\n\nFecha Operacion;Detalle Movimiento;Debitos;Creditos;Saldo\n03/02/2026;PAGO LUZ;45.000;;100\n"
    propuesta = proponer_plantilla(leer_tabla("mibanco.csv", texto.encode()))
    assert propuesta["rol"] == "banco" and propuesta["_fila_encabezado"] == 3
    assert propuesta["columnas"] == {"fecha": "Fecha Operacion", "descripcion": "Detalle Movimiento",
                                     "cargo": "Debitos", "abono": "Creditos"}
    assert propuesta["separador"] == ";" and propuesta["formato_fecha"] == ["%d/%m/%Y"]
    limpia = {k: v for k, v in propuesta.items() if not k.startswith("_")}
    plantilla = Plantilla.desde_dict(limpia)
    assert not plantilla.faltantes()
    lectura = reconocer_archivo("mibanco.csv", texto.encode(), [plantilla])       # la propuesta funciona tal cual
    assert lectura.fila_encabezado == 3


def test_plantilla_mal_escrita_da_error_claro(tmp_path):
    with pytest.raises(ErrorLectura, match="rol desconocido"):
        Plantilla.desde_dict({"nombre": "x", "rol": "bancos", "columnas": {}})
    with pytest.raises(ErrorLectura, match="no existe para"):
        Plantilla.desde_dict({"nombre": "x", "rol": "banco", "columnas": {"glosa": "Glosa"}})
    (tmp_path / "mala.json").write_text("{no es json", encoding="utf-8")
    with pytest.raises(ErrorLectura, match="no es un JSON"):
        cargar_plantillas(tmp_path)


def test_config_por_defecto_y_errores(tmp_path):
    config = cargar_config(None)
    assert (config.tasa_iva, config.dias_pago_pendiente, config.dias_gracia_cotizacion, config.tolerancia_clp) == (0.19, 30, 15, 2)
    assert config.avisos and "valores por defecto" in config.avisos[0]
    with pytest.raises(ErrorLectura, match="fecha_corte"):
        cargar_config(b'{"fecha_corte": "ayer"}')
    with pytest.raises(ErrorLectura, match="JSON"):
        cargar_config(b"{")
