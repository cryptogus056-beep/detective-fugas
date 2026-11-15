# Informe de fugas: Climatizacion Austral Ficticia SpA

Periodo revisado: 01/08/2026 al 31/10/2026 (3 meses). Fecha de corte: 31/10/2026.

## Resumen en 5 líneas

1. **En juego:** $3.817.410 en los 3 meses revisados (unos $1.272.471 al mes).
2. **Qué encontré:** 12 fugas: 3 ingresos sin boleta ni factura, 3 cotizaciones aceptadas sin facturar, 2 facturas impagas, 2 pagos de software de más y 2 diferencias de IVA.
3. **La más grande:** PRE-0519: Clinica Dental Demo Sonrisa SpA la aceptó el 03/09/2026 y nunca se facturó ($1.332.800, H01).
4. **Qué hacer primero esta semana:** Emite la factura y envía el mensaje de cobro M01. Después sigue con la tabla, de arriba hacia abajo.
5. **Si cobras lo pendiente:** recuperas $3.445.050 (3 cotizaciones sin facturar y 2 facturas impagas). Los mensajes ya están redactados en `mensajes_cobro.md`.

## Fugas encontradas, de mayor a menor impacto mensual

| N° | Tipo | Qué pasó | Monto | Impacto mensual | Evidencia | Acción |
|---|---|---|---|---|---|---|
| 1 | Trabajo aceptado que nunca se facturó | PRE-0519: Clinica Dental Demo Sonrisa SpA la aceptó el 03/09/2026 y nunca se facturó | $1.332.800 | $444.267 (promedio mensual) | `presupuestos.csv` fila 20, 03/09/2026, $1.120.000 | Emite la factura y envía el mensaje de cobro M01. |
| 2 | Factura que no te han pagado | Factura folio 3404 a Cafeteria Demo Grano Fino SpA: 72 días sin pago | $815.150 | $271.717 (promedio mensual) | `rcv_ventas.csv` fila 24, 20/08/2026, $815.150 | Llama al cliente y envía el mensaje de cobro M02. |
| 3 | Trabajo aceptado que nunca se facturó | PRE-0505: Colegio Demo Los Aromos la aceptó el 12/08/2026 y nunca se facturó | $595.000 | $198.333 (promedio mensual) | `presupuestos.csv` fila 6, 12/08/2026, $500.000 | Emite la factura y envía el mensaje de cobro M03. |
| 4 | Factura que no te han pagado | Factura folio 3415 a Bodega Ficticia Austral SpA: 46 días sin pago | $440.300 | $146.767 (promedio mensual) | `rcv_ventas.csv` fila 47, 15/09/2026, $440.300 | Llama al cliente y envía el mensaje de cobro M04. |
| 5 | Trabajo aceptado que nunca se facturó | PRE-0534: Martina Ficticia Fuentes la aceptó el 29/09/2026 y nunca se facturó | $261.800 | $87.267 (promedio mensual) | `presupuestos.csv` fila 35, 29/09/2026, $220.000 | Emite la factura y envía el mensaje de cobro M05. |
| 6 | IVA que salió de tu bolsillo | PRE-0524 de Restaurante Ficticio La Caleta Ltda: se facturó el neto como si fuera el total (folio 3413) | $870.000 | $55.100 (promedio mensual) | `rcv_ventas.csv` fila 44, 10/09/2026, $870.000 (y 2 filas más en el detalle) | Revisa con tu contador cómo corregir el documento y cobra la diferencia al cliente (nota interna N01). |
| 7 | Plata que entró sin boleta ni factura | Abono del 09/10/2026 sin boleta ni factura (TRANSF. DE 76.468.166-5 INMOBILIARIA FICTICIA...) | $374.850 | $19.950 (promedio mensual) | `movimientos_cuenta.csv` fila 68, 09/10/2026, $374.850 | Emite la boleta o factura que falta (nota interna N02). |
| 8 | IVA que salió de tu bolsillo | Documento folio 3422 a Oficina Contable Demo Cuentas Claras SpA: IVA mal calculado | $489.500 | $13.350 (promedio mensual) | `rcv_ventas.csv` fila 64, 06/10/2026, $489.500 | Revisa con tu contador si corresponde una nota de débito y cobra la diferencia (nota interna N03). |
| 9 | Software que pagas de más | Canva Pro: 2 cobros al mes con 1 licencia | $12.990 | $12.990 cada mes | `movimientos_cuenta.csv` fila 5, 03/08/2026, $12.990 (y 6 filas más en el detalle) | Entra a la cuenta de Canva Pro, revisa por qué hay más de un cobro y cancela el que sobra (nota interna N04). |
| 10 | Plata que entró sin boleta ni factura | Abono del 27/08/2026 sin boleta ni factura (TRANSF. DE 12.737.842-8 NICOLAS FICTICIO VARGAS) | $201.000 | $10.697 (promedio mensual) | `movimientos_cuenta.csv` fila 18, 27/08/2026, $201.000 | Emite la boleta o factura que falta (nota interna N05). |
| 11 | Software que pagas de más | Licencia de Google Workspace de Bruno Ficticio Vera, que ya no trabaja contigo | $8.600 | $8.600 cada mes | `movimientos_cuenta.csv` fila 2, 02/08/2026, $34.400 (y 4 filas más en el detalle) | Da de baja la licencia de bruno@climatizacionaustral-ficticia.cl en Google Workspace (nota interna N06). |
| 12 | Plata que entró sin boleta ni factura | Venta con tarjeta del 18/09/2026 sin boleta (Credito, operación 2958094) | $64.500 | $3.433 (promedio mensual) | `ventas_transbank.csv` fila 30, 18/09/2026, $64.500 | Emite la boleta que falta (nota interna N07). |

