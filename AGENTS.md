# AGENTS.md — Guía para agentes de código

> Este documento describe la arquitectura, convenciones y detalles operativos del proyecto `empleados_abm` para que un agente de IA pueda trabajar sobre él sin necesidad de preguntar. La información se basa únicamente en el contenido real del repositorio.

---

## 1. Visión general del proyecto

`empleados_abm` es una aplicación web interna escrita en **Python** con el framework **Flask 3.0.0**. Su propósito es el **control interno de empleados**: registro, edición, eliminación, búsqueda, exportación a Excel, gestión de anexos (archivos adjuntos) y trazabilidad de cambios (historial).

Además incluye un módulo de **gestión de usuarios** con autenticación por sesión y roles (`admin`, `editor`, `viewer`).

La interfaz está en español, los comentarios del código están en español y los documentos del proyecto (incluido este) se mantienen en español.

---

## 2. Stack tecnológico

| Capa | Tecnología | Versión / Detalle |
|------|-----------|-------------------|
| Lenguaje | Python | 3.12 (según bytecode de `__pycache__`) |
| Framework web | Flask | 3.0.0 |
| Servidor WSGI (desarrollo) | Werkzeug | 3.0.1 (`run_simple` + `DispatcherMiddleware`) |
| Plantillas | Jinja2 | 3.1.2 |
| Base de datos | MySQL | Conector `mysql-connector-python` 8.2.0 |
| Pool de conexiones | `mysql.connector.pooling` | Tamaño fijo de 5 conexiones |
| Variables de entorno | `python-dotenv` | 1.0.0 |
| Exportación Excel | `openpyxl` | 3.1.2 |
| Frontend | Bootstrap 5 | CDN (`bootstrap@5.3.2`) + Bootstrap Icons + Google Fonts Inter |
| Estilos propios | `static/css/styles.css` | Tema con color escarlata (`#b30000`) |

No se utiliza `pyproject.toml`, `setup.py`, `package.json` ni ningún otro archivo de configuración de build. Las dependencias están declaradas en `requirements.txt`.

---

## 3. Estructura de directorios y organización del código

```
empleados_abm/
├── app.py                      # Punto de entrada; crea la app Flask y la expone bajo prefijo /sge
├── config/
│   ├── settings.py             # Clase Config: lee variables de entorno (.env)
│   └── constants.py            # Listas desplegables, extensiones permitidas, helpers
├── db/
│   ├── connection.py           # Clase Database con pool de conexiones MySQL
│   ├── empleados.py            # CRUD de empleados + historial + anexos
│   └── usuarios.py             # CRUD de usuarios
├── routes/
│   ├── auth_routes.py          # Login / logout
│   ├── empleados_routes.py     # Rutas de empleados, anexos, exportación e historial
│   └── usuarios_routes.py      # Rutas de usuarios (solo admin)
├── utils/
│   ├── security.py             # Decoradores login_required y admin_required
│   ├── validators.py           # Validaciones comunes
│   └── excel_utils.py          # Generación de archivos Excel
├── static/
│   ├── css/styles.css
│   └── img/logo.png
├── templates/
│   ├── base.html               # Layout principal con navbar, footer, modal confirmación
│   ├── login.html
│   ├── 404.html / 500.html
│   ├── empleados/              # list, edit, add, anexos, historial
│   └── usuarios/               # list, edit, add
├── uploads/                    # Archivos subidos (organizados por empleado_id)
├── logs/                       # stdout.log.txt / stderr.log.txt (logs de ejecución)
├── requirements.txt
├── readme.MD
└── .env                        # Variables de entorno (no versionar)
```

### División funcional

- **`app.py`**: factoría `create_flask_app()` y `create_prefixed_app()`. Expone la aplicación bajo el prefijo `/sge` usando `DispatcherMiddleware`.
- **`config/`**: centraliza configuración y datos estáticos.
- **`db/`**: capa de acceso a datos. No usa ORM; ejecuta SQL directamente con parámetros `%s`.
- **`routes/`**: blueprints de Flask. Contienen la lógica de presentación y control de permisos.
- **`utils/`**: helpers transversales (autenticación, validación, Excel).
- **`templates/`**: vistas Jinja2. Extienden `base.html`.

