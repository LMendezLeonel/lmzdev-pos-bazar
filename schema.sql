-- schema.sql
-- Esquema base para cada bazar cliente.
-- Este archivo se usa para crear clients_db/_template.db,
-- que luego se clona cada vez que se da de alta un cliente nuevo.

PRAGMA foreign_keys = ON;

-- ===========================
-- USUARIOS
-- ===========================
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('dueño', 'empleado', 'vendedor')),
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- CATEGORIAS
-- ===========================
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- ===========================
-- PRODUCTOS
-- ===========================
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    codigo_barras TEXT UNIQUE,
    categoria_id INTEGER,
    precio_venta REAL NOT NULL DEFAULT 0,
    precio_costo REAL NOT NULL DEFAULT 0,
    stock_actual INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    alertas_activas BOOLEAN NOT NULL DEFAULT 1,
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    imagen TEXT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- ===========================
-- CAJA
-- ===========================
CREATE TABLE caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_apertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    monto_inicial REAL NOT NULL DEFAULT 0,
    monto_final REAL,
    usuario_id INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ===========================
-- PROMOCIONES
-- ===========================
CREATE TABLE promociones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('porcentaje', 'monto_fijo')),
    valor REAL NOT NULL,
    medio_pago TEXT CHECK (medio_pago IN ('efectivo', 'tarjeta', 'transferencia') OR medio_pago IS NULL),
    activa BOOLEAN NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- VENTAS
-- ===========================
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER NOT NULL,
    caja_id INTEGER NOT NULL,
    promocion_id INTEGER,
    subtotal REAL NOT NULL,
    descuento REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL,
    medio_pago TEXT NOT NULL CHECK (medio_pago IN ('efectivo', 'tarjeta', 'transferencia')),
    monto_recibido REAL,
    vuelto REAL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (caja_id) REFERENCES caja(id),
    FOREIGN KEY (promocion_id) REFERENCES promociones(id)
);

-- ===========================
-- DETALLE_VENTA
-- ===========================
CREATE TABLE detalle_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ===========================
-- NOTAS
-- ===========================
CREATE TABLE notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contenido TEXT NOT NULL,
    hecha BOOLEAN NOT NULL DEFAULT 0,
    usuario_id INTEGER,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ===========================
-- INDICES para búsquedas rápidas (clave para que el cobro sea ágil)
-- ===========================
CREATE INDEX idx_productos_codigo_barras ON productos(codigo_barras);
CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_detalle_venta_venta ON detalle_venta(venta_id);
