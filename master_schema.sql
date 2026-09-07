-- master_schema.sql
-- Esta es TU base (la del dueño del sistema, no la de cada bazar cliente).
-- Registra qué clientes existen y a qué archivo .db corresponde cada uno.

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_bazar TEXT NOT NULL,
    db_filename TEXT NOT NULL UNIQUE,   -- ej: 'donpepe.db'
    usuario_admin TEXT NOT NULL UNIQUE, -- login que identifica al cliente (el del Dueño)
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_alta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
