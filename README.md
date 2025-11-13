Url page:

https://petcare-r8tf.onrender.com


# 🐾 PetCare - Sistema de Gestión Veterinaria

![PetCare Banner](https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?w=1200&h=300&fit=crop)

Sistema integral de gestión para clínicas veterinarias desarrollado con Django y MongoDB, con diseño responsivo dark-themed y sistema de pagos integrado.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Roles y Permisos](#-roles-y-permisos)
- [Autor](#-autor)

---

## ✨ Características

### 🎯 Funcionalidades Principales

#### **Gestión de Usuarios**
- ✅ Sistema de autenticación con roles (Administrador, Veterinario, Cliente)
- ✅ Registro de usuarios con validación de datos
- ✅ Gestión completa de perfiles de usuario
- ✅ Control de acceso basado en roles

#### **Gestión de Mascotas (Pacientes)**
- ✅ Registro completo de mascotas con especies y razas
- ✅ Historial médico de cada mascota
- ✅ Asociación de mascotas con dueños
- ✅ Búsqueda y filtrado avanzado

#### **Sistema de Citas**
- ✅ Programación de citas con selección de veterinario
- ✅ Calendario interactivo con disponibilidad
- ✅ Estados de citas (Pendiente, Completada, Cancelada, Pendiente de Pago)
- ✅ Observaciones médicas por parte de veterinarios
- ✅ Notificaciones de citas próximas

#### **Sistema de Pagos**
- ✅ Integración de pagos demo
- ✅ Gestión de pagos pendientes
- ✅ Estados de pago (Aprobado, Pendiente, Rechazado)
- ✅ Historial de transacciones
- ✅ Referencias de pago únicas

#### **Dashboard Interactivo**
- ✅ Estadísticas en tiempo real
- ✅ Gráficos y visualizaciones
- ✅ Dashboard personalizado por rol
- ✅ Top 5 especies de mascotas
- ✅ Ranking de veterinarios
- ✅ Distribución de usuarios

#### **Diseño y UX**
- ✅ Interfaz dark-themed moderna
- ✅ Diseño 100% responsivo (móvil, tablet, desktop)
- ✅ Colores principales: Olive Green (#6B8E23, #556B2F)
- ✅ Animaciones y transiciones suaves
- ✅ Iconos Font Awesome
- ✅ Tailwind CSS para estilos

---

## 🛠️ Tecnologías

### Backend
- **Django 5.2.7** - Framework web de Python
- **PyMongo** - Driver de MongoDB para Python
- **Python 3.13.7** - Lenguaje de programación

### Base de Datos
- **MongoDB** - Base de datos NoSQL

### Frontend
- **HTML5** - Estructura
- **Tailwind CSS** - Estilos y diseño responsivo
- **JavaScript** - Interactividad
- **Font Awesome 6.5.1** - Iconografía

---

## 📦 Requisitos Previos

Antes de instalar el proyecto, asegúrate de tener instalado:

- **Python 3.13+**
- **MongoDB 4.0+**
- **pip** (gestor de paquetes de Python)
- **Git**

---

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/petcare.git
cd petcare
```

### 2. Crear Entorno Virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install django pymongo
```

### 4. Configurar MongoDB

Asegúrate de que MongoDB esté corriendo:

```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

---

## ⚙️ Configuración

### 1. Configurar Base de Datos

Edita `Hello/settings.py` y configura tu conexión a MongoDB:

```python
# Configuración de MongoDB
MONGO_URI = "aqui pones tu conexion de mongodb"
MONGO_DB_NAME = "Clinica_Veterinaria"
```

### 2. Estructura de MongoDB

El sistema creará automáticamente las siguientes colecciones:

- `users` - Usuarios del sistema
- `pacientes` - Mascotas registradas
- `citas` - Citas programadas
- `historia_clinica` - Historias clinicas

---

## 💻 Uso

### 1. Iniciar el Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000/`

### 2. Acceder al Sistema

Accede a `/registro` para crear tu primer usuario o usa usuarios de prueba.

---

# 📁 ESTRUCTURA DEL PROYECTO PETCARE

```
petcare/
│
├── 📁 Hello/                              # Configuración principal de Django
│   ├── 📁 __pycache__/
│   ├── 📄 __init__.py
│   ├── 📄 asgi.py
│   ├── 📄 settings.py                     # Configuración de Django
│   ├── 📄 urls.py                         # URLs principales
│   └── 📄 wsgi.py
│
├── 📁 home/                               # Aplicación principal
│   │
│   ├── 📁 __pycache__/
│   │
│   ├── 📁 migrations/                     # Migraciones de Django
│   │   └── 📄 __init__.py
│   │
│   ├── 📁 static/                         # Archivos estáticos
│   │   └── 📁 uploads/                    # Imágenes subidas por usuarios
│   │       └── (archivos de usuarios)
│   │
│   ├── 📁 templates/                      # Templates HTML
│   │   │
│   │   ├── 📁 payments/                   # Templates de pagos
│   │   │   ├── 📄 complete_payment.html   # Completar pago pendiente
│   │   │   ├── 📄 payment_demo.html       # Demo de pasarela de pago
│   │   │   ├── 📄 payment_failure.html    # Pago fallido
│   │   │   ├── 📄 payment_form.html       # Formulario de pago
│   │   │   ├── 📄 payment_pending.html    # Pago pendiente
│   │   │   └── 📄 payment_success.html    # Pago exitoso
│   │   │
│   │   ├── 📄 admin_users_form.html       # Formulario admin usuarios
│   │   ├── 📄 admin_users_list.html       # Lista de usuarios (admin)
│   │   ├── 📄 admin_users_reset.html      # Reset password admin
│   │   ├── 📄 appointments_form.html      # Formulario de citas
│   │   ├── 📄 appointments_list.html      # Lista de citas
│   │   ├── 📄 base.html                   # Template base
│   │   ├── 📄 edit_profile.html           # Editar perfil usuario
│   │   ├── 📄 index.html                  # Dashboard principal
│   │   ├── 📄 login.html                  # Página de login
│   │   ├── 📄 medical_history_detail.html # Detalle historial médico
│   │   ├── 📄 medical_history_form.html   # Formulario historial médico
│   │   ├── 📄 medical_history_list.html   # Lista historial médico
│   │   ├── 📄 patients_form.html          # Formulario de pacientes/mascotas
│   │   ├── 📄 patients_list.html          # Lista de pacientes/mascotas
│   │   ├── 📄 register.html               # Registro de usuarios
│   │   ├── 📄 reports.html                # Reportes
│   │   ├── 📄 vets_form.html              # Formulario veterinarios
│   │   └── 📄 vets_list.html              # Lista veterinarios
│   │
│   ├── 📄 __init__.py
│   ├── 📄 admin.py                        # Configuración admin Django
│   ├── 📄 apps.py                         # Configuración de la app
│   ├── 📄 context_processors.py           # Procesadores de contexto
│   ├── 📄 db_connection.py                # Conexión a MongoDB
│   ├── 📄 models.py                       # Modelos (si se usan)
│   ├── 📄 tests.py                        # Tests
│   ├── 📄 urls.py                         # URLs de la app
│   └── 📄 views.py                        # Vistas principales
│
├── 📁 .vscode/                            # Configuración VS Code
│   └── 📄 settings.json
│
├── 📁 media/                              # Archivos multimedia (generados)
│   └── 📄 db.sqlite3                      # DB SQLite (si se usa)
│
├── 📄 .env                                # Variables de entorno (NO subir a Git)
├── 📄 .env.example                        # Ejemplo de variables de entorno
├── 📄 .gitignore                          # Archivos ignorados por Git
├── 📄 LICENSE                             # Licencia MIT
├── 📄 manage.py                           # Script de gestión Django
├── 📄 README.md                           # Documentación principal
└── 📄 requirements.txt                    # Dependencias Python
```

---

## 📝 DESCRIPCIÓN DE DIRECTORIOS Y ARCHIVOS CLAVE

### 🔧 **Hello/** - Configuración Django
- `settings.py`: Configuración principal (DB, apps, middleware, etc.)
- `urls.py`: Rutas principales del proyecto
- `wsgi.py` / `asgi.py`: Configuración de servidor

### 🏠 **home/** - Aplicación Principal
Contiene toda la lógica del negocio, vistas, templates y archivos estáticos.

### 🎨 **home/templates/** - Templates HTML
Todos los archivos HTML del proyecto organizados por funcionalidad:
- **Base**: `base.html` (template padre)
- **Auth**: `login.html`, `register.html`
- **Dashboard**: `index.html`
- **Usuarios**: `admin_users_*.html`
- **Pacientes**: `patients_*.html`
- **Citas**: `appointments_*.html`
- **Pagos**: carpeta `payments/`
- **Veterinarios**: `vets_*.html`
- **Historial Médico**: `medical_history_*.html`
- **Perfil**: `edit_profile.html`
- **Reportes**: `reports.html`

### 💾 **home/static/** - Archivos Estáticos
- `uploads/`: Fotos de mascotas y usuarios

### 🐍 **home/*.py** - Archivos Python
- `views.py`: Toda la lógica de las vistas
- `urls.py`: Rutas de la aplicación
- `db_connection.py`: Conexión a MongoDB
- `context_processors.py`: Variables globales en templates
- `admin.py`: Panel de administración Django
- `models.py`: Modelos de datos (opcional)

### 📦 **Archivos de Configuración**
- `.env`: Variables de entorno (secretas)
- `.env.example`: Ejemplo de configuración
- `requirements.txt`: Dependencias Python
- `.gitignore`: Archivos a ignorar en Git
- `README.md`: Documentación completa
- `LICENSE`: Licencia MIT
- `manage.py`: Comandos de Django

---

## 🗂️ ORGANIZACIÓN DE TEMPLATES

### Templates de Pagos (`payments/`)
```
payments/
├── complete_payment.html    → Completar pago pendiente ⏳
├── payment_demo.html        → Simulador de pasarela 🎮
├── payment_failure.html     → Pago rechazado ❌
├── payment_form.html        → Formulario de pago 💳
├── payment_pending.html     → Estado pendiente ⏰
└── payment_success.html     → Pago exitoso ✅
```

### Templates Principales
```
├── base.html                → Template padre (navbar, sidebar)
├── index.html               → Dashboard con estadísticas
├── login.html               → Inicio de sesión
├── register.html            → Registro de usuarios
```

### Templates de Gestión
```
Admin:
├── admin_users_form.html    → Crear/editar usuarios
├── admin_users_list.html    → Lista de usuarios
└── admin_users_reset.html   → Resetear contraseña

Citas:
├── appointments_form.html   → Crear/editar citas
└── appointments_list.html   → Lista de citas

Pacientes:
├── patients_form.html       → Crear/editar mascotas
└── patients_list.html       → Lista de mascotas

Veterinarios:
├── vets_form.html          → Crear/editar veterinarios
└── vets_list.html          → Lista de veterinarios

Historial Médico:
├── medical_history_detail.html  → Ver detalle
├── medical_history_form.html    → Crear/editar
└── medical_history_list.html    → Lista de historiales

Otros:
├── edit_profile.html        → Editar perfil usuario
└── reports.html             → Reportes del sistema
```

---

## 📊 ESTRUCTURA DE MONGODB

### Colecciones en la base de datos:

```
petcare_db/
├── users                    → Usuarios del sistema
│   ├── _id (ObjectId)
│   ├── User (string)
│   ├── nombre (string)
│   ├── email (string)
│   ├── contraseña (hash)
│   └── Rol (string)
│
├── pacientes               → Mascotas
│   ├── _id (ObjectId)
│   ├── nombre (string)
│   ├── especie (string)
│   ├── raza (string)
│   ├── edad (int)
│   ├── peso (float)
│   ├── id_user (string)
│   └── foto (string)
│
└── citas                   → Citas
    ├── _id (ObjectId)
    ├── id_paciente (string)
    ├── id_veterinario (string)
    ├── fecha (string)
    ├── motivo (string)
    ├── estado (string)
    ├── payment_status (string)
    └── observacion (string)
```

---

## 🎯 ARCHIVOS IMPORTANTES POR ROL

### 👨‍💼 Administrador
```
✅ admin_users_*.html
✅ index.html (dashboard completo)
✅ Todos los demás templates
```

### 👨‍⚕️ Veterinario
```
✅ appointments_list.html
✅ patients_list.html
✅ medical_history_*.html
✅ index.html (dashboard veterinario)
```

### 👤 Cliente
```
✅ appointments_list.html (solo sus citas)
✅ patients_list.html (solo sus mascotas)
✅ payments/* (pagos)
✅ index.html (dashboard cliente)
```

---

## 📋 CHECKLIST DE ARCHIVOS NECESARIOS

### ✅ Archivos Base del Proyecto
- [x] `manage.py`
- [x] `requirements.txt`
- [x] `.env.example`
- [x] `.gitignore`
- [x] `README.md`
- [x] `LICENSE`

### ✅ Configuración Django
- [x] `Hello/settings.py`
- [x] `Hello/urls.py`
- [x] `Hello/wsgi.py`

### ✅ Aplicación Home
- [x] `home/views.py`
- [x] `home/urls.py`
- [x] `home/db_connection.py`
- [x] `home/context_processors.py`

### ✅ Templates Esenciales
- [x] `base.html`
- [x] `index.html`
- [x] `login.html`
- [x] `register.html`
- [x] `appointments_list.html`
- [x] `patients_list.html`
- [x] `payments/*` (todos)

---

Esta es la estructura completa y organizada de tu proyecto PetCare! 🐾✨
```



---

## 👥 Roles y Permisos

### 🔴 Administrador
- ✅ Acceso completo al sistema
- ✅ Gestión de usuarios (crear, editar, eliminar)
- ✅ Gestión de veterinarios
- ✅ Gestión de mascotas
- ✅ Gestión de citas
- ✅ Visualización de estadísticas completas
- ✅ Dashboard con métricas del sistema

### 🟣 Veterinario
- ✅ Ver citas asignadas
- ✅ Agregar observaciones médicas
- ✅ Ver información de mascotas
- ✅ Dashboard con sus estadísticas
- ✅ Gestionar su disponibilidad
- ❌ No puede eliminar usuarios
- ❌ No puede eliminar mascotas

### 🔵 Cliente
- ✅ Registrar mascotas propias
- ✅ Programar citas
- ✅ Ver sus citas
- ✅ Realizar pagos
- ✅ Completar pagos pendientes
- ✅ Ver observaciones médicas
- ✅ Dashboard personal
- ❌ No puede ver otras mascotas
- ❌ No puede modificar datos de veterinarios

---

## 📝 Endpoints Principales

### Autenticación
- `GET /login` - Página de login
- `POST /login` - Procesar login
- `GET /logout` - Cerrar sesión
- `GET /registro` - Página de registro
- `POST /registro` - Procesar registro

### Usuarios
- `GET /users/` - Listar usuarios
- `GET /users/add/` - Formulario nuevo usuario
- `POST /users/add/` - Crear usuario
- `GET /users/edit/<id>/` - Editar usuario
- `POST /users/edit/<id>/` - Actualizar usuario
- `GET /users/delete/<id>/` - Eliminar usuario

### Mascotas
- `GET /mascotas/` - Listar mascotas
- `GET /mascotas/add/` - Formulario nueva mascota
- `POST /mascotas/add/` - Crear mascota
- `GET /mascotas/edit/<id>/` - Editar mascota
- `GET /mascotas/delete/<id>/` - Eliminar mascota

### Citas
- `GET /citas/` - Listar citas
- `GET /citas/add/` - Formulario nueva cita
- `POST /citas/add/` - Crear cita
- `GET /citas/edit/<id>/` - Editar cita
- `GET /citas/cancel/<id>/` - Cancelar cita
- `POST /citas/add-observation/<id>/` - Agregar observación

### Pagos
- `POST /pagos/demo/` - Procesar pago demo
- `GET /pagos/completar/<id>/` - Página completar pago pendiente
- `POST /pagos/procesar/<id>/` - Procesar pago pendiente

---

## 🎨 Paleta de Colores

```css
/* Colores Principales */
--olive-500: #6B8E23;      /* Olive Green Principal */
--olive-600: #556B2F;      /* Olive Green Oscuro */
--olive-700: #4A5F28;      /* Olive Green Más Oscuro */

/* Colores de Fondo (Dark Theme) */
--dark-900: #0F1419;       /* Fondo Principal */
--dark-800: #1A1F26;       /* Fondo Secundario */
--dark-700: #252B33;       /* Fondo Terciario */

/* Colores de Estado */
--success: #10B981;        /* Verde - Completado */
--warning: #F59E0B;        /* Amarillo - Pendiente */
--error: #EF4444;          /* Rojo - Cancelado/Error */
--info: #3B82F6;           /* Azul - Información */
```

---

## 🔮 Roadmap

### Versión 2.0 (Planificado)
- [ ] Sistema de notificaciones por email/SMS
- [ ] Integración con pasarela de pago real (Stripe/PayU)
- [ ] Generación de reportes PDF
- [ ] Sistema de inventario de medicamentos
- [ ] Historial médico detallado con imágenes
- [ ] Calendario compartido entre veterinarios
- [ ] App móvil (React Native)
- [ ] API REST para integraciones

### Versión 1.5 (Completado)
- [x] Sistema de pagos pendientes ✅
- [x] Dashboard responsivo ✅
- [x] Observaciones médicas ✅
- [x] Gestión completa de citas ✅

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

```
MIT License

Copyright (c) 2025 PIZZO

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👨‍💻 Autores

**Pizzeto y Sofia**
- Desarrolladores Full Stack
- Especializado en Django y MongoDB
- La Virginia-Risaralda y Cartago-Valle del Cauca, Colombia 🇨🇴

---

## 🙏 Agradecimientos

- **Django Community** - Por el excelente framework
- **MongoDB** - Por la base de datos flexible
- **Tailwind CSS** - Por el sistema de diseño
- **Font Awesome** - Por los iconos
- **Unsplash** - Por las imágenes de stock

---

## 🌟 Características Destacadas

### 💡 Sistema de Observaciones Médicas
Los veterinarios pueden agregar observaciones detalladas a cada cita, creando un historial médico completo.

### 💳 Pagos Flexibles
Sistema de pagos con estados pendientes, permitiendo a los clientes completar pagos posteriormente.

### 📱 100% Responsivo
Diseño que se adapta perfectamente a cualquier dispositivo, desde móviles hasta pantallas 4K.

### 🎨 Diseño Moderno
Interfaz dark-themed profesional con colores olive green que transmiten confianza y naturaleza.

### 🔒 Seguridad
Sistema de autenticación robusto con control de acceso basado en roles.

---

<div align="center">

**Desarrollado con amor❤️ y cariño🐾 por pizzeto y sofi**

**PetCare - Cuidando a tus mascotas con tecnología** 🐶🐱

[⬆ Volver arriba](#-petcare---sistema-de-gestión-veterinaria)

</div>