---

## 4. Configuración y variables de entorno

El archivo `config/settings.py` carga variables desde `.env` mediante `python-dotenv`. Variables reconocidas:

| Variable | Propósito | Valor por defecto |
|----------|-----------|-------------------|
| `SECRET_KEY` | Clave de sesión Flask | `dev_secret` |
| `UPLOAD_FOLDER` | Carpeta de archivos subidos | `uploads` |
| `MAX_CONTENT_LENGTH` | Tamaño máximo de request (bytes) | `10485760` (10 MB) |
| `DB_HOST` | Host de MySQL | `localhost` |
| `DB_PORT` | Puerto de MySQL | `3306` |
| `DB_NAME` | Nombre de la base de datos | `empleados_db` |
| `DB_USER` | Usuario de MySQL | `bagit` |
| `DB_PASSWORD` | Contraseña de MySQL | `bagit!.` |

**Importante**: `.env` contiene credenciales. No debe versionarse ni leerse directamente salvo para depuración controlada.

### Constantes de negocio (`config/constants.py`)

- `MOTIVOS_DESVINCULACION`: lista de 21 motivos posibles de desvinculación laboral.
- `EVALUACIONES_INTERNAS`: lista de evaluaciones (`Grave`, `Negativa`, `Leve`, `Moderado`).
- `MAX_FILE_SIZE`: 10 MB.
- `ALLOWED_EXTENSIONS`: extensiones de archivo permitidas para anexos.
- `allowed_file(filename)`: helper para validar extensiones.

---

## 5. Base de datos

### Conexión (`db/connection.py`)

- Se usa un pool de conexiones `MySQLConnectionPool` de tamaño 5.
- Cursor con `dictionary=True` para obtener resultados como diccionarios.
- Métodos disponibles:
  - `execute_query(query, params)`: INSERT/UPDATE/DELETE; retorna `lastrowid`.
  - `fetch_all(query, params)`: SELECT múltiples filas.
  - `fetch_one(query, params)`: SELECT una fila.
- Se hace `commit`/`rollback` manual en `execute_query`.

### Tablas principales (inferidas del código)

1. **`empleados`** — registros de empleados.
2. **`empleados_historial`** — cambios realizados a un empleado (campo, valor anterior, valor nuevo, usuario, fecha).
3. **`empleados_anexos`** — metadatos de archivos adjuntos.
4. **`usuarios`** — usuarios del sistema (`id`, `nombre`, `username`, `password`, `rol`).

### Nota sobre nombres de tablas

El código referencia `empleados`, `empleados_historial` y `empleados_anexos` directamente. No hay migraciones ni scripts SQL en el repositorio. Para resetear la numeración de tablas se incluye en `readme.MD`:

```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE empleados_anexos;
TRUNCATE TABLE empleados;
SET FOREIGN_KEY_CHECKS = 1;
```

---

## 6. Autenticación y roles

La autenticación es por **sesión de Flask** (`session['user']`).

### Roles

- `admin`: acceso total; puede ver lista completa sin búsqueda, exportar Excel, gestionar usuarios, ver historial y eliminar anexos.
- `editor`: puede crear/editar empleados, buscar y eliminar anexos.
- `viewer` (u otros): solo puede buscar; la lista inicial aparece vacía si no hay término de búsqueda.

### Decoradores (`utils/security.py`)

- `@login_required`: redirige a `auth.login` si no hay sesión.
- `@admin_required`: redirige al listado de empleados si el rol no es `admin`.

Las contraseñas de usuarios se almacenan con `werkzeug.security.generate_password_hash` y se validan con `check_password_hash`.

---

## 7. Funcionalidades principales

### Empleados

