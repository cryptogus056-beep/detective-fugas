# Informe de fugas: Climatizacion Austral Ficticia SpA

Periodo revisado: 01/08/2026 al 31/10/2026 (3 meses). Último día que cubren tus archivos (fecha de corte): 31/10/2026.

## Resumen en 5 líneas

1. **En juego:** $3.738.472 en los 3 meses revisados: $3.373.650 que te deben o no has facturado y $364.822 entre IVA en riesgo o mal cobrado y software pagado de más. Casi todo pasó una sola vez; lo único que se repite cada mes son $21.590 de software.
2. **Qué encontré:** 12 fugas: 3 ingresos sin boleta ni factura, 3 cotizaciones aceptadas sin facturar, 2 facturas impagas, 2 pagos de software de más y 2 diferencias de IVA. De ellas, 1 es de seguridad media: confírmala antes de actuar.
3. **La más grande:** COT-0118: Restaurante Ficticio La Caleta Ltda la aceptó el 03/09/2026 y nunca se facturó ($1.499.400, H01).
4. **Qué hacer primero esta semana:** Emite la factura y envía el mensaje de cobro M01. Después sigue con la tabla, de arriba hacia abajo.
5. **Si cobras lo pendiente:** recuperas $3.373.650 (3 cotizaciones sin facturar y 2 facturas impagas). Los mensajes ya están redactados en `mensajes_cobro.md`.

## Fugas encontradas, de mayor a menor impacto mensual

