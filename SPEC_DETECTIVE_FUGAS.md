# SPEC: Detective de Fugas Pyme

Versión 1.0 · 14 de noviembre de 2026 · Autor del encargo: Gustavo Scheel
Concurso: "Built with FABLE" de Imperio Agéntico · Entrega: jueves 19 de noviembre de 2026, 23:59 (hora de Chile)

---

## 0. Instrucciones para Fable (lee esto primero)

Eres el ingeniero a cargo de este proyecto de principio a fin. Gustavo programa a nivel básico, así que tú decides lo técnico y él solo aprueba lo importante.

### 0.1 Cómo trabajar

1. Lee completos, en este orden: `CLAUDE.md`, este archivo (`SPEC_DETECTIVE_FUGAS.md`), `data/demo/LEEME.md`, `data/demo_b/LEEME.md`, `scripts/generar_dataset.py` y `scripts/evaluar.py`. No abras nada dentro de `data/*/_respuestas/` (ver regla 0.4).
2. Escribe `PLAN.md` en la raíz con: las fases de la sección 10 convertidas en tareas concretas, los archivos que vas a crear, los riesgos que ves y cómo vas a verificar cada fase.
3. Muéstrale a Gustavo un resumen de `PLAN.md` en 10 líneas como máximo y espera su "Sí, aprobado el PLAN.md". Es la ÚNICA pausa planificada.
4. Después de la aprobación, EJECUTA todas las fases hasta cumplir los criterios de aceptación de la sección 12, sin pedir permiso entre fase y fase.
5. Al cerrar cada fase: corre las pruebas, actualiza `PLAN.md` (marca lo hecho con [x]), escribe en `BITACORA.md` y haz un commit local con un mensaje claro en español (por ejemplo `fase 2: motor de deteccion`). Commit local sí; `git push` nunca.
6. Antes de cada tarea larga, di en una línea qué vas a hacer. Al final de cada turno, deja un resumen corto de lo hecho y lo que sigue.

### 0.2 Terminar el trabajo

> Termina el trabajo. No te detengas hasta que la tarea esté completa y verificada contra los criterios de aceptación de la sección 12. Si un comando falla, una prueba no pasa, una herramienta se cae o algo se demora, investiga la causa, corrígela y sigue. Esos son obstáculos normales, no motivos para parar. No termines un turno con una lista de "lo que falta" ni con un "¿quieres que continúe?" cuando todavía puedes hacer ese trabajo tú mismo: hazlo. Detente solo ante un bloqueo real: una decisión que la sección 0.5 reserva para Gustavo, un acceso que no tienes, o un archivo marcado como intocable. Si te detienes, explica exactamente qué necesitas y por qué, en una sola pregunta con todas las opciones.

### 0.3 Si te interrumpen (límite del plan Pro, cierre de sesión, error)

Al retomar, lee `PLAN.md` y las últimas entradas de `BITACORA.md`, corre `python -m pytest -q` y `python scripts/evaluar.py`, y continúa desde la primera tarea sin marcar. No rehagas lo que ya está hecho y verificado.

### 0.4 Reglas que no se negocian