- **Listado** (`/`): filtrado por texto libre en todos los campos. Reglas de visibilidad según rol.
- **Agregar** (`/add`): formulario con datos personales, laborales, motivo de desvinculación, evaluación interna y observaciones. Permite adjuntar múltiples archivos.
- **Editar** (`/edit/<id>`): actualiza campos y registra automáticamente cada cambio real en `empleados_historial`.
- **Eliminar** (`/delete/<id>`): elimina registro.
- **Exportar Excel** (`/export`): genera `empleados.xlsx` con el mismo filtro de búsqueda y orden configurable (`order_by`, `order_dir`).
- **Historial** (`/empleado/<id>/historial`): solo admin. Muestra quién cambió qué y cuándo.

### Anexos

- Se almacenan físicamente en `uploads/empleados/<empleado_id>/`.
- Nombre de archivo final: `{empleado_id}_{timestamp}_{nombre_seguro}`.
- Se registran metadatos en `empleados_anexos`.
- Rutas: ver (`/empleados/<id>/anexos`), subir (`/empleados/<id>/anexos/upload`), descargar (`/empleados/anexo/<anexo_id>`), eliminar (`/empleados/anexo/delete/<anexo_id>/<empleado_id>`).

### Usuarios

- Solo administradores (`/usuarios/`).
- CRUD completo: listar, agregar, editar, eliminar.

---

## 8. Cómo ejecutar el proyecto

### Entorno virtual

El repositorio incluye una carpeta `venv/` con el entorno virtual. Para activarlo en Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

### Instalación de dependencias

```powershell
pip install -r requirements.txt
```

### Configuración

Crear/editar `.env` en la raíz con al menos:

```env
SECRET_KEY=una_clave_secreta_segura
DB_HOST=localhost
DB_NAME=empleados_db
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
```

### Ejecutar en desarrollo

```powershell
python app.py
```

El servidor se levanta en:

- `http://0.0.0.0:5000`
- `http://127.0.0.1:5000`

La aplicación responde bajo el prefijo **`/sge`**. La raíz `/sge/` redirige a `/sge/empleados`.

Ejemplo de URLs válidas:

- Login: `http://localhost:5000/sge/auth/login`
- Listado: `http://localhost:5000/sge/`
- Usuarios: `http://localhost:5000/sge/usuarios/`

### Servidor de producción

El código actual usa `run_simple` con `use_reloader=True` y `use_debugger=True`. **No debe usarse en producción**. Se recomienda desplegar la aplicación WSGI resultante de `create_prefixed_app()` detrás de un servidor WSGI productivo (por ejemplo, Gunicorn + reverse proxy o mod_wsgi).

---

## 9. Convenciones de estilo y desarrollo

### Idioma

- Todo el código, comentarios, plantillas e interfaces de usuario están en **español**.
- Nombres de funciones, variables y endpoints también están en español (por ejemplo, `lista_empleados`, `agregar_empleado`, `editar_usuario`).

### Comentarios

- Se usan bloques de comentarios con `=` para separar secciones (ej. `# ============ GET ============`).
- Se incluyen emojis ocasionalmente en comentarios y mensajes de `flash` para distinguir acciones.

### Formato

- No hay linter ni formatter configurado (sin `.flake8`, `.black`, `ruff`, etc.).
- Se prefiere legibilidad sobre compacidad extrema.

### SQL

- No se usa ORM. Las consultas se escriben directamente con placeholders `%s`.
- El módulo `db.connection` centraliza la conexión mediante un singleton `db = Database()`.

### Manejo de fechas

- Las fechas se muestran al usuario en formato **`dd/mm/aaaa`**.
- En Python se convierten con `datetime.strptime(fecha, "%d/%m/%Y").date()`.
- En plantillas se formatean con `.strftime('%d/%m/%Y')`.

### Subida de archivos

- Siempre usar `werkzeug.utils.secure_filename` antes de guardar.
- Los archivos se guardan en subcarpetas por `empleado_id`.
- El registro en base de datos ocurre después de confirmar el tamaño real en disco.

---

## 10. Pruebas

El proyecto **no cuenta actualmente con un framework de pruebas** ni con tests unitarios, de integración ni end-to-end. No existe carpeta `tests/`, ni configuración de `pytest`, ni scripts de testing.

### Recomendación para nuevas pruebas

Si se desea agregar tests, se sugiere:

