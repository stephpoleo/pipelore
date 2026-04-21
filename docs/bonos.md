# Bonos Retail (México y Brasil)

## Descripción General

Calcula los bonos y comisiones de los empleados retail para tiendas de México y Brasil. Este dominio alimenta los dashboards de BI que el equipo de operaciones retail usa para rastrear el cumplimiento de bonos individuales y por tienda cada mes. También maneja el archivado mensual de snapshots de bonos en una tabla de historial (`EMPLOYEE_BONUSES_HISTORY`).

## Owner

Stephanie Poleo — [TO COMPLETE — agregar equipo y canal de Slack antes de indexar]

## Arquitectura

```
SILVER (merge)                        GOLD_DASHBOARDS                           GOLD (archival)
──────────────────────────────────────────────────────────────────────────────────────────────────
R__zecore_silver_merge_into.sql    → R__retail_bonos_mexico.sql              → R__manage_bonuses_history.sql
  (zecore_merge_salesgoal)            (EMPLOYEE_COMMISSIONS_LEDGER,             (INSERT_INTO_BONUSES_HISTORY,
        │                              DIM_BONO,                                 REFRESH_BONUSES_HISTORY)
        │                              BONOS_RETAIL_SNAPSHOT,                          ▲
        │                              COMMERCIAL_AND_ACCOUNTING_SALES)                │
        │                                                                              │
        └──────────────────────── TRIGGERS on new/updated sales goals ─────────────────┘

                                   → R__retail_bonos_brazil.sql
                                     (RETAIL_BONOS_BRAZIL)
```

Flujo general:
1. `zecore_merge_salesgoal` fusiona metas de ventas de STG → SILVER y dispara el archivado cuando se crean o actualizan metas
2. Los archivos de México y Brasil calculan bonos en tiempo real como views en `GOLD_DASHBOARDS`
3. `manage_bonuses_history` archiva snapshots mensuales en `EMPLOYEE_BONUSES_HISTORY` (tabla permanente)

## Fuentes de Datos

**Tablas Silver (transaccionales):**
- `SILVER.ZECORE_SALESGOAL` — metas de ventas por período y empleado
- `SILVER.ZECORE_EMPLOYEE` — datos de empleados (incluyendo historial de re-ingresos)
- `SILVER.GETIN_STORE_VISITS` — visitas a tienda (tráfico), usadas para calcular CR y filtrar por uptime del sensor Getin
- `SILVER.FILE_UPLOADER_POS_DAILY_GOAL` — metas diarias de CR y AOV por tienda

**Tablas Gold (hechos y dimensiones):**
- `GOLD.ZESALES_PAYMENT_DEFINITION` — hechos de ventas (fuente principal de cálculo de bonos)
- `GOLD.DIM_BONO` — dimensión de control: activa/desactiva bonos por código y rango de fechas
- `GOLD.RETAIL_LAST_YEAR_PAYMENT_DEFINITION` — ventas del año anterior para reconciliación

**File Uploaders (configuración manual):**
- `file_uploader_brazil_bonus_notes` — tabla de notas por logro de ventas/AOV/CR para Brasil
- `file_uploader_brazil_bonus_multiplier` — mapeo de nota total a multiplicador de comisión para Brasil
- `zecore_commissiontabulatorrange` — rango de comisiones para México y Brasil

## Transformaciones

**`silver/R__zecore_silver_merge_into.sql` → `SILVER.zecore_merge_salesgoal()`**

Procedimiento de merge que carga metas de ventas de STG → SILVER (deduplicadas por nombre, la más reciente gana) y dispara el archivado de historial de bonos cuando se detectan metas nuevas o actualizadas.

**`gold_dashboards/R__retail_bonos_mexico.sql` → 4 objetos:**
- `GOLD.EMPLOYEE_COMMISSIONS_LEDGER`: view de comisiones por empleado por período de meta; usa `paid_date` (no `created_date`) para asignar el período
- `GOLD.DIM_BONO`: dimensión que controla qué bonos están activos por código y rango de fechas
- `GOLD.BONOS_RETAIL_SNAPSHOT`: view principal con el cálculo completo de todos los bonos por orden y por empleado (fuente del archivado)
- `GOLD.COMMERCIAL_AND_ACCOUNTING_SALES`: view de reconciliación entre ventas retail y contabilidad

**`gold_dashboards/R__retail_bonos_brazil.sql` → `GOLD.RETAIL_BONOS_BRAZIL`**

View de bonos para Brasil basada en un sistema de notas: cada métrica (ventas, AOV, CR) recibe una nota, el producto nota×factor se suma en `total_note_score`, que se mapea a un `bonus_multiplier` vía tabla de lookup.

**`gold/R__manage_bonuses_history.sql` → 2 procedimientos:**
- `GOLD.INSERT_INTO_BONUSES_HISTORY(ledger_sales_goal_name)`: archiva `BONOS_RETAIL_SNAPSHOT` → `EMPLOYEE_BONUSES_HISTORY`. Maneja evolución de esquema automáticamente (añade columnas nuevas via `ALTER TABLE`)
- `GOLD.REFRESH_BONUSES_HISTORY(...)`: re-sincroniza filas específicas en `EMPLOYEE_BONUSES_HISTORY` desde `BONOS_RETAIL_SNAPSHOT`; automatiza el flujo manual DELETE + re-INSERT para correcciones

