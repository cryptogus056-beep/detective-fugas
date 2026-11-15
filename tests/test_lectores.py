import datetime as dt
import io

import pytest

from detective.lectores import ErrorLectura, leer_tabla, separadores_probables


def test_preambulo_y_numero_de_linea_fisica():
    texto = "Banco de Prueba;;;\nTitular: X;;;\n;;;\nFecha;Detalle;Cargos;Abonos\n01/02/2026;UNO;1.000;\n\n02/02/2026;DOS;;2.000\n"
    tabla = leer_tabla("cartola.csv", texto.encode("utf-8"))
    assert tabla.separador == ";"
    assert [f.numero for f in tabla.filas] == [1, 2, 4, 5, 7]        # las lineas vacias no cuentan, pero numeran
    assert tabla.fila(5).celdas == ["01/02/2026", "UNO", "1.000", ""]
    assert tabla.fila(7).crudo == "02/02/2026;DOS;;2.000"
    assert tabla.fila(6) is None


def test_campo_con_salto_de_linea_no_corre_la_numeracion():
    texto = 'fecha,glosa,monto\n2026-01-01,"linea uno\nlinea dos",100\n2026-01-02,simple,200\n'
    tabla = leer_tabla("x.csv", texto.encode("utf-8"))
    assert [f.numero for f in tabla.filas] == [1, 2, 4]              # la fila 2 ocupa las lineas 2 y 3
    assert tabla.fila(4).celdas == ["2026-01-02", "simple", "200"]
    assert "linea dos" in tabla.fila(2).crudo


def test_bom_y_latin1():
    con_bom = "﻿Fecha,Glosa,Monto\n2026-01-01,Café,100\n".encode("utf-8")
    tabla = leer_tabla("a.csv", con_bom)
    assert tabla.codificacion == "utf-8-sig"
    assert tabla.filas[0].celdas[0] == "Fecha"                      # el BOM no ensucia el encabezado
    latin = "Fecha;Descripción;Monto\n01/01/2026;Peñalolén;100\n".encode("latin-1")
    tabla = leer_tabla("b.csv", latin)
    assert tabla.codificacion == "latin-1"
    assert tabla.filas[1].celdas[1] == "Peñalolén"


def test_separador_coma_aunque_haya_punto_y_coma_en_un_texto():
    texto = "fecha,descripcion,monto\n2026-01-01,pago; con detalle,100\n2026-01-02,otro,200\n2026-01-03,mas,300\n"
    assert separadores_probables(texto)[0] == ","
    texto = "Fecha;Detalle;Monto\n01/01/2026;Pago, con coma;1.000,50\n02/01/2026;Otro;2.000,00\n"
    assert separadores_probables(texto)[0] == ";"


def test_fin_de_linea_de_windows():
    tabla = leer_tabla("w.csv", b"a;b\r\n1;2\r\n3;4\r\n")
    assert [f.numero for f in tabla.filas] == [1, 2, 3]
    assert tabla.fila(3).crudo == "3;4"


def test_xlsx_con_titulo_fechas_nativas_y_fila_de_excel():
    from openpyxl import Workbook
    libro = Workbook()
    hoja = libro.active
    hoja.append(["Mis cotizaciones"])
    hoja.append(["Numero", "Fecha", "Total"])
    hoja.append(["C-1", dt.datetime(2026, 3, 5), 119000])
    hoja.append([None, None, None])
    hoja.append(["C-2", dt.datetime(2026, 3, 9), 59500])
    memoria = io.BytesIO()
    libro.save(memoria)
    tabla = leer_tabla("cot.xlsx", memoria.getvalue())
    assert tabla.formato == "xlsx"
    assert [f.numero for f in tabla.filas] == [1, 2, 3, 5]
    assert tabla.fila(3).celdas[1] == dt.datetime(2026, 3, 5)
    assert tabla.fila(5).crudo == "C-2 | 09/03/2026 | 59500"


def test_errores_claros():
    with pytest.raises(ErrorLectura, match="Excel antiguo"):
        leer_tabla("viejo.xls", b"x")
    with pytest.raises(ErrorLectura, match="Acepto archivos"):
        leer_tabla("foto.pdf", b"x")
    with pytest.raises(ErrorLectura, match="como Excel"):
        leer_tabla("roto.xlsx", b"esto no es un excel")
