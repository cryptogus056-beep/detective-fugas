# Informe de fugas: Taller Ficticio de Prueba SpA

Periodo revisado: 01/08/2026 al 30/09/2026 (2 meses). Fecha de corte: 30/09/2026.

## Resumen en 5 líneas

1. **En juego:** $72.568 en los 2 meses revisados (unos $36.284 al mes).
2. **Qué encontré:** 3 fugas: 3 ingresos sin boleta ni factura.
3. **La más grande:** Abono del 15/09/2026 sin boleta ni factura (DEPOSITO CHEQUE CLIENTE TALLER) ($38.000, H01).
4. **Qué hacer primero esta semana:** Emite la boleta o factura que falta (nota interna N01). Después sigue con la tabla, de arriba hacia abajo.
5. **Si cobras lo pendiente:** no hay cobros pendientes a clientes; lo que encontré se arregla puertas adentro.

## Fugas encontradas, de mayor a menor impacto mensual

| N° | Tipo | Qué pasó | Monto | Impacto mensual | Evidencia | Acción |
|---|---|---|---|---|---|---|
| 1 | Plata que entró sin boleta ni factura | Abono del 15/09/2026 sin boleta ni factura (DEPOSITO CHEQUE CLIENTE TALLER) | $238.000 | $19.000 (promedio mensual) | `banco.csv` fila 6, 15/09/2026, $238.000 | Emite la boleta o factura que falta (nota interna N01). |
| 2 | Plata que entró sin boleta ni factura | Abono del 04/08/2026 sin boleta ni factura (DEPOSITO EN EFECTIVO SUCURSAL CENTRO) | $120.000 | $9.580 (promedio mensual) | `banco.csv` fila 2, 04/08/2026, $120.000 | Emite la boleta o factura que falta (nota interna N02). |
| 3 | Plata que entró sin boleta ni factura | Abono del 28/09/2026 sin boleta ni factura (ABONO REMESA VENTA MOSTRADOR SEMANA 39) | $96.500 | $7.704 (promedio mensual) | `banco.csv` fila 7, 28/09/2026, $96.500 | Emite la boleta o factura que falta (nota interna N03). |

"Promedio mensual" quiere decir que la fuga pasó una vez y la repartí entre los meses del periodo. "Cada mes" quiere decir que se repite todos los meses hasta que la arregles.

## Detalle de cada fuga

### H01 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 15/09/2026 entraron $238.000 a tu cuenta ("DEPOSITO CHEQUE CLIENTE TALLER") y no encontré boleta ni factura por ese monto. IVA en riesgo: $38.000. Riesgo de multa del SII [sin verificar el monto de la multa]. La descripción del movimiento no trae RUT, así que no sé quién pagó: revísalo antes de emitir el documento.
- **Monto:** $238.000
- **Impacto en el periodo:** $38.000
- **Impacto mensual:** $19.000 (promedio mensual)
- **Qué hacer:** Emite la boleta o factura que falta (nota interna N01).
- **Confianza:** media: revísalo antes de actuar.
- **Evidencia:**

  - `banco.csv` fila 6, 15/09/2026, $238.000. DEPOSITO CHEQUE CLIENTE TALLER

    ```text
    15/09/2026;DEPOSITO CHEQUE CLIENTE TALLER;;238.000
    ```

### H02 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 04/08/2026 entraron $120.000 a tu cuenta ("DEPOSITO EN EFECTIVO SUCURSAL CENTRO") y no encontré boleta ni factura por ese monto. IVA en riesgo: $19.160. Riesgo de multa del SII [sin verificar el monto de la multa]. La descripción del movimiento no trae RUT, así que no sé quién pagó: revísalo antes de emitir el documento.
- **Monto:** $120.000
- **Impacto en el periodo:** $19.160
- **Impacto mensual:** $9.580 (promedio mensual)
- **Qué hacer:** Emite la boleta o factura que falta (nota interna N02).
- **Confianza:** media: revísalo antes de actuar.
- **Evidencia:**

  - `banco.csv` fila 2, 04/08/2026, $120.000. DEPOSITO EN EFECTIVO SUCURSAL CENTRO

    ```text
    04/08/2026;DEPOSITO EN EFECTIVO SUCURSAL CENTRO;;120.000
    ```

### H03 · Entró plata al banco sin boleta ni factura

- **Qué pasó:** El 28/09/2026 entraron $96.500 a tu cuenta ("ABONO REMESA VENTA MOSTRADOR SEMANA 39") y no encontré boleta ni factura por ese monto. IVA en riesgo: $15.408. Riesgo de multa del SII [sin verificar el monto de la multa]. La descripción del movimiento no trae RUT, así que no sé quién pagó: revísalo antes de emitir el documento.
- **Monto:** $96.500
- **Impacto en el periodo:** $15.408
- **Impacto mensual:** $7.704 (promedio mensual)
- **Qué hacer:** Emite la boleta o factura que falta (nota interna N03).
- **Confianza:** media: revísalo antes de actuar.
- **Evidencia:**

  - `banco.csv` fila 7, 28/09/2026, $96.500. ABONO REMESA VENTA MOSTRADOR SEMANA 39

    ```text
    28/09/2026;ABONO REMESA VENTA MOSTRADOR SEMANA 39;;96.500
    ```

## Cómo verificar este informe

1. Elige cualquier hallazgo y mira su evidencia: dice el archivo, la fila, la fecha y el monto.
2. Abre ese archivo en Excel o en cualquier editor y ve a esa fila. La fila 1 es la primera línea del archivo, así que los títulos y encabezados también cuentan: es el mismo número que muestra Excel a la izquierda.
3. Compara la fecha y el monto de la fila con los del informe. Deben ser iguales.
4. En el detalle de cada hallazgo está copiada la fila original, para que la reconozcas sin buscar.
5. El detector hizo esta misma comprobación antes de escribir el informe: lo que no calzó no aparece aquí.

Archivos que leí:

- `banco.csv`: cartola o movimientos del banco, 6 filas leídas.
- `rcv_ventas.csv`: registro de ventas del sii, 1 filas leídas.

## Lo que no pude revisar

- No había archivo de ventas con tarjeta: no revisé ventas con tarjeta sin boleta.
- No había planilla de cotizaciones: no revisé cotizaciones sin cobro ni netos cobrados como total.
- No había archivo de licencias: no revisé suscripciones duplicadas ni huérfanas.
- No había archivo del equipo: no revisé licencias de personas que ya salieron.
- No había Registro de Compras del SII: no pude reconocer devoluciones de proveedores por su RUT (solo por las palabras de la configuración).

Ten en cuenta:

- Dejé fuera 2 posibles hallazgos porque no pasaron la verificación o la clasificación. El detalle está en `descartados.json`.

---

Este informe no reemplaza a tu contador. Montos en CLP.
