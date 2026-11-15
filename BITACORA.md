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

## 2026-11-14 23:30 · Fase 0 · El repositorio llegó vacío a la sesión

- Qué pasó: al primer intento de leer `CLAUDE.md` y la spec, ningún archivo existía. El repositorio de GitHub no tenía ramas ni commits.
- Por qué: la sesión se abrió en la nube antes de que el kit inicial se subiera a GitHub.
- Qué cambié: nada en el código. Revisé la carpeta, el remoto y el resto del contenedor, y le pedí a Gustavo que subiera el kit. Cuando apareció la rama `main`, creé la rama de trabajo desde ahí.
- Cómo lo verifiqué: `git ls-remote origin` pasó de no mostrar nada a mostrar `refs/heads/main`; `git ls-files` lista el kit completo.

## 2026-11-15 00:10 · Fase 0 · Lectura, comprobaciones previas y PLAN.md

- Qué pasó: leí los 6 archivos en el orden que pide la sección 0.1 (sin abrir `data/*/_respuestas/`) y escribí `PLAN.md` con tareas, archivos, riesgos y verificaciones.
- Por qué: es la única pausa planificada; nada se construye antes de la aprobación de Gustavo.
- Qué cambié: `PLAN.md` (nuevo).
- Cómo lo verifiqué: `python scripts/generar_dataset.py --todas` seguido de `git status --short` no muestra cambios, o sea que el generador es reproducible.

## 2026-11-15 00:10 · Fase 0 · Descubrimientos que cambian el plan

- Qué pasó: (1) `pytest` no está instalado en este entorno; (2) `openpyxl` no viene incluido en la distribución de Pyodide 0.26.4; (3) Playwright está disponible con Node, no con Python; (4) la sesión corre en un contenedor temporal de la nube y la spec prohíbe `git push` sin permiso.
- Por qué: la spec y `PASO_A_PASO.md` asumen que Claude Code corre en el computador de Gustavo, donde los commits locales quedan guardados. En la nube, lo que no se sube se puede perder.
- Qué cambié: en `PLAN.md` quedaron los riesgos R1 (respaldo), R8 (copia local de `openpyxl` para la web, o solo CSV si falla) y R9 (prueba con navegador opcional). No hice ningún push: la decisión de respaldo es de Gustavo.
- Cómo lo verifiqué: `python3 -m pytest --version` falla con "No module named pytest"; el archivo `pyodide-lock.json` del CDN oficial no lista `openpyxl`; `node -e "require('playwright')"` funciona.

## 2026-11-15 00:25 · Fase 0 · Plan aprobado y decisión de respaldo

- Qué pasó: Gustavo aprobó `PLAN.md` y eligió la opción A de respaldo: push solo a la rama de trabajo `claude/wizardly-hawking-b7n711` al cierre de cada fase.
- Por qué: la sesión corre en un contenedor temporal de la nube; sin respaldo, un reciclaje del contenedor borraría los commits locales. El push sigue reservado a Gustavo (sección 0.5) y él lo autorizó solo para esa rama.
- Qué cambié: estado en `PLAN.md`. No se toca `main`, no hay despliegue ni publicación.
- Cómo lo verifiqué: mensaje de Gustavo en la sesión ("Sí, aprobado el PLAN.md" y luego "A").

## Crítico

(Fable completa esta sección en la fase 7: los máximo 5 problemas encontrados y qué se hizo con cada uno.)
