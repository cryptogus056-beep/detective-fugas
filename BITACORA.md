# Bitácora del Detective de Fugas Pyme

Aquí queda registrado cada error, corrección y decisión durante la construcción con Claude Fable 5.2. Es la base de la parte "cómo lo hice" del post del concurso.

**Resumen:** Fable corrigió 19 cosas (12 que detectó con sus propias pruebas y relecturas, 5 que encontró el crítico y 2 a partir de lo que vio Gustavo al usar la web publicada: la tabla que se salía de su recuadro y la falta de una guía de uso); las 3 más importantes fueron:

1. **El informe mezclaba montos.** El crítico (como dueña de pyme) no podía saber cuánta plata era suya: la columna "Monto" a veces era la deuda y a veces el total de un documento cuya pérdida real era otra, y el resumen decía "al mes" para cosas que pasaron una sola vez. Fable separó "monto del documento" de "plata en juego" y reescribió el resumen.
2. **Los mensajes de cobro envejecían al enviarlos.** Decían "al 31/10 lleva 72 días sin pago" y prometían "le enviaremos la factura esta semana", sin datos para transferir. Ahora no citan fechas que cambian, adjuntan el documento, piden disculpas por la demora y traen entre corchetes lo que el dueño debe completar.
3. **Una prueba se delató a sí misma.** La prueba que prohíbe el guion largo falló apuntando a su propio archivo: la herramienta había convertido el código de escape en el carácter real. Es la clase de error que solo aparece si de verdad corres las pruebas en vez de suponer que pasan.

Resultado final: demo A y demo B con 12 de 12 fugas y 0 falsos positivos; 173 pruebas automáticas en verde; la web da el mismo resultado que la línea de comandos. Además de las correcciones hay 12 decisiones de diseño registradas (por ejemplo, que los subagentes solo pueden quitar hallazgos, nunca agregar) y un bloqueo que no se resolvió por decisión propia: el respaldo con `git push` quedó denegado por `.claude/settings.json` y no se saltó.

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

## 2026-11-15 00:12 · Fase 1 · Regla explícita para punto de miles y punto decimal

- Qué pasó: decisión de diseño: `34.400` (cartola) y `65000.00` (Mercado Pago) usan el punto con significados distintos.
- Por qué: un grupo de miles siempre tiene 3 dígitos; un decimal en pesos casi nunca. Además cada plantilla declara su modo (`chileno` o `decimal_punto`).
- Qué cambié: `detective/normalizar.py` (`parsear_numero` con la regla escrita en su documentación) y el campo `numeros` de cada plantilla.
- Cómo lo verifiqué: `python -m pytest -q tests/test_normalizar.py`: 15 casos de números (miles, decimales, signo, paréntesis) en verde.

## 2026-11-15 00:12 · Fase 1 · Separador detectado por regularidad y plantillas con alias

- Qué pasó: decisión de diseño: el separador se elige por el que aparece la misma cantidad de veces en más líneas, y las plantillas aceptan varios nombres posibles por columna y un bloque `estados`.
- Por qué: una coma dentro de un nombre o una coma decimal no es regular; un separador de columnas sí. Los alias permiten que una misma plantilla sirva para variantes pequeñas (con o sin tilde, con o sin `($)`).
- Qué cambié: `detective/lectores.py`, `detective/plantillas.py` y los 10 JSON de `plantillas/`.
- Cómo lo verifiqué: prueba `test_lee_todos_los_archivos_de_las_demos`: los 8 archivos de datos de demo A y los 7 de demo B se reconocen con la plantilla esperada y sin filas saltadas (más `config.json` en cada una: 9 y 8).

## 2026-11-15 00:12 · Fase 1 · Cierre de fase 1

- Qué pasó: base terminada: normalización, lectores CSV y XLSX con línea física, plantillas, configuración y comandos `version` y `plantilla`. La tarea 1.7 (archivos repetidos) se hace junto con `auditoria.py` en la fase 2, porque ahí se reúnen los archivos.
- Por qué: el orden natural del código: la regla de repetidos necesita comparar registros ya cargados.
- Qué cambié: `detective/` (6 módulos), `plantillas/` (10 JSON), `tests/` (3 archivos de prueba).
- Cómo lo verifiqué: `python -m pytest -q`: 67 passed in 0.35s.

## 2026-11-15 00:20 · Fase 1 · El respaldo autorizado quedó bloqueado por el propio repositorio