| N° | Tipo | Qué pasó | Monto del documento o movimiento | Plata en juego | Impacto mensual | Qué tan seguro | Evidencia | Acción |
|---|---|---|---|---|---|---|---|---|
| 1 | Trabajo aceptado que nunca se facturó | COT-0118: Restaurante Ficticio La Caleta Ltda la aceptó el 03/09/2026 y nunca se facturó | $1.499.400 | $1.499.400 | $499.800 (promedio mensual) | Alta | `cotizaciones.xlsx` fila 20, 03/09/2026, $1.499.400 | Emite la factura y envía el mensaje de cobro M01. |
| 2 | Factura que no te han pagado | Factura folio 1203 a Minimarket Ficticio Las Lomas SpA: 72 días sin pago | $791.350 | $791.350 | $263.783 (promedio mensual) | Alta | `rcv_ventas.csv` fila 17, 20/08/2026, $791.350 | Llama al cliente y envía el mensaje de cobro M02. |
| 3 | Trabajo aceptado que nunca se facturó | COT-0108: Oficina Contable Demo Cuentas Claras SpA la aceptó el 12/08/2026 y nunca se facturó | $476.000 | $476.000 | $158.667 (promedio mensual) | Alta | `cotizaciones.xlsx` fila 10, 12/08/2026, $476.000 | Emite la factura y envía el mensaje de cobro M03. |
| 4 | Factura que no te han pagado | Factura folio 1216 a Gimnasio Demo Fuerza Sur SpA: 46 días sin pago | $386.750 | $386.750 | $128.917 (promedio mensual) | Alta | `rcv_ventas.csv` fila 40, 15/09/2026, $386.750 | Llama al cliente y envía el mensaje de cobro M04. |
| 5 | Trabajo aceptado que nunca se facturó | COT-0134: Tamara Ficticia Morales la aceptó el 29/09/2026 y nunca se facturó | $220.150 | $220.150 | $73.383 (promedio mensual) | Alta | `cotizaciones.xlsx` fila 36, 29/09/2026, $220.150 | Emite la factura y envía el mensaje de cobro M05. |
| 6 | IVA que salió de tu bolsillo | COT-0121 de Colegio Demo Los Aromos: se facturó el neto como si fuera el total (folio 1212) | $835.000 | $158.650 | $52.883 (promedio mensual) | Alta | `rcv_ventas.csv` fila 33, 10/09/2026, $835.000 (y 2 filas más en el detalle) | Revisa con tu contador cómo corregir el documento y cobra la diferencia al cliente (nota interna N01). |
| 7 | Plata que entró sin boleta ni factura | Abono del 09/10/2026 sin boleta ni factura (TRANSF. DE 77.436.922-8 VETERINARIA FICTICIA...) | $398.650 | $63.650 | $21.217 (promedio mensual) | Alta | `cartola_banco.csv` fila 74, 09/10/2026, $398.650 | Confirma que fue una venta y que no tiene documento; si es así, emite la boleta o factura (nota interna N02). |
| 8 | IVA que salió de tu bolsillo | Documento folio 1222 a Inmobiliaria Ficticia Altos del Sur SpA: IVA mal calculado | $500.500 | $40.950 | $13.650 (promedio mensual) | Alta | `rcv_ventas.csv` fila 57, 06/10/2026, $500.500 | Revisa con tu contador si corresponde una nota de débito y cobra la diferencia (nota interna N03). |
| 9 | Software que pagas de más | Canva Pro: 2 cobros al mes con 1 licencia | $12.990 | $38.970 | $12.990 cada mes | Alta | `cartola_banco.csv` fila 8, 03/08/2026, $12.990 (y 6 filas más en el detalle) | Entra a la cuenta de Canva Pro, revisa por qué hay más de un cobro y cancela el que sobra (nota interna N04). |
| 10 | Software que pagas de más | Licencia de Google Workspace de Bruno Ficticio Vera, que ya no trabaja contigo | $8.600 | $25.800 | $8.600 cada mes | Alta | `cartola_banco.csv` fila 7, 02/08/2026, $34.400 (y 4 filas más en el detalle) | Da de baja la licencia de bruno@climatizacionaustral-ficticia.cl en Google Workspace (nota interna N05). |
| 11 | Plata que entró sin boleta ni factura | Abono del 27/08/2026 sin boleta ni factura (TRANSF. DE 23.564.221-2 BENJAMIN FICTICIO SILVA) | $157.000 | $25.067 | $8.356 (promedio mensual) | Media: confirma antes | `cartola_banco.csv` fila 23, 27/08/2026, $157.000 | Confirma que fue una venta y que no tiene documento; si es así, emite la boleta o factura (nota interna N06). |
| 12 | Plata que entró sin boleta ni factura | Venta con tarjeta del 18/09/2026 sin boleta (Mantencion preventiva domicilio, operación 70...) | $73.500 | $11.735 | $3.912 (promedio mensual) | Alta | `ventas_mercadopago.csv` fila 25, 18/09/2026, $73.500 | Confirma que la boleta no existe con otra fecha u otro monto; si falta, emítela (nota interna N07). |

"Monto del documento o movimiento" es el total de la factura, cotización, cobro o abono. "Plata en juego" es la parte que pierdes, te deben o arriesgas: a veces es todo el monto y a veces solo el IVA. "Promedio mensual" quiere decir que la fuga pasó una vez y la repartí entre los meses del periodo para poder ordenar la tabla; "cada mes" quiere decir que se repite hasta que la arregles.

Palabras que uso: **neto** es el precio sin IVA; **folio** es el número de la factura o boleta; **fecha de corte** es el último día que cubren tus archivos; una **nota de crédito o de débito** es un documento que corrige una factura ya emitida (te la emite tu contador o tu sistema de facturación).

## Detalle de cada fuga

### H01 · Cotización aceptada que nunca se facturó

- **Qué pasó:** COT-0118 fue aceptada por Restaurante Ficticio La Caleta Ltda el 03/09/2026 por $1.499.400 (neto $1.260.000 más IVA). Pasaron 58 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto del documento o movimiento:** $1.499.400
- **Plata en juego:** $1.499.400
- **Impacto mensual:** $499.800 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M01.
- **Evidencia:**

  - `cotizaciones.xlsx` fila 20, 03/09/2026, $1.499.400. COT-0118 Aceptada Restaurante Ficticio La Caleta Ltda: Reparacion compresor

    ```text
    COT-0118 | 30/08/2026 | Restaurante Ficticio La Caleta Ltda | 77.424.781-5 | Reparacion compresor | 1260000 | 239400 | 1499400 | Aceptada | 03/09/2026
    ```

