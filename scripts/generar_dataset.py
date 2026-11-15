#!/usr/bin/env python3
"""Genera el dataset FICTICIO del Detective de Fugas Pyme.

Todo es inventado: la empresa, los clientes, los RUT (formato valido, elegidos al azar),
los montos y los movimientos. Si un RUT coincide con uno real es pura casualidad.

Uso:
    python scripts/generar_dataset.py                 # variante A en data/demo
    python scripts/generar_dataset.py --variante b    # variante B en data/demo_b
    python scripts/generar_dataset.py --todas

La salida es reproducible: misma semilla, mismos archivos.
Esconde exactamente 12 fugas de 5 tipos y escribe la llave de respuestas en
<carpeta>/_respuestas/respuestas.json. El detector NUNCA debe leer esa carpeta.
"""
import argparse
import csv
import datetime as dt
import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INICIO = dt.date(2026, 8, 1)
CORTE = dt.date(2026, 10, 31)
MESES = 3

# --------------------------------------------------------------------------- utilidades

def dv_rut(numero: int) -> str:
    s, m = 0, 2
    for d in reversed(str(numero)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - (s % 11)
    return "0" if r == 11 else "K" if r == 10 else str(r)


def fmt_rut(numero: int) -> str:
    return f"{numero:,}".replace(",", ".") + "-" + dv_rut(numero)


def iva(neto: int) -> int:
    return (neto * 19 + 50) // 100


def neto_desde_total(total: int) -> int:
    return (total * 100 + 59) // 119


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def d_cl(f: dt.date) -> str:
    return f.strftime("%d/%m/%Y")


def sin_tildes(s: str) -> str:
    t = str.maketrans("áéíóúÁÉÍÓÚñÑüÜ", "aeiouAEIOUnNuU")
    return s.translate(t)


# --------------------------------------------------------------------------- catalogos ficticios

EMPRESAS_BASE = [
    "Panaderia Demo El Trigal SpA", "Hostal Ficticio Rio Claro Ltda", "Clinica Dental Demo Sonrisa SpA",
    "Minimarket Ficticio Las Lomas SpA", "Gimnasio Demo Fuerza Sur SpA", "Restaurante Ficticio La Caleta Ltda",
    "Colegio Demo Los Aromos", "Farmacia Ficticia Vida SpA", "Oficina Contable Demo Cuentas Claras SpA",
    "Taller Ficticio Motores del Valle Ltda", "Cafeteria Demo Grano Fino SpA", "Bodega Ficticia Austral SpA",
    "Optica Demo Mirada SpA", "Veterinaria Ficticia Patitas SpA", "Hotel Demo Bahia Azul SpA",
    "Inmobiliaria Ficticia Altos del Sur SpA",
]
NOMBRES = ["Ana", "Benjamin", "Carla", "Diego", "Elena", "Felipe", "Gabriela", "Hector", "Isidora", "Joaquin",
           "Karen", "Luis", "Martina", "Nicolas", "Olga", "Pablo", "Rocio", "Sebastian", "Tamara", "Vicente"]
APELLIDOS = ["Perez", "Soto", "Munoz", "Rojas", "Diaz", "Contreras", "Silva", "Morales", "Fuentes", "Vargas"]
PROVEEDORES_BASE = [
    ("Frioparts Demo SpA", "repuestos"), ("Gases Refrigerantes Ficticios Ltda", "gas"),
    ("Herramientas Demo del Sur SpA", "herramientas"), ("Combustibles Ficticios Ruta 5 SpA", "combustible"),
    ("Ductos y Filtros Demo SpA", "filtros"),
]
SERVICIOS = [
    "Mantencion preventiva equipo split", "Instalacion equipo 12.000 BTU", "Instalacion equipo 24.000 BTU",
    "Reparacion compresor", "Carga de gas refrigerante", "Limpieza de ductos", "Contrato mantencion trimestral",
    "Diagnostico y reparacion tarjeta electronica", "Mantencion camara de frio", "Revision sistema de ventilacion",
]

# --------------------------------------------------------------------------- generador


class Generador:
    def __init__(self, semilla: int, variante: str):
        self.r = random.Random(semilla)
        self.variante = variante
        self.totales_usados = set()
        self.ruts_usados = set()
        self.cot_n = 100 if variante == "a" else 500
        self.folio_f = 1200 if variante == "a" else 3400
        self.folio_b = 5100 if variante == "a" else 8800
        self.op_mp = 70_000_000_000 if variante == "a" else 400_000
        # registros canonicos
        self.banco = []        # {fecha, desc, cargo, abono, leak}
        self.pos = []          # ventas Mercado Pago / Transbank
        self.ventas = []       # RCV ventas
        self.compras = []      # RCV compras
        self.cots = []         # cotizaciones
        self.licencias = []
        self.equipo = []
        self.fugas = {}        # id -> metadatos
        self.senuelos = []

    # ---- helpers
    def rut(self, empresa: bool) -> str:
        while True:
            n = self.r.randint(76_000_000, 77_999_999) if empresa else self.r.randint(9_000_000, 24_999_999)
            if n not in self.ruts_usados:
                self.ruts_usados.add(n)
                return fmt_rut(n)

    def neto_unico(self, lo: int, hi: int, paso: int = 5000) -> int:
        while True:
            neto = self.r.randint(lo // paso, hi // paso) * paso
            t = neto + iva(neto)
            if t not in self.totales_usados and neto not in self.totales_usados:
                self.totales_usados.update({t, neto})
                return neto

    def total_unico(self, lo: int, hi: int, paso: int = 500) -> int:
        while True:
            t = self.r.randint(lo // paso, hi // paso) * paso
            if t not in self.totales_usados:
                self.totales_usados.add(t)
                return t

    def fecha(self, a: dt.date, b: dt.date) -> dt.date:
        return a + dt.timedelta(days=self.r.randint(0, (b - a).days))

    def nueva_cot(self, fecha, cliente, servicio, neto, estado, f_acept, leak=None):
        self.cot_n += 1
        c = dict(numero=f"COT-{self.cot_n:04d}", fecha=fecha, cliente=cliente["nombre"], rut=cliente["rut"],
                 servicio=servicio, neto=neto, iva=iva(neto), total=neto + iva(neto), estado=estado,
                 fecha_aceptacion=f_acept, leak=leak)
        self.cots.append(c)
        return c

    def nueva_venta(self, tipo, fecha, cliente, neto, iva_monto, leak=None):
        if tipo == 33:
            self.folio_f += 1
            folio = self.folio_f
        else:
            self.folio_b += 1
            folio = self.folio_b
        v = dict(tipo=tipo, folio=folio, fecha=fecha, rut=cliente["rut"], razon=cliente["nombre"], neto=neto,
                 iva=iva_monto, total=neto + iva_monto, leak=leak)
        self.ventas.append(v)
        return v

    def abono_transf(self, fecha, cliente, monto, leak=None):
        desc = f"TRANSF. DE {cliente['rut']} {sin_tildes(cliente['nombre']).upper()}"[:60]
        self.banco.append(dict(fecha=fecha, desc=desc, cargo=0, abono=monto, leak=leak))

    def cargo(self, fecha, desc, monto, leak=None):
        self.banco.append(dict(fecha=fecha, desc=desc, cargo=monto, abono=0, leak=leak))

    def venta_pos(self, fecha, desc, bruto, estado="aprobado", leak=None, medio=None):
        self.op_mp += self.r.randint(1000, 99999)
        com = (bruto * 349 + 5000) // 10000
        medio = medio or self.r.choice(["tarjeta_debito", "tarjeta_credito", "qr", "link_de_pago"])
        p = dict(fecha=fecha, hora=f"{self.r.randint(9, 19):02d}:{self.r.randint(0, 59):02d}", id=self.op_mp, desc=desc,
                 bruto=bruto, comision=com if estado == "aprobado" else 0,
                 neto=bruto - com if estado == "aprobado" else 0, estado=estado, medio=medio, leak=leak)
        self.pos.append(p)
        return p

    # ---- construccion
    def construir(self):
        r = self.r
        nombres_emp = EMPRESAS_BASE[:]
        r.shuffle(nombres_emp)
        self.empresas = [dict(nombre=n, rut=self.rut(True)) for n in nombres_emp]
        personas = []
        combos = [(n, a) for n in NOMBRES for a in APELLIDOS]
        r.shuffle(combos)
        for n, a in combos[:26]:
            personas.append(dict(nombre=f"{n} Ficticio {a}" if n[-1] != "a" else f"{n} Ficticia {a}", rut=self.rut(False)))
        self.personas = personas
        self.proveedores = [dict(nombre=n, rut=self.rut(True), rubro=ru) for n, ru in PROVEEDORES_BASE]
        self.empresa_propia = dict(nombre="Climatizacion Austral Ficticia SpA", rut=self.rut(True))
        self.socia = dict(nombre="Camila Ficticia Rojas", rut=self.rut(False))

        emp_normales = self.empresas[:12]
        emp_leak = self.empresas[12:]
        per_normales = personas[:20]
        per_leak = personas[20:]

        # ---------------- ventas normales a empresas (factura, pago por transferencia)
        for i in range(22):
            cli = emp_normales[i % len(emp_normales)]
            d = self.fecha(INICIO, dt.date(2026, 10, 24))
            neto = self.neto_unico(60_000, 1_400_000)
            cot_f = d - dt.timedelta(days=r.randint(4, 14))
            acept = cot_f + dt.timedelta(days=r.randint(1, 3))
            self.nueva_cot(cot_f, cli, r.choice(SERVICIOS), neto, "Aceptada", acept)
            v = self.nueva_venta(33, d, cli, neto, iva(neto))
            pago = d + dt.timedelta(days=r.randint(3, 26))
            if pago <= CORTE:
                self.abono_transf(pago, cli, v["total"])
            else:
                self.senuelos.append(f"Factura a {cli['nombre']} del {d_cl(d)} sin pago al corte, pero con {(CORTE - d).days} dias (menos de 30): no es fuga.")

        # senuelo: factura pagada a los 29 dias
        cli = emp_normales[0]
        neto = self.neto_unico(200_000, 600_000)
        d = dt.date(2026, 9, 8)
        self.nueva_cot(d - dt.timedelta(days=6), cli, "Mantencion camara de frio", neto, "Aceptada", d - dt.timedelta(days=5))
        v = self.nueva_venta(33, d, cli, neto, iva(neto))
        self.abono_transf(d + dt.timedelta(days=29), cli, v["total"])
        self.senuelos.append(f"Factura a {cli['nombre']} del {d_cl(d)} pagada a los 29 dias: no es fuga.")

        # ---------------- ventas normales a personas (boleta)
        for i in range(24):
            cli = per_normales[i % len(per_normales)]
            d = self.fecha(INICIO, dt.date(2026, 10, 29))
            total = self.total_unico(45_000, 390_000)
            neto = neto_desde_total(total)
            if r.random() < 0.4:
                cot_f = d - dt.timedelta(days=r.randint(3, 10))
                c = self.nueva_cot(cot_f, cli, r.choice(SERVICIOS), neto, "Aceptada", cot_f + dt.timedelta(days=1))
                c["iva"] = total - neto
                c["total"] = total
            self.nueva_venta(39, d, cli, neto, total - neto)
            if r.random() < 0.6:
                self.venta_pos(d, f"Servicio tecnico {cli['nombre'].split()[0]}", total)
            else:
                pago = d - dt.timedelta(days=r.randint(0, 3))
                pago = max(pago, INICIO)
                self.abono_transf(pago, cli, total)
        self.senuelos.append("Varias transferencias de personas llegan 1 a 3 dias ANTES de su boleta: no son fuga si la boleta existe.")

        # ---------------- ventas de mostrador por POS con boleta
        for i in range(27):
            d = self.fecha(INICIO, CORTE)
            total = self.total_unico(18_000, 69_000)
            cli = dict(nombre="Consumidor final", rut="66.666.666-6")
            self.nueva_venta(39, d, cli, neto_desde_total(total), total - neto_desde_total(total))
            self.venta_pos(d, r.choice(["Venta repuesto filtro", "Visita diagnostico", "Venta control remoto", "Limpieza express"]), total)

        # senuelo: venta POS rechazada (sin boleta, pero sin plata)
        t = self.total_unico(40_000, 90_000)
        self.venta_pos(dt.date(2026, 9, 25), "Visita diagnostico", t, estado="rechazado")
        self.senuelos.append(f"Venta POS rechazada por {t} sin boleta: no entro plata, no es fuga.")

        # ---------------- cotizaciones sin fuga
        for estado in ["Rechazada"] * 4 + ["Pendiente"] * 3:
            cli = r.choice(self.empresas + per_normales)
            f = self.fecha(dt.date(2026, 7, 25), dt.date(2026, 10, 20))
            self.nueva_cot(f, cli, r.choice(SERVICIOS), self.neto_unico(80_000, 900_000), estado, None)
        self.senuelos.append("Cotizaciones Rechazadas o Pendientes sin factura: no son fuga.")
        cli = emp_normales[3]
        self.nueva_cot(dt.date(2026, 10, 22), cli, "Instalacion equipo 24.000 BTU", self.neto_unico(500_000, 900_000),
                       "Aceptada", dt.date(2026, 10, 24))
        self.senuelos.append("Cotizacion aceptada el 24/10/2026 sin factura aun: esta dentro de los 15 dias de gracia, no es fuga.")

        # =============== FUGAS ===============
        # A1 transferencia de persona sin boleta
        cli = per_leak[0]
        m = self.total_unico(150_000, 220_000, 1000)
        f = dt.date(2026, 8, 27)
        self.abono_transf(f, cli, m, leak="F01")
        self.fugas["F01"] = dict(tipo="abono_sin_documento", fecha=f, monto=m, impacto=m - neto_desde_total(m),
                                 recurrente=False, descripcion=f"Transferencia de {cli['nombre']} por {miles(m)} sin boleta ni factura.")
        # A2 transferencia de empresa sin factura
        cli = emp_leak[0]
        neto = self.neto_unico(280_000, 360_000)
        m = neto + iva(neto)
        f = dt.date(2026, 10, 9)
        self.abono_transf(f, cli, m, leak="F02")
        self.fugas["F02"] = dict(tipo="abono_sin_documento", fecha=f, monto=m, impacto=m - neto_desde_total(m),
                                 recurrente=False, descripcion=f"Transferencia de {cli['nombre']} por {miles(m)} sin factura emitida.")
        # A3 venta POS aprobada sin boleta
        m = self.total_unico(55_000, 79_000)
        f = dt.date(2026, 9, 18)
        self.venta_pos(f, "Mantencion preventiva domicilio", m, leak="F03")
        self.fugas["F03"] = dict(tipo="abono_sin_documento", fecha=f, monto=m, impacto=m - neto_desde_total(m),
                                 recurrente=False, descripcion=f"Venta aprobada en el POS por {miles(m)} sin boleta.")

        # B1..B3 cotizaciones aceptadas sin cobro
        for fid, cli, f_acept, lo, hi in [("F04", emp_leak[1], dt.date(2026, 8, 12), 400_000, 520_000),
                                          ("F05", emp_leak[2], dt.date(2026, 9, 3), 1_100_000, 1_300_000),
                                          ("F06", per_leak[1], dt.date(2026, 9, 29), 180_000, 240_000)]:
            neto = self.neto_unico(lo, hi)
            c = self.nueva_cot(f_acept - dt.timedelta(days=4), cli, r.choice(SERVICIOS), neto, "Aceptada", f_acept, leak=fid)
            self.fugas[fid] = dict(tipo="cotizacion_sin_cobro", fecha=f_acept, monto=c["total"], impacto=c["total"],
                                   recurrente=False, cot=c,
                                   descripcion=f"{{cot}} aceptada por {cli['nombre']} el {d_cl(f_acept)} por {miles(c['total'])} y nunca se facturo ni se cobro.")

        # C1..C2 facturas impagas > 30 dias
        for fid, cli, f, lo, hi in [("F07", emp_leak[3], dt.date(2026, 8, 20), 600_000, 750_000),
                                    ("F08", emp_normales[5], dt.date(2026, 9, 15), 300_000, 420_000)]:
            neto = self.neto_unico(lo, hi)
            self.nueva_cot(f - dt.timedelta(days=7), cli, r.choice(SERVICIOS), neto, "Aceptada", f - dt.timedelta(days=5))
            v = self.nueva_venta(33, f, cli, neto, iva(neto), leak=fid)
            self.fugas[fid] = dict(tipo="pago_pendiente_30d", fecha=f, monto=v["total"], impacto=v["total"], recurrente=False, venta=v,
                                   descripcion=f"Factura folio {{folio}} a {cli['nombre']} por {miles(v['total'])} sin pago: {(CORTE - f).days} dias al corte.")

        # E1 cobraste el neto como total (IVA absorbido)
        cli = emp_normales[7]
        neto_cot = self.neto_unico(800_000, 900_000)
        f = dt.date(2026, 9, 10)
        c = self.nueva_cot(f - dt.timedelta(days=8), cli, "Instalacion equipo 24.000 BTU", neto_cot, "Aceptada",
                           f - dt.timedelta(days=6), leak="F11")
        neto_fac = neto_desde_total(neto_cot)
        v = self.nueva_venta(33, f, cli, neto_fac, neto_cot - neto_fac, leak="F11")
        self.abono_transf(f + dt.timedelta(days=12), cli, v["total"], leak="F11")
        self.fugas["F11"] = dict(tipo="diferencia_iva", fecha=f, monto=v["total"], impacto=c["total"] - v["total"], recurrente=False, cot=c, venta=v,
                                 descripcion=f"{{cot}} cotizo {miles(neto_cot)} + IVA, pero la factura folio {{folio}} se emitio por {miles(neto_cot)} total: el IVA salio de tu bolsillo.")
        # E2 IVA mal calculado en factura
        cli = emp_normales[9]
        neto = self.neto_unico(380_000, 460_000)
        f = dt.date(2026, 10, 6)
        iva_mal = neto // 10
        self.totales_usados.add(neto + iva_mal)
        self.nueva_cot(f - dt.timedelta(days=5), cli, "Reparacion compresor", neto, "Aceptada", f - dt.timedelta(days=3))
        v = self.nueva_venta(33, f, cli, neto, iva_mal, leak="F12")
        self.abono_transf(f + dt.timedelta(days=9), cli, v["total"], leak="F12")
        self.fugas["F12"] = dict(tipo="diferencia_iva", fecha=f, monto=v["total"], impacto=iva(neto) - iva_mal, recurrente=False, venta=v,
                                 descripcion=f"Factura folio {{folio}}: neto {miles(neto)} con IVA {miles(iva_mal)} (10%) en vez de {miles(iva(neto))} (19%).")

        # ---------------- equipo y licencias
        dom = "climatizacionaustral-ficticia.cl"
        self.equipo = [
            dict(nombre=self.socia["nombre"], email=f"camila@{dom}", cargo="Socia gerente", estado="Activo", ingreso="2021-03-01", salida=""),
            dict(nombre="Diego Ficticio Lagos", email=f"diego@{dom}", cargo="Tecnico", estado="Activo", ingreso="2022-06-15", salida=""),
            dict(nombre="Sofia Ficticia Mella", email=f"sofia@{dom}", cargo="Administracion", estado="Activo", ingreso="2023-01-09", salida=""),
            dict(nombre="Bruno Ficticio Vera", email=f"bruno@{dom}", cargo="Tecnico", estado="Inactivo", ingreso="2022-02-01", salida="2026-07-31"),
            dict(nombre="Matias Ficticio Reyes", email=f"matias@{dom}", cargo="Ayudante", estado="Inactivo", ingreso="2024-03-01", salida="2026-05-31"),
        ]
        self.senuelos.append("Matias dejo la empresa en mayo y su licencia ya fue dada de baja: no es fuga.")
        GW = 8_600
        self.licencias = [
            dict(servicio="Google Workspace", usuario=f"camila@{dom}", plan="Business Starter", costo=GW, estado="Activa"),
            dict(servicio="Google Workspace", usuario=f"diego@{dom}", plan="Business Starter", costo=GW, estado="Activa"),
            dict(servicio="Google Workspace", usuario=f"sofia@{dom}", plan="Business Starter", costo=GW, estado="Activa"),
            dict(servicio="Google Workspace", usuario=f"bruno@{dom}", plan="Business Starter", costo=GW, estado="Activa", leak="F10"),
            dict(servicio="Canva Pro", usuario=f"camila@{dom}", plan="Pro individual", costo=12_990, estado="Activa", leak="F09"),
            dict(servicio="Dropbox Plus", usuario=f"sofia@{dom}", plan="Plus", costo=12_990, estado="Activa"),
            dict(servicio="Microsoft 365", usuario=f"sofia@{dom}", plan="Business Basic", costo=6_490, estado="Activa"),
        ]
        self.senuelos.append("Dropbox cuesta lo mismo que Canva (12.990), pero es otro servicio: no es duplicado.")

        # ---------------- gastos fijos, suscripciones, compras
        for mes in (8, 9, 10):
            self.cargo(dt.date(2026, mes, 5), "PAGO ARRIENDO BODEGA TALLER", 650_000)
            self.cargo(dt.date(2026, mes, 2), "COMPRA TARJETA GOOGLE*WORKSPACE", GW * 4, leak="F10")
            self.cargo(dt.date(2026, mes, 3), "COMPRA TARJETA CANVA* PRO", 12_990, leak="F09")
            self.cargo(dt.date(2026, mes, 17), "COMPRA TARJETA CANVA* PRO", 12_990, leak="F09")
            self.cargo(dt.date(2026, mes, 8), "COMPRA TARJETA DROPBOX*PLUS", 12_990)
            self.cargo(dt.date(2026, mes, 11), "COMPRA TARJETA MICROSOFT*365", 6_490)
            self.cargo(dt.date(2026, mes, 13), "PAGO PREVIRED COTIZACIONES", 612_400 + r.randint(0, 20) * 100)
            self.cargo(dt.date(2026, mes, 20), "PAGO SII FORMULARIO 29", 380_000 + r.randint(0, 900) * 100)
            ultimo = (dt.date(2026, mes + 1, 1) - dt.timedelta(days=1)) if mes < 12 else dt.date(2026, 12, 31)
            self.cargo(ultimo, "PAGO REMUNERACIONES NOMINA", 2_450_000)
            self.cargo(ultimo, "COMISION MANTENCION CUENTA", 9_990)
        self.fugas["F09"] = dict(tipo="suscripcion_duplicada_o_huerfana", fecha=dt.date(2026, 8, 3), monto=12_990, impacto=12_990 * MESES,
                                 recurrente=True, mensual=12_990,
                                 descripcion="Canva Pro se cobra dos veces al mes (dia 3 y dia 17) y solo hay una licencia registrada.")
        self.fugas["F10"] = dict(tipo="suscripcion_duplicada_o_huerfana", fecha=dt.date(2026, 8, 2), monto=GW, impacto=GW * MESES,
                                 recurrente=True, mensual=GW,
                                 descripcion="Licencia de Google Workspace de Bruno Ficticio Vera sigue activa y pagada aunque salio de la empresa el 31/07/2026.")

        for i in range(12):
            prov = self.proveedores[i % len(self.proveedores)]
            d = self.fecha(INICIO, dt.date(2026, 10, 15))
            neto = self.neto_unico(40_000, 520_000, 1000)
            folio = r.randint(10_000, 99_999)
            self.compras.append(dict(tipo=33, rut=prov["rut"], razon=prov["nombre"], folio=folio, fecha=d, neto=neto,
                                     iva=iva(neto), total=neto + iva(neto)))
            pago = min(d + dt.timedelta(days=r.randint(1, 20)), CORTE)
            self.cargo(pago, f"TRANSF. A {prov['rut']} {prov['nombre'].upper()}"[:60], neto + iva(neto))

        # ---------------- senuelos de abonos
        self.banco.append(dict(fecha=dt.date(2026, 9, 2), desc=f"TRANSF. DE {self.socia['rut']} APORTE SOCIO CAMILA ROJAS",
                               cargo=0, abono=1_500_000, leak=None))
        self.senuelos.append("Aporte de la socia por 1.500.000: no es venta, se excluye por configuracion.")
        prov = self.proveedores[0]
        self.banco.append(dict(fecha=dt.date(2026, 10, 3), desc=f"DEVOLUCION {prov['rut']} {prov['nombre'].upper()}"[:60],
                               cargo=0, abono=23_800, leak=None))
        self.senuelos.append("Devolucion de un proveedor por 23.800: no es venta, se excluye por configuracion.")

        # ---------------- liquidaciones POS al banco (lunes, semana anterior)
        lunes = INICIO + dt.timedelta(days=(7 - INICIO.weekday()) % 7)
        while lunes <= CORTE:
            ini = lunes - dt.timedelta(days=7)
            s = sum(p["neto"] for p in self.pos if ini <= p["fecha"] < lunes and p["estado"] == "aprobado")
            if s:
                glosa = "TRANSF. MERCADO PAGO LIQUIDACION" if self.variante == "a" else "ABONO TRANSBANK VENTAS TARJETA"
                self.banco.append(dict(fecha=lunes, desc=glosa, cargo=0, abono=s, leak=None))
            lunes += dt.timedelta(days=7)
        self.senuelos.append("Liquidaciones semanales del POS al banco: ya estan respaldadas por boletas en el archivo del POS.")

    # --------------------------------------------------------------------------- escritura
    def escribir(self, carpeta: Path):
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "_respuestas").mkdir(exist_ok=True)
        filas = {}  # leak -> [(archivo, fila)]

        def marca(leak, archivo, fila):
            if leak:
                filas.setdefault(leak, []).append({"archivo": archivo, "fila": fila})

        # orden estable
        self.banco.sort(key=lambda m: (m["fecha"], 0 if m["abono"] else 1, m["desc"], m["abono"] + m["cargo"]))
        self.pos.sort(key=lambda p: (p["fecha"], p["hora"], p["id"]))
        self.ventas.sort(key=lambda v: (v["fecha"], v["tipo"], v["folio"]))
        self.compras.sort(key=lambda v: (v["fecha"], v["folio"]))
        self.cots.sort(key=lambda c: (c["fecha"], c["cliente"]))
        base = 100 if self.variante == "a" else 500
        for i, c in enumerate(self.cots, start=base + 1):
            c["numero"] = f"{'COT' if self.variante == 'a' else 'PRE'}-{i:04d}"
        sig = {33: 1201 if self.variante == "a" else 3401, 39: 5101 if self.variante == "a" else 8801}
        for v in self.ventas:
            v["folio"] = sig[v["tipo"]]
            sig[v["tipo"]] += 1

        saldo = 3_800_000
        if self.variante == "a":
            # ---- cartola estilo banco A: preambulo, ';', dd/mm/aaaa, miles con punto, Cargos/Abonos separados
            nombre = "cartola_banco.csv"
            with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
                fh.write("Banco Ficticio de Chile;;;;;\n")
                fh.write(f"Titular: {self.empresa_propia['nombre']} RUT {self.empresa_propia['rut']};;;;;\n")
                fh.write("Cuenta Corriente N 00-123-45678-09 (FICTICIA);;;;;\n")
                fh.write(f"Periodo: {d_cl(INICIO)} al {d_cl(CORTE)};;;;;\n")
                fh.write(";;;;;\n")
                w = csv.writer(fh, delimiter=";")
                w.writerow(["Fecha", "Descripcion", "N Documento", "Cargos ($)", "Abonos ($)", "Saldo ($)"])
                linea = 7
                for i, m in enumerate(self.banco):
                    saldo += m["abono"] - m["cargo"]
                    w.writerow([d_cl(m["fecha"]), m["desc"], f"{(i * 7919) % 1000000:06d}",
                                miles(m["cargo"]) if m["cargo"] else "", miles(m["abono"]) if m["abono"] else "", miles(saldo)])
                    marca(m["leak"], nombre, linea)
                    linea += 1
            # ---- Mercado Pago (',', ISO, decimales)
            nombre = "ventas_mercadopago.csv"
            with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["fecha_creacion", "id_operacion", "descripcion", "monto_bruto", "comision_mp", "monto_neto", "estado", "medio_pago"])
                for linea, p in enumerate(self.pos, start=2):
                    w.writerow([f"{p['fecha'].isoformat()}T{p['hora']}:00-03:00", p["id"], p["desc"], f"{p['bruto']:.2f}",
                                f"{p['comision']:.2f}", f"{p['neto']:.2f}", "approved" if p["estado"] == "aprobado" else "rejected", p["medio"]])
                    marca(p["leak"], nombre, linea)
            # ---- cotizaciones XLSX + CSV espejo
            self._cotizaciones_xlsx(carpeta / "cotizaciones.xlsx", marca)
        else:
            # ---- cartola estilo banco B: ',', aaaa-mm-dd, un solo monto con signo, sin preambulo
            nombre = "movimientos_cuenta.csv"
            with open(carpeta / nombre, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh)
                w.writerow(["Fecha Movimiento", "Glosa", "Sucursal", "Monto", "Saldo Disponible"])
                for linea, m in enumerate(self.banco, start=2):
                    monto = m["abono"] - m["cargo"]
                    saldo += monto
                    w.writerow([m["fecha"].isoformat(), m["desc"], "OFICINA CENTRAL", str(monto), str(saldo)])
                    marca(m["leak"], nombre, linea)
            # ---- Transbank (';', dd-mm-aaaa)
            nombre = "ventas_transbank.csv"
            with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["Fecha Venta", "Hora", "Codigo Autorizacion", "Tipo Tarjeta", "Monto Venta", "Comision + IVA", "Monto Abono", "Estado"])
                for linea, p in enumerate(self.pos, start=2):
                    w.writerow([p["fecha"].strftime("%d-%m-%Y"), p["hora"], p["id"], "Debito" if "debito" in p["medio"] else "Credito",
                                miles(p["bruto"]), miles(p["comision"]), miles(p["neto"]), "Aprobada" if p["estado"] == "aprobado" else "Rechazada"])
                    marca(p["leak"], nombre, linea)
            # ---- cotizaciones CSV con otros encabezados
            nombre = "presupuestos.csv"
            with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["Folio Presupuesto", "Fecha Emision", "Razon Social", "RUT Cliente", "Detalle", "Valor Neto", "Estado", "Aceptado El"])
                for linea, c in enumerate(self.cots, start=2):
                    w.writerow([c["numero"], c["fecha"].isoformat(), c["cliente"], c["rut"], c["servicio"],
                                str(c["neto"]), {"Aceptada": "APROBADO", "Rechazada": "RECHAZADO", "Pendiente": "ENVIADO"}[c["estado"]],
                                c["fecha_aceptacion"].isoformat() if c["fecha_aceptacion"] else ""])
                    marca(c["leak"], nombre, linea)

        # ---- RCV SII (mismo formato en ambas variantes: el SII es igual para todos)
        enc_v = ["Nro", "Tipo Doc", "Tipo Venta", "Rut cliente", "Razon Social", "Folio", "Fecha Docto", "Fecha Recepcion",
                 "Fecha Acuse Recibo", "Monto Exento", "Monto Neto", "Monto IVA", "Monto total"]
        nombre = "rcv_ventas.csv"
        with open(carpeta / nombre, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(enc_v)
            for linea, v in enumerate(self.ventas, start=2):
                w.writerow([linea - 1, v["tipo"], "Del Giro", v["rut"], v["razon"], v["folio"], d_cl(v["fecha"]),
                            f"{d_cl(v['fecha'])} 12:00:00", "", 0, v["neto"], v["iva"], v["total"]])
                marca(v["leak"], nombre, linea)
        enc_c = ["Nro", "Tipo Doc", "Tipo Compra", "RUT Proveedor", "Razon Social", "Folio", "Fecha Docto", "Fecha Recepcion",
                 "Fecha Acuse", "Monto Exento", "Monto Neto", "Monto IVA Recuperable", "Monto Iva No Recuperable", "Monto Total"]
        with open(carpeta / "rcv_compras.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(enc_c)
            for linea, v in enumerate(self.compras, start=2):
                w.writerow([linea - 1, v["tipo"], "Del Giro", v["rut"], v["razon"], v["folio"], d_cl(v["fecha"]),
                            f"{d_cl(v['fecha'])} 10:00:00", "", 0, v["neto"], v["iva"], 0, v["total"]])

        # ---- equipo y licencias (iguales en ambas variantes)
        with open(carpeta / "equipo.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["nombre", "email", "cargo", "estado", "fecha_ingreso", "fecha_salida"])
            for linea, e in enumerate(self.equipo, start=2):
                w.writerow([e["nombre"], e["email"], e["cargo"], e["estado"], e["ingreso"], e["salida"]])
                if e["email"].startswith("bruno@"):
                    marca("F10", "equipo.csv", linea)
        with open(carpeta / "licencias.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["servicio", "usuario", "plan", "costo_mensual_clp", "estado"])
            for linea, l in enumerate(self.licencias, start=2):
                w.writerow([l["servicio"], l["usuario"], l["plan"], l["costo"], l["estado"]])
                marca(l.get("leak"), "licencias.csv", linea)

        # ---- configuracion de la empresa (la lee el detector)
        config = {
            "empresa": self.empresa_propia["nombre"],
            "rut_empresa": self.empresa_propia["rut"],
            "fecha_corte": CORTE.isoformat(),
            "periodo_desde": INICIO.isoformat(),
            "periodo_hasta": CORTE.isoformat(),
            "tasa_iva": 0.19,
            "dias_pago_pendiente": 30,
            "dias_gracia_cotizacion": 15,
            "ventana_dias_abono_documento": 7,
            "tolerancia_clp": 2,
            "palabras_excluidas_abonos": ["APORTE SOCIO", "DEVOLUCION", "TRASPASO ENTRE CUENTAS", "INTERESES",
                                          "MERCADO PAGO LIQUIDACION", "ABONO TRANSBANK"],
            "ruts_excluidos_abonos": [self.socia["rut"]],
            "nota": "Datos 100% ficticios generados por scripts/generar_dataset.py",
        }
        (carpeta / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

        # ---- llave de respuestas
        fugas = []
        for fid in sorted(self.fugas):
            f = self.fugas[fid]
            mensual = f.get("mensual", round(f["impacto"] / MESES))
            desc = f["descripcion"].format(cot=f["cot"]["numero"] if "cot" in f else "",
                                           folio=f["venta"]["folio"] if "venta" in f else "")
            fugas.append(dict(id=fid, tipo=f["tipo"], descripcion=desc, fecha=f["fecha"].isoformat(),
                              monto_clp=f["monto"], impacto_clp=f["impacto"], impacto_mensual_clp=mensual,
                              recurrente=f["recurrente"], filas_clave=filas.get(fid, [])))
        llave = dict(
            advertencia="SOLO para scripts/evaluar.py. El detector y los agentes de deteccion NO deben leer este archivo.",
            variante=self.variante, fecha_corte=CORTE.isoformat(), total_fugas=len(fugas),
            regla_de_coincidencia="Un hallazgo cuenta si tiene el mismo 'tipo' y cita al menos una (archivo, fila) de 'filas_clave'.",
            convencion_filas="fila = numero de linea fisica del archivo (la primera linea es 1). En XLSX, numero de fila de Excel.",
            fugas=fugas, senuelos=self.senuelos,
        )
        (carpeta / "_respuestas" / "respuestas.json").write_text(json.dumps(llave, ensure_ascii=False, indent=2), encoding="utf-8")
        return llave

    def _cotizaciones_xlsx(self, ruta: Path, marca):
        from openpyxl import Workbook
        from openpyxl.styles import Font
        wb = Workbook()
        ws = wb.active
        ws.title = "Cotizaciones"
        ws.append(["Registro de cotizaciones 2026 (FICTICIO)"])
        ws["A1"].font = Font(bold=True)
        ws.append(["N Cotizacion", "Fecha", "Cliente", "RUT", "Servicio", "Neto", "IVA", "Total", "Estado", "Fecha aceptacion"])
        filas_csv = []
        for c in self.cots:
            fila = [c["numero"], c["fecha"], c["cliente"], c["rut"], c["servicio"], c["neto"], c["iva"], c["total"], c["estado"],
                    c["fecha_aceptacion"]]
            ws.append(fila)
            marca(c["leak"], "cotizaciones.xlsx", ws.max_row)
            filas_csv.append(fila)
        for col in ("B", "J"):
            for celda in ws[col][2:]:
                celda.number_format = "DD/MM/YYYY"
        for col in ("F", "G", "H"):
            for celda in ws[col][2:]:
                celda.number_format = "#,##0"
        for col, ancho in zip("ABCDEFGHIJ", (14, 12, 38, 14, 40, 12, 12, 12, 11, 16)):
            ws.column_dimensions[col].width = ancho
        wb.properties.creator = "generar_dataset.py (FICTICIO)"
        wb.save(ruta)
        _xlsx_determinista(ruta)
        # espejo CSV para quien no use XLSX (mismas filas que el XLSX: titulo en linea 1, encabezado en 2)
        with open(ruta.with_suffix(".csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["Registro de cotizaciones 2026 (FICTICIO)"])
            w.writerow(["N Cotizacion", "Fecha", "Cliente", "RUT", "Servicio", "Neto", "IVA", "Total", "Estado", "Fecha aceptacion"])
            for linea, f in enumerate(filas_csv, start=3):
                w.writerow([f[0], d_cl(f[1]), f[2], f[3], f[4], f[5], f[6], f[7], f[8], d_cl(f[9]) if f[9] else ""])
                marca(self.cots[linea - 3]["leak"], "cotizaciones.csv", linea)


def _xlsx_determinista(ruta: Path):
    """Fija fechas internas del XLSX para que el archivo sea identico en cada corrida."""
    import re
    import zipfile
    fijo = "2026-11-01T00:00:00Z"
    with zipfile.ZipFile(ruta) as z:
        entradas = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in entradas:
            if nombre == "docProps/core.xml":
                texto = datos.decode("utf-8")
                texto = re.sub(r"(<dcterms:(?:created|modified)[^>]*>)[^<]*(<)", rf"\g<1>{fijo}\g<2>", texto)
                datos = texto.encode("utf-8")
            info = zipfile.ZipInfo(nombre, date_time=(2026, 11, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, datos)


def generar(variante: str):
    semilla = 2026 if variante == "a" else 7
    carpeta = RAIZ / "data" / ("demo" if variante == "a" else "demo_b")
    g = Generador(semilla, variante)
    g.construir()
    llave = g.escribir(carpeta)
    print(f"Variante {variante.upper()}: {llave['total_fugas']} fugas escondidas en {carpeta.relative_to(RAIZ)}")
    return llave


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera el dataset ficticio del Detective de Fugas Pyme")
    ap.add_argument("--variante", choices=["a", "b"], default="a")
    ap.add_argument("--todas", action="store_true")
    a = ap.parse_args()
    for v in (["a", "b"] if a.todas else [a.variante]):
        generar(v)
