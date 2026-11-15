# CLAUDE.md · Detective de Fugas Pyme

Reglas cortas para cualquier sesión en este repo. La spec completa está en `SPEC_DETECTIVE_FUGAS.md`.

1. **Idioma:** todo texto para usuarios en español neutro latinoamericano con "tú". Nunca uses el guion largo (carácter Unicode U+2014): usa dos puntos, comas o paréntesis.
2. **Solo datos ficticios.** No pidas, no uses y no subas datos reales de nadie. Lo de `data/` es inventado.
3. **Regla de oro:** cada hallazgo cita archivo, fila (línea física, la primera es 1), fecha y monto exactos. Sin evidencia verificada, se descarta.
4. **La llave es secreta:** no leas `data/*/_respuestas/`. Solo `scripts/evaluar.py` la lee, y tú solo miras su resultado.
5. **Sin secretos:** no escribas claves ni tokens en archivos. La capa LLM es opcional y lee `ANTHROPIC_API_KEY` del entorno.
6. **Nada sale sin permiso:** no hagas `git push`, no despliegues, no publiques, no envíes mensajes. Commits locales sí.
7. **Bitácora:** cada error, corrección o decisión va a `BITACORA.md` con el formato de la sección 14 de la spec. Es la prueba de "cómo lo hice".
8. **Plan vivo:** marca avances en `PLAN.md`. Al retomar una sesión, lee `PLAN.md` y la bitácora, corre `python -m pytest -q` y `python scripts/evaluar.py`, y sigue desde lo pendiente.
9. **Termina el trabajo:** no te detengas mientras quede trabajo que puedes hacer tú. Solo para por lo que la sección 0.5 de la spec reserva para Gustavo.
10. **Verifica antes de decir "listo":** corre las pruebas y el evaluador, y pega el resultado.

Comandos útiles:

```bash
python scripts/generar_dataset.py --todas
python -m detective auditar --datos data/demo --salida salida/demo
python scripts/evaluar.py --dataset data/demo
python -m pytest -q
python scripts/construir_web.py && python -m http.server -d web 8000
```