1. Crear una carpeta `tests/` en la raíz.
2. Instalar `pytest` y `pytest-flask`.
3. Usar una base de datos de prueba separada configurada por variable de entorno.
4. Escribir fixtures para la aplicación Flask y un cliente de pruebas.
5. Cubrir al menos:
   - Autenticación (login exitoso/fallido).
   - CRUD de empleados con cada rol.
   - Subida/descarga/eliminación de anexos.
   - Exportación a Excel.

---

## 11. Consideraciones de seguridad

### Aspectos a tener presentes

1. **Clave secreta por defecto**: `settings.py` define `dev_secret` como fallback. En producción siempre debe establecerse `SECRET_KEY` en `.env`.
2. **Credenciales de base de datos**: están en `.env`. No versionar este archivo.
3. **Debugger activo en desarrollo**: `use_debugger=True` permite ejecución remota de código; desactivar en producción.
4. **Validación de archivos**: `config/constants.py` define extensiones permitidas, pero no hay validación de tipo MIME profundo ni análisis de contenido.
5. **Autorización**: `@admin_required` y `@login_required` manejan permisos, pero algunas rutas (por ejemplo, eliminar empleado) usan `@login_required` sin verificar rol. Revisar si se requiere mayor granularidad.
6. **SQL Injection**: las consultas usan placeholders `%s`, lo cual es seguro. Evitar concatenar strings directamente en SQL.
7. **Path traversal**: el uso de `secure_filename` mitiga el riesgo en nombres de archivo, pero las rutas de upload se construyen con `os.path.join(current_app.root_path, ...)`. Mantener validación de `empleado_id` y `anexo_id`.
8. **Logs**: `logs/stderr.log.txt` y `logs/stdout.log.txt` pueden contener trazas con IPs, datos de formularios o errores. No exponerlos públicamente.

### Buenas prácticas recomendadas

- Forzar HTTPS en producción.
- Configurar `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY` y `SESSION_COOKIE_SAMESITE`.
- Limitar `MAX_CONTENT_LENGTH` según necesidad real.
- Realizar backups periódicos de la base de datos y la carpeta `uploads/`.

---

## 12. Despliegue

No hay scripts de despliegue, Dockerfile, archivo de CI/CD ni configuración de plataforma en la nube. El despliegue es manual.

### Pasos generales sugeridos

1. Clonar/transferir el código al servidor.
2. Crear y activar un entorno virtual Python.
3. Instalar dependencias: `pip install -r requirements.txt`.
4. Crear `.env` con valores de producción.
5. Asegurar que la base de datos MySQL y las tablas existan.
6. Exponer la aplicación WSGI a través de `create_prefixed_app()` usando Gunicorn/uWSGI/mod_wsgi.
7. Colocar un reverse proxy (Nginx/Apache) frente al servidor WSGI, sirviendo bajo `/sge`.
8. Asegurar permisos de escritura para la carpeta `uploads/`.

---

## 13. Notas para el mantenimiento

- **Prefijo `/sge`**: si se cambia, debe actualizarse tanto en `create_prefixed_app()` en `app.py` como en cualquier configuración de reverse proxy.
- **Endpoints legacy**: existen rutas de compatibilidad (`/old_anexos/<id>`, `/legacy/view_anexos/<id>`) que redirigen al listado actual de anexos.
- **Carpetas `__pycache__`**: se generan automáticamente. No es necesario versionarlas.
- **Archivo `mcp.json`**: contiene `"mcpServers": {}` y no parece estar en uso actualmente.
- **`routes/empleados_routes_old2.py`**: archivo obsoleto presente en el repositorio; no está registrado en la aplicación actual.

---

## 14. Contacto y contexto

Este es un sistema interno de control de empleados. Si necesitas modificar comportamiento, prioriza:

1. Mantener la separación actual entre `db/`, `routes/`, `utils/` y `templates/`.
2. Respetar las reglas de visibilidad por rol.
3. Registrar cambios en `empleados_historial` al editar empleados.
4. Guardar archivos adjuntos tanto en disco como en la tabla `empleados_anexos`.