"Promedio mensual" quiere decir que la fuga pasó una vez y la repartí entre los meses del periodo. "Cada mes" quiere decir que se repite todos los meses hasta que la arregles.

## Detalle de cada fuga

### H01 · Cotización aceptada que nunca se facturó

- **Qué pasó:** PRE-0519 fue aceptada por Clinica Dental Demo Sonrisa SpA el 03/09/2026 por $1.332.800 (el archivo trae solo el neto, $1.120.000; le sumé el IVA). Pasaron 58 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto:** $1.332.800
- **Impacto en el periodo:** $1.332.800
- **Impacto mensual:** $444.267 (promedio mensual)
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M01.
- **Evidencia:**

  - `presupuestos.csv` fila 20, 03/09/2026, $1.120.000. PRE-0519 APROBADO Clinica Dental Demo Sonrisa SpA: Reparacion compresor

    ```text
    PRE-0519;2026-08-30;Clinica Dental Demo Sonrisa SpA;77.315.822-3;Reparacion compresor;1120000;APROBADO;2026-09-03
    ```

### H02 · Factura emitida que no te han pagado

- **Qué pasó:** La factura folio 3404 a Cafeteria Demo Grano Fino SpA, del 20/08/2026, por $815.150, no tiene pago en tu banco. Lleva 72 días al 31/10/2026 (42 sobre el plazo de 30 días).
- **Monto:** $815.150
- **Impacto en el periodo:** $815.150
- **Impacto mensual:** $271.717 (promedio mensual)
- **Qué hacer:** Llama al cliente y envía el mensaje de cobro M02.
- **Evidencia:**

  - `rcv_ventas.csv` fila 24, 20/08/2026, $815.150. Factura folio 3404 a Cafeteria Demo Grano Fino SpA

    ```text
    23;33;Del Giro;77.222.633-0;Cafeteria Demo Grano Fino SpA;3404;20/08/2026;20/08/2026 12:00:00;;0;685000;130150;815150
    ```

### H03 · Cotización aceptada que nunca se facturó

- **Qué pasó:** PRE-0505 fue aceptada por Colegio Demo Los Aromos el 12/08/2026 por $595.000 (el archivo trae solo el neto, $500.000; le sumé el IVA). Pasaron 80 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto:** $595.000
- **Impacto en el periodo:** $595.000
- **Impacto mensual:** $198.333 (promedio mensual)
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M03.
- **Evidencia:**

  - `presupuestos.csv` fila 6, 12/08/2026, $500.000. PRE-0505 APROBADO Colegio Demo Los Aromos: Instalacion equipo 24.000 BTU

    ```text
    PRE-0505;2026-08-08;Colegio Demo Los Aromos;77.322.518-4;Instalacion equipo 24.000 BTU;500000;APROBADO;2026-08-12
    ```

