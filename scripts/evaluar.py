#!/usr/bin/env python3
"""Compara los hallazgos del detector con la llave de respuestas del dataset ficticio.

Es el UNICO programa del proyecto que puede leer data/<dataset>/_respuestas/.

Uso:
    python scripts/evaluar.py                                   # demo A
    python scripts/evaluar.py --dataset data/demo_b --hallazgos salida/demo_b/hallazgos.json
    python scripts/evaluar.py --json                            # salida en JSON

Regla: un hallazgo cuenta si tiene el mismo "tipo" que una fuga de la llave y cita
al menos una (archivo, fila) de sus "filas_clave". Cada fuga se cuenta una sola vez.
Un hallazgo que no calza con ninguna fuga, o que repite una fuga ya encontrada,
es un falso positivo.

Aprueba (codigo de salida 0) si encuentra al menos --minimo fugas (por defecto 10)
y tiene 0 falsos positivos.
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def clave(archivo: str, fila) -> tuple:
    return (Path(str(archivo)).name.lower(), int(fila))


def evaluar(llave: dict, hallazgos: list, minimo: int) -> dict:
    fugas = llave["fugas"]
    filas_por_fuga = {f["id"]: {clave(e["archivo"], e["fila"]) for e in f["filas_clave"]} for f in fugas}
    tipo_por_fuga = {f["id"]: f["tipo"] for f in fugas}
    encontradas, falsos, detalle = {}, [], []
    for h in hallazgos:
        evid = set()
        for e in h.get("evidencia", []):
            try:
                evid.add(clave(e["archivo"], e["fila"]))
            except (KeyError, TypeError, ValueError):
                pass
        candidatas = [fid for fid in filas_por_fuga
                      if tipo_por_fuga[fid] == h.get("tipo") and filas_por_fuga[fid] & evid]
        libres = [fid for fid in candidatas if fid not in encontradas]
        hid = h.get("id", "?")
        if libres:
            fid = libres[0]
            encontradas[fid] = hid
            detalle.append(f"OK   {hid} -> {fid} ({h.get('tipo')})")
        elif candidatas:
            falsos.append(hid)
            detalle.append(f"DUP  {hid} repite {candidatas[0]} ({h.get('tipo')})")
        else:
            falsos.append(hid)
            detalle.append(f"FALSO {hid} ({h.get('tipo')}) no calza con ninguna fuga")
        if not h.get("evidencia"):
            detalle.append(f"     {hid} no trae evidencia: incumple la regla de oro")
    no_encontradas = [f["id"] for f in fugas if f["id"] not in encontradas]
    aprobado = len(encontradas) >= minimo and not falsos
    return dict(total_fugas=len(fugas), encontradas=len(encontradas), falsos_positivos=len(falsos),
                no_encontradas=no_encontradas, ids_falsos=falsos, minimo=minimo, aprobado=aprobado, detalle=detalle,
                faltantes_detalle=[f"{f['id']} {f['tipo']}: {f['descripcion']}" for f in fugas if f["id"] not in encontradas])


def main() -> int:
    ap = argparse.ArgumentParser(description="Evalua hallazgos contra la llave de respuestas (solo datos ficticios)")
    ap.add_argument("--dataset", default="data/demo", help="carpeta del dataset (contiene _respuestas/)")
    ap.add_argument("--hallazgos", default=None, help="ruta a hallazgos.json (por defecto salida/<nombre_dataset>/hallazgos.json)")
    ap.add_argument("--minimo", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    dataset = (RAIZ / a.dataset) if not Path(a.dataset).is_absolute() else Path(a.dataset)
    llave_ruta = dataset / "_respuestas" / "respuestas.json"
    h_ruta = Path(a.hallazgos) if a.hallazgos else RAIZ / "salida" / dataset.name / "hallazgos.json"
    if not h_ruta.is_absolute():
        h_ruta = RAIZ / h_ruta
    if not llave_ruta.exists():
        print(f"No encuentro la llave {llave_ruta}. Corre primero: python scripts/generar_dataset.py --todas")
        return 2
    if not h_ruta.exists():
        print(f"No encuentro {h_ruta}. Corre primero el detector sobre {dataset}.")
        return 2
    llave = json.loads(llave_ruta.read_text(encoding="utf-8"))
    datos = json.loads(h_ruta.read_text(encoding="utf-8"))
    hallazgos = datos["hallazgos"] if isinstance(datos, dict) else datos
    r = evaluar(llave, hallazgos, a.minimo)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"Dataset: {dataset.name}   Hallazgos: {len(hallazgos)}")
        for linea in r["detalle"]:
            print("  " + linea)
        print(f"\nEncontradas: {r['encontradas']} de {r['total_fugas']}   Falsos positivos: {r['falsos_positivos']}")
        for f in r["faltantes_detalle"]:
            print(f"  Falta: {f}")
        print("RESULTADO: APROBADO" if r["aprobado"] else f"RESULTADO: NO APROBADO (minimo {a.minimo} y 0 falsos)")
    return 0 if r["aprobado"] else 1


if __name__ == "__main__":
    sys.exit(main())