- Qué pasó: Gustavo autorizó el push a la rama de trabajo (opción A), pero el comando `git push -u origin claude/wizardly-hawking-b7n711` fue denegado.
- Por qué: `.claude/settings.json` tiene la regla `Bash(git push:*)` en `deny`, y la spec (sección 0.4) prohíbe desactivarla. No la salté por otra vía (por ejemplo, la API de GitHub), porque sería burlar un bloqueo puesto a propósito.
- Qué cambié: nada. Sigo con commits locales y le explico a Gustavo cómo destrabarlo si quiere.
- Cómo lo verifiqué: mensaje del sistema: "Permission to use Bash with command git push ... has been denied".

## 2026-11-15 00:20 · Fase 2 · Demo A: 12 de 12 en la primera corrida, y por qué no me fío solo de eso

- Qué pasó: la primera ejecución completa del motor encontró las 12 fugas de demo A sin falsos positivos, y demo B (otro banco, otros formatos) también dio 12 de 12 sin cambiar código.
- Por qué: las reglas de la sección 4 de la spec son precisas, y la spec me pidió leer el generador, así que conozco la forma de los datos. Justamente por eso un 12 de 12 no prueba que el detector sirva fuera de la demo.
- Qué cambié: agregué 54 pruebas con datos propios (otras empresas, otros montos, otros servicios): cada regla con su caso positivo, sus señuelos y sus límites exactos (día 30 contra día 31, 2 pesos contra 3 pesos, día 7 contra día 8).
- Cómo lo verifiqué: `python scripts/evaluar.py --dataset data/demo` y `--dataset data/demo_b`: "Encontradas: 12 de 12   Falsos positivos: 0   RESULTADO: APROBADO" en ambas; `python -m pytest -q`: 121 passed.

## 2026-11-15 00:20 · Fase 2 · Mejoras sobre las reglas base de la spec

- Qué pasó: decisiones de diseño que van más allá del texto de la sección 4 (la spec lo permite si se anota): (1) emparejamiento con reacomodo, para no informar una fuga solo por haber elegido mal el orden de los pares; (2) una venta con tarjeta también puede pagar una factura; (3) una nota de crédito (tipo 61) anula su factura; (4) si una cotización aceptada no tiene factura pero sí llegó el pago, se informa una sola vez como abono sin documento; (5) un abono que viene del RUT de un proveedor (según el Registro de Compras) se trata como devolución; (6) quien dejó la empresa a mitad del periodo solo cuenta los meses siguientes; (7) las duplicadas solo se buscan en servicios que están en el archivo de licencias.
- Por qué: sin estas reglas, con datos reales habría falsos positivos evidentes (comisiones bancarias repetidas, facturas pagadas con tarjeta, facturas anuladas) o la misma plata contada dos veces.
- Qué cambié: `detective/emparejar.py` y los módulos de `detective/reglas/`.
- Cómo lo verifiqué: cada mejora tiene su prueba en `tests/test_emparejar.py` y `tests/test_regla_*.py`; las dos demos siguen en 12 de 12.

## 2026-11-15 00:20 · Fase 2 · Evidencia en archivos sin fecha o sin monto

- Qué pasó: `licencias.csv` no tiene fechas y `equipo.csv` no tiene montos, pero la regla de oro pide archivo, fila, fecha y monto.
- Por qué: la spec pide citar esas filas como evidencia de las licencias huérfanas, y a la vez exige fecha y monto exactos leídos de la fila.
- Qué cambié: esas filas van como evidencia de apoyo con el campo faltante en `null`, y cada hallazgo debe tener además al menos una evidencia completa (la fila del cobro en el banco). El verificador comprueba todo campo presente. Si no hay cobro en el banco, no hay hallazgo: queda un aviso para revisarlo a mano.
- Cómo lo verifiqué: pruebas `test_licencia_activa_de_alguien_que_ya_se_fue`, `test_huerfana_sin_cobro_en_el_banco_no_se_cuenta_pero_se_avisa` y `test_un_hallazgo_necesita_al_menos_una_evidencia_completa`.

## 2026-11-15 00:20 · Fase 2 · Corrección: una prueba del verificador estaba mal planteada

- Qué pasó: `test_descarta_una_cita_falsa_y_dice_por_que` falló: esperaba el motivo "encabezado" y recibió "ninguna evidencia tiene archivo, fila, fecha y monto a la vez".
- Por qué: el error era de la prueba, no del verificador: armé un hallazgo cuya única evidencia no tenía fecha ni monto, así que se descartaba antes (y con razón) por no tener ninguna evidencia completa.
- Qué cambié: `tests/test_verificador.py`: el caso del encabezado ahora se revisa directo con `revisar_evidencia`.
- Cómo lo verifiqué: `python -m pytest -q`: 121 passed.

