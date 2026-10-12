# 📚 Libreta Digital

**Libreta Digital** es una aplicación web desarrollada para mejorar y centralizar la comunicación entre la **institución educativa, docentes, preceptores, alumnos y familias**.

El proyecto busca solucionar problemas relacionados con la comunicación escolar, como avisos que no llegan a tiempo, dificultades para informar ausencias de docentes, actividades, actos, reuniones y otras situaciones importantes de la institución.

---

## 🎯 Objetivo

El objetivo principal de Libreta Digital es crear un medio de comunicación **rápido, organizado y accesible** que permita a los distintos integrantes de la comunidad educativa recibir y consultar información importante desde un mismo lugar.

---

## 👥 Usuarios

La aplicación contempla diferentes tipos de usuarios:

* 👨‍🎓 **Alumnos**
* 👩‍🏫 **Docentes**
* 🧑‍💼 **Preceptores**
* 👨‍👩‍👧 **Familias**

Cada tipo de usuario tendrá acceso a diferentes funcionalidades según su rol, controlado a través de permisos definidos en el backend.

---

## ⚙️ Funcionalidades principales

### 📢 Comunicaciones

Permite publicar y consultar información importante de la institución, como:

* Avisos generales.
* Comunicados.
* Actividades escolares.
* Actos.
* Reuniones.
* Proyectos.
* Información para alumnos y familias.

### 📝 Asistencias

Permite gestionar información relacionada con:

* Asistencia de alumnos.
* Inasistencias.
* Registro de asistencia.
* Consulta de información por parte de usuarios autorizados.

### 🔔 Notificaciones

El sistema permite informar a los usuarios sobre situaciones importantes, por ejemplo:

* Nuevas comunicaciones.
* Inasistencias.
* Avisos institucionales.
* Cambios o cancelaciones de clases.
* Ausencias de docentes.

### 👤 Usuarios y roles

Cada usuario posee un rol dentro del sistema (`Admin`, `Docente`, `Preceptor`, `Familia`, `Alumno`).

Los permisos y funcionalidades disponibles dependen del rol del usuario autenticado. El backend expone esta información en la respuesta de autenticación para que el frontend adapte la interfaz (menús, rutas, acciones visibles) según corresponda.

### 🔐 Autenticación

El backend expone un sistema de autenticación basado en **tokens** (login / logout / refresh) consumido por el frontend vía API REST, protegiendo el acceso a los distintos endpoints según el rol del usuario.

---

## 🛠️ Tecnologías utilizadas

### Backend (`backend/`)

* **Python**
* **Django**
* **Django REST Framework (DRF)** — expone la lógica de negocio como API REST consumida por el frontend.

Django se utiliza para gestionar usuarios, modelos, autenticación, permisos y la comunicación con la base de datos. DRF se encarga de serializar los datos y exponerlos como endpoints JSON.

### Frontend (`frontend/`)

* **Vue.js**
* **Tailwind CSS**
* **JavaScript**

El frontend es una SPA (Single Page Application) desarrollada en Vue, alojada en un proyecto separado del backend, que consume la API REST de Django para renderizar la interfaz y gestionar la navegación según el rol del usuario autenticado.

### Base de datos

* **PostgreSQL**

PostgreSQL se utiliza para almacenar la información del sistema, como usuarios, alumnos, docentes, comunicaciones, asistencias y notificaciones.

---

## 🏗️ Arquitectura del proyecto

El proyecto está **desacoplado** en dos aplicaciones independientes que se comunican mediante una API REST:

* **`backend/`** → proyecto Django + DRF, expone la API y concentra toda la lógica de negocio, autenticación y permisos.
* **`frontend/`** → proyecto Vue (SPA), consume la API del backend y es responsable únicamente de la presentación.

Dentro del backend, la lógica está dividida en apps de Django según la funcionalidad que cumple cada una:

* `users` → gestión de usuarios, roles, autenticación y permisos (`users/permissions.py`).
* `asistencias` → gestión de asistencias e inasistencias.
* `comunicaciones` → creación y consulta de comunicaciones.
* `notificaciones` → gestión de notificaciones y avisos.

Esta organización permite mantener el proyecto **modular, ordenado y fácil de mantener**, y permite evolucionar backend y frontend de forma independiente (incluso desplegarlos en servidores distintos).

### Flujo de un request

```text
Vue (frontend) --HTTP/JSON--> DRF views/viewsets (backend)
                                   │
                                   ├── users/permissions.py valida rol
                                   │   (permission_classes)
                                   │
                                   └── serializer + queryset filtrado
                                       --JSON--> Vue renderiza
```

La autorización (qué puede ver o hacer cada rol) se resuelve **siempre en el backend**, en `permission_classes` de cada vista/viewset de DRF. El frontend puede ocultar botones o rutas según el rol para mejorar la UX, pero eso es solo cosmético: la validación real ocurre en la API.

