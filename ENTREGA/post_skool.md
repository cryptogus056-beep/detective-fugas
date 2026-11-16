# Borrador del post para Skool (Imperio Agéntico · Built with FABLE)

> BORRADOR. No publicado. Los números ya son los reales (actualizados por Fable el 15/11/2026). Los links de la web y de GitHub ya están puestos. Solo te falta completar `[[LINK_VIDEO]]` y `[[LINK_POST_X]]`.

---

**Título:**

[FABLE] Detective de Fugas: encuentra la plata que tu pyme pierde sin darse cuenta

---

## 1. El proyecto

Las pymes pierden plata que nadie ve: una cotización aceptada que nadie facturó, una transferencia que entró sin boleta, un cliente que no pagó hace dos meses, la licencia de alguien que ya no trabaja contigo, un IVA mal calculado.

Construí con **Claude Fable 5.2** el **Detective de Fugas Pyme**: le pasas los archivos que cualquier pyme ya puede descargar (cartola del banco, ventas de Mercado Pago o Transbank, Registro de Compras y Ventas del SII y tu planilla de cotizaciones) y te entrega un informe con cada fuga, cuánta plata hay en juego y **la fila exacta del archivo que lo prueba**. Si no hay fila que lo pruebe, no aparece. Así de simple.

- Funciona en el navegador: tus archivos no salen de tu computador.
- No necesita claves de API ni pagar nada.
- Sirve para cualquier banco: si tu cartola tiene otras columnas, se agrega una plantilla.
- Te deja borradores de mensajes de cobro (no envía nada solo).

## 2. El resultado

- 🔗 Pruébalo: https://detective-fugas-web.vercel.app
- 🎥 Video de 2 minutos: [[LINK_VIDEO]]
- 💻 Código abierto: https://github.com/cryptogus056-beep/detective-fugas

**La prueba:** armé una pyme ficticia (una empresa de climatización con 3 meses de movimientos) y escondí 12 fugas de 5 tipos, más varias trampas que parecen fuga pero no lo son. Un script aparte compara el resultado con la llave de respuestas.

| Prueba | Fugas encontradas | Inventadas (falsos positivos) |
|---|---|---|
| Demo A (banco con Cargos y Abonos, Mercado Pago, XLSX) | 12 de 12 | 0 |
| Demo B (otro banco, monto con signo, Transbank, otros encabezados) | 12 de 12 | 0 |

En la demo A, el total en juego fue **$3.738.472** en 3 meses: $3.373.650 que le deben a la empresa o que nunca facturó, y $364.822 entre IVA y software pagado de más. La fuga más grande: una cotización por $1.499.400 que el cliente aceptó y nadie facturó. La demo B usa el mismo código, solo con otras plantillas de columnas.

Lo honesto: está probado solo con datos ficticios. Con tu banco real lo más probable es que necesite una plantilla de columnas (el README explica cómo crearla) y cada hallazgo hay que confirmarlo contra tu archivo.

Todos los datos son 100% ficticios.

## 3. Cómo lo hice

**Proceso:**

1. Escribí una spec completa (`SPEC_DETECTIVE_FUGAS.md`) con la regla de oro: "cada hallazgo cita archivo, fila, fecha y monto, o se descarta".
2. Generé el dataset ficticio con un script con semilla fija, así cualquiera obtiene exactamente los mismos archivos.
3. Le pedí a Fable 5.2 (esfuerzo alto) que leyera todo, escribiera un `PLAN.md` y, después de aprobarlo, construyera todo hasta terminar.
4. Fable orquestó: el núcleo es código Python determinista (por eso corre sin claves); subagentes económicos clasifican filas raras; un verificador vuelve a abrir cada archivo y confirma la fila antes de aceptar un hallazgo.
5. Al final, un crítico con contexto limpio revisó el informe como si fuera una dueña de pyme que no programa, encontró 5 problemas y Fable corrigió los 5.

**Correcciones (de la bitácora):** Fable registró 17 correcciones: 12 que detectó con sus propias pruebas y relecturas, y 5 que encontró el crítico. Además 173 pruebas automáticas, incluida una que abre la web en un navegador real. Las 3 más importantes:

1. **El informe mezclaba montos.** El crítico (como dueña de pyme) no podía saber cuánta plata era suya: la columna "Monto" a veces era la deuda y a veces el total de un documento cuya pérdida real era otra, y el resumen decía "al mes" para cosas que pasaron una sola vez. Fable separó "monto del documento" de "plata en juego" y reescribió el resumen.
2. **Los mensajes de cobro envejecían al enviarlos.** Decían "al 31/10 lleva 72 días sin pago" y prometían "le enviaremos la factura esta semana", sin datos para transferir. Ahora no citan fechas que cambian, adjuntan el documento, piden disculpas por la demora y traen entre corchetes lo que el dueño debe completar.
3. **Una prueba se delató a sí misma.** La prueba que prohíbe el guion largo falló apuntando a su propio archivo: la herramienta había convertido el código de escape en el carácter real. Es la clase de error que solo aparece si de verdad corres las pruebas en vez de suponer que pasan.

**Prompts para copiar:** están todos en `PROMPTS.md` del repo. Los dos que hicieron el 80% del trabajo:

```
Hola Fable. Vas a construir el proyecto "Detective de Fugas Pyme" para un concurso.

1. Lee completos, en este orden: CLAUDE.md, SPEC_DETECTIVE_FUGAS.md, data/demo/LEEME.md, data/demo_b/LEEME.md, scripts/generar_dataset.py y scripts/evaluar.py. No abras nada dentro de data/*/_respuestas/.
2. Sigue la sección 0 de SPEC_DETECTIVE_FUGAS.md al pie de la letra.
3. Escribe PLAN.md en la raíz con las fases de la sección 10 convertidas en tareas concretas, los archivos que vas a crear, los riesgos y cómo vas a verificar cada fase.
4. Muéstrame un resumen de PLAN.md en 10 líneas como máximo y espera mi "Sí, aprobado el PLAN.md".

Yo programo a nivel básico: explícame en español simple, con "tú", y solo pregúntame lo que la sección 0.5 de la spec reserva para mí.
```

```
Sí, aprobado el PLAN.md.

Ahora ejecuta todas las fases de PLAN.md hasta cumplir TODOS los criterios de aceptación de la sección 12 de SPEC_DETECTIVE_FUGAS.md, sin pedirme permiso entre fases.

Termina el trabajo. No te detengas hasta que esté completo y verificado. Si algo falla, investiga la causa, corrígela y sigue. No termines un turno con una lista de pendientes ni preguntando si continúas cuando puedes hacerlo tú. Solo detente por lo que la sección 0.5 reserva para mí.

Al cerrar cada fase: pruebas en verde, PLAN.md actualizado, entrada en BITACORA.md y commit local. Nunca hagas git push ni despliegues.
Antes de cada tarea larga dime en una línea qué vas a hacer.
```

**Para usarlo con tus datos:** abre https://detective-fugas-web.vercel.app, aprieta "Usar mis archivos" y arrastra tus CSV. Si tu banco no calza, el README explica cómo crear la plantilla en 2 minutos.

## 4. La moraleja

**La plata que se pierde no hace ruido: hay que contarla fila por fila.**

Y lo que aprendí con Fable: no le pidas que "encuentre problemas", pídele que **pruebe** cada problema. Cuando la regla es "sin evidencia no existe", el agente deja de adivinar y empieza a contar.

---

También en X: [[LINK_POST_X]] #FableImperial
