"""mensajes_cobro.md cumple la seccion 6.3: son borradores, nunca se envia nada."""
import sys
import types

import pytest
from conftest import ANA, banco, correr, cotizaciones, rcv

from detective import mensajes
from detective.__main__ import main
from detective.mensajes import ENCABEZADO, borradores, mensajes_md

PERSONA = "12.345.678-5"


@pytest.fixture()
def res():
    return correr({
        "banco.csv": banco([("09/10/2026", f"TRANSF. DE {ANA} ANA SPA", 398650)]),
        "rcv_ventas.csv": rcv([(33, ANA, "Ana SpA", 1203, "20/08/2026", 665000)]),
        "cotizaciones.csv": cotizaciones([("C-7", "30/08/2026", "Pedro Soto", PERSONA, 100000, "Aceptada", "03/09/2026")]),
    })


def test_encabezado_de_borrador_exacto(res):
    md = mensajes_md(res)
    assert ENCABEZADO == "BORRADORES. Nada de esto se ha enviado. Revísalo antes de usarlo."
    assert md.splitlines()[2] == f"> **{ENCABEZADO}**"


def test_un_mensaje_por_cobro_y_una_nota_interna_para_el_resto(res):
    lista = borradores(res)
    por_codigo = {b["codigo"]: b for b in lista}
    assert sorted(por_codigo) == ["M01", "M02", "N01"]
    assert [b["codigo"] for b in lista] == [h.mensaje for h in res.hallazgos]
    factura = next(b for b in lista if "Factura" in b["asunto"])
    assert factura["clase"] == "mensaje" and factura["para"] == "Ana SpA"
    for dato in ("1203", "$791.350", "20/08/2026"):                            # monto, folio y fecha
        assert dato in factura["cuerpo"]
    assert "72 días" not in factura["cuerpo"] and "31/10/2026" not in factura["cuerpo"]    # nada que envejezca al enviarlo
    assert "72 días" in " ".join(factura["antes"])                                       # el dato queda para el dueño
    cot = next(b for b in lista if "Cotización" in b["asunto"])
    for dato in ("C-7", "$119.000", "03/09/2026"):
        assert dato in cot["cuerpo"]
    nota = por_codigo["N01"]
    assert nota["clase"] == "nota" and "Confirma primero qué fue el abono del 09/10/2026 por $398.650" in nota["cuerpo"]
    assert "config.json" not in nota["cuerpo"] and "no emitas nada y avísale a tu contador" in nota["cuerpo"]
    for b in (factura, cot):                                                    # datos que completa el dueño
        assert "[tu banco, tipo y número de cuenta, RUT y correo para el comprobante]" in b["cuerpo"]
        assert "[tu correo o teléfono]" in b["cuerpo"] and "[Tu nombre]" in b["cuerpo"]
    assert "se la adjuntamos" in cot["cuerpo"] and "esta semana" not in cot["cuerpo"]
    assert "adjúntala al mensaje" in " ".join(cot["antes"])
    md = mensajes_md(res, lista)
    assert md.index("## Mensajes para clientes") < md.index("## Notas internas (no se envían a nadie)")


def test_por_defecto_trata_de_usted_y_se_puede_pedir_tu(res):
    usted = "\n".join(b["cuerpo"] for b in borradores(res) if b["clase"] == "mensaje")
    tu = "\n".join(b["cuerpo"] for b in borradores(res, "tu") if b["clase"] == "mensaje")
    assert "le escribo" in usted and "usted aceptó" in usted and "Te escribo" not in usted
    assert "Te escribo" in tu and "aceptaste" in tu and "usted" not in tu
    assert "Buenos días, equipo de Ana SpA:" in usted and "Buenos días, Pedro Soto:" in usted  # empresa y persona
    assert "Hola, equipo de Ana SpA:" in tu and "Hola, Pedro Soto:" in tu
    assert "la boleta o factura" in usted                                                    # a una persona


def test_tono_cordial_y_firme_sin_amenazas(res):
    for b in borradores(res) + borradores(res, "tu"):
        texto = b["cuerpo"].lower()
        for palabra in ("demanda", "dicom", "abogad", "intereses", "último aviso", "ultimo aviso", "urgente"):
            assert palabra not in texto
        if b["clase"] == "mensaje":
            assert texto.rstrip().endswith("empresa de prueba spa")            # firma con el nombre de la empresa


def test_sin_cobros_lo_dice_y_no_inventa_mensajes():
    res = correr({"banco.csv": banco([("09/10/2026", f"TRANSF. DE {ANA} ANA", 398650)]),
                  "rcv_ventas.csv": rcv([(39, ANA, "Ana", 1, "01/08/2026", 1000)])})
    md = mensajes_md(res)
    assert "No hay cobros pendientes a clientes" in md and "### N01" in md and "### M01" not in md


def test_el_codigo_de_mensajes_no_sabe_enviar_nada(raiz):
    for nombre in ("mensajes.py", "informe.py", "auditoria.py"):
        texto = (raiz / "detective" / nombre).read_text(encoding="utf-8")
        for peligro in ("smtplib", "urllib", "requests", "http.client", "socket", "subprocess"):
            assert peligro not in texto, f"{nombre} usa {peligro}"


