"""Utilidades comunes de las pruebas."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from detective.plantillas import cargar_plantillas  # noqa: E402


@pytest.fixture(scope="session")
def raiz():
    return RAIZ


@pytest.fixture(scope="session")
def plantillas():
    return cargar_plantillas(RAIZ / "plantillas")