### H04 · Factura emitida que no te han pagado

- **Qué pasó:** La factura folio 3415 a Bodega Ficticia Austral SpA, del 15/09/2026, por $440.300, no tiene pago en tu banco. Lleva 46 días al 31/10/2026 (16 sobre el plazo de 30 días).
- **Monto:** $440.300
- **Impacto en el periodo:** $440.300
- **Impacto mensual:** $146.767 (promedio mensual)
- **Qué hacer:** Llama al cliente y envía el mensaje de cobro M04.
- **Evidencia:**

  - `rcv_ventas.csv` fila 47, 15/09/2026, $440.300. Factura folio 3415 a Bodega Ficticia Austral SpA

    ```text
    46;33;Del Giro;77.155.629-9;Bodega Ficticia Austral SpA;3415;15/09/2026;15/09/2026 12:00:00;;0;370000;70300;440300
    ```

### H05 · Cotización aceptada que nunca se facturó

- **Qué pasó:** PRE-0534 fue aceptada por Martina Ficticia Fuentes el 29/09/2026 por $261.800 (el archivo trae solo el neto, $220.000; le sumé el IVA). Pasaron 32 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto:** $261.800
- **Impacto en el periodo:** $261.800
- **Impacto mensual:** $87.267 (promedio mensual)
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M05.
- **Evidencia:**

  - `presupuestos.csv` fila 35, 29/09/2026, $220.000. PRE-0534 APROBADO Martina Ficticia Fuentes: Diagnostico y reparacion tarjeta electronica

    ```text
    PRE-0534;2026-09-25;Martina Ficticia Fuentes;17.935.417-9;Diagnostico y reparacion tarjeta electronica;220000;APROBADO;2026-09-29
    ```

### H06 · Cobraste el neto como si fuera el total

- **Qué pasó:** PRE-0524 cotizó a Restaurante Ficticio La Caleta Ltda $870.000 más IVA (total $1.035.300), pero el documento folio 3413 del 10/09/2026 se emitió por $870.000 en total. El IVA ($165.300) salió de tu bolsillo.
- **Monto:** $870.000
- **Impacto en el periodo:** $165.300
- **Impacto mensual:** $55.100 (promedio mensual)
- **Qué hacer:** Revisa con tu contador cómo corregir el documento y cobra la diferencia al cliente (nota interna N01).
- **Evidencia:**

  - `rcv_ventas.csv` fila 44, 10/09/2026, $870.000. Documento folio 3413: neto $731.092, IVA $138.908, total $870.000

    ```text
    43;33;Del Giro;76.123.963-5;Restaurante Ficticio La Caleta Ltda;3413;10/09/2026;10/09/2026 12:00:00;;0;731092;138908;870000
    ```

  - `presupuestos.csv` fila 25, 04/09/2026, $870.000. PRE-0524 APROBADO: neto $870.000 más IVA

    ```text
    PRE-0524;2026-09-02;Restaurante Ficticio La Caleta Ltda;76.123.963-5;Instalacion equipo 24.000 BTU;870000;APROBADO;2026-09-04
    ```

  - `movimientos_cuenta.csv` fila 51, 22/09/2026, $870.000. Pago recibido: TRANSF. DE 76.123.963-5 RESTAURANTE FICTICIO LA CALETA LTDA

    ```text
    2026-09-22,TRANSF. DE 76.123.963-5 RESTAURANTE FICTICIO LA CALETA LTDA,OFICINA CENTRAL,870000,13264556
    ```

### H07 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 09/10/2026 entraron $374.850 a tu cuenta ("TRANSF. DE 76.468.166-5 INMOBILIARIA FICTICIA ALTOS DEL SUR") y no encontré boleta ni factura por ese monto. IVA en riesgo: $59.850. Riesgo de multa del SII [sin verificar el monto de la multa].
- **Monto:** $374.850
- **Impacto en el periodo:** $59.850
- **Impacto mensual:** $19.950 (promedio mensual)
- **Qué hacer:** Emite la boleta o factura que falta (nota interna N02).
- **Evidencia:**

  - `movimientos_cuenta.csv` fila 68, 09/10/2026, $374.850. TRANSF. DE 76.468.166-5 INMOBILIARIA FICTICIA ALTOS DEL SUR

    ```text
    2026-10-09,TRANSF. DE 76.468.166-5 INMOBILIARIA FICTICIA ALTOS DEL SUR ,OFICINA CENTRAL,374850,11647159
    ```

