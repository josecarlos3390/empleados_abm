empleados_abm/
│
├── app.py                      # Crea la app y registra los blueprints
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuración Flask, DB, rutas
│   └── constants.py             # Listas y parámetros fijos
│
├── db/
│   ├── __init__.py
│   ├── connection.py            # Clase Database con pool
│   ├── usuarios.py              # CRUD de usuarios
│   └── empleados.py             # CRUD de empleados
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py           # Login / logout
│   ├── empleados_routes.py      # Rutas de empleados
│   └── usuarios_routes.py       # Rutas de usuarios
│
├── utils/
│   ├── __init__.py
│   ├── validators.py            # validaciones comunes
│   ├── excel_utils.py           # generación de Excel
│   └── security.py              # helpers de autenticación / roles
│
├── static/
│   └── css/
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── empleados/
│   │   ├── list.html
│   │   ├── edit.html
│   │   └── add.html
│   └── usuarios/
│       ├── list.html
│       ├── edit.html
│       └── add.html
│
└── requirements.txt




Para resetear la numeracion

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE empleados_anexos;
TRUNCATE TABLE empleados;
SET FOREIGN_KEY_CHECKS = 1;