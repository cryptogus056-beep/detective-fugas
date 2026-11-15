# PLAN.md · Detective de Fugas Pyme

Plan vivo. Cada tarea se marca con [x] cuando está hecha y verificada. Al retomar una sesión: leer este archivo y `BITACORA.md`, correr `python -m pytest -q` y `python scripts/evaluar.py`, y seguir desde la primera tarea sin marcar.

- Estado: **Plan aprobado por Gustavo el 15/11/2026. En ejecución.** Respaldo: Gustavo eligió la opción A (push solo a la rama de trabajo `claude/wizardly-hawking-b7n711` al cierre de cada fase; nunca a `main`, sin despliegues).
- Entrega del concurso: jueves 19 de noviembre de 2026, 23:59 (hora de Chile).
- Meta de puntaje: 12 de 12 fugas en las dos demos, con 0 falsos positivos (el mínimo exigido es 10 de 12).

---

## 1. Lo que ya comprobé antes de planificar

| Comprobación | Resultado |
|---|---|
| Leí completos `CLAUDE.md`, la spec, los dos `LEEME.md`, `generar_dataset.py` y `evaluar.py` | Hecho. No abrí nada de `data/*/_respuestas/` |
| `python scripts/generar_dataset.py --todas` regenera los mismos archivos | Sí: `git status` queda limpio después de regenerar |
| Python disponible | 3.13 (el código se escribe compatible con 3.10 o superior) |
| `openpyxl` | Instalado (3.1.5) |
| `pytest` | No estaba instalado: se instala con `pip install -r requirements.txt` al empezar la fase 1 |
| Pyodide desde su CDN oficial | Responde bien. Pero `openpyxl` NO viene dentro de Pyodide (lo revisé en la versión 0.26.4): ver riesgo R8 |
| Playwright (para probar la web con un navegador de verdad) | Disponible aquí con Node, no con Python: ver riesgo R9 |
| No encontré errores en el generador | No hay nada que tocar ahí |

---

## 2. Decisiones técnicas (las tomo yo y las anoto en la bitácora)

1. **Una sola forma de emparejar.** `emparejar.py` calcula una vez qué abono paga qué documento y qué cotización corresponde a qué documento. Las 5 reglas usan ese mismo resultado. Así una misma fuga no aparece dos veces (el evaluador cuenta los repetidos como falsos positivos).
2. **Evidencia siempre literal.** El `monto_clp` y la `fecha` de cada evidencia son valores que están escritos en esa fila. Si el hallazgo usa un monto calculado (por ejemplo, el total de un presupuesto que solo trae el neto), la evidencia cita el neto de la fila y la descripción explica el cálculo.
3. **Filas sin fecha o sin monto.** `licencias.csv` no tiene fechas y `equipo.csv` no tiene montos. Esas filas van como evidencia de apoyo (con el campo que falta en `null`), y cada hallazgo lleva además al menos una evidencia completa (por ejemplo, la fila del cobro en el banco). El verificador comprueba todos los campos presentes.
4. **Nada de nombres de columna en el código.** Todo pasa por `plantillas/*.json`, incluidos los valores de estado ("approved", "Aprobada", "APROBADO", "OK").
5. **Regla explícita para los números.** Cada plantilla dice cómo vienen (`chileno`: el punto es de miles; `decimal_punto`: el punto es decimal). Sin plantilla se usa una regla automática documentada y probada.
6. **Mismo código en la terminal y en la web.** Un módulo `auditoria.py` hace todo el recorrido (leer, detectar, verificar, escribir) y lo llaman tanto la CLI como la página.
7. **La capa LLM nunca se usa con una clave real en este trabajo.** Se programa y se prueba con una respuesta simulada. Usarla de verdad cuesta plata y eso lo decides tú.
8. **Filas ambiguas.** El núcleo escribe `ambiguas.json` con los abonos que no sabe clasificar. El modo agéntico puede devolver clasificaciones con `--clasificaciones`, que solo sirven para quitar o anotar hallazgos, nunca para inventar uno.

---

