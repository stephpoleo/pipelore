# POS Aftersales

## Descripción General

Consolida todas las operaciones de post-venta POS (cancelaciones, garantías, cambios de producto, reenvíos, reembolsos, incidentes) en una única view que calcula el impacto económico de cada caso a nivel de ítem. Alimenta los dashboards de KPIs del equipo de post-venta, vinculando casos, documentos de post-venta POS, devoluciones de envío, notas de entrega, órdenes nuevas y órdenes de venta.

## Owner

[TO COMPLETE — agregar nombre, equipo y canal de Slack antes de indexar]

## Arquitectura

```
SILVER                              GOLD                          GOLD_DASHBOARDS
────────────────────────────────────────────────────────────────────────────────────
zecore_posaftersalesitem (PASI)  → inventory_cost_by_shipping_item → R__pos_aftersales.sql
zecore_posaftersales (PAS)       → pointofsale                       (GOLD.pos_aftersales view)
zecore_shippingcoreitem (SCI)    → item
zecore_shippingreturnitem (SRI)  → zesales_payment_definition
zecore_shippingreturn (SR)
zecore_deliverynote (DN)
zecore_deliverynoteitem (DNI)
zecore_salesorder (SO)
zecore_shippingcore (SC)
zecore_posaftersalesorder (PASO)
zecore_case
zecore_employee
zecore_departmentmembers
zecore_salesorderitem
```

La view se construye como una cadena de CTEs en tres fases: (1) matching PASI↔SRI, (2) enriquecimiento y cálculo de impacto económico, (3) contexto y output final con dos FULL OUTER JOINs.

## Fuentes de Datos

**Tablas Silver (13 fuentes):**
- `SILVER.ZECORE_POSAFTERSALESITEM (PASI)` — ítems de documentos de post-venta POS; fuente principal
- `SILVER.ZECORE_POSAFTERSALES (PAS)` — documentos de post-venta POS (cabecera)
- `SILVER.ZECORE_SHIPPINGCOREITEM (SCI)` — ítems de envíos de salida
- `SILVER.ZECORE_SHIPPINGRETURNITEM (SRI)` — ítems de devoluciones de envío
- `SILVER.ZECORE_SHIPPINGRETURN (SR)` — cabeceras de devoluciones de envío
- `SILVER.ZECORE_DELIVERYNOTE (DN)` — notas de entrega (fuente de costo real)
- `SILVER.ZECORE_DELIVERYNOTEITEM (DNI)` — ítems de notas de entrega
- `SILVER.ZECORE_SALESORDER (SO)` — órdenes de venta (nuevas órdenes y órdenes originales)
- `SILVER.ZECORE_SHIPPINGCORE (SC)` — envíos de salida vinculados a nuevas órdenes
- `SILVER.ZECORE_POSAFTERSALESORDER (PASO)` — ítems de órdenes de post-venta (precio y detalles)
- `SILVER.ZECORE_CASE` — casos de atención (metadata, owner, squad, estado, SLA)
- `SILVER.ZECORE_EMPLOYEE` — empleados con departamento y cargo
- `SILVER.ZECORE_DEPARTMENTMEMBERS` — membresía de empleados por departamento
- `SILVER.ZECORE_SALESORDERITEM` — ítems de órdenes de venta (para conteo total de ítems)

**Tablas Gold:**
- `GOLD.INVENTORY_COST_BY_SHIPPING_ITEM` — costo de inventario por ítem de envío (fallback de costo cuando no hay nota de entrega)
- `GOLD.ZESALES_PAYMENT_DEFINITION` — estado de pago y envío de órdenes de venta
- `GOLD.POINTOFSALE` — perfil de punto de venta (país)

## Transformaciones

La view `GOLD.pos_aftersales` se construye en tres fases de CTEs:

**Fase 1: Matching PASI↔SRI (líneas 6–145)**

Vincula ítems de post-venta POS (PASI) con ítems de devolución de envío (SRI) usando una estrategia de dos pasos:
1. **Match exacto**: pareo PASI↔SRI por `shipping_core_item + item_code + rn` (número de fila)
2. **Match fallback**: los PASI sin match exacto se parean con SRI no consumidos solo por `item_code + rn` dentro del mismo post-venta POS

Esta estrategia de dos pasos existe porque los registros SRI pueden tener `from_shipping_core_item` parcial o nulo: el match exacto captura datos limpios; el fallback maneja los casos imperfectos.

**Fase 2: Enriquecimiento e impacto económico (líneas 147–504)**

- Pre-materializa notas de entrega (DN) con sus ítems y nuevas órdenes vinculadas a post-ventas con sus envíos
- Une ítems PASI con PASO (detalles de precio) y notas de entrega (dos joins separados: uno para Return Shipping, otro para otros estados)
- `calculate_economic_impact`: lógica central de negocio; clasifica el impacto económico de cada ítem y calcula su costo. Usa CROSS JOIN para manejar doble impacto. Incluye 4 ramas UNION ALL para distintas fuentes de impacto

**Fase 3: Contexto y output final (líneas 505–665)**

- Agrega metadata de casos, empleados, estado de pago/envío, perfil POS y validación de empleado
- Agrega lista y conteo de post-ventas vinculados a cada orden de venta
- El SELECT final usa dos FULL OUTER JOINs: uno para traer todos los casos (aunque no tengan post-venta POS) y otro para traer todas las órdenes de venta calificadas (aunque no tengan post-venta POS)

## Reglas de Negocio

### Clasificación de impacto económico

Cada ítem recibe una `impact_classification` y un `impact_cost` según la combinación de `case_type`, `reason`, `resolution` y `shipping_state`:

