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

## Crítico

(Fable completa esta sección en la fase 7: los máximo 5 problemas encontrados y qué se hizo con cada uno.)