## 3. Archivos que voy a crear

```
PLAN.md                         este plan
detective/
  __init__.py                   versión del detector
  __main__.py                   CLI: auditar, plantilla, version
  config.py                     lee config.json con valores por defecto
  modelo.py                     registros comunes (movimiento, venta, documento, cotización...) con archivo y fila
  lectores.py                   CSV y XLSX: codificación, separador, preámbulo, número de línea física
  normalizar.py                 números chilenos, fechas, RUT, glosas
  plantillas.py                 carga plantillas, detecta cuál calza, propone una nueva
  emparejar.py                  abono con documento, cotización con documento
  reglas/
    __init__.py
    abono_sin_documento.py
    cotizacion_sin_cobro.py
    pago_pendiente.py
    suscripciones.py
    diferencia_iva.py
  verificador.py                relee cada fila citada y descarta lo que no calza
  auditoria.py                  recorrido completo, usado por la CLI y por la web
  informe.py                    hallazgos.json, informe.md, informe.html
  mensajes.py                   borradores de cobro (plantillas y LLM opcional)
plantillas/
  banco_cargos_abonos_separados.json   banco_monto_con_signo.json
  mercadopago_ventas.json              transbank_ventas.json
  sii_rcv_ventas.json                  sii_rcv_compras.json
  cotizaciones_generica.json           presupuestos_generica.json
  equipo.json                          licencias.json
tests/
  conftest.py
  test_normalizar.py   test_lectores.py   test_plantillas.py   test_emparejar.py
  test_regla_abono.py  test_regla_cotizacion.py  test_regla_pago.py
  test_regla_suscripciones.py  test_regla_iva.py
  test_verificador.py  test_contrato.py  test_informe.py  test_mensajes.py
  test_cli.py          test_punta_a_punta.py
  test_anti_trampa.py  test_idioma.py     test_web.py
  navegador/prueba_web.mjs      prueba opcional con un navegador real
scripts/
  construir_web.py              copia detective/, plantillas/ y data/demo/ (sin la llave) a web/
web/
  index.html  estilo.css  app.js
  py/  plantillas/  demo/  vendor/     (copias generadas por construir_web.py)
salida/demo/  salida/demo_b/    hallazgos.json, informe.md, informe.html, mensajes_cobro.md, descartados.json
```

Archivos que ya existen y voy a modificar: `README.md`, `BITACORA.md`, `ENTREGA/*.md`, `.claude/agents/*.md`, `.claude/commands/auditar.md`, `.gitignore` (solo si hace falta). No toco `scripts/generar_dataset.py`, `scripts/evaluar.py`, la llave ni los bloqueos de `.claude/settings.json`.

---

## 4. Fases y tareas

Cada fase cierra con: pruebas en verde, este plan actualizado, entrada en `BITACORA.md` y commit local.

### Fase 0 · Plan

- [x] Leer los 6 archivos en el orden pedido
- [x] Comprobar que el generador es reproducible
- [x] Escribir `PLAN.md`
- [x] Aprobación de Gustavo: "Sí, aprobado el PLAN.md"

**Verificación:** tu aprobación.

### Fase 1 · Base: lectores, normalización y plantillas

- [ ] 1.1 Instalar dependencias (`pip install -r requirements.txt`) y crear la estructura de `detective/` y `tests/`
- [ ] 1.2 `normalizar.py`: números (`1.234.567`, `$ 1.234.567`, `-34400`, `65000.00`), fechas (`dd/mm/aaaa`, `dd-mm-aaaa`, `aaaa-mm-dd`, ISO con hora y zona, fechas de Excel), RUT (formato `12.345.678-9` y dígito verificador), glosas (mayúsculas, sin códigos ni números de tarjeta)
- [ ] 1.3 `lectores.py`: detecta codificación (UTF-8 con y sin BOM, Latin-1) y separador (`;` o `,`), encuentra el encabezado aunque haya preámbulo, y guarda la línea física real de cada fila (también cuando un campo trae saltos de línea). Lee XLSX con `openpyxl`
- [ ] 1.4 `plantillas.py` y las 10 plantillas de la sección 5.3. Si ninguna calza, el error dice qué columnas encontró y cómo copiar `plantillas/_ejemplo.json`
- [ ] 1.5 `modelo.py` y `config.py` (umbrales con valores por defecto si falta `config.json`)
- [ ] 1.6 CLI: `python -m detective version` y `python -m detective plantilla --archivo ...`
- [ ] 1.7 Regla de archivos repetidos: si `cotizaciones.xlsx` y `cotizaciones.csv` traen lo mismo, usar el XLSX y avisarlo
- [ ] 1.8 Pruebas de lectores, normalización y plantillas