| Tipo de caso | Condición | Clasificación | Fórmula de costo |
|---|---|---|---|
| Cancel, Garantía por satisfacción | Return/Cancel Shipping | Pérdida de ingreso | `pos_afts_item_total` |
| Garantía por defecto | Reemplazo de producto + Return Shipping | Gasto | `pos_afts_item_total + incoming_rate` |
| Garantía por defecto | Reemplazo parcial + no Delivered | Gasto | `pos_afts_item_total + incoming_rate` |
| Garantía por defecto | Reenvío de producto + no Delivered | Gasto | `pos_afts_item_total + incoming_rate` |
| Cambio de producto | Nuevo pago <= 0 + Return/Cancel Shipping | Pérdida de ingreso | `pos_afts_new_payment` |
| Reenvío de orden entregada | Reshipment | Gasto | `pos_afts_item_total + incoming_rate` |
| Incidentes | (cualquier) | Gasto | `incoming_rate` |

### Regla de doble impacto

Un ítem genera dos líneas de impacto cuando se cumplen las tres condiciones simultáneamente:
- `return_item_is_resellable = 0` (el producto devuelto no es revendible)
- `shipping_state = 'Return Shipping'`
- `case_type` es 'Satisfaction warranty' o 'Product change'

En ese caso se agrega una línea `resellable_cost` con `incoming_rate` como costo, clasificada como "Gasto".

### Fuentes adicionales de impacto (ramas UNION ALL)

| Rama | Valor de `impact_line` | Condición de disparo |
|------|------------------------|----------------------|
| Productos de compensación | `compensation_product` | `resolution = 'Product compensation'` |
| Reembolsos económicos | `compensation_fund` | `case_type IN ('Refund for wrong payment', 'Refund for containment', 'Refund for promotion not applied')` |
| Nuevas órdenes de reemplazo parcial | `partial_replacement_new_order` | `case_type IN ('Partial defect warranty', 'Containment order', 'Defect warranty')` e ítem no consumido en el match principal |

### Filtrado de órdenes de venta

El CTE `sales_orders` excluye:
- Tipos de orden relacionados con post-venta (garantías, compensaciones, contenciones, etc.)
- Órdenes en borrador (Draft)
- Órdenes canceladas antes del pago (`status = 'Cancelled' AND reference_date IS NULL`)

Este filtro vive en el CTE (no en el WHERE final) para evitar eliminar inadvertidamente casos o post-ventas POS vinculados a esas órdenes a través del FULL OUTER JOIN.

### Resolución de notas de entrega

Las notas de entrega se resuelven vía dos LEFT JOINs separados (sin OR en la condición de join):
- **Return Shipping**: match por `shipping_return + shipping_return_item_name`
- **Otros estados**: match por `shipping_core + shipping_core_item_name`

Si no se encuentra nota de entrega, el costo cae al fallback de `inventory_cost_by_shipping_item`.

## Frecuencia de Ejecución

`GOLD.pos_aftersales` es una **view** — se calcula on-demand cada vez que se consulta. No hay job programado ni archivado periódico. La latencia de los datos depende de cuándo se actualicen las tablas SILVER fuente.

## Dependencias

**Upstream (fuentes que alimentan esta view):**
- Las 13 tablas SILVER listadas en Fuentes de Datos, especialmente `ZECORE_POSAFTERSALESITEM` (PASI) y `ZECORE_CASE`
- `GOLD.INVENTORY_COST_BY_SHIPPING_ITEM` — si esta view tiene errores, el cálculo de costo falla para ítems sin nota de entrega
- `GOLD.ZESALES_PAYMENT_DEFINITION` — estado de pago de órdenes; si no está actualizado, el estado de envío en el output estará desactualizado

**Downstream (que dependen de esta view):**
- Dashboards de KPIs del equipo de post-venta (reportes de impacto económico, métricas de casos)
- [TO COMPLETE — confirmar si algún pipeline lee directamente de `GOLD.pos_aftersales`]

## Output / Entregables

- **`GOLD.pos_aftersales`** (view en `gold_dashboards/R__pos_aftersales.sql`): view única con impacto económico a nivel de ítem por cada caso/post-venta POS. Incluye clasificación de impacto, costo calculado, metadata del caso, empleado, estado de pago y perfil POS.
- Alimenta directamente los **dashboards de KPIs** del equipo de post-venta para seguimiento de impacto económico por tipo de caso, tienda y período.

## Consideraciones Conocidas

- **Filtro de fecha hardcodeado:** `DATE(pas.creation) >= '2024-01-01'` en `pasi_numbered` limita el alcance de los datos. Modificar este valor requiere un deploy.
- **Fallback de matching PASI↔SRI:** el match de fallback (`match_type = 'fallback'`) pareo ítems solo por `item_code + rn` sin `shipping_core_item`, lo que puede producir pares incorrectos si múltiples ítems comparten el mismo `item_code` dentro de un mismo post-venta POS.
- **FULL OUTER JOINs en el output final:** el SELECT final usa dos FULL OUTER JOINs (casos y órdenes de venta). Esto significa que el output incluye casos sin post-venta POS y órdenes de venta sin post-venta POS como filas separadas.
- **Typo en `inventory_cost_by_shipping_item`:** la columna `deliveryt_note` (con typo) es referenciada desde esta view. Es el nombre real de la columna en la view fuente, no un error en esta query.
- **Join con PASO excluye ítems Delivered:** el join con `paso_numbered` tiene `shipping_state != 'Delivered'` en la cláusula ON. Si `shipping_state` es NULL, el join no hará match (NULL != 'X' evalúa a NULL/false en SQL).
- **Split del join de notas de entrega:** los joins de DN están divididos en dos LEFT JOINs (return vs core) para evitar condiciones OR en predicados de join, lo que mejora el rendimiento de la query.