## 2026-11-15 00:20 · Fase 2 · Corrección: tres textos que sonaban mal al leer los hallazgos

- Qué pasó: al leer la salida completa de demo A encontré: "Envía el mensaje de cobro y llama al cliente M02.", "solo hay una sola licencia registrada" y "(Mantencion preventiva domicilio operación 7000...)" sin coma.
- Por qué: armé las frases por partes y no las había leído completas.
- Qué cambié: `reglas/pago_pendiente.py` ("Llama al cliente y envía el mensaje de cobro M02."), `reglas/suscripciones.py` y `reglas/abono_sin_documento.py`.
- Cómo lo verifiqué: lectura de `salida/demo/hallazgos.json` después del cambio.

## 2026-11-15 00:20 · Fase 2 · Cierre de fase 2

- Qué pasó: motor completo: emparejamiento único, 5 reglas, verificador en código, `auditoria.py` y el comando `auditar`.
- Por qué: checkpoint de la spec: al menos 10 de 12 y 0 falsos en demo A.
- Qué cambié: `detective/emparejar.py`, `detective/reglas/` (5 reglas), `detective/verificador.py`, `detective/auditoria.py`, `detective/informe.py` (solo JSON por ahora), `detective/__main__.py`, 8 archivos de prueba nuevos.
- Cómo lo verifiqué: demo A: 12 de 12, 0 falsos, APROBADO. `python -m pytest -q`: 121 passed in 1.01s.

## 2026-11-15 00:21 · Fase 3 · Corrección: la prueba de idioma se delató a sí misma

- Qué pasó: `test_ningun_texto_tiene_guion_largo` falló señalando a `tests/test_idioma.py`: la propia prueba tenía el guion largo escrito de forma literal.
- Por qué: escribí el carácter con su código de escape, pero la herramienta con la que creé el archivo lo convirtió en el carácter real antes de guardarlo. Es exactamente la trampa que la spec advierte en la sección 9.
- Qué cambié: `tests/test_idioma.py`: el carácter ahora está como secuencia de escape de verdad en el archivo, comprobado leyendo la línea.
- Cómo lo verifiqué: `python -m pytest -q`: 134 passed. La línea del archivo se lee `GUION_LARGO = "\u2014"` (con una sola barra).

## 2026-11-15 00:21 · Fase 3 · Corrección: la prueba anti trampa encontró un nombre de la demo en el código

- Qué pasó: `test_el_codigo_y_las_plantillas_no_nombran_nada_propio_de_la_demo` falló por `detective/__main__.py`, que mencionaba `data/demo`.
- Por qué: era solo un ejemplo de uso en el comentario inicial, no una regla; pero la prueba es estricta a propósito: ningún nombre de archivo, empresa o servicio de las demos puede aparecer en `detective/` ni en `plantillas/`.
- Qué cambié: `detective/__main__.py`: el ejemplo ahora dice `<carpeta con tus archivos>`.
- Cómo lo verifiqué: `python -m pytest -q tests/test_anti_trampa.py`: 4 passed.

## 2026-11-15 00:21 · Fase 3 · Cierre de fase 3: demo B pasa solo con plantillas

- Qué pasó: demo B (otro banco con monto con signo y BOM, Transbank, presupuestos solo con neto) dio 12 de 12 sin tocar una línea de las reglas.
- Por qué: las diferencias entre A y B viven en `plantillas/*.json` (separador, formato de fecha, modo de números, nombres de columna y estados), no en el código.
- Qué cambié: pruebas nuevas: `tests/test_punta_a_punta.py` (regenera los datasets, corre el detector y ejecuta `evaluar.py` en ambas demos), `tests/test_anti_trampa.py`, `tests/test_idioma.py` y `tests/test_cli.py`.
- Cómo lo verifiqué: `python scripts/evaluar.py --dataset data/demo_b`: "Encontradas: 12 de 12   Falsos positivos: 0   RESULTADO: APROBADO". `python -m pytest -q`: 134 passed in 1.62s.

## 2026-11-15 07:48 · Fase 4 · La sesión se cortó a mitad de la fase 4 y se retomó sin perder nada