- **Solo datos ficticios.** No uses ni pidas datos reales de Gustavo, de Parrillero, de Barreau Mol ni de nadie. Todo lo de `data/` es inventado.
- **Regla de oro de la evidencia:** cada hallazgo cita archivo de origen, fila, fecha y monto exactos. Si no puedes citarlo, se descarta. Sin excepciones.
- **La llave es secreta para el detector.** Ni el código del detector, ni los subagentes de detección, ni tú mientras diseñas reglas, leen `data/*/_respuestas/`. Solo `scripts/evaluar.py` la lee. Si una regla funciona solo porque viste la respuesta, es trampa y el jurado lo va a notar. Diseña las reglas a partir de esta spec y de los datos de entrada. Hay una prueba automática que verifica que el código de `detective/` y `web/` no menciona `_respuestas`.
- **Nada sale de la máquina sin permiso.** No hagas `git push`, no despliegues en Vercel, no publiques en Skool ni en X, no envíes mensajes de cobro. Gustavo hace eso él mismo (ver `PASO_A_PASO.md`). Tú dejas todo listo y le dices el comando exacto.
- `.claude/settings.json` ya bloquea leer la llave, `git push` y `vercel`. No lo desactives.
- **Sin secretos en el repo.** Nada de claves de API en archivos. La capa LLM opcional lee `ANTHROPIC_API_KEY` desde el entorno y funciona sin ella.
- **No modifiques la lógica de `scripts/generar_dataset.py` ni la llave** para que tu detector "pase". Si encuentras un error real en el generador, anótalo en `BITACORA.md`, explícalo y pregunta antes de tocarlo.
- Español neutro latinoamericano con "tú" en todo texto para usuarios. Sin guiones largos (el carácter Unicode U+2014); usa dos puntos, comas o paréntesis.

### 0.5 Decisiones que SÍ requieren a Gustavo (y nada más)

1. Aprobar `PLAN.md`.
2. Cualquier `git push`, despliegue, publicación o envío.
3. Tocar el generador o la llave por un error real.
4. Gastar dinero (por ejemplo, usar la API de Anthropic con su clave).

Todo lo demás (librerías, estructura, nombres, diseño de la web, textos) lo decides tú y lo anotas en `BITACORA.md`.

---

## 1. Contexto y objetivo

Las pymes de Chile y Latinoamérica pierden plata sin darse cuenta: cotizaciones aceptadas que nadie facturó, transferencias que llegaron sin boleta, clientes que no pagaron, suscripciones de gente que ya se fue, IVA mal calculado. Nadie lo nota porque esa plata "no hace ruido".

El **Detective de Fugas Pyme** lee los archivos que cualquier pyme ya puede exportar (cartola del banco, ventas de Mercado Pago o Transbank, Registro de Compras y Ventas del SII, planilla de cotizaciones) y entrega un informe con cada fuga, su monto y la fila exacta que la prueba.

El jurado evalúa:

| Criterio | Cómo lo cubrimos |
|---|---|
| Impacto | Plata concreta en CLP, ordenada por impacto mensual, con mensajes de cobro listos |
| Claridad y replicabilidad | Funciona sin claves de API, cualquiera lo corre con sus propios archivos, README y plantillas de columnas |
| Prueba | Dataset ficticio con 12 fugas escondidas y llave de respuestas; `evaluar.py` muestra el puntaje; una segunda variante con otro banco y otros formatos |

El post del concurso debe tener 4 partes: el proyecto, el resultado (link y video), cómo lo hiciste (prompts copiables, proceso y correcciones) y la moraleja. Por eso `BITACORA.md` es obligatoria.

## 2. Producto

### 2.1 Entradas (todas opcionales salvo la cartola; el detector usa lo que haya)

| Rol | Ejemplo demo A | Ejemplo demo B | Uso |
|---|---|---|---|
| `banco` | `cartola_banco.csv` | `movimientos_cuenta.csv` | Abonos y cargos |
| `pos` | `ventas_mercadopago.csv` | `ventas_transbank.csv` | Ventas con tarjeta o link |
| `rcv_ventas` | `rcv_ventas.csv` | `rcv_ventas.csv` | Facturas (33) y boletas (39) emitidas |
| `rcv_compras` | `rcv_compras.csv` | `rcv_compras.csv` | Facturas de proveedores (contexto, devoluciones) |
| `cotizaciones` | `cotizaciones.xlsx` (o `.csv`) | `presupuestos.csv` | Lo cotizado y aceptado |
| `equipo` | `equipo.csv` | `equipo.csv` | Personas activas e inactivas |
| `licencias` | `licencias.csv` | `licencias.csv` | Asientos de software por usuario |
| `config` | `config.json` | `config.json` | Fecha de corte, umbrales, exclusiones |

