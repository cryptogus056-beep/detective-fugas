# Bitácora del Detective de Fugas Pyme

Aquí queda registrado cada error, corrección y decisión durante la construcción con Claude Fable 5.2. Es la base de la parte "cómo lo hice" del post del concurso.

**Resumen (Fable lo completa al final):** Fable corrigió [[N]] cosas; las 3 más importantes fueron [[...]].

Formato de cada entrada:

```
## AAAA-MM-DD HH:MM · Fase N · título corto
- Qué pasó:
- Por qué:
- Qué cambié:
- Cómo lo verifiqué:
```

---

## 2026-11-14 · Fase previa · Kit inicial

- Qué pasó: se preparó el kit de partida (spec, reglas, prompts, dataset ficticio con 12 fugas en dos variantes de formato, evaluador y borradores de entrega).
- Por qué: que Fable pueda construir todo de forma autónoma y que el resultado sea medible.
- Qué cambié: se crearon `SPEC_DETECTIVE_FUGAS.md`, `CLAUDE.md`, `PROMPTS.md`, `PASO_A_PASO.md`, `scripts/generar_dataset.py`, `scripts/evaluar.py`, `data/demo/`, `data/demo_b/`, `.claude/` y `ENTREGA/`.
- Cómo lo verifiqué: `python scripts/generar_dataset.py --todas` genera 12 fugas por variante; `scripts/evaluar.py` aprueba un detector de referencia descartable (no incluido) y rechaza uno con fugas faltantes o inventadas.

## Crítico

(Fable completa esta sección en la fase 7: los máximo 5 problemas encontrados y qué se hizo con cada uno.)