**Verificación:** `python -m pytest -q` en verde. Una prueba lee los 9 archivos de demo A y los 8 de demo B y comprueba rol, plantilla y cantidad de filas de cada uno.

### Fase 2 · Motor: emparejamiento, 5 reglas y verificador

- [ ] 2.1 `emparejar.py`: abono con documento (uno a uno, monto igual con tolerancia, ventana de fechas, prefiere mismo RUT y fecha más cercana), venta POS con boleta, cotización con documento
- [ ] 2.2 `abono_sin_documento` (banco y POS) respetando los señuelos: liquidaciones del POS, aportes de socios, devoluciones, transferencias que llegan antes de su boleta, ventas rechazadas
- [ ] 2.3 `cotizacion_sin_cobro` (normaliza estados, días de gracia)
- [ ] 2.4 `pago_pendiente_30d` (días de atraso)
- [ ] 2.5 `suscripcion_duplicada_o_huerfana` (duplicada y huérfana)
- [ ] 2.6 `diferencia_iva` (IVA mal calculado y neto cobrado como total)
- [ ] 2.7 Impacto en el periodo e impacto mensual (sección 4.6)
- [ ] 2.8 `verificador.py`: relee cada fila citada; lo que no calza va a `descartados.json` con su motivo
- [ ] 2.9 `auditoria.py` y `python -m detective auditar`, que escribe `hallazgos.json` según el contrato 6.1
- [ ] 2.10 Pruebas: cada regla con un caso positivo y su señuelo, el verificador descartando una cita falsa, el contrato de `hallazgos.json`, y que ninguna fila quede citada por dos hallazgos del mismo tipo

**Verificación:** `python -m detective auditar --datos data/demo --salida salida/demo` y luego `python scripts/evaluar.py --dataset data/demo`: al menos 10 de 12 y 0 falsos (meta: 12 de 12). Pego la salida aquí.

### Fase 3 · Generalidad (demo B)

- [ ] 3.1 Correr demo B sin tocar el código de las reglas. Si algo falla, se arregla en las plantillas o en el lector general, nunca con un "si es demo B"
- [ ] 3.2 Presupuestos que solo traen neto: el total se calcula con la tasa de IVA
- [ ] 3.3 Prueba de punta a punta: genera los datasets, corre el detector en las dos demos y ejecuta `evaluar.py` en ambas
- [ ] 3.4 Prueba anti trampa: `detective/`, `web/` y `plantillas/` no mencionan `_respuestas` ni `respuestas.json`, ni nombres de archivo o de carpeta de las demos

**Verificación:** `python scripts/evaluar.py --dataset data/demo_b` aprobado, demo A sigue aprobada y la prueba anti trampa en verde.

### Fase 4 · Informe y mensajes

- [ ] 4.1 `informe.md` con las 7 partes de la sección 6.2: título, resumen de exactamente 5 líneas, tabla ordenada por impacto mensual, detalle con la fila original copiada tal cual, cómo verificar, lo que no pude revisar y el pie
- [ ] 4.2 Formatos: montos `$1.234.567`, fechas `dd/mm/aaaa`
- [ ] 4.3 `informe.html`: el mismo informe con estilo, en un solo archivo, sin recursos externos
- [ ] 4.4 `mensajes_cobro.md`: encabezado de borrador, un mensaje por cada cobro (cotización sin cobro, pago pendiente) en "usted" por defecto con opción de "tú", y una nota interna para el resto
- [ ] 4.5 Modo `--llm`: si existe `ANTHROPIC_API_KEY` pule los textos; si no, avisa y usa las plantillas. Nunca envía nada. Se prueba con una respuesta simulada
- [ ] 4.6 Pruebas del informe y de los mensajes

