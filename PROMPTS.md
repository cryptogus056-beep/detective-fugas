# PROMPTS.md · Prompts para copiar y pegar en Claude Code

Úsalos en orden. Cada uno funciona solo, sin contexto previo. Copia el bloque completo (lo que está entre las líneas de tres comillas).

Antes de pegar cualquiera: abre Claude Code dentro de la carpeta `detective-fugas`, con el modelo Fable 5.2 y esfuerzo alto (ver `PASO_A_PASO.md`).

| N° | Cuándo | Para qué |
|---|---|---|
| P0 | Sábado, sesión nueva | Arrancar: leer todo y escribir `PLAN.md` |
| P1 | Después de leer el plan | Aprobar y ejecutar todo hasta terminar |
| P2 | Si se cortó (límite del plan Pro, cerraste la ventana, error) | Retomar donde quedó |
| P3 | Si se detuvo antes de tiempo o te pregunta "¿continúo?" | Empujar a terminar |
| P4 | Cuando quieras saber cómo va | Estado rápido sin tocar nada |
| P5 | Sesión NUEVA y limpia, cuando el detector y la web estén listos | El crítico (máximo 5 problemas) |
| P6 | En la sesión principal, después del crítico | Aplicar las correcciones del crítico |
| P7 | Martes | Verificación final completa |
| P8 | Martes | Pulir el README |
| P9 | Miércoles | Guion del video con los números reales |
| P10 | Miércoles o jueves | Borradores finales del post de Skool y X |
| P11 | Antes de subir a GitHub y Vercel | Revisión de seguridad previa a publicar |

---

## P0 · Arrancar

```
Hola Fable. Vas a construir el proyecto "Detective de Fugas Pyme" para un concurso.

1. Lee completos, en este orden: CLAUDE.md, SPEC_DETECTIVE_FUGAS.md, data/demo/LEEME.md, data/demo_b/LEEME.md, scripts/generar_dataset.py y scripts/evaluar.py. No abras nada dentro de data/*/_respuestas/.
2. Sigue la sección 0 de SPEC_DETECTIVE_FUGAS.md al pie de la letra.
3. Escribe PLAN.md en la raíz con las fases de la sección 10 convertidas en tareas concretas, los archivos que vas a crear, los riesgos y cómo vas a verificar cada fase.
4. Muéstrame un resumen de PLAN.md en 10 líneas como máximo y espera mi "Sí, aprobado el PLAN.md".

Yo programo a nivel básico: explícame en español simple, con "tú", y solo pregúntame lo que la sección 0.5 de la spec reserva para mí.
```

## P1 · Aprobar y ejecutar hasta terminar

```
Sí, aprobado el PLAN.md.

Ahora ejecuta todas las fases de PLAN.md hasta cumplir TODOS los criterios de aceptación de la sección 12 de SPEC_DETECTIVE_FUGAS.md, sin pedirme permiso entre fases.

Termina el trabajo. No te detengas hasta que esté completo y verificado. Si algo falla, investiga la causa, corrígela y sigue. No termines un turno con una lista de pendientes ni preguntando si continúas cuando puedes hacerlo tú. Solo detente por lo que la sección 0.5 reserva para mí.

Al cerrar cada fase: pruebas en verde, PLAN.md actualizado, entrada en BITACORA.md y commit local. Nunca hagas git push ni despliegues.
Antes de cada tarea larga dime en una línea qué vas a hacer.
```

## P2 · Retomar después de una interrupción

```
Retomamos el proyecto Detective de Fugas Pyme. La sesión anterior se cortó.

1. Lee CLAUDE.md, PLAN.md y las últimas 5 entradas de BITACORA.md. Si necesitas detalle, consulta SPEC_DETECTIVE_FUGAS.md.
2. Corre: python -m pytest -q y python scripts/evaluar.py --dataset data/demo (si ya existe el detector). Dime en 3 líneas en qué fase estamos y qué falta.
3. Continúa desde la primera tarea sin marcar en PLAN.md hasta cumplir todos los criterios de la sección 12. No rehagas lo que ya está hecho y verificado.

Termina el trabajo: no te detengas mientras puedas avanzar tú. Solo para por lo que la sección 0.5 de la spec reserva para mí. Nunca hagas git push ni despliegues.
```

## P3 · Si se detuvo antes de tiempo

```
Todavía no está terminado. Revisa la sección 12 de SPEC_DETECTIVE_FUGAS.md, marca qué criterios faltan y sigue trabajando hasta cumplirlos todos. No me preguntes si continúas: continúa. Solo detente por lo que la sección 0.5 reserva para mí, y si lo haces, hazme una sola pregunta con todas las opciones.
```

## P4 · Estado rápido (no cambia nada)

```
Sin modificar ningún archivo, dime en máximo 8 líneas: en qué fase de PLAN.md estamos, el resultado actual de python scripts/evaluar.py para data/demo y data/demo_b (encontradas y falsos positivos), si python -m pytest -q está en verde, qué criterios de la sección 12 faltan y cuánto trabajo estimas que queda.
```

## P5 · El crítico (sesión NUEVA y limpia)

Antes de pegarlo, cierra la sesión actual y abre una nueva (o escribe `/clear`), para que el crítico no conozca el contexto.