---

## 📁 Estructura del proyecto

```text
libreta_digital/
│
├── backend/
│   ├── manage.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── users/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── asistencias/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── comunicaciones/
│   │   └── ... (misma estructura)
│   │
│   ├── notificaciones/
│   │   └── ... (misma estructura)
│   │
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── views/
│   │   ├── router/
│   │   ├── stores/          # manejo de estado (auth, rol, etc.)
│   │   ├── services/        # llamadas a la API del backend
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── .env
│
└── README.md
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd libreta_digital
```

### 2. Backend (Django + DRF)

```bash
cd backend
python -m venv venv
```

Activar el entorno virtual en Windows:

```bash
venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear un archivo `.env` en `backend/`:

```env
SECRET_KEY=tu_clave_secreta
DEBUG=True

DB_NAME=libreta_digital
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> Las variables pueden variar dependiendo de la configuración utilizada en cada entorno.

Crear la base de datos PostgreSQL:

```text
libreta_digital
```

Ejecutar migraciones y crear superusuario:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Levantar el servidor de la API:

```bash
python manage.py runserver
```

La API estará disponible normalmente en:

```text
http://127.0.0.1:8000/
```

### 3. Frontend (Vue)

En otra terminal:

```bash
cd frontend
```

Crear un archivo `.env` en `frontend/`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Instalar dependencias y levantar el servidor de desarrollo:

```bash
npm install
npm run dev
```

El frontend estará disponible normalmente en:

```text
http://localhost:5173/
```

> Backend y frontend corren como dos procesos independientes durante el desarrollo. En producción pueden desplegarse en servidores/dominios distintos, siempre que el backend tenga configurado CORS para aceptar el origen del frontend.

---

## 📦 Dependencias

### Backend

Las principales dependencias se encuentran en `backend/requirements.txt`.

```text
Django
djangorestframework
django-cors-headers
psycopg
python-dotenv
```

### Frontend

Las principales dependencias se encuentran en `frontend/package.json`.

```text
vue
vue-router
pinia
tailwindcss
axios
```

Las versiones pueden variar durante el desarrollo.

---

## 🔐 Seguridad

El proyecto utiliza diferentes mecanismos para proteger la información:

* Autenticación basada en tokens, validada en cada request a la API.
* Control de acceso según el rol del usuario, resuelto en el backend (`permission_classes` de DRF).
* CORS configurado explícitamente para aceptar únicamente el origen del frontend autorizado.
* Variables de entorno separadas para backend y frontend, ninguna subida al repositorio.
* Protección de las credenciales de la base de datos.
* Uso de `.gitignore` para evitar subir archivos sensibles al repositorio.

Los archivos `.env` **no deben subirse a GitHub**.

---

## 📊 Base de datos

PostgreSQL almacena la información necesaria para el funcionamiento del sistema.

Entre las principales entidades se encuentran:

* Usuarios.
* Alumnos.
* Docentes.
* Preceptores.
* Asistencias.
* Comunicaciones.
* Notificaciones.

Las relaciones entre estas entidades permiten organizar la información y controlar qué datos puede consultar o modificar cada usuario.

---

## 🧩 Organización del desarrollo

El proyecto se desarrolla de manera modular, separando responsabilidades en dos niveles:

* **Backend / Frontend**: dos proyectos independientes que se comunican por API REST, permitiendo trabajarlos, versionarlos y desplegarlos por separado.
* **Apps de Django** (dentro del backend): separan cada funcionalidad (usuarios, asistencias, comunicaciones, notificaciones) en módulos independientes.

Esto permite:

* Facilitar el mantenimiento.
* Separar responsabilidades.
* Evitar concentrar todo el código en una única aplicación.
* Facilitar futuras modificaciones.
* Permitir agregar nuevas funcionalidades (incluso una futura app móvil) sin modificar la lógica del backend.

---

## 🔮 Futuras mejoras

Algunas funcionalidades que podrían incorporarse en futuras versiones son:

* 📱 Aplicación móvil (consumiendo la misma API REST del backend).
* 📩 Notificaciones mediante correo electrónico.
* 🔔 Notificaciones push.
* 📅 Calendario escolar.
* 📊 Estadísticas de asistencia.
* 📎 Envío de archivos y documentos.
* 💬 Sistema de mensajería.
* 👨‍👩‍👧 Vinculación entre alumnos y familiares.
* 🏫 Gestión de diferentes instituciones educativas.

---

## 👨‍💻 Proyecto

**Libreta Digital**
Proyecto escolar desarrollado por estudiantes de la **Escuela Técnica Nº 2 de Tandil**.

### Tecnologías

```text
Python
Django
Django REST Framework
Vue.js
Tailwind CSS
PostgreSQL
JavaScript
```

---

## 📄 Licencia

Este proyecto fue desarrollado con fines educativos.