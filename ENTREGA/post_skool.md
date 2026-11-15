# Borrador del post para Skool (Imperio Agéntico · Built with FABLE)

> BORRADOR. No publicado. Completa los marcadores `[[...]]` antes de publicar. Fable actualiza los números con el prompt P10.

---

**Título:**

[FABLE] Detective de Fugas: encuentra la plata que tu pyme pierde sin darse cuenta

---

## 1. El proyecto

Las pymes pierden plata que nadie ve: una cotización aceptada que nadie facturó, una transferencia que entró sin boleta, un cliente que no pagó hace dos meses, la licencia de alguien que ya no trabaja contigo, un IVA mal calculado.

Construí con **Claude Fable 5.2** el **Detective de Fugas Pyme**: le pasas los archivos que cualquier pyme ya puede descargar (cartola del banco, ventas de Mercado Pago o Transbank, Registro de Compras y Ventas del SII y tu planilla de cotizaciones) y te entrega un informe con cada fuga, cuánto te cuesta al mes y **la fila exacta del archivo que lo prueba**. Si no hay fila que lo pruebe, no aparece. Así de simple.

- Funciona en el navegador: tus archivos no salen de tu computador.
- No necesita claves de API ni pagar nada.
- Sirve para cualquier banco: si tu cartola tiene otras columnas, se agrega una plantilla.
- Te deja borradores de mensajes de cobro (no envía nada solo).

## 2. El resultado

- 🔗 Pruébalo: [[LINK_WEB]]
- 🎥 Video de 2 minutos: [[LINK_VIDEO]]
- 💻 Código abierto: [[LINK_GITHUB]]

**La prueba:** armé una pyme ficticia (una empresa de climatización con 3 meses de movimientos) y escondí 12 fugas de 5 tipos, más varias trampas que parecen fuga pero no lo son. Un script aparte compara el resultado con la llave de respuestas.

| Prueba | Fugas encontradas | Inventadas (falsos positivos) |
|---|---|---|
| Demo A (banco con Cargos y Abonos, Mercado Pago, XLSX) | [[X]] de 12 | [[0]] |
| Demo B (otro banco, monto con signo, Transbank, otros encabezados) | [[X]] de 12 | [[0]] |

En la demo, el total en juego fue **$[[TOTAL_CLP]]** en 3 meses. La fuga más grande: [[FUGA_MAS_GRANDE]].

Todos los datos son 100% ficticios.

## 3. Cómo lo hice

**Proceso:**

1. Escribí una spec completa (`SPEC_DETECTIVE_FUGAS.md`) con la regla de oro: "cada hallazgo cita archivo, fila, fecha y monto, o se descarta".
2. Generé el dataset ficticio con un script con semilla fija, así cualquiera obtiene exactamente los mismos archivos.
3. Le pedí a Fable 5.2 (esfuerzo alto) que leyera todo, escribiera un `PLAN.md` y, después de aprobarlo, construyera todo hasta terminar.
4. Fable orquestó: el núcleo es código Python determinista (por eso corre sin claves); subagentes económicos clasifican filas raras; un verificador vuelve a abrir cada archivo y confirma la fila antes de aceptar un hallazgo.
5. Al final, un crítico con contexto limpio revisó el informe como si fuera una dueña de pyme que no programa, encontró [[N_CRITICO]] problemas y Fable los corrigió.

**Correcciones (de la bitácora):** Fable registró [[N_CORRECCIONES]] correcciones. Las 3 más importantes:

1. [[CORRECCION_1]]
2. [[CORRECCION_2]]
3. [[CORRECCION_3]]

**Prompts para copiar:** están todos en `PROMPTS.md` del repo. Los dos que hicieron el 80% del trabajo:

```
[[PEGAR P0 DE PROMPTS.md]]
```

```
[[PEGAR P1 DE PROMPTS.md]]
```

**Para usarlo con tus datos:** abre [[LINK_WEB]], aprieta "Usar mis archivos" y arrastra tus CSV. Si tu banco no calza, el README explica cómo crear la plantilla en 2 minutos.

## 4. La moraleja

**La plata que se pierde no hace ruido: hay que contarla fila por fila.**

Y lo que aprendí con Fable: no le pidas que "encuentre problemas", pídele que **pruebe** cada problema. Cuando la regla es "sin evidencia no existe", el agente deja de adivinar y empieza a contar.

---

También en X: [[LINK_POST_X]] #FableImperial