**Verificación:** pruebas que cuentan las 5 líneas del resumen, revisan el orden de la tabla y el encabezado de borrador. Además leo yo los dos informes completos como si fuera el dueño de la pyme.

### Fase 5 · Modo agéntico

- [ ] 5.1 Revisar y mejorar los 3 subagentes y el comando `/auditar`
- [ ] 5.2 `ambiguas.json` y la opción `--clasificaciones` en la CLI
- [ ] 5.3 Ejecutar los pasos de `/auditar data/demo` con subagentes y comparar el resultado con el de la CLI

**Verificación:** el resultado del modo agéntico tiene los mismos hallazgos que la CLI y `evaluar.py` sigue aprobado. Queda anotado en la bitácora.

### Fase 6 · Web

- [ ] 6.1 `scripts/construir_web.py`: copia el código, las plantillas y la demo (sin la llave) y deja el informe de la demo ya calculado
- [ ] 6.2 `web/index.html`, `estilo.css`, `app.js`: título, la frase, aviso "Datos 100% ficticios", aviso "Tus archivos no salen de tu computador", diseño legible en celular
- [ ] 6.3 Pyodide con versión fija desde su CDN oficial, ejecutando el mismo paquete `detective/`
- [ ] 6.4 "Usar mis archivos": arrastrar y soltar, detectar la plantilla de cada archivo, mostrar el rol asignado y permitir cambiarlo, correr la auditoría, mostrar el informe y descargar `informe.md`, `hallazgos.json` y `mensajes_cobro.md`
- [ ] 6.5 XLSX en el navegador: copia local de `openpyxl` en `web/vendor/`. Si no carga, la web acepta solo CSV y lo explica en pantalla (decisión a la bitácora)
- [ ] 6.6 Pruebas: (a) siempre: los archivos copiados existen, están al día con el código y la web no tiene llamadas de red a dominios que no sean el CDN de Pyodide; (b) opcional con navegador real: la demo se ve, no hay errores en la consola y subir los CSV de demo B da el mismo `hallazgos.json` que la CLI

**Verificación:** `python scripts/construir_web.py`, servidor local, prueba con navegador real y captura de pantalla en ancho de computador y de celular.

### Fase 7 · Crítico

- [ ] 7.1 Lanzar el subagente `critico-pyme` con contexto limpio, solo con `salida/demo/informe.md`, `salida/demo/mensajes_cobro.md`, `README.md` y la web local
- [ ] 7.2 Corregir cada problema (máximo 5) o justificar por escrito por qué no
- [ ] 7.3 Registrar todo en `BITACORA.md`, sección "Crítico"

**Verificación:** sección "Crítico" completa, pruebas y evaluador en verde después de los cambios.

### Fase 8 · Documentación y entrega

- [ ] 8.1 `README.md` completo según la sección 13 (incluye "Cómo sacar tus archivos" con **[sin verificar]** en todo lo que no pueda comprobar en la fuente oficial)
- [ ] 8.2 `ENTREGA/`: reemplazar los marcadores que dependen del resultado; dejar los de link y video para ti
- [ ] 8.3 `BITACORA.md`: resumen arriba ("Fable corrigió N cosas; las 3 más importantes fueron...")
- [ ] 8.4 `salida/demo/` y `salida/demo_b/` regeneradas y dentro del repositorio como ejemplo

**Verificación:** prueba de idioma en verde (sin guion largo en ningún `.md` ni en la web), y una búsqueda de marcadores `[[` que solo debe dejar los de link y video.

### Fase 9 · Verificación final