### H02 · Factura emitida que no te han pagado

- **Qué pasó:** La factura folio 1203 a Minimarket Ficticio Las Lomas SpA, del 20/08/2026, por $791.350, no tiene pago en tu banco. Lleva 72 días al 31/10/2026 (42 sobre el plazo de 30 días).
- **Monto del documento o movimiento:** $791.350
- **Plata en juego:** $791.350
- **Impacto mensual:** $263.783 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Llama al cliente y envía el mensaje de cobro M02.
- **Evidencia:**

  - `rcv_ventas.csv` fila 17, 20/08/2026, $791.350. Factura folio 1203 a Minimarket Ficticio Las Lomas SpA

    ```text
    16;33;Del Giro;76.658.994-4;Minimarket Ficticio Las Lomas SpA;1203;20/08/2026;20/08/2026 12:00:00;;0;665000;126350;791350
    ```

### H03 · Cotización aceptada que nunca se facturó

- **Qué pasó:** COT-0108 fue aceptada por Oficina Contable Demo Cuentas Claras SpA el 12/08/2026 por $476.000 (neto $400.000 más IVA). Pasaron 80 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto del documento o movimiento:** $476.000
- **Plata en juego:** $476.000
- **Impacto mensual:** $158.667 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M03.
- **Evidencia:**

  - `cotizaciones.xlsx` fila 10, 12/08/2026, $476.000. COT-0108 Aceptada Oficina Contable Demo Cuentas Claras SpA: Instalacion equipo 24.000 BTU

    ```text
    COT-0108 | 08/08/2026 | Oficina Contable Demo Cuentas Claras SpA | 77.028.205-5 | Instalacion equipo 24.000 BTU | 400000 | 76000 | 476000 | Aceptada | 12/08/2026
    ```

### H04 · Factura emitida que no te han pagado

- **Qué pasó:** La factura folio 1216 a Gimnasio Demo Fuerza Sur SpA, del 15/09/2026, por $386.750, no tiene pago en tu banco. Lleva 46 días al 31/10/2026 (16 sobre el plazo de 30 días).
- **Monto del documento o movimiento:** $386.750
- **Plata en juego:** $386.750
- **Impacto mensual:** $128.917 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Llama al cliente y envía el mensaje de cobro M04.
- **Evidencia:**

  - `rcv_ventas.csv` fila 40, 15/09/2026, $386.750. Factura folio 1216 a Gimnasio Demo Fuerza Sur SpA

    ```text
    39;33;Del Giro;76.602.386-K;Gimnasio Demo Fuerza Sur SpA;1216;15/09/2026;15/09/2026 12:00:00;;0;325000;61750;386750
    ```

### H05 · Cotización aceptada que nunca se facturó

- **Qué pasó:** COT-0134 fue aceptada por Tamara Ficticia Morales el 29/09/2026 por $220.150 (neto $185.000 más IVA). Pasaron 32 días y no encontré factura, boleta ni pago por ese trabajo.
- **Monto del documento o movimiento:** $220.150
- **Plata en juego:** $220.150
- **Impacto mensual:** $73.383 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Emite la factura y envía el mensaje de cobro M05.
- **Evidencia:**

  - `cotizaciones.xlsx` fila 36, 29/09/2026, $220.150. COT-0134 Aceptada Tamara Ficticia Morales: Contrato mantencion trimestral

    ```text
    COT-0134 | 25/09/2026 | Tamara Ficticia Morales | 21.661.927-7 | Contrato mantencion trimestral | 185000 | 35150 | 220150 | Aceptada | 29/09/2026
    ```

### H06 · Cobraste el neto como si fuera el total