- Qué pasó: el turno se interrumpió justo después de escribir `detective/mensajes.py`. Gustavo pidió reintentar.
- Por qué: un corte de la sesión en la nube, no un error del código.
- Qué cambié: nada. Seguí la regla de reanudación: revisé `git status`, las tareas sin marcar de `PLAN.md` y corrí las pruebas antes de tocar algo.
- Cómo lo verifiqué: `git log` mostraba los 6 commits; `python -m pytest -q`: 134 passed; los dos archivos a medio hacer seguían en el disco.

## 2026-11-15 07:48 · Fase 4 · El informe se arma una sola vez y se escribe en dos formatos

- Qué pasó: decisión de diseño: `informe.py` construye el informe como estructura (`construir`) y de ahí salen `informe.md` e `informe.html`.
- Por qué: si cada formato armara sus propios textos, tarde o temprano dirían cosas distintas. Además la web reutiliza el mismo HTML.
- Qué cambié: `detective/informe.py` (resumen de 5 líneas, tabla, detalle con la fila original, cómo verificar, lo que no pude revisar, pie) y `detective/mensajes.py`.
- Cómo lo verifiqué: `tests/test_informe.py`: 5 líneas exactas, orden de la tabla igual al de `hallazgos.json`, fila original igual a la línea física del archivo, montos y fechas con el formato pedido, HTML sin recursos externos y con el texto escapado.

## 2026-11-15 07:48 · Fase 4 · Capa LLM opcional: programada y probada sin gastar un peso

- Qué pasó: el modo `--llm` usa la librería oficial de Anthropic con el modelo económico `claude-haiku-5-5`, solo si existe `ANTHROPIC_API_KEY`. No la ejecuté con una clave real.
- Por qué: gastar dinero está reservado a Gustavo (sección 0.5). Además el texto de un modelo puede cambiar un dato sin querer.
- Qué cambié: `detective/llm.py`: después de pulir, comprueba que el texto conserve monto, fecha y folio o número de cotización, que no use guion largo y que no se alargue demasiado; si algo falla, queda la plantilla fija. La librería `anthropic` es opcional y se carga solo al pedir `--llm`.
- Cómo lo verifiqué: `tests/test_mensajes.py` con un cliente simulado: 8 casos de falla (pierde el monto, respuesta vacía, texto cortado, negativa, clave inválida, sin conexión, error del servidor, guion largo) dejan la plantilla y un aviso. `python -m detective auditar --datos data/demo --llm` sin clave avisa y sigue.

## 2026-11-15 07:48 · Fase 4 · Corrección: cuatro cosas que confundían al leer el informe como dueño de pyme

- Qué pasó: al leer `salida/demo/informe.md` completo encontré: (1) la licencia huérfana decía monto $8.600 pero su evidencia mostraba $34.400; (2) la palabra "glosa" en textos para el usuario; (3) el saludo "Buenos días, Restaurante ..." a una empresa y el cierre "Quedo atento" en masculino; (4) nombres técnicos de plantilla en la lista de archivos leídos.
- Por qué: el cobro del banco es por las 4 licencias juntas y el informe no lo explicaba; el resto eran textos escritos pensando como programador.
- Qué cambié: `reglas/suscripciones.py` (explica que el cobro incluye todas las licencias), `reglas/abono_sin_documento.py` y `mensajes.py` ("descripción del movimiento", "Estimado equipo de ...", "Quedamos atentos"), `informe.py` (tipo de archivo en palabras simples).
- Cómo lo verifiqué: relectura de `salida/demo/informe.md` y `salida/demo/mensajes_cobro.md`; `python scripts/evaluar.py`: 12 de 12, 0 falsos.

## 2026-11-15 07:48 · Fase 4 · Cierre de fase 4

- Qué pasó: informe y mensajes listos: `informe.md`, `informe.html`, `mensajes_cobro.md`, opciones `--tratamiento` y `--llm`.
- Por qué: checkpoint de la spec: resumen de 5 líneas, tabla ordenada, evidencia y encabezado de borrador.
- Qué cambié: `detective/informe.py`, `detective/mensajes.py`, `detective/llm.py`, `detective/__main__.py`, `requirements.txt` (nota sobre la librería opcional), `salida/demo/` y `salida/demo_b/`.
- Cómo lo verifiqué: `python -m pytest -q`: 163 passed in 3.00s. Demo A y demo B: 12 de 12, 0 falsos.

## 2026-11-15 07:51 · Fase 5 · Modo agéntico: los subagentes solo pueden quitar, nunca agregar

