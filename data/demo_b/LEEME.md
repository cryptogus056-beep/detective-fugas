# Dataset demo B (100% ficticio, otros formatos)

La misma empresa inventada, con otra semilla (otros clientes y montos) y **otros formatos de archivo**, para probar que el detector sirve para cualquier pyme y no solo para la demo A.

| Archivo | Qué simula | Diferencia con la demo A |
|---|---|---|
| `movimientos_cuenta.csv` | Cartola de otro banco | `,`, UTF-8 con BOM, sin preámbulo, fechas aaaa-mm-dd, **un solo monto con signo** (negativo = cargo) |
| `ventas_transbank.csv` | Ventas con tarjeta tipo Transbank | `;`, fechas dd-mm-aaaa, montos con punto de miles, estado `Aprobada` o `Rechazada` |
| `presupuestos.csv` | Planilla de presupuestos | otros encabezados, **solo neto** (el total se calcula), estados `APROBADO`, `RECHAZADO`, `ENVIADO` |
| `rcv_ventas.csv`, `rcv_compras.csv` | SII | igual que en A (el SII es el mismo para todos) |
| `equipo.csv`, `licencias.csv`, `config.json` | igual que en A | |

También tiene 12 fugas escondidas. El criterio de aceptación es que el detector pase aquí **solo agregando plantillas**, sin código especial para esta carpeta. Los formatos de Transbank y del banco son aproximados **[sin verificar]**.