- **Qué pasó:** COT-0121 cotizó a Colegio Demo Los Aromos $835.000 más IVA (total $993.650), pero el documento folio 1212 del 10/09/2026 se emitió por $835.000 en total. El IVA ($158.650) salió de tu bolsillo.
- **Monto del documento o movimiento:** $835.000
- **Plata en juego:** $158.650
- **Impacto mensual:** $52.883 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Revisa con tu contador cómo corregir el documento y cobra la diferencia al cliente (nota interna N01).
- **Evidencia:**

  - `rcv_ventas.csv` fila 33, 10/09/2026, $835.000. Documento folio 1212: neto $701.681, IVA $133.319, total $835.000

    ```text
    32;33;Del Giro;76.205.629-1;Colegio Demo Los Aromos;1212;10/09/2026;10/09/2026 12:00:00;;0;701681;133319;835000
    ```

  - `cotizaciones.xlsx` fila 23, 04/09/2026, $835.000. COT-0121 Aceptada: neto $835.000 más IVA

    ```text
    COT-0121 | 02/09/2026 | Colegio Demo Los Aromos | 76.205.629-1 | Instalacion equipo 24.000 BTU | 835000 | 158650 | 993650 | Aceptada | 04/09/2026
    ```

  - `cartola_banco.csv` fila 54, 22/09/2026, $835.000. Pago recibido: TRANSF. DE 76.205.629-1 COLEGIO DEMO LOS AROMOS

    ```text
    22/09/2026;TRANSF. DE 76.205.629-1 COLEGIO DEMO LOS AROMOS;372193;;835.000;8.749.848
    ```

### H07 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 09/10/2026 entraron $398.650 a tu cuenta ("TRANSF. DE 77.436.922-8 VETERINARIA FICTICIA PATITAS SPA") y no encontré boleta ni factura por ese monto. IVA en riesgo (el IVA que habría que declarar si esta plata fue una venta): $63.650. Riesgo de multa del SII [sin verificar el monto de la multa]: no sé de cuánto sería, pregúntale a tu contador.
- **Monto del documento o movimiento:** $398.650
- **Plata en juego:** $63.650
- **Impacto mensual:** $21.217 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Confirma que fue una venta y que no tiene documento; si es así, emite la boleta o factura (nota interna N02).
- **Evidencia:**

  - `cartola_banco.csv` fila 74, 09/10/2026, $398.650. TRANSF. DE 77.436.922-8 VETERINARIA FICTICIA PATITAS SPA

    ```text
    09/10/2026;TRANSF. DE 77.436.922-8 VETERINARIA FICTICIA PATITAS SPA;530573;;398.650;10.766.434
    ```

### H08 · Documento con el IVA mal calculado

- **Qué pasó:** El documento folio 1222 a Inmobiliaria Ficticia Altos del Sur SpA, del 06/10/2026, tiene neto $455.000 con IVA $45.500 (10%) en vez de $86.450 (19%). Cobraste $40.950 de menos y esa parte del IVA la terminas poniendo tú.
- **Monto del documento o movimiento:** $500.500
- **Plata en juego:** $40.950
- **Impacto mensual:** $13.650 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Revisa con tu contador si corresponde una nota de débito y cobra la diferencia (nota interna N03).
- **Evidencia:**

  - `rcv_ventas.csv` fila 57, 06/10/2026, $500.500. Documento folio 1222: neto $455.000, IVA $45.500, total $500.500

    ```text
    56;33;Del Giro;76.024.093-1;Inmobiliaria Ficticia Altos del Sur SpA;1222;06/10/2026;06/10/2026 12:00:00;;0;455000;45500;500500
    ```

### H09 · Canva Pro se cobra dos veces al mes