```
Eres Marcela, dueña de una pyme de servicios en Chile con 6 trabajadores. No sabes programar. Te pasaron una herramienta para revisar tus cuentas y quieres saber si sirve.

Reglas: NO leas SPEC_DETECTIVE_FUGAS.md, PLAN.md, BITACORA.md ni nada dentro de data/*/_respuestas/.

Lee solo: salida/demo/informe.md, salida/demo/mensajes_cobro.md y README.md. Si existe la carpeta web/, levanta la web con: python scripts/construir_web.py && python -m http.server -d web 8000, y revísala.

Entrega como máximo 5 problemas, del más grave al menos grave. Para cada uno: qué te confundió, asustó o no te sirvió; dónde está (archivo y línea, o pantalla); y el cambio concreto que lo arreglaría. Busca sobre todo montos o fechas que no se entienden, palabras técnicas sin explicar, pasos que no sabrías hacer, mensajes de cobro agresivos o poco claros, y cualquier cosa que te haga desconfiar del resultado.

Escribe tu respuesta también en el archivo CRITICO.md, sin modificar ningún otro archivo.
```

## P6 · Aplicar las correcciones del crítico

```
Lee CRITICO.md: son hasta 5 problemas que encontró una revisora sin contexto (una dueña de pyme que no programa).

Para cada problema: corrígelo o, si no corresponde, justifica por escrito por qué no. Después corre python -m pytest -q y python scripts/evaluar.py en data/demo y data/demo_b para confirmar que nada se rompió.

Registra cada problema y lo que hiciste en la sección "Crítico" de BITACORA.md, marca la fase 7 en PLAN.md y haz un commit local. Termina el trabajo sin preguntarme entre problema y problema. Nunca hagas git push.
```

## P7 · Verificación final completa

```
Haz la verificación final del proyecto, sin confiar en lo que dice PLAN.md: compruébalo de nuevo.

1. Borra la carpeta salida/ y regenera todo: python scripts/generar_dataset.py --todas, el detector sobre data/demo y data/demo_b, y python scripts/evaluar.py en ambos.
2. Corre python -m pytest -q.
3. Construye la web y pruébala en local (demo precargada y subida de los archivos de data/demo_b).
4. Busca el guion largo (carácter Unicode U+2014) en todos los .md y textos de la web, claves o tokens en el repo, y cualquier dato que no sea ficticio.
5. Revisa uno por uno los criterios de la sección 12 de SPEC_DETECTIVE_FUGAS.md.

Corrige lo que falle (y anótalo en BITACORA.md). Pega al final de PLAN.md la salida de los comandos y la lista de criterios marcada. Haz un commit local. No hagas git push ni despliegues.
```

## P8 · Pulir el README

```
Revisa README.md como si fueras alguien que llega desde el post del concurso y nunca vio el proyecto. Debe cumplir la sección 13 de SPEC_DETECTIVE_FUGAS.md.

Asegúrate de que: las primeras 3 líneas expliquen qué es y para quién; aparezca el puntaje real de la demo (copiado de la salida de scripts/evaluar.py); se pueda usar en 3 comandos; explique cómo usar la web sin instalar nada; tenga "Cómo sacar tus archivos" con lo no comprobado marcado [sin verificar]; explique cómo crear una plantilla para otro banco; resuma cómo se construyó con Fable (con link a PROMPTS.md y BITACORA.md); y diga con honestidad las limitaciones.

Español neutro con "tú", sin el guion largo (carácter Unicode U+2014), frases cortas. Haz un commit local. No hagas git push.
```

## P9 · Guion del video con los números reales

```
Actualiza ENTREGA/guion_video.md con los números y pantallas reales del proyecto terminado: puntaje de scripts/evaluar.py en data/demo y data/demo_b, la fuga más grande, el total en juego del informe y los nombres exactos de los botones de la web.

El video dura entre 2 y 3 minutos. Mantén la estructura de escenas con tiempos, qué se ve en pantalla y qué digo yo. El texto hablado en español neutro, con "tú", frases cortas, sin el guion largo (carácter Unicode U+2014). No inventes nada que el proyecto no haga.
```

## P10 · Borradores finales del post de Skool y X

```
Actualiza ENTREGA/post_skool.md y ENTREGA/post_x.md con los resultados reales del proyecto (puntajes de scripts/evaluar.py, total en juego, cantidad de correcciones registradas en BITACORA.md y las 3 más importantes).

Reglas del concurso: título con [FABLE] (usa exactamente "[FABLE] Detective de Fugas: encuentra la plata que tu pyme pierde sin darse cuenta"), y 4 partes: el proyecto, el resultado (link y video), cómo lo hiciste (prompts copiables de PROMPTS.md, proceso y correcciones) y la moraleja: "La plata que se pierde no hace ruido: hay que contarla fila por fila."

El post de X debe tener menos de 280 caracteres (cuenta cada link como 23) e incluir #FableImperial.

Deja los marcadores [[LINK_WEB]], [[LINK_VIDEO]], [[LINK_GITHUB]] y [[LINK_POST_X]] para que yo los complete. No publiques nada.
```

## P11 · Revisión de seguridad antes de publicar

```
Voy a subir este repo a GitHub como público y la carpeta web/ a Vercel. Antes de eso, sin hacer push ni desplegar:

1. Revisa con git status y git log que no haya archivos fuera de lugar.
2. Busca claves, tokens, correos o datos que no sean ficticios en todo el repo, incluido el historial (git log -p).
3. Confirma que mis_datos/ y .env están en .gitignore y que web/ no incluye data/*/_respuestas/.
4. Confirma que la web no envía datos a ningún servidor.

Dime en una lista corta qué encontraste y corrígelo con un commit local. Después dame, sin ejecutarlos, los comandos exactos para: crear el repo en GitHub y hacer push, y desplegar web/ en Vercel.
```