- Qué pasó: decisión de diseño: el comando `/auditar` corre el núcleo, manda las filas ambiguas al subagente `clasificador-filas`, pide una segunda opinión al subagente `verificador-evidencia` y vuelve a correr el núcleo con sus respuestas (`--clasificaciones` y `--descartes`).
- Por qué: un modelo de lenguaje puede equivocarse o inventar. Si solo puede sacar hallazgos (y solo los que el núcleo marcó como ambiguos, en el caso del clasificador), el resultado agéntico nunca contradice la regla de oro.
- Qué cambié: `detective/auditoria.py` (`_aplicar_clasificaciones`, `_aplicar_descartes`), `detective/__main__.py` (opción `--descartes`), los 3 archivos de `.claude/agents/` y `.claude/commands/auditar.md`. Agregué las categorías `prestamo` y `reembolso` al clasificador.
- Cómo lo verifiqué: prueba `test_modo_agentico_clasificaciones_y_descartes_solo_pueden_quitar`: una clasificación de una fila no ambigua y un descarte de un hallazgo inexistente se ignoran con aviso.

## 2026-11-15 07:51 · Fase 5 · Ejecución real del flujo /auditar con subagentes

- Qué pasó: corrí los pasos de `/auditar data/demo` con subagentes de verdad. El verificador (modelo económico) revisó los 12 hallazgos y confirmó los 12, sin descartes. Como demo A no tiene filas ambiguas, probé el clasificador con un mini caso ficticio nuevo (`tests/datos/pyme_ambigua`): de 5 depósitos sin RUT dejó 2 como venta, 1 como dudoso ("otro"), y sacó un préstamo bancario y un reembolso de seguro.
- Por qué: el checkpoint de la fase pide que el modo agéntico llegue al mismo resultado que la CLI. En el mini caso, el total en juego bajó de $421.482 a $72.568 porque un préstamo de $2.000.000 ya no cuenta como venta sin boleta.
- Qué cambié: `salida/demo/verificacion_agente.json`, `salida/pyme_ambigua/` (con `clasificaciones.json`) y `tests/datos/pyme_ambigua/`.
- Cómo lo verifiqué: comparé `hallazgos.json` del modo agéntico con el de la CLI para demo A (sin contar la hora de generación): idénticos, 12 hallazgos. `python scripts/evaluar.py --dataset data/demo`: 12 de 12, 0 falsos. `python -m pytest -q`: 164 passed.

## 2026-11-15 13:48 · Fase 6 · Pyodide: versión comprobada en el CDN, no de memoria

- Qué pasó: antes de escribir la web consulté el CDN oficial: la última versión estable de Pyodide es la 314.0.8 (Python 3.14), y `openpyxl` no viene incluido en ninguna versión que revisé.
- Por qué: mi recuerdo de las versiones de Pyodide era antiguo (0.26). Fijar una versión sin comprobarla habría sido adivinar.
- Qué cambié: `web/app.js` fija `PYODIDE_VERSION = "314.0.8"`. Para leer Excel en el navegador, `scripts/construir_web.py` empaqueta `openpyxl` y `et_xmlfile` (Python puro, licencia MIT, con sus licencias dentro) en `web/vendor/openpyxl.zip`, servido desde el mismo sitio. No hizo falta `web/vercel.json`: es un sitio estático.
- Cómo lo verifiqué: en Chromium real, "Volver a calcular la demo aquí" lee `cotizaciones.xlsx` y da 12 fugas; los dominios contactados fueron solo el sitio local y `cdn.jsdelivr.net`.

## 2026-11-15 13:48 · Fase 6 · Privacidad con candado del navegador, no solo con promesas

- Qué pasó: decisión de diseño: además de no tener código que envíe datos, la página declara una política de seguridad (Content-Security-Policy) que solo permite conexiones al propio sitio y a la carpeta de Pyodide en su CDN.
- Por qué: "Tus archivos no salen de tu computador" es la promesa central. Con esa política, aunque alguien agregara por error una llamada a otro dominio, el navegador la bloquearía.
- Qué cambié: `web/index.html` (meta de la política, sin formularios), `web/app.js` (solo descargas con GET de archivos propios), `web/puente.py` (los archivos del usuario viven en una carpeta virtual en memoria).
- Cómo lo verifiqué: `tests/test_web.py`: revisa todas las direcciones escritas en `web/`, prohíbe las formas de enviar datos y, con navegador real, comprueba que el único método HTTP usado fue GET.

## 2026-11-15 13:48 · Fase 6 · Corrección: la comprobación de la web daba una falsa alarma

