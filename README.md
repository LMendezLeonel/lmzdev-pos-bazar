# Sistema POS - Bazar (v1, sin nombre aún)

Estructura inicial del proyecto. Multi-tenant: una base de datos SQLite por cliente.

## Carpetas clave
- app/db.py        -> selecciona el .db del cliente logueado (aislamiento entre bazares)
- master.db         -> (se crea luego) registro de clientes/bazares dados de alta
- clients_db/       -> acá viven los .db de cada bazar cliente
  - _template.db    -> (se crea luego) base vacía que se clona al alta de un cliente nuevo

## Roles
- Dueño: acceso total
- Empleado: cobra, ve stock
- Vendedor: solo lectura (precios + stock)

## Próximo paso
Definir modelo de datos (tablas dentro de _template.db)
