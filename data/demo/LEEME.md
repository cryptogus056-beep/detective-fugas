# Dataset demo A (100% ficticio)

Empresa inventada: **Climatizacion Austral Ficticia SpA**, una pyme de mantención e instalación de aire acondicionado. Periodo: 01/08/2026 al 31/10/2026. Fecha de corte: 31/10/2026.

Todo es inventado: nombres, RUT (formato válido con dígito verificador correcto, elegidos al azar; si alguno coincide con uno real es pura casualidad), montos y movimientos. Lo genera `scripts/generar_dataset.py` con semilla fija, así que siempre sale igual.

| Archivo | Qué simula | Formato |
|---|---|---|
| `cartola_banco.csv` | Cartola de cuenta corriente | `;`, 5 líneas de preámbulo, encabezado en la línea 6, fechas dd/mm/aaaa, montos con punto de miles, columnas Cargos y Abonos separadas |
| `ventas_mercadopago.csv` | Reporte de ventas de Mercado Pago | `,`, fechas ISO con hora y zona, montos con 2 decimales, estado `approved` o `rejected` |
| `rcv_ventas.csv` | Registro de Ventas del SII | `;`, tipo 33 = factura, 39 = boleta, montos enteros |
| `rcv_compras.csv` | Registro de Compras del SII | `;` |
| `cotizaciones.xlsx` | Planilla de cotizaciones | título en la fila 1, encabezado en la fila 2 |
| `cotizaciones.csv` | Espejo del XLSX en CSV (mismas filas) | `;`. Usa uno solo de los dos |
| `equipo.csv` | Personas de la empresa, activas e inactivas | `,` |
| `licencias.csv` | Asientos de software por usuario | `,` |
| `config.json` | Fecha de corte, umbrales y exclusiones | JSON |

Hay **12 fugas escondidas** de 5 tipos y varios señuelos (cosas que parecen fuga pero no lo son). La llave está en `_respuestas/` y **solo la lee `scripts/evaluar.py`**.

Los formatos imitan exportaciones reales, pero los encabezados exactos de cada banco, de Mercado Pago y del SII pueden variar **[sin verificar]**. Para eso están las plantillas de columnas.