- Qué pasó: `python scripts/construir_web.py --comprobar` decía "web/py/manifiesto.json está desactualizado" justo después de construir.
- Por qué: la comprobación arma una copia temporal sin el lector de Excel, y el manifiesto anotaba "xlsx: false" en la copia y "true" en la real.
- Qué cambié: `scripts/construir_web.py`: al comprobar, el dato del lector de Excel se toma de la carpeta `web/` real.
- Cómo lo verifiqué: `python scripts/construir_web.py --comprobar`: "web/ está al día."

## 2026-11-15 13:48 · Fase 6 · Corrección: una prueba de privacidad confundía "import json" con "import js"

- Qué pasó: `test_privacidad_...` falló acusando a `detective/__main__.py` de usar el puente a JavaScript.
- Por qué: busqué el texto "import js" tal cual, y "import json" lo contiene.
- Qué cambié: `tests/test_web.py`: ahora es una expresión regular que exige la palabra completa al inicio de la línea.
- Cómo lo verifiqué: `python -m pytest -q`: 172 passed in 9.16s (incluye la prueba con navegador real).

## 2026-11-15 13:48 · Fase 6 · Cierre de fase 6: la web da lo mismo que la línea de comandos

- Qué pasó: la página muestra el informe de la demo ya calculado, deja subir archivos, reconoce qué es cada uno (y permite cambiarlo o quitarlo), corre el mismo paquete `detective/` con Pyodide y deja descargar `informe.md`, `hallazgos.json`, `mensajes_cobro.md` e `informe.html`. El proceso de la sesión se reinició una vez durante esta fase y se retomó sin pérdidas.
- Por qué: checkpoint de la spec: la demo se ve y subir los CSV de demo B da el mismo informe que la CLI.
- Qué cambié: `scripts/construir_web.py`, `web/` (página, estilos, `app.js`, `puente.py`, copias de código, plantillas y demo), `tests/test_web.py`, `tests/navegador/prueba_web.cjs`.
- Cómo lo verifiqué: prueba con Chromium: `hallazgos.json`, `informe.md` y `mensajes_cobro.md` del navegador son idénticos a los de la CLI para demo B; 0 errores en la consola; capturas revisadas en ancho de computador (1200) y de celular (390, sin desborde horizontal). La prueba con navegador se salta sola si no hay Node con Playwright o no hay acceso al CDN.

## 2026-11-15 13:55 · Fase 8 · Cierre de fase 8: documentación y entrega con números reales

- Qué pasó: README completo según la sección 13, borradores de `ENTREGA/` con los números reales y resumen al comienzo de esta bitácora.
- Por qué: el post del concurso necesita 4 partes (proyecto, resultado, cómo se hizo y moraleja) y no puede salir con marcadores vacíos ni con números inventados.
- Qué cambié: `README.md` (qué es, resultado, uso en 3 comandos, web, cómo sacar los archivos con **[sin verificar]** donde no pude comprobar la fuente oficial, plantillas, diagrama, cómo se construyó, limitaciones, privacidad, licencia). `ENTREGA/post_skool.md`, `ENTREGA/post_x.md` y `ENTREGA/guion_video.md`: 12 de 12 en ambas demos, $3.738.472 en juego, 17 correcciones, 5 problemas del crítico, y los prompts P0 y P1 pegados. Quedan solo los marcadores de links (`[[LINK_WEB]]`, `[[LINK_VIDEO]]`, `[[LINK_GITHUB]]`, `[[LINK_POST_X]]`), que le tocan a Gustavo.
- Cómo lo verifiqué: búsqueda de `[[` en `ENTREGA/`, `README.md` y `BITACORA.md`: solo aparecen marcadores `LINK_`. Los textos para X miden 255 y 196 caracteres (contando cada link como 23). `python -m pytest -q`: 173 passed.

## 2026-11-15 13:56 · Fase 9 · Verificación final: los 12 criterios de aceptación, con la salida pegada

- Qué pasó: recorrí uno por uno los criterios de la sección 12 de la spec y pegué la salida real de cada comando en la sección 7 de `PLAN.md`.
- Por qué: regla 10 de `CLAUDE.md`: verificar antes de decir "listo".
- Qué cambié: `PLAN.md` (todas las tareas marcadas, criterios con su evidencia y lo que queda en manos de Gustavo).
- Cómo lo verifiqué: generador reproducible (`git status --short data` sin cambios); demo A y demo B: "Encontradas: 12 de 12   Falsos positivos: 0   RESULTADO: APROBADO"; `python -m pytest -q`: 173 passed in 10.76s; `python scripts/construir_web.py --comprobar`: "web/ está al día."; búsqueda de claves: 0 archivos; `git ls-remote origin`: solo `main` en el commit inicial, o sea que no hubo push ni despliegue.