### H08 · Documento con el IVA mal calculado

- **Qué pasó:** El documento folio 3422 a Oficina Contable Demo Cuentas Claras SpA, del 06/10/2026, tiene neto $445.000 con IVA $44.500 (10%) en vez de $84.550 (19%). Cobraste $40.050 de menos y esa parte del IVA la terminas poniendo tú.
- **Monto:** $489.500
- **Impacto en el periodo:** $40.050
- **Impacto mensual:** $13.350 (promedio mensual)
- **Qué hacer:** Revisa con tu contador si corresponde una nota de débito y cobra la diferencia (nota interna N03).
- **Evidencia:**

  - `rcv_ventas.csv` fila 64, 06/10/2026, $489.500. Documento folio 3422: neto $445.000, IVA $44.500, total $489.500

    ```text
    63;33;Del Giro;77.185.842-2;Oficina Contable Demo Cuentas Claras SpA;3422;06/10/2026;06/10/2026 12:00:00;;0;445000;44500;489500
    ```

### H09 · Canva Pro se cobra dos veces al mes

- **Qué pasó:** Canva Pro se cobra dos veces al mes por $12.990 (los días 3 y 17) y hay una sola licencia registrada. Pasó en 3 meses del periodo. Pagas $12.990 de más cada mes.
- **Monto:** $12.990
- **Impacto en el periodo:** $38.970
- **Impacto mensual:** $12.990 cada mes
- **Qué hacer:** Entra a la cuenta de Canva Pro, revisa por qué hay más de un cobro y cancela el que sobra (nota interna N04).
- **Evidencia:**

  - `movimientos_cuenta.csv` fila 5, 03/08/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-08-03,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,3897650
    ```

  - `movimientos_cuenta.csv` fila 13, 17/08/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-08-17,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,4001388
    ```

  - `movimientos_cuenta.csv` fila 28, 03/09/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-09-03,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,6471718
    ```

  - `movimientos_cuenta.csv` fila 44, 17/09/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-09-17,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,10038958
    ```

  - `movimientos_cuenta.csv` fila 62, 03/10/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-10-03,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,11422858
    ```

  - `movimientos_cuenta.csv` fila 78, 17/10/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    2026-10-17,COMPRA TARJETA CANVA* PRO,OFICINA CENTRAL,-12990,15295534
    ```

  - `licencias.csv` fila 6, $12.990. Licencia Canva Pro de camila@climatizacionaustral-ficticia.cl (Pro individual)

    ```text
    Canva Pro,camila@climatizacionaustral-ficticia.cl,Pro individual,12990,Activa
    ```

### H10 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 27/08/2026 entraron $201.000 a tu cuenta ("TRANSF. DE 12.737.842-8 NICOLAS FICTICIO VARGAS") y no encontré boleta ni factura por ese monto. IVA en riesgo: $32.092. Riesgo de multa del SII [sin verificar el monto de la multa]. Ojo: llegó al comienzo del periodo, así que podría ser el pago de un documento emitido antes de lo que cubren tus archivos.
- **Monto:** $201.000
- **Impacto en el periodo:** $32.092
- **Impacto mensual:** $10.697 (promedio mensual)
- **Qué hacer:** Emite la boleta o factura que falta (nota interna N05).
- **Confianza:** media: revísalo antes de actuar.
- **Evidencia:**

  - `movimientos_cuenta.csv` fila 18, 27/08/2026, $201.000. TRANSF. DE 12.737.842-8 NICOLAS FICTICIO VARGAS

    ```text
    2026-08-27,TRANSF. DE 12.737.842-8 NICOLAS FICTICIO VARGAS,OFICINA CENTRAL,201000,4257798
    ```

### H11 · Pagas la licencia de Google Workspace de alguien que ya se fue