- **Qué pasó:** Canva Pro se cobra dos veces al mes por $12.990 (los días 3 y 17) y hay una sola licencia registrada. Pasó en 3 meses del periodo. Pagas $12.990 de más cada mes.
- **Monto del documento o movimiento:** $12.990
- **Plata en juego:** $38.970
- **Impacto mensual:** $12.990 cada mes
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Entra a la cuenta de Canva Pro, revisa por qué hay más de un cobro y cancela el que sobra (nota interna N04).
- **Evidencia:**

  - `cartola_banco.csv` fila 8, 03/08/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    03/08/2026;COMPRA TARJETA CANVA* PRO;007919;12.990;;3.752.610
    ```

  - `cartola_banco.csv` fila 18, 17/08/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    17/08/2026;COMPRA TARJETA CANVA* PRO;087109;12.990;;5.559.596
    ```

  - `cartola_banco.csv` fila 32, 03/09/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    03/09/2026;COMPRA TARJETA CANVA* PRO;197975;12.990;;6.627.177
    ```

  - `cartola_banco.csv` fila 48, 17/09/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    17/09/2026;COMPRA TARJETA CANVA* PRO;324679;12.990;;7.709.412
    ```

  - `cartola_banco.csv` fila 67, 03/10/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    03/10/2026;COMPRA TARJETA CANVA* PRO;475140;12.990;;9.804.631
    ```

  - `cartola_banco.csv` fila 82, 17/10/2026, $12.990. COMPRA TARJETA CANVA* PRO

    ```text
    17/10/2026;COMPRA TARJETA CANVA* PRO;593925;12.990;;12.775.784
    ```

  - `licencias.csv` fila 6, $12.990. Licencia Canva Pro de camila@climatizacionaustral-ficticia.cl (Pro individual)

    ```text
    Canva Pro,camila@climatizacionaustral-ficticia.cl,Pro individual,12990,Activa
    ```

### H10 · Pagas la licencia de Google Workspace de alguien que ya se fue

- **Qué pasó:** La licencia de Google Workspace de bruno@climatizacionaustral-ficticia.cl sigue activa y cuesta $8.600 al mes, pero Bruno Ficticio Vera dejó la empresa el 31/07/2026. En el periodo la pagaste 3 meses sin que nadie la use. El cobro de $34.400 que ves en el banco es por todas las licencias de Google Workspace; la de esta persona es $8.600 de ese total.
- **Monto del documento o movimiento:** $8.600
- **Plata en juego:** $25.800
- **Impacto mensual:** $8.600 cada mes
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Da de baja la licencia de bruno@climatizacionaustral-ficticia.cl en Google Workspace (nota interna N05).
- **Evidencia:**

  - `cartola_banco.csv` fila 7, 02/08/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    02/08/2026;COMPRA TARJETA GOOGLE*WORKSPACE;000000;34.400;;3.765.600
    ```

  - `cartola_banco.csv` fila 31, 02/09/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    02/09/2026;COMPRA TARJETA GOOGLE*WORKSPACE;190056;34.400;;6.640.167
    ```

  - `cartola_banco.csv` fila 65, 02/10/2026, $34.400. COMPRA TARJETA GOOGLE*WORKSPACE (cobro mensual de todas las licencias del servicio; incluye esta)

    ```text
    02/10/2026;COMPRA TARJETA GOOGLE*WORKSPACE;459302;34.400;;9.793.821
    ```

  - `licencias.csv` fila 5, $8.600. Licencia Google Workspace de bruno@climatizacionaustral-ficticia.cl, estado activa

    ```text
    Google Workspace,bruno@climatizacionaustral-ficticia.cl,Business Starter,8600,Activa
    ```

  - `equipo.csv` fila 5, 31/07/2026. Bruno Ficticio Vera, inactivo, salida 31/07/2026

    ```text
    Bruno Ficticio Vera,bruno@climatizacionaustral-ficticia.cl,Tecnico,Inactivo,2022-02-01,2026-07-31
    ```

### H11 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 27/08/2026 entraron $157.000 a tu cuenta ("TRANSF. DE 23.564.221-2 BENJAMIN FICTICIO SILVA") y no encontré boleta ni factura por ese monto. IVA en riesgo (el IVA que habría que declarar si esta plata fue una venta): $25.067. Riesgo de multa del SII [sin verificar el monto de la multa]: no sé de cuánto sería, pregúntale a tu contador. Ojo: llegó al comienzo del periodo, así que podría ser el pago de un documento emitido antes de lo que cubren tus archivos.
- **Monto del documento o movimiento:** $157.000
- **Plata en juego:** $25.067
- **Impacto mensual:** $8.356 (promedio mensual)
- **Qué tan seguro:** Media: confírmalo antes de actuar.
- **Qué hacer:** Confirma que fue una venta y que no tiene documento; si es así, emite la boleta o factura (nota interna N06).
- **Evidencia:**

  - `cartola_banco.csv` fila 23, 27/08/2026, $157.000. TRANSF. DE 23.564.221-2 BENJAMIN FICTICIO SILVA

    ```text
    27/08/2026;TRANSF. DE 23.564.221-2 BENJAMIN FICTICIO SILVA;126704;;157.000;6.524.290
    ```

### H12 · Venta con tarjeta sin boleta

- **Qué pasó:** El 18/09/2026 se aprobó una venta con tarjeta por $73.500 (Mantencion preventiva domicilio, operación 70002411866) y no encontré su boleta de ese día ni del día siguiente. IVA en riesgo (el IVA que habría que declarar si esta plata fue una venta): $11.735. Riesgo de multa del SII [sin verificar el monto de la multa]: no sé de cuánto sería, pregúntale a tu contador.
- **Monto del documento o movimiento:** $73.500
- **Plata en juego:** $11.735
- **Impacto mensual:** $3.912 (promedio mensual)
- **Qué tan seguro:** Alta: la evidencia es directa.
- **Qué hacer:** Confirma que la boleta no existe con otra fecha u otro monto; si falta, emítela (nota interna N07).
- **Evidencia:**

  - `ventas_mercadopago.csv` fila 25, 18/09/2026, $73.500. Mantencion preventiva domicilio, operación 70002411866

    ```text
    2026-09-18T14:48:00-03:00,70002411866,Mantencion preventiva domicilio,73500.00,2565.00,70935.00,approved,qr
    ```

## Cómo verificar este informe

1. Elige cualquier hallazgo y mira su evidencia: dice el archivo, la fila, la fecha y el monto.
2. Abre ese archivo en Excel o en cualquier editor y ve a esa fila. La fila 1 es la primera línea del archivo, así que los títulos y encabezados también cuentan: es el mismo número que muestra Excel a la izquierda.
3. Compara la fecha y el monto de la fila con los del informe. Deben ser iguales.
4. En el detalle de cada hallazgo está copiada la fila original, para que la reconozcas sin buscar.
5. El detector hizo esta misma comprobación antes de escribir el informe: lo que no calzó no aparece aquí.

Archivos que leí:

- `cartola_banco.csv`: cartola o movimientos del banco, 86 filas leídas.
- `cotizaciones.csv`: cotizaciones o presupuestos, 49 filas leídas. No lo usé porque repite a otro archivo.
- `cotizaciones.xlsx`: cotizaciones o presupuestos, 49 filas leídas.
- `equipo.csv`: personas del equipo, 5 filas leídas.
- `licencias.csv`: licencias de software por usuario, 7 filas leídas.
- `rcv_compras.csv`: registro de compras del sii, 12 filas leídas.
- `rcv_ventas.csv`: registro de ventas del sii, 78 filas leídas.
- `ventas_mercadopago.csv`: ventas con tarjeta o link de pago, 47 filas leídas.

## Lo que no pude revisar

Revisé todos los tipos de fuga: no faltó ningún archivo.

Ten en cuenta:

- 'cotizaciones.xlsx' y 'cotizaciones.csv' traen las mismas filas: usé solo 'cotizaciones.xlsx' para no contar nada dos veces.
- Dejé fuera 14 abonos que no son ventas (aportes de socios, devoluciones, liquidaciones de tarjetas), según tu configuración.

---

Este informe no reemplaza a tu contador. Montos en CLP.