Si el mismo rol llega dos veces con el mismo contenido (en la demo A, `cotizaciones.xlsx` y su espejo `cotizaciones.csv`), usa uno solo, prefiriendo el XLSX, y dilo en el informe; así no duplicas hallazgos. Si falta un archivo, el informe lo dice en "Lo que no pude revisar" y salta los tipos de fuga que dependen de él. Nunca falla en silencio.

### 2.2 Salidas (en `salida/<nombre_dataset>/`)

1. `hallazgos.json`: contrato de la sección 6.1 (lo lee `evaluar.py`).
2. `informe.md`: informe para el dueño de la pyme (sección 6.2).
3. `mensajes_cobro.md`: borradores de mensajes, NUNCA enviados (sección 6.3).
4. `informe.html` opcional: el mismo informe con estilo, para imprimir o compartir.

### 2.3 Cómo se usa

```bash
python -m detective auditar --datos data/demo --salida salida/demo
python scripts/evaluar.py --dataset data/demo
```

Y en la web: abres la página, ves el informe de la demo precargada, subes tus archivos y obtienes tu informe en el navegador. Tus datos no salen de tu computador.

## 3. Regla de oro de la evidencia

Un hallazgo es válido solo si su lista `evidencia` tiene al menos un elemento con:

- `archivo`: nombre del archivo tal como lo subió el usuario.
- `fila`: número de línea física del archivo, donde la primera línea es 1 (incluye preámbulos y encabezado). En XLSX, el número de fila de Excel. Así el usuario abre el archivo y llega directo.
- `fecha` (AAAA-MM-DD) y `monto_clp` (entero) leídos de esa fila.
- `detalle`: el texto relevante de la fila (glosa, folio, número de cotización).

El **verificador** (sección 7.3) vuelve a abrir cada archivo citado, lee esa fila y confirma que la fecha y el monto coinciden. Si no coinciden, el hallazgo se descarta y se registra en `salida/<dataset>/descartados.json` con el motivo. Esto se hace en código, no solo con un agente.

## 4. Tipos de fuga

Usa exactamente estos 5 valores de `tipo`. Los umbrales vienen de `config.json` (con valores por defecto si falta). Las reglas son la base sugerida; puedes mejorarlas, pero cada mejora va a `BITACORA.md` con el motivo.

Notación: `tol` = `tolerancia_clp` (por defecto 2). `corte` = `fecha_corte`.

### 4.1 `abono_sin_documento`: entró plata sin boleta ni factura

- **Banco:** cada abono que NO contenga ninguna de `palabras_excluidas_abonos` ni ningún RUT de `ruts_excluidos_abonos`, y que no calce con un documento de `rcv_ventas` (tipo 33 o 39) de monto total igual (± tol), con fecha del documento entre 60 días antes y `ventana_dias_abono_documento` días después del abono. Cada documento se usa una sola vez (emparejamiento uno a uno; prefiere la fecha más cercana y, si la glosa trae RUT, el mismo RUT).
- **POS:** cada venta aprobada que no calce con una boleta (39) de igual total (± tol) del mismo día o del día siguiente. Las ventas rechazadas no cuentan.
- **Impacto:** el IVA en riesgo, `monto - round(monto / 1,19)`, más la nota "riesgo de multa del SII [sin verificar el monto de la multa]". `monto_clp` = monto del abono.
- **Señuelos que debes respetar:** liquidaciones del POS al banco, aportes de socios, devoluciones de proveedores, transferencias que llegan 1 a 3 días antes de su boleta.

### 4.2 `cotizacion_sin_cobro`: se aceptó y nunca se facturó

