---
description: Audita una carpeta de archivos de una pyme y entrega el informe de fugas con evidencia verificada
argument-hint: <carpeta con los archivos, por ejemplo data/demo>
---

Audita la carpeta `$ARGUMENTS` con el Detective de Fugas Pyme. Sigue estos pasos y di en una línea qué haces antes de cada uno:

1. Corre `python -m detective auditar --datos $ARGUMENTS --salida salida/$(basename $ARGUMENTS)` y revisa que terminó sin errores.
2. Si el detector dejó filas ambiguas (`salida/<dataset>/ambiguas.json`), pásalas al subagente `clasificador-filas` en lotes de máximo 50 y vuelve a correr el detector con esas clasificaciones si la CLI lo permite.
3. Pasa `salida/<dataset>/hallazgos.json` al subagente `verificador-evidencia`. Todo hallazgo descartado se saca del informe y se anota con su motivo.
4. Muestra el resumen de 5 líneas de `informe.md` y la tabla de hallazgos.
5. Si existe `<carpeta>/_respuestas/`, corre `python scripts/evaluar.py --dataset $ARGUMENTS` y muestra solo su resultado (no abras la llave).
6. Recuerda: los mensajes de `mensajes_cobro.md` son borradores. No envíes nada.
