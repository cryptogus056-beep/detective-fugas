---
description: Audita una carpeta de archivos de una pyme y entrega el informe de fugas con evidencia verificada
argument-hint: <carpeta con los archivos, por ejemplo data/demo>
---

Audita la carpeta `$ARGUMENTS` con el Detective de Fugas Pyme. Tú orquestas; el trabajo repetitivo lo hacen los subagentes económicos; el verificador tiene la última palabra. Di en una línea qué haces antes de cada paso.

Llama `SALIDA` a la carpeta `salida/<nombre de la carpeta auditada>` (por ejemplo, `salida/demo`).

1. **Núcleo determinista.** Corre `python -m detective auditar --datos $ARGUMENTS --salida SALIDA` y revisa que terminó sin errores. Esto ya incluye la verificación en código de cada fila citada.
2. **Filas ambiguas.** Lee `SALIDA/ambiguas.json`. Si es una lista vacía, salta al paso 3. Si tiene filas, pásalas al subagente `clasificador-filas` (en lotes de máximo 50) con la ruta de `ambiguas.json` y la carpeta `$ARGUMENTS`. Guarda su respuesta JSON en `SALIDA/clasificaciones.json` y vuelve a correr el paso 1 agregando `--clasificaciones SALIDA/clasificaciones.json`.
3. **Segunda opinión.** Pasa `SALIDA/hallazgos.json` y la carpeta `$ARGUMENTS` al subagente `verificador-evidencia`. Guarda su respuesta JSON en `SALIDA/verificacion_agente.json`.
4. **Aplicar descartes.** Si el verificador descartó algo, vuelve a correr el paso 1 agregando `--descartes SALIDA/verificacion_agente.json` (y `--clasificaciones ...` si la usaste). Los hallazgos descartados salen del informe y quedan en `SALIDA/descartados.json` con su motivo. Si no descartó nada, no hagas nada.
5. **Resultado.** Muestra el resumen de 5 líneas de `SALIDA/informe.md` y la tabla de hallazgos.
6. **Medición (solo datasets de ejemplo).** Si existe `$ARGUMENTS/_respuestas/`, corre `python scripts/evaluar.py --dataset $ARGUMENTS` y muestra solo su resultado. No abras la llave.

Reglas que no se negocian:

- La regla de oro manda: los subagentes solo pueden QUITAR o anotar hallazgos, nunca agregar uno. Si un subagente propone un hallazgo nuevo, ignóralo.
- Nadie lee `data/*/_respuestas/`, salvo `scripts/evaluar.py`.
- Los mensajes de `SALIDA/mensajes_cobro.md` son borradores. No envíes nada a nadie.