- Cotización con estado aceptado (normaliza: "Aceptada", "APROBADO", "Aprobada", "OK", etc.), con `fecha_aceptacion` al menos `dias_gracia_cotizacion` días antes del corte, para la que no existe documento en `rcv_ventas` del mismo RUT, con fecha igual o posterior a la cotización y con neto igual, o total igual, o total igual al neto cotizado (± tol).
- **Impacto:** total cotizado (neto + IVA).
- **Señuelos:** cotizaciones rechazadas o pendientes; una aceptada hace pocos días.

### 4.3 `pago_pendiente_30d`: facturaste y no te pagaron

- Factura (33) de `rcv_ventas` sin abono emparejado en el banco (usa el mismo emparejamiento de 4.1) y con `corte - fecha_documento > dias_pago_pendiente`.
- **Impacto:** total de la factura. Muestra los días de atraso.
- **Señuelos:** facturas recientes sin pagar (menos de 30 días), facturas pagadas al día 29.

### 4.4 `suscripcion_duplicada_o_huerfana`: pagas software de más

- **Duplicada:** el mismo comercio (glosa normalizada: mayúsculas, sin números de tarjeta ni códigos) cobrado 2 o más veces en el mismo mes por el mismo monto, en al menos 2 meses del periodo, con menos asientos en `licencias` que cobros por mes. Un solo hallazgo agrupa todas las filas.
- **Huérfana:** licencia "Activa" en `licencias` cuyo usuario figura "Inactivo" en `equipo` con `fecha_salida` anterior al periodo. Evidencia: fila de la licencia, fila del equipo y las filas de cobro del servicio en el banco.
- **Impacto mensual:** el costo mensual del asiento o del cobro duplicado. `impacto_clp` = mensual × meses del periodo.
- **Señuelos:** dos servicios distintos que cuestan lo mismo; un ex empleado cuya licencia ya se dio de baja.

### 4.5 `diferencia_iva`: el IVA salió de tu bolsillo

- **IVA mal calculado:** documento en `rcv_ventas` donde `|IVA - round(neto × tasa_iva)| > tol`. Impacto: la diferencia.
- **Neto cobrado como total:** cotización aceptada con neto N y su documento tiene total = N (± tol) y neto distinto de N. Le cobraste al cliente el neto y el IVA lo pusiste tú. Impacto: total cotizado menos total facturado.
- **Señuelos:** boletas donde el IVA va incluido y el redondeo da ±1 peso.

### 4.6 Impacto mensual y orden

Cada hallazgo trae `impacto_clp` (en el periodo) e `impacto_mensual_clp`. Para fugas recurrentes es el costo mensual; para fugas puntuales es `impacto_clp / meses_del_periodo` y el informe lo llama "promedio mensual". El informe ordena por `impacto_mensual_clp` de mayor a menor.

## 5. Formatos de entrada y mapeo de columnas

Cada banco y cada sistema exporta distinto. El detector NO debe tener nombres de columna fijos en el código: usa **plantillas de mapeo** en `plantillas/*.json`.

### 5.1 Formato de plantilla

```json
{
  "nombre": "banco_cargos_abonos_separados",
  "rol": "banco",
  "descripcion": "Cartolas con columnas Cargos y Abonos separadas, separador ';', fechas dd/mm/aaaa",
  "deteccion": {"encabezado_contiene": ["Fecha", "Cargos", "Abonos"]},
  "separador": ";",
  "formato_fecha": ["%d/%m/%Y"],
  "numeros": "chileno",
  "columnas": {"fecha": "Fecha", "descripcion": "Descripcion", "cargo": "Cargos ($)", "abono": "Abonos ($)"}
}
```

Variante de monto único con signo: `"columnas": {"fecha": "...", "descripcion": "...", "monto_con_signo": "Monto"}`.

### 5.2 Requisitos del lector

