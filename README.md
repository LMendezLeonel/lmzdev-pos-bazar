# Sistema POS para bazares

Sistema de punto de venta y control de stock pensado para bazares y comercios chicos de Argentina. Funciona como **SaaS multi-tenant**: una sola aplicación atiende a varios comercios, y cada uno tiene su propia base de datos aislada.

Desarrollado por **LMZ Dev** (Oberá, Misiones). Está en producción con su primer cliente real.

## Qué hace

| Módulo | Descripción |
|---|---|
| **Punto de venta** | Cobro rápido con lector de código de barras (o búsqueda por nombre), carrito, promociones, medios de pago, vuelto y ticket interno imprimible (térmica 80 mm). |
| **Stock y precios** | Alta, edición y baja de productos, categorías propias de cada comercio, alertas de stock bajo, imagen del producto y etiquetas con código de barras (impresora de etiquetas). |
| **Cuotas** | Cada producto muestra cuánto sale en cuotas: entrega del 50 %, el resto con 80 % de interés en 3 cuotas. Los valores se configuran en `config.py`. |
| **Caja** | Apertura y cierre de caja, con el detalle de ventas del turno. |
| **Promociones** | Alta, edición y baja de promociones aplicables en la venta. |
| **Reportes** | Ventas y stock, con exportación a Excel y PDF. |
| **Control** | Panel con métricas y gráficos del negocio. |
| **Notas** | Anotaciones internas del comercio. |
| **Usuarios** | Gestión de usuarios y roles de cada comercio. |
| **Panel de administración** | Acceso del dueño del sistema para dar de alta comercios nuevos. |

### Roles

- **Dueño:** acceso total (productos, usuarios, reportes, caja, control).
- **Empleado:** cobra, consulta stock, maneja caja y notas.
- **Vendedor:** solo lectura. Ve la lista de precios y stock con fotos y cuotas, y puede descargar la lista en Excel o PDF (sin costos).

## Arquitectura multi-tenant

```
master.db                  registro de los comercios dados de alta
clients_db/
  _template.db             base vacía que se clona al dar de alta un comercio
  <comercio>.db            base propia de cada comercio
uploads/<comercio>/        imágenes de productos, separadas por comercio
```

- Al iniciar sesión se ingresa el **código de negocio**, el usuario y la contraseña. El código elige el `.db` del comercio y queda guardado en la sesión (`app/db.py`).
- Todas las consultas se hacen sobre la base del comercio logueado, por lo que un comercio nunca ve datos de otro.
- Las bases existentes se actualizan solas al arrancar (migraciones livianas e idempotentes).
- Los datos viven en `DATA_DIR`, separados del código, para poder actualizar la app sin tocarlos.

## Stack

- Python 3 + **Flask** (blueprints, plantillas Jinja)
- **SQLite** (una base por comercio)
- Flask-WTF (protección CSRF), Pillow (imágenes), openpyxl y fpdf2 (exportaciones)
- Chart.js y JsBarcode en el frontend, HTML/CSS/JS sin framework
- **gunicorn** + nginx con HTTPS en un VPS

## Seguridad

- Contraseñas con hash; protección CSRF en todos los formularios.
- Límite de intentos de login por IP.
- Cookies de sesión `HttpOnly`, `SameSite=Lax` y `Secure` en producción.
- Defensa contra path traversal en los nombres de base y de archivos.
- Las imágenes se validan con Pillow, se reprocesan y solo se sirven a usuarios logueados del mismo comercio.
- Las claves se leen de variables de entorno, nunca del repositorio.

## Correrlo en local

```bash
git clone https://github.com/LMendezLeonel/lmzdev-pos-bazar.git
cd lmzdev-pos-bazar
python -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abrir <http://127.0.0.1:5000>. Al primer arranque se crean `master.db` y `clients_db/_template.db` automáticamente.

Para crear el primer comercio, entrar a `/admin/login` con la clave de superadministrador (en local, sin configurar nada, es la que figura por defecto en `config.py`; **solo sirve para desarrollo**) y dar de alta un comercio con su usuario Dueño.

## Variables de entorno (producción)

| Variable | Para qué |
|---|---|
| `SECRET_KEY` | Firma de las sesiones. Obligatoria en producción, larga y aleatoria. |
| `SUPERADMIN_PASSWORD` | Clave del panel `/admin`. Obligatoria en producción. |
| `SESSION_COOKIE_SECURE` | `1` cuando se sirve por HTTPS. |
| `DATA_DIR` | Carpeta donde viven las bases y las imágenes (opcional). |
| `FLASK_DEBUG` | `1` solo en desarrollo. |

## Estructura

```
app/
  auth/  pos/  stock/  caja/  promociones/
  reportes/  control/  notas/  usuarios/  admin/
  db.py              conexión por comercio y migraciones
  productos_util.py  imágenes y cálculo de cuotas
  rate_limit.py      límite de intentos de login
  templates/  static/
config.py            configuración
schema.sql           esquema de cada comercio
master_schema.sql    esquema del registro de comercios
run.py               punto de entrada
```