## 2026-11-15 22:46 · Fase 9 · Corrección: la tabla del informe se salía de su recuadro en la web publicada

- Qué pasó: Gustavo revisó la web publicada en su iMac y vio partes que se veían mal. Con capturas por sección a 1440 px encontré: (1) la tabla de 9 columnas medía 1148 px dentro de un recuadro de 1048 px, así que la columna "Acción" quedaba cortada fuera del borde; (2) las columnas angostas partían los textos en muchas líneas (una fila medía 201 px de alto); (3) el pie "Este informe no reemplaza a tu contador" salía dos veces; (4) "registro de ventas del sii" en minúsculas; (5) nombres de archivo entre apóstrofes en los avisos.
- Por qué: al agregar las columnas que pidió el crítico ("Plata en juego" y "Qué tan seguro") no volví a medir la tabla en pantalla ancha: la prueba con navegador solo revisaba el celular.
- Qué cambié: `detective/informe.py`: en la versión HTML el tipo de fuga va como etiqueta encima de "Qué pasó" (8 columnas en vez de 9), montos alineados a la derecha, "Plata en juego" en negrita, la nota del impacto mensual en una segunda línea pequeña, anchos mínimos por columna y un estilo intermedio para pantallas de 900 a 1100 px. `web/estilo.css`: página más ancha (1240 px). `web/index.html`: pie sin la frase repetida. `detective/auditoria.py`: nombres de archivo como código. El informe en Markdown no cambió de estructura.
- Cómo lo verifiqué: medí en Chromium a 1440, 1280, 1024, 768 y 390 px: la tabla queda dentro de su recuadro en todos y la fila más alta bajó de 201 a 124 px. Nueva prueba `test_navegador_la_tabla_no_se_sale_de_su_recuadro_en_ningun_ancho`. `python -m pytest -q`: 174 passed. Demo A y demo B siguen en 12 de 12, 0 falsos.

## 2026-11-16 09:17 · Fase 9 · Guía paso a paso dentro de la web, a pedido de Gustavo

- Qué pasó: Gustavo, al usar la web publicada, dijo que ni él sabía bien cómo usarla ni cómo sacarle provecho, y pidió una guía para que cualquier dueño de pyme pueda usarla de forma intuitiva.
- Por qué: la página asumía que la persona ya sabía qué archivos descargar, dónde conseguirlos, qué hacer si le faltaba alguno y qué hacer con el informe. Un informe largo sin un "qué hago ahora" no se aprovecha.
- Qué cambié: `web/index.html` y `web/app.js`: sección "Cómo se usa, en 3 pasos"; "Usar mis archivos" convertido en un asistente de 3 pasos con indicador de avance y una ayuda "¿Qué hago aquí?" en cada paso; una tarjeta por tipo de archivo (para qué sirve, prioridad, cómo conseguirlo con **[sin verificar]** donde corresponde) que se marca con ✓ al subirlo; recuadro "Qué puedo revisar con lo que subiste" que dice qué falta para cada tipo de fuga; plan de acción agrupado por lo que hay que hacer (`detective/informe.py`, `plan_de_accion`), con códigos que llevan al detalle; mensajes de cobro con botón "Copiar mensaje"; guía "¿Cómo leo este informe?"; descargas con nombres y explicación en palabras simples; 10 preguntas frecuentes. Planillas para llenar (`plantillas_para_llenar/`: cotizaciones, licencias y equipo) con dos plantillas nuevas que las reconocen (`equipo_planilla`, `licencias_planilla`). Los archivos no reconocidos ahora se explican sin comandos ni nombres de carpetas.
- Cómo lo verifiqué: recorrido completo en Chromium a 1440 y 390 px con capturas revisadas: sin errores de consola, sin desborde horizontal, el recuadro pasa de 3 de 5 a 5 de 5 al subir los archivos, las 7 tarjetas se marcan, el plan tiene 4 grupos y el código H01 lleva al detalle. Corrección en el camino: una tabla de ejemplo dentro de una tarjeta abierta estiraba la columna en celular (se arregló con `minmax(0,1fr)`). Pruebas nuevas en `tests/test_guia.py` y `tests/test_web.py`. `python -m pytest -q`: 182 passed.