- Detecta solo la plantilla que calza (por los encabezados) y busca la fila de encabezado aunque haya líneas de preámbulo antes.
- Acepta `;` y `,`, UTF-8 con y sin BOM, y Latin-1 (muchos bancos chilenos exportan así [sin verificar]).
- Números chilenos: `1.234.567`, `$ 1.234.567`, `-34400`, `65000.00`. Distingue punto de miles de punto decimal con una regla explícita y probada.
- Fechas: `dd/mm/aaaa`, `dd-mm-aaaa`, `aaaa-mm-dd`, ISO con hora y zona, y fechas nativas de Excel.
- RUT: normaliza a `12.345.678-9` y valida el dígito verificador (si no valida, igual lo usa, pero lo anota).
- Si ninguna plantilla calza, el error dice qué columnas encontró y cómo crear una plantilla nueva copiando `plantillas/_ejemplo.json`.
- `python -m detective plantilla --archivo mi_cartola.csv` muestra los encabezados detectados y propone una plantilla.

### 5.3 Plantillas mínimas que debes incluir

1. `banco_cargos_abonos_separados` (demo A).
2. `banco_monto_con_signo` (demo B).
3. `mercadopago_ventas` (demo A) y `transbank_ventas` (demo B).
4. `sii_rcv_ventas` y `sii_rcv_compras`.
5. `cotizaciones_generica` (demo A, XLSX y CSV) y `presupuestos_generica` (demo B, solo neto: el total se calcula con la tasa de IVA).
6. `equipo` y `licencias`.

### 5.4 Cómo exportar desde fuentes reales (para el README)

Escribe una sección "Cómo sacar tus archivos" con pasos cortos para: cartola de los bancos más usados por pymes en Chile, Mercado Pago, Transbank, Registro de Compras y Ventas del SII y una planilla de cotizaciones. Todo paso que no hayas comprobado en la fuente oficial va marcado **[sin verificar]**. No inventes nombres de menús con seguridad que no tienes; mejor describe "busca la opción de descargar movimientos en Excel o CSV [sin verificar]".

## 6. Contratos de salida

### 6.1 `hallazgos.json`

```json
{
  "empresa": "Climatizacion Austral Ficticia SpA",
  "fecha_corte": "2026-10-31",
  "generado_en": "2026-11-15T10:00:00-03:00",
  "version_detector": "1.0.0",
  "archivos_leidos": [{"archivo": "cartola_banco.csv", "rol": "banco", "plantilla": "banco_cargos_abonos_separados", "filas": 120}],
  "hallazgos": [
    {
      "id": "H01",
      "tipo": "cotizacion_sin_cobro",
      "titulo": "Cotización aceptada que nunca se facturó",
      "descripcion": "COT-0999 aceptada el 01/01/2026 por $1.190.000 sin factura ni pago.",
      "monto_clp": 1190000,
      "impacto_clp": 1190000,
      "impacto_mensual_clp": 396667,
      "recurrente": false,
      "confianza": "alta",
      "evidencia": [
        {"archivo": "cotizaciones.xlsx", "fila": 99, "fecha": "2026-01-01", "monto_clp": 1190000, "detalle": "COT-0999 Aceptada (ejemplo inventado, no está en la demo)"}
      ],
      "accion_sugerida": "Emite la factura y envía el mensaje de cobro M01.",
      "verificado": true
    }
  ],
  "no_revisado": ["No había archivo de licencias: no revisé suscripciones huérfanas."]
}
```

### 6.2 `informe.md`

1. Título con nombre de la empresa y periodo.
2. **Resumen en 5 líneas** (exactamente 5): total en juego en CLP, cuántas fugas y de qué tipos, la más grande, qué hacer primero esta semana, y cuánto se recupera si cobras lo pendiente.
3. Tabla de hallazgos ordenada por impacto mensual: N°, tipo (en palabras simples), qué pasó, monto, impacto mensual, evidencia (`archivo` fila N, fecha, monto) y acción.
4. Detalle por hallazgo con la fila original copiada tal cual.
5. "Cómo verificar este informe": abre el archivo y ve a la fila indicada.
6. "Lo que no pude revisar".
7. Pie: "Este informe no reemplaza a tu contador. Montos en CLP."

