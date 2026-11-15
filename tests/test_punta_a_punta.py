"""De punta a punta: generar los datasets, correr el detector y medir con el evaluador oficial."""
import hashlib
import json
import subprocess
import sys

import pytest

DATASETS = ["data/demo", "data/demo_b"]


def _huellas(raiz):
    """Huella de cada archivo de entrada (los de primer nivel de cada dataset)."""
    return {str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
            for carpeta in DATASETS for p in sorted((raiz / carpeta).iterdir()) if p.is_file()}


@pytest.fixture(scope="module")
def generado(raiz):
    antes = _huellas(raiz)
    corrida = subprocess.run([sys.executable, "scripts/generar_dataset.py", "--todas"], cwd=raiz,
                             capture_output=True, text=True)
    assert corrida.returncode == 0, corrida.stderr
    return antes, _huellas(raiz), corrida.stdout


def test_el_generador_es_reproducible(generado):
    antes, despues, salida = generado
    assert antes == despues, "regenerar cambió los archivos de entrada"
    assert salida.count("12 fugas escondidas") == 2


@pytest.mark.parametrize("dataset", DATASETS)
def test_el_detector_aprueba_el_evaluador(raiz, tmp_path, generado, dataset):
    auditoria = subprocess.run([sys.executable, "-m", "detective", "auditar", "--datos", dataset,
                                "--salida", str(tmp_path)], cwd=raiz, capture_output=True, text=True)
    assert auditoria.returncode == 0, auditoria.stdout + auditoria.stderr
    evaluacion = subprocess.run([sys.executable, "scripts/evaluar.py", "--dataset", dataset, "--hallazgos",
                                 str(tmp_path / "hallazgos.json"), "--json"], cwd=raiz, capture_output=True, text=True)
    resultado = json.loads(evaluacion.stdout)
    assert resultado["falsos_positivos"] == 0, resultado["detalle"]
    assert resultado["encontradas"] >= 10 and resultado["aprobado"] is True, resultado["faltantes_detalle"]
    assert evaluacion.returncode == 0
    assert resultado["encontradas"] == resultado["total_fugas"] == 12, resultado["faltantes_detalle"]
    assert json.loads((tmp_path / "descartados.json").read_text(encoding="utf-8")) == []