- **Qué pasó:** La licencia de Google Workspace de bruno@climatizacionaustral-ficticia.cl sigue activa y cuesta $8.600 al mes, pero Bruno Ficticio Vera dejó la empresa el 31/07/2026. En el periodo la pagaste 3 meses sin que nadie la use. El cobro de $34.400 que ves en el banco es por todas las licencias de Google Workspace; la de esta persona es $8.600 de ese total.
- **Monto:** $8.600
- **Impacto en el periodo:** $25.800
- **Impacto mensual:** $8.600 cada mes
- **Qué hacer:** Da de baja la licencia de bruno@climatizacionaustral-ficticia.cl en Google Workspace (nota interna N06).
- **Evidencia:**

  - `movimientos_cuenta.csv` fila 2, 02/08/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    2026-08-02,COMPRA TARJETA GOOGLE*WORKSPACE,OFICINA CENTRAL,-34400,3765600
    ```

  - `movimientos_cuenta.csv` fila 26, 02/09/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    2026-09-02,COMPRA TARJETA GOOGLE*WORKSPACE,OFICINA CENTRAL,-34400,5687408
    ```

  - `movimientos_cuenta.csv` fila 59, 02/10/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    2026-10-02,COMPRA TARJETA GOOGLE*WORKSPACE,OFICINA CENTRAL,-34400,10281548
    ```

  - `licencias.csv` fila 5, $8.600. Licencia Google Workspace de bruno@climatizacionaustral-ficticia.cl, estado activa

    ```text
    Google Workspace,bruno@climatizacionaustral-ficticia.cl,Business Starter,8600,Activa
    ```

  - `equipo.csv` fila 5, 31/07/2026. Bruno Ficticio Vera, inactivo, salida 31/07/2026

    ```text
    Bruno Ficticio Vera,bruno@climatizacionaustral-ficticia.cl,Tecnico,Inactivo,2022-02-01,2026-07-31
    ```

### H12 · Venta con tarjeta sin boleta

- **Qué pasó:** El 18/09/2026 se aprobó una venta con tarjeta por $64.500 (Credito, operación 2958094) y no encontré su boleta de ese día ni del día siguiente. IVA en riesgo: $10.298. Riesgo de multa del SII [sin verificar el monto de la multa].
- **Monto:** $64.500
- **Impacto en el periodo:** $10.298
- **Impacto mensual:** $3.433 (promedio mensual)
- **Qué hacer:** Emite la boleta que falta (nota interna N07).
- **Evidencia:**

  - `ventas_transbank.csv` fila 30, 18/09/2026, $64.500. Credito, operación 2958094

    ```text
    18-09-2026;10:10;2958094;Credito;64.500;2.251;62.249;Aprobada
    ```

## Cómo verificar este informe

1. Elige cualquier hallazgo y mira su evidencia: dice el archivo, la fila, la fecha y el monto.
2. Abre ese archivo en Excel o en cualquier editor y ve a esa fila. La fila 1 es la primera línea del archivo, así que los títulos y encabezados también cuentan: es el mismo número que muestra Excel a la izquierda.
3. Compara la fecha y el monto de la fila con los del informe. Deben ser iguales.
4. En el detalle de cada hallazgo está copiada la fila original, para que la reconozcas sin buscar.
5. El detector hizo esta misma comprobación antes de escribir el informe: lo que no calzó no aparece aquí.

Archivos que leí:

- `equipo.csv`: personas del equipo, 5 filas leídas.
- `licencias.csv`: licencias de software por usuario, 7 filas leídas.
- `movimientos_cuenta.csv`: cartola o movimientos del banco, 85 filas leídas.
- `presupuestos.csv`: cotizaciones o presupuestos, 44 filas leídas.
- `rcv_compras.csv`: registro de compras del sii, 12 filas leídas.
- `rcv_ventas.csv`: registro de ventas del sii, 78 filas leídas.
- `ventas_transbank.csv`: ventas con tarjeta o link de pago, 48 filas leídas.

## Lo que no pude revisar

Revisé todos los tipos de fuga: no faltó ningún archivo.

Ten en cuenta:

- Dejé fuera 15 abonos que no son ventas (aportes de socios, devoluciones, liquidaciones de tarjetas), según tu configuración.

---

Este informe no reemplaza a tu contador. Montos en CLP.