Formato de montos: `$1.234.567`. Fechas: `dd/mm/aaaa`.

### 6.3 `mensajes_cobro.md`

- Encabezado: "BORRADORES. Nada de esto se ha enviado. Revísalo antes de usarlo."
- Un mensaje por hallazgo que implique cobrar (cotización sin cobro, pago pendiente): asunto, texto cordial y firme en "tú" o "usted" según la plantilla que elija el usuario (por defecto "usted" para clientes), monto, folio o número de cotización y fecha.
- Para el resto (abono sin documento, suscripciones, IVA): una "nota interna" con la acción (emitir boleta, dar de baja la licencia, revisar con tu contador).
- Modo por defecto: plantillas deterministas en código. Modo opcional `--llm`: si existe `ANTHROPIC_API_KEY`, pule los textos con un modelo económico; si no existe, avisa y usa las plantillas. Nunca envía nada.

## 7. Arquitectura

### 7.1 Núcleo determinista (obligatorio)

Paquete `detective/` en Python 3.10+ con solo biblioteca estándar más `openpyxl` (para XLSX). Sin pandas: el mismo código debe correr en el navegador con Pyodide.

Estructura sugerida:

```
detective/
  __init__.py
  __main__.py        # CLI: auditar, plantilla, version
  lectores.py        # CSV/XLSX, encabezado, separador, codificación
  normalizar.py      # números, fechas, RUT, glosas
  plantillas.py      # carga y detecta plantillas
  emparejar.py       # abono <-> documento, cotización <-> documento
  reglas/            # un módulo por tipo de fuga
  verificador.py     # relee cada fila citada y descarta lo que no calza
  informe.py         # hallazgos.json, informe.md, informe.html
  mensajes.py        # borradores de cobro (plantillas + LLM opcional)
plantillas/*.json
tests/
web/
```

### 7.2 Modo agéntico en Claude Code (para mostrar cómo trabajó Fable)

Además del código, deja un flujo agéntico reproducible que cualquiera con Claude Code pueda correr:

- `.claude/agents/clasificador-filas.md` (modelo económico): clasifica filas ambiguas (por ejemplo, glosas de banco raras) en "venta", "aporte", "devolución", "proveedor", "suscripción" u "otro", y devuelve JSON con archivo y fila. Nunca inventa filas.
- `.claude/agents/verificador-evidencia.md` (modelo económico): recibe `hallazgos.json`, abre cada archivo citado y confirma fila, fecha y monto. Devuelve la lista de hallazgos confirmados y descartados.
- `.claude/agents/critico-pyme.md`: revisa el informe como dueño de pyme sin contexto (sección 11).
- `.claude/commands/auditar.md`: comando `/auditar <carpeta>` que corre el núcleo, manda las filas ambiguas al clasificador, pasa todo por el verificador y entrega el informe.

Fable orquesta y planifica; los subagentes económicos hacen el trabajo repetitivo; el verificador tiene la última palabra. Ya hay borradores de estos 4 archivos en `.claude/`: revísalos y mejóralos. El resultado del modo agéntico nunca puede contradecir la regla de oro.

### 7.3 Verificación en dos capas

1. `verificador.py` (código): relee cada fila citada y compara fecha y monto. Es obligatorio y corre siempre.
2. Subagente verificador (opcional, en Claude Code): segunda opinión, útil para el video.

## 8. Web de demostración

