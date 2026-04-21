# Pipeline de Prueba

## Descripción General
Pipeline de prueba para verificar el reindexado automático de Pipelore.
Detecta si el sistema identifica archivos nuevos al arrancar el servidor.

## Owner
equipo-data@empresa.com

## Arquitectura
Ingesta desde tabla `test_source` → transformación mínima → carga en `test_output`.

## Fuentes de Datos
- Tabla: `test_source` (base de datos: `dw_test`)
- Formato: incremental por `updated_at`

## Transformaciones
- Limpieza de nulos en columna `value`
- Normalización de `category` a minúsculas

## Reglas de Negocio
- Registros con `status = 'inactive'` se excluyen del output
- `value` no puede ser negativo

## Frecuencia de Ejecución
Diaria a las 03:00 UTC.

## Dependencias
Ninguna.

## Output / Entregables
- Tabla: `test_output`

## Contacto
equipo-data@empresa.com