## Crítico

Fase 7. El subagente `critico-pyme` se lanzó con contexto limpio el 15/11/2026: sin la spec, sin el plan, sin la bitácora, sin el código y sin la llave. Solo recibió `salida/demo/informe.md`, `salida/demo/mensajes_cobro.md`, `README.md` y la web local (página y 4 capturas). Actuó como Marcela, dueña de una pyme de servicios que no programa. Entregó 5 problemas, ordenados por gravedad. Los 5 se corrigieron; ninguno se rechazó.

| N° | Problema que encontró | Qué hice | Dónde |
|---|---|---|---|
| 1 | **Los montos se mezclan.** La columna "Monto" a veces era lo que te deben y a veces el total de un documento cuya pérdida real era otra (folio 1222: monto $500.500, pérdida $40.950). El resumen decía "unos $1.246.158 al mes", que parecía un gasto mensual y no lo es | La tabla ahora separa "Monto del documento o movimiento" de "Plata en juego", con una nota que lo explica. La línea 1 del resumen separa lo que te deben ($3.373.650) del resto ($364.822) y dice que casi todo pasó una sola vez; lo único mensual son $21.590 de software | `detective/informe.py` |
| 2 | **Palabras técnicas y pasos que no sabría hacer.** "config.json", "palabras_excluidas_abonos", "neto", "folio", "nota de débito", "fecha de corte", "terminal" | El informe trae un glosario corto. Las notas internas ya no piden editar un archivo: dicen "no emitas nada y avísale a tu contador". El README parte con "¿No programas? Usa la web" y explica el archivo de datos de empresa en palabras simples. La web ya no exige ese archivo: pregunta el nombre de la empresa y el último día que cubren los archivos | `detective/informe.py`, `detective/mensajes.py`, `README.md`, `web/index.html`, `web/app.js` |
| 3 | **"Riesgo de multa del SII [sin verificar...]" asusta y no ayuda; la confianza queda escondida.** La acción decía "Emite la boleta" sin condiciones, y un hallazgo de confianza media contaba igual que los seguros | La frase ahora termina con "no sé de cuánto sería, pregúntale a tu contador" y explica qué es el IVA en riesgo. La tabla tiene la columna "Qué tan seguro". El resumen avisa cuántas fugas hay que confirmar. La acción pasó a "Confirma que fue una venta y que no tiene documento; si es así, emite la boleta o factura" | `detective/reglas/abono_sin_documento.py`, `detective/informe.py` |
| 4 | **Mensajes de cobro incompletos o fuera de fecha.** "Al 31/10/2026 lleva 72 días" envejece el día que se envía; prometían "le enviaremos la factura esta semana"; no traían datos para transferir ni contacto; saludos distintos entre mensajes | Los mensajes ya no citan la fecha de corte ni cuentan días (ese dato quedó en una línea "Antes de enviarlo", solo para el dueño). El de cotización adjunta el documento y pide disculpas por la demora. Todos traen datos de pago, contacto y nombre entre corchetes para completar, y el mismo saludo. Si se usa la capa LLM, los corchetes son datos obligatorios | `detective/mensajes.py`, `detective/llm.py` |
| 5 | **La prueba de calidad es con datos inventados y la advertencia estaba escondida.** "12 de 12" no significa nada para ella; la advertencia de que no se probó con cartolas reales estaba en la línea 199 del README; "sin instalar nada" pero descarga 15 MB | La advertencia subió al inicio del README y al aviso amarillo de la web ("todavía no se ha probado con archivos reales de bancos..."). El puntaje se explica como "fugas que escondimos a propósito". El README aclara qué prueba y qué no prueba la demo, y que el motor pesa unos 15 MB la primera vez | `README.md`, `web/index.html`, `web/app.js` |

Cómo lo verifiqué: 5 pruebas se actualizaron y 1 se agregó para dejar fijo cada cambio (montos separados en la tabla, resumen sin "al mes", mensajes sin fechas que envejecen y con corchetes, advertencia visible en la web, formulario de datos de empresa). `python -m pytest -q`: 173 passed. `python scripts/evaluar.py` en demo A y demo B: 12 de 12, 0 falsos positivos. La web se volvió a probar en Chromium real después de los cambios.

Lo que el crítico pidió y no se hizo tal cual: propuso eliminar "impacto mensual" salvo en software. Se mantuvo la columna porque la spec exige ordenar la tabla por impacto mensual (sección 4.6), pero ahora se explica y ya no aparece sumada en el resumen.