- Sitio estático en `web/` (HTML, CSS y JavaScript sin framework, o el mínimo necesario), desplegable en Vercel sin configuración especial. Agrega `web/vercel.json` solo si hace falta.
- Corre el MISMO paquete `detective/` en el navegador con Pyodide (versión fija, cargada desde su CDN oficial). Un script `scripts/construir_web.py` copia `detective/`, `plantillas/` y `data/demo/` (sin `_respuestas/`) a `web/` para que la web siempre use el código probado.
- Si `openpyxl` no carga en Pyodide, la web acepta solo CSV y lo explica en pantalla; la CLI sigue aceptando XLSX. Anota la decisión en la bitácora.
- Al abrir: muestra el informe de la demo ficticia ya calculado, con un aviso claro "Datos 100% ficticios".
- Botón "Usar mis archivos": arrastrar y soltar varios CSV o XLSX, detectar plantilla por archivo, mostrar qué rol asignó a cada uno (y permitir cambiarlo), correr la auditoría y mostrar el informe, con botón para descargar `informe.md`, `hallazgos.json` y `mensajes_cobro.md`.
- Privacidad: ningún `fetch` ni envío de datos del usuario. Solo se descarga Pyodide. Escríbelo visible en la página: "Tus archivos no salen de tu computador".
- Diseño simple, legible en celular, en español, con el título "Detective de Fugas Pyme" y la frase "La plata que se pierde no hace ruido: hay que contarla fila por fila."
- Prueba local: `python -m http.server -d web 8000` y abrir `http://localhost:8000`. Debe funcionar sin errores en la consola.
- Agrega una prueba automática que levante la web (por ejemplo con Playwright, si está disponible; si no, una prueba que valide que los archivos copiados existen y que el HTML no contiene llamadas de red a dominios distintos al CDN de Pyodide).

## 9. Pruebas

- `pytest` con pruebas de comportamiento: lectores (preámbulo, BOM, separadores, números chilenos), normalización de RUT y fechas, cada regla con su caso positivo y su señuelo, el verificador descartando una fila mal citada, y el contrato de `hallazgos.json`.
- Prueba de punta a punta: genera los datasets, corre el detector sobre `data/demo` y `data/demo_b`, y ejecuta `scripts/evaluar.py` en ambos. Debe aprobar.
- Prueba anti trampa: ningún archivo de `detective/`, `web/` ni `plantillas/` contiene la cadena `_respuestas` o `respuestas.json`.
- Prueba de idioma: los `.md` en español y los textos de la web no contienen el guion largo (carácter Unicode U+2014). En el código de la prueba escríbelo como `"\u2014"`, no literal, para que la prueba no se delate a sí misma.
- Prueba de privacidad de la web (sección 8).
- Todo corre con `python -m pytest -q` en menos de 60 segundos.

## 10. Fases y checkpoints

Cada fase cierra con: pruebas en verde, `PLAN.md` actualizado, entrada en `BITACORA.md` y commit local.

| Fase | Qué | Checkpoint (cómo sabes que terminó) |
|---|---|---|
| 0 | Plan | `PLAN.md` aprobado por Gustavo |
| 1 | Base: `requirements.txt`, estructura, lectores, normalización, plantillas | Lee los 9 archivos de demo A y los 8 de demo B, con pruebas de lectores en verde |
| 2 | Motor: emparejamiento y las 5 reglas, verificador | `python scripts/evaluar.py` sobre demo A: al menos 10 de 12 y 0 falsos |
| 3 | Generalidad | Demo B pasa igual, solo con plantillas (sin código especial para demo B) |
| 4 | Informe y mensajes | `informe.md` con 5 líneas de resumen, tabla ordenada, evidencia; `mensajes_cobro.md` con encabezado de borrador |
| 5 | Modo agéntico | `/auditar data/demo` funciona en Claude Code y llega al mismo resultado que la CLI |
| 6 | Web | `scripts/construir_web.py` + servidor local: la demo se ve, subir los CSV de demo B da el mismo informe que la CLI |
| 7 | Crítico | Sección 11 completa, problemas corregidos |
| 8 | Documentación y entrega | README completo, `ENTREGA/` actualizada con números reales, `BITACORA.md` resumida |
| 9 | Verificación final | Todos los criterios de la sección 12 marcados, con la salida de los comandos pegada en `PLAN.md` |

## 11. Fase del crítico

