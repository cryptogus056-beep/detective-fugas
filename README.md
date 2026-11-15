# Detective de Fugas Pyme

> Fable reemplaza este README en la fase 8 (ver sección 13 de `SPEC_DETECTIVE_FUGAS.md`). Esto es solo el punto de partida.

Encuentra la plata que tu pyme pierde sin darse cuenta: cotizaciones aceptadas que nadie facturó, transferencias sin boleta, facturas impagas, suscripciones duplicadas o de gente que ya se fue, y diferencias de IVA. Cada hallazgo trae el archivo, la fila, la fecha y el monto que lo prueban.

**La plata que se pierde no hace ruido: hay que contarla fila por fila.**

## Estado

- [x] Dataset ficticio con 12 fugas escondidas (`data/demo`, `data/demo_b`)
- [x] Evaluador (`scripts/evaluar.py`)
- [ ] Detector (`detective/`)
- [ ] Web de demostración (`web/`)

## Probar el dataset y el evaluador

```bash
python -m venv .venv && source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generar_dataset.py --todas
```

Todos los datos son 100% ficticios. Licencia MIT.