## Reglas de Negocio

### México — Filtrado de ventas

- Se incluyen ventas con: `operative_sale=1`, tipo D2C, estatus Paid, país México, canal Offline D2C
- Órdenes "Cambio de tamano" se zeroan en `net_sale_value` (no cuentan para bonos)
- Cancelaciones (valor negativo) se zeroan para cálculos de bonos

### México — Bonos individuales por orden

| Bono | Regla |
|------|-------|
| `BONO_LUUNA` | $400 para órdenes 40k–100k (con IVA), luego $1,000 por cada 100k adicional. Solo tiendas no-Mappa. |
| `BONO_MAPPA` | $400 para órdenes 20k–50k (con IVA), luego $1,000 por cada 50k adicional. Solo tiendas Mappa. |
| `BONO_PUFF` | $50/puff, $100/puff si orden > 40k, $150/puff si orden > 100k |
| `BONO_SOFAS` | $300 si el total de sofás en la orden >= 30k (con IVA) |

### México — Bonos por tienda (mensuales)

| Bono | Regla |
|------|-------|
| `BONO_SHARE_COLCHONES` | $1,000 si Luuna One >= 30% de qty de colchones Y ventas de colchones >= 70% de ventas totales de la tienda |
| `BONO_SHARE_SOFAS` | $1,000 si sofás >= 10% de las ventas totales del empleado |
| `BONO_CR_AOV` | Requiere >= 90% de cumplimiento en CR y AOV (modificado desde 100% en Oct 2025) |
| `BONO_CR_AOV_CUSTOM` | Tabulador personalizado introducido Nov 2025 con lookup matricial (alcance_ventas × AOV × CR) |
| `BONO_AIO` | $1,000 si el ratio artículos-por-orden >= 3.0 |
| `BONO_GARANTIA` | $1,500 para Guru, $2,000 para Store Manager; solo empleados no-TEMPORAL en su tienda original, dentro de los 30 días de ingreso |

### México — Control por DIM_BONO

`DIM_BONO` controla la activación de cada bono vía flag `IS_ACTIVE` y rangos de fecha (`CHANGED_FROM`/`CHANGED_TO`). Cada código de bono puede tener múltiples filas con distintos períodos activos (ej. `BONO_SOFAS` fue desactivado sep–oct 2025, reactivado nov 2025).

### México — Lógica de re-ingreso de empleados

`COALESCE(em.employee, o.employee)` maneja casos donde el código de empleado cambió después de un re-ingreso. La tabla de empleados históricos hace join entre `BRONZE.zecore_employee` y `SILVER.zecore_employee` para rastrear cambios de `user_id`.

### Brasil — Sistema de notas

- Logros de ventas, AOV y CR reciben una "nota" (puntaje) desde `file_uploader_brazil_bonus_notes`
- Cada nota tiene un factor; el producto (nota × factor) por cada métrica se suma en `total_note_score`
- `total_note_score` se mapea a un `bonus_multiplier` vía `file_uploader_brazil_bonus_multiplier`
- El factor de comisión final viene de `zecore_commissiontabulatorrange` usando el multiplicador

### Brasil — Diferencias clave respecto a México

- Tipos de órdenes más amplios: incluye Marketplace, B2B Retail, Roadshow, etc.
- Metas por período (no necesariamente mensual) desde `zecore_salesgoal`
- Filtrado por uptime de sensor Getin: solo cuenta visitas y órdenes en días donde el sensor estaba operativo
- Store Managers reciben todas las órdenes de la tienda; Gurus solo sus propias órdenes (match por `user_id`)

### Trigger — `SILVER.zecore_merge_salesgoal`

El trigger de archivado se activa desde `silver/R__zecore_silver_merge_into.sql`:

| Evento | Acción | Procedimiento llamado |
|--------|--------|-----------------------|
| Nueva meta creada (`op='I'`) | Archivar snapshot de bonos para esa meta | `INSERT_INTO_BONUSES_HISTORY(ledger_sales_goal_name)` |
| Meta existente actualizada (`op='U'`) | Refrescar historial para esa meta | `REFRESH_BONUSES_HISTORY(ledger_sales_goal_name)` |

**Importante:** el refresh solo se dispara cuando no hay nuevos inserts en el mismo batch. Previene procesar la misma meta dos veces.

**Filtro de fecha:** solo procesa registros desde `2026-01-01` en adelante (fecha de lanzamiento de la feature).

## Frecuencia de Ejecución