1. Lanza el subagente `critico-pyme` (contexto limpio, sin acceso a esta spec ni a `_respuestas/`). Dale solo: `salida/demo/informe.md`, `salida/demo/mensajes_cobro.md`, `README.md` y la web local.
2. Pídele que actúe como dueña de una pyme de servicios que no sabe de programación, y que entregue como máximo 5 problemas, ordenados por gravedad, cada uno con la evidencia (qué línea o pantalla) y una propuesta concreta.
3. Corrige cada problema o justifica por escrito por qué no.
4. Registra los 5 problemas y lo que hiciste en `BITACORA.md`, sección "Crítico".
5. Si Gustavo prefiere hacer el crítico en una sesión nueva, el prompt está en `PROMPTS.md` (P5) y deja su resultado en `CRITICO.md`; luego se aplica con P6.

## 12. Criterios de aceptación (todos obligatorios)

- [ ] `python scripts/generar_dataset.py --todas` regenera exactamente los mismos archivos (reproducible).
- [ ] Demo A: `python scripts/evaluar.py --dataset data/demo` encuentra **al menos 10 de 12** fugas con **0 falsos positivos**.
- [ ] Demo B: lo mismo con `--dataset data/demo_b`, sin código específico para demo B.
- [ ] Todos los hallazgos tienen evidencia verificada (archivo, fila, fecha, monto) y el verificador descarta una cita falsa en las pruebas.
- [ ] `python -m pytest -q` en verde.
- [ ] Ningún código de detección lee `_respuestas/` (prueba anti trampa en verde).
- [ ] `informe.md` cumple la sección 6.2 y `mensajes_cobro.md` la 6.3.
- [ ] La web corre en local, muestra la demo precargada, acepta archivos del usuario y no envía datos (prueba en verde).
- [ ] `README.md` completo (sección 13).
- [ ] `BITACORA.md` con todas las correcciones y la sección "Crítico".
- [ ] `ENTREGA/` actualizada con los números reales del resultado (reemplaza los marcadores `[[...]]` que dependen del resultado; deja los de link y video para Gustavo).
- [ ] Ningún archivo en español tiene el guion largo (U+2014). No hay secretos en el repo. No se hizo push ni despliegue.

## 13. Entregables finales

1. Código: `detective/`, `plantillas/`, `tests/`, `scripts/`, `web/`, `requirements.txt`.
2. `README.md` con: qué es (3 líneas), resultado en la demo (tabla con el puntaje), cómo usarlo en 3 comandos, cómo usar la web, cómo sacar tus archivos (sección 5.4), cómo crear una plantilla para tu banco, cómo funciona por dentro (diagrama simple en texto o Mermaid), cómo lo construí con Fable (resumen de la bitácora y link a `PROMPTS.md`), limitaciones honestas, privacidad, licencia MIT.
3. `salida/demo/` y `salida/demo_b/` generadas (se pueden subir al repo como ejemplo; no tienen datos reales).
4. `BITACORA.md` final con un resumen arriba: "Fable corrigió N cosas; las 3 más importantes fueron...".
5. `ENTREGA/post_skool.md`, `ENTREGA/post_x.md`, `ENTREGA/guion_video.md` actualizados.
6. `PLAN.md` con todo marcado y la salida de los comandos finales.
7. Mensaje final a Gustavo, corto: puntaje logrado, qué quedó listo y los comandos exactos que le tocan a él (push, Vercel, grabar video, publicar), en el orden de `PASO_A_PASO.md`.

## 14. Formato de `BITACORA.md`

Cada entrada:

```
## AAAA-MM-DD HH:MM · Fase N · título corto
- Qué pasó: (error, prueba fallida, decisión, descubrimiento)
- Por qué: (la causa real)
- Qué cambié: (archivos y en qué)
- Cómo lo verifiqué: (comando y resultado)
```

Registra todo lo que corregiste o decidiste, incluido lo que salió mal al principio. Esa honestidad es la parte "cómo lo hiciste" del post y es lo que más valora el jurado en replicabilidad.