- [ ] 9.1 Recorrer uno por uno los 12 criterios de la sección 12 y marcarlos aquí
- [ ] 9.2 Pegar aquí la salida de: generador, auditoría de las dos demos, `evaluar.py` de las dos demos y `python -m pytest -q`
- [ ] 9.3 Revisión de seguridad: sin claves, sin datos reales, sin push ni despliegue no autorizados
- [ ] 9.4 Mensaje final a Gustavo con el puntaje y los comandos que le tocan, en el orden de `PASO_A_PASO.md`

**Verificación:** todos los criterios marcados con su evidencia.

---

## 5. Riesgos y cómo los manejo

| N° | Riesgo | Qué hago |
|---|---|---|
| R1 | **Esta sesión corre en la nube, no en tu computador.** El contenedor es temporal: si se recicla por inactividad, los commits locales que no se hayan subido se pierden. La spec prohíbe `git push` sin tu permiso | Es la única decisión extra que te pido (ver sección 6) |
| R2 | Corte por límite de uso o cierre de sesión | Commit, plan y bitácora al cierre de cada fase. Se retoma con P2 |
| R3 | Reglas "hechas a la medida" de la demo. Leí el generador porque la spec lo pide, así que sé cómo se arman las fugas | Las reglas salen de la sección 4 de la spec, sin nombres ni montos de la demo en el código. Pruebas con casos propios, prueba anti trampa y demo B solo con plantillas |
| R4 | Confundir punto de miles con punto decimal (`34.400` contra `65000.00`) | Cada plantilla lo declara; regla automática documentada y probada con los casos de la spec |
| R5 | Número de fila corrido por preámbulos o por campos con saltos de línea | El lector guarda la línea física real y hay prueba para eso |
| R6 | Una fuga contada dos veces, o con dos tipos distintos | Emparejamiento único compartido y prueba que impide filas repetidas entre hallazgos del mismo tipo |
| R7 | Evidencia de filas sin fecha o sin monto (licencias, equipo) | Decisión 3 de la sección 2 |
| R8 | `openpyxl` no viene dentro de Pyodide | Copia local en `web/vendor/` (mismo origen, sin dominios extra). Si falla, la web queda solo con CSV, como permite la spec |
| R9 | La prueba con navegador real puede ser lenta y Playwright quizá no esté en tu computador | Esa prueba es opcional y se salta sola si falta Playwright. La prueba de archivos y privacidad corre siempre. Todo el conjunto debe tardar menos de 60 segundos |
| R10 | Limpiar de más las glosas (por ejemplo, borrar el "365" de Microsoft 365) | Solo se quitan números de tarjeta y códigos largos; hay prueba con esos casos |
| R11 | Los subagentes del proyecto no quedaron registrados en esta sesión (el repositorio llegó vacío al inicio) | Si no aparecen, lanzo un agente general con las mismas instrucciones del archivo y lo anoto |
| R12 | Formatos reales de bancos, Mercado Pago, Transbank y SII distintos a los de la demo | README honesto, plantillas fáciles de copiar y todo lo no comprobado marcado **[sin verificar]** |
| R13 | Plazo: jueves 19 | Fases 1 a 4 primero (son las que dan el puntaje); la web y el crítico después |

---

## 6. Lo único que necesito de ti (sección 0.5 de la spec)

1. **Aprobar este plan** con "Sí, aprobado el PLAN.md".
2. **Decidir cómo respaldar el trabajo** (riesgo R1). Opciones:
   - **A (recomendada):** me autorizas a subir respaldos solo a la rama de trabajo `claude/wizardly-hawking-b7n711` al cierre de cada fase. No toco `main`, no despliego y no publico nada. El repositorio es privado.
   - **B:** sin ningún push, tal como dice la spec. Si el contenedor se recicla antes de terminar, se pierde lo avanzado.
   - **C:** correr el proyecto en Claude Code dentro de tu computador, como describe `PASO_A_PASO.md`, donde los commits locales sí quedan guardados.

No voy a usar la API de Anthropic ni a gastar dinero, y no encontré errores en el generador, así que no hay más decisiones pendientes para ti.

---

## 7. Salida de los comandos finales

(Se completa en la fase 9.)