- **Views en `GOLD_DASHBOARDS`** (`BONOS_RETAIL_SNAPSHOT`, `EMPLOYEE_COMMISSIONS_LEDGER`, `RETAIL_BONOS_BRAZIL`): se calculan on-demand; se refrescan cada vez que se consultan
- **Archivado mensual** (`INSERT_INTO_BONUSES_HISTORY` en modo Mode 2): job programado que corre el mes siguiente, apunta al mes anterior y salta si el dato ya existe (idempotente)
- **Archivado por trigger** (`INSERT_INTO_BONUSES_HISTORY` en modo Mode 1): se dispara automáticamente desde `zecore_merge_salesgoal` cuando se crea una nueva meta de ventas
- **Refresh de correcciones** (`REFRESH_BONUSES_HISTORY`): manual o disparado por trigger cuando se actualiza una meta existente

## Dependencias

**Upstream (fuentes que alimentan este dominio):**
- `SILVER.ZECORE_SALESGOAL` — metas de ventas; si no están actualizadas, los bonos del período no se archivan
- `GOLD.ZESALES_PAYMENT_DEFINITION` — hechos de ventas; fuente de toda la lógica de bonos
- `SILVER.GETIN_STORE_VISITS` — tráfico a tienda; necesario para cálculo de CR en México y Brasil
- `SILVER.FILE_UPLOADER_POS_DAILY_GOAL` — metas de CR/AOV; necesarias para `BONO_CR_AOV`
- `file_uploader_brazil_bonus_notes` y `file_uploader_brazil_bonus_multiplier` — configuración de Brasil; si no están cargados, el cálculo de Brasil falla

**Downstream (que dependen de este dominio):**
- Dashboards QuickSight que consumen `EMPLOYEE_BONUSES_HISTORY`
- `GOLD.BONOS_RETAIL_SNAPSHOT` — fuente de `EMPLOYEE_BONUSES_HISTORY`; si cambia su esquema, el procedimiento de archivado lo detecta y evoluciona automáticamente

## Output / Entregables

- **`GOLD.BONOS_RETAIL_SNAPSHOT`**: view en tiempo real con el cálculo completo de bonos por orden y por empleado para México
- **`GOLD.RETAIL_BONOS_BRAZIL`**: view en tiempo real de bonos para Brasil
- **`GOLD.EMPLOYEE_BONUSES_HISTORY`**: tabla permanente con snapshot mensual de bonos archivados; consumida por dashboards QuickSight
- **`GOLD.EMPLOYEE_COMMISSIONS_LEDGER`**: view de comisiones acumuladas por empleado por período de meta
- **`GOLD.COMMERCIAL_AND_ACCOUNTING_SALES`**: view de reconciliación de ventas retail vs contabilidad

## Consideraciones Conocidas

- **Prioridad del trigger:** cuando `zecore_merge_salesgoal` corre, las metas nuevas (inserts) tienen prioridad sobre las actualizaciones. Si en el mismo batch hay metas nuevas y actualizadas, solo las nuevas disparan archivado; las actualizadas se saltan para evitar procesamiento duplicado.
- **Filtro de fecha del trigger:** el trigger solo procesa metas de ventas desde `2026-01-01` en adelante. Registros anteriores se fusionan en SILVER pero no disparan archivado de historial de bonos.
- **Views auto-referenciadas:** `BONOS_RETAIL_SNAPSHOT` lee de `EMPLOYEE_COMMISSIONS_LEDGER`, que se crea en el mismo archivo SQL. Ambas son views en el mismo `CREATE OR REPLACE`, por lo que el orden importa.
- **Tiendas fraccionadas:** algunas tiendas están divididas en múltiples perfiles POS. El CTE `comisiones` re-agrega para evitar duplicados de tiendas fraccionadas.
- **Downtime del sensor Getin:** los días donde el sensor reporta 0 de uptime se excluyen del cálculo de CR para evitar tasas de conversión artificialmente bajas.
- **Tabulador CR/AOV personalizado:** desde nov 2025, el bono CR/AOV usa un lookup matricial 5×2×2 (`custom_cr_aov_tab`) en lugar del tabulador de comisiones tradicional. Controlado por `DIM_BONO.BONO_CR_AOV_CUSTOM.IS_ACTIVE`.
- **Atribución de período aftersales:** órdenes pagadas fuera de su período original de meta quedan marcadas con `aftersales_move_outside_period = 1`.
- **Lookup de notas en Brasil:** el patrón `QUALIFY ROW_NUMBER()` se usa ampliamente en Brasil para seleccionar la fila de nota con mejor match, priorizando filas donde `since_date <= period_start`.
- **Evolución de esquema en historial:** si se agrega una columna a `BONOS_RETAIL_SNAPSHOT`, el procedimiento de archivado la agrega automáticamente a `EMPLOYEE_BONUSES_HISTORY`. Sin embargo, si se elimina una columna del snapshot, los meses anteriores tendrán datos pero los nuevos mostrarán `NULL`.

## Contacto

- **Owner técnico:** Stephanie Poleo — [TO COMPLETE — agregar Slack y repo antes de indexar]
- **Reglas de negocio:** [TO COMPLETE — agregar contacto del área de Recursos Humanos o Retail Ops]
- **Datos de ventas (Zecore):** [TO COMPLETE — agregar contacto del equipo que mantiene la ingesta de Zecore]
