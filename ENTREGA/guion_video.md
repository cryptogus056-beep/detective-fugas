# Guion del video (2 a 3 minutos)

> BORRADOR con los números y pantallas reales (actualizado por Fable el 15/11/2026). Graba la pantalla con tu voz; no hace falta salir en cámara.

| # | Tiempo | Qué se ve | Qué dices |
|---|---|---|---|
| 1 | 0:00 a 0:15 | La web abierta con el título y la frase | "Tu pyme pierde plata que nadie ve. Hice con Claude Fable 5.2 un detective que la encuentra fila por fila." |
| 2 | 0:15 a 0:35 | Los archivos de la demo: cartola, Mercado Pago, SII, cotizaciones | "Esta es una pyme ficticia de climatización, con 3 meses de movimientos. Son los mismos archivos que tú puedes descargar de tu banco, de Mercado Pago y del SII. Escondí 12 fugas." |
| 3 | 0:35 a 1:05 | Botón "Usar mis archivos", arrastrar los archivos, la lista "Revisa qué es cada archivo" y el botón "Buscar fugas" | "Arrastro los archivos. La página reconoce sola qué es cada uno. Todo corre en mi navegador: nada sale de mi computador. Aprieto Buscar fugas y en segundos tengo el informe." |
| 4 | 1:05 a 1:35 | El resumen de 5 líneas y la tabla ordenada por impacto mensual | "Encontró 12 de 12 fugas, sin inventar ninguna. La más grande: una cotización por $1.499.400 que el cliente aceptó y nadie facturó. En total, $3.738.472 en juego, y de eso $3.373.650 es plata que se puede cobrar." |
| 5 | 1:35 a 1:55 | Clic en la evidencia de un hallazgo, abrir el archivo en Excel en esa fila | "Lo importante: cada fuga dice archivo, fila, fecha y monto. Esta dice cartola, fila 74, 9 de octubre, $398.650. Abro la cartola, voy a la fila 74 y ahí está. Si no hay prueba, no aparece." |
| 6 | 1:55 a 2:15 | `mensajes_cobro.md` | "Además me deja los mensajes de cobro redactados. No envía nada solo: yo completo mis datos, los reviso y los mando." |
| 7 | 2:15 a 2:40 | Terminal: `python scripts/evaluar.py` con "APROBADO", y un vistazo a `BITACORA.md` | "¿Cómo sé que funciona? Un script lo compara con la llave de respuestas. Y con otro banco y otros formatos también pasa. Fable planificó, construyó, se corrigió 17 veces y un crítico sin contexto lo revisó como si fuera una dueña de pyme." |
| 8 | 2:40 a 2:55 | La frase final en pantalla y el link | "La plata que se pierde no hace ruido: hay que contarla fila por fila. El link está abajo, es gratis." |

**Consejos para grabar:**

- Ten todo abierto antes de grabar (web, Excel con la cartola, terminal) para no buscar ventanas.
- Usa la demo ficticia, nunca archivos reales. Los archivos para arrastrar están en `data/demo/` (o bájalos desde la misma página).
- Para la escena 5, abre `data/demo/cartola_banco.csv` en Excel: la fila 74 es la transferencia del 09/10/2026 por $398.650 (hallazgo H07 del informe).
- Si te equivocas, sigue: después cortas. Mejor 2:30 claros que 3:00 apurados.