# --------------------------------------------------------------------------- capa LLM opcional (simulada)

class Falso:
    """Cliente simulado: no hay red ni gasto. Guarda lo que se le pidio."""

    def __init__(self, transformar, stop_reason="end_turn", error=None):
        self.transformar, self.stop_reason, self.error, self.pedidos = transformar, stop_reason, error, []
        self.messages = self

    def create(self, **kwargs):
        self.pedidos.append(kwargs)
        if self.error:
            raise self.error
        texto = self.transformar(kwargs["messages"][0]["content"])
        return types.SimpleNamespace(stop_reason=self.stop_reason,
                                     content=[types.SimpleNamespace(type="thinking", thinking=""),
                                              types.SimpleNamespace(type="text", text=texto)])


@pytest.fixture()
def llm(monkeypatch):
    falso = types.ModuleType("anthropic")
    for nombre in ("AuthenticationError", "RateLimitError", "APIConnectionError"):
        setattr(falso, nombre, type(nombre, (Exception,), {}))
    falso.APIStatusError = type("APIStatusError", (Exception,), {"status_code": 500})
    falso.Anthropic = lambda: (_ for _ in ()).throw(AssertionError("una prueba no debe crear un cliente real"))
    monkeypatch.setitem(sys.modules, "anthropic", falso)
    from detective import llm as modulo
    return modulo, falso


def test_llm_pule_solo_los_mensajes_y_conserva_los_datos(res, llm):
    modulo, _ = llm
    cliente = Falso(lambda t: t.replace("Junto con saludar, le escribo", "Le escribo cordialmente"))
    lista, avisos = modulo.pulir(borradores(res), cliente)
    assert not avisos and len(cliente.pedidos) == 2                       # las notas internas no se mandan al modelo
    assert all(b["pulido"] for b in lista if b["clase"] == "mensaje")
    assert not any(b["pulido"] for b in lista if b["clase"] == "nota")
    assert "Le escribo cordialmente" in lista[0]["cuerpo"] or "Le escribo cordialmente" in lista[1]["cuerpo"]
    pedido = cliente.pedidos[0]
    assert pedido["model"] == "claude-haiku-5-5" and "no cambies ni quites ningún dato" in pedido["system"]
    assert "Textos pulidos" not in mensajes_md(res, borradores(res)) and ENCABEZADO in mensajes_md(res, lista)


def test_llm_si_pierde_un_dato_o_falla_queda_la_plantilla(res, llm):
    modulo, falso = llm
    originales = borradores(res)
    casos = {
        "pierde el monto": Falso(lambda t: t.replace("$791.350", "el monto adeudado").replace("$119.000", "lo acordado")),
        "usa guion largo": Falso(lambda t: t + " " + chr(0x2014) + " gracias"),
        "respuesta vacia": Falso(lambda t: "  "),
        "se corto": Falso(lambda t: t, stop_reason="max_tokens"),
        "se nego": Falso(lambda t: t, stop_reason="refusal"),
        "clave invalida": Falso(lambda t: t, error=falso.AuthenticationError()),
        "sin conexion": Falso(lambda t: t, error=falso.APIConnectionError()),
        "error del servidor": Falso(lambda t: t, error=falso.APIStatusError()),
    }
    for nombre, cliente in casos.items():
        lista, avisos = modulo.pulir(originales, cliente)
        assert [b["cuerpo"] for b in lista] == [b["cuerpo"] for b in originales], nombre
        assert avisos and not any(b["pulido"] for b in lista), nombre
    assert len(casos["clave invalida"].pedidos) == 1                      # no insiste con una clave mala


def test_llm_sin_clave_avisa_y_usa_plantillas(tmp_path, capsys, monkeypatch, raiz, llm):
    modulo, _ = llm
    assert modulo.disponible({}) == (False, modulo.disponible({})[1]) and "ANTHROPIC_API_KEY" in modulo.disponible({})[1]
    assert modulo.disponible({"ANTHROPIC_API_KEY": "x"}) == (True, "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["auditar", "--datos", str(raiz / "data" / "demo"), "--salida", str(tmp_path), "--llm"]) == 0
    assert "No encontré la variable ANTHROPIC_API_KEY: usé las plantillas fijas" in capsys.readouterr().out
    assert ENCABEZADO in (tmp_path / "mensajes_cobro.md").read_text(encoding="utf-8")


def test_cli_tratamiento_tu(tmp_path, raiz):
    assert main(["auditar", "--datos", str(raiz / "data" / "demo"), "--salida", str(tmp_path), "--tratamiento", "tu"]) == 0
    texto = (tmp_path / "mensajes_cobro.md").read_text(encoding="utf-8")
    assert "Te escribo" in texto and "le escribo" not in texto


def test_no_hay_claves_escritas_en_el_repositorio(raiz):
    import re
    patron = re.compile(r"sk-ant-[A-Za-z0-9_-]{8,}|ANTHROPIC_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{12,}")
    for ruta in raiz.rglob("*"):
        if ruta.is_file() and ".git" not in ruta.parts and ruta.suffix in {".py", ".md", ".json", ".js", ".html", ".txt", ".env"}:
            assert not patron.search(ruta.read_text(encoding="utf-8", errors="replace")), ruta
