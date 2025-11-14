"""
Django settings for Hello project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ywzcn&pi5q8o^d3ut4d6@3k&1_0kmoq#buh+^itgszi4fz&v5&'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Hello.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'home' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'home.context_processors.user_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'Hello.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
ALLOWED_HOSTS = ['*']  # Temporal

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# EPAYCO CONFIGURATION
# ============================================

# ePayco Credentials (PRODUCCIÓN)
EPAYCO_PUBLIC_KEY = '9b8e606610117c29486dbb2f5301384c'
EPAYCO_PRIVATE_KEY = 'a72fc549fbe48a3db43db76e35e46dcf'
EPAYCO_CUST_ID = '1567292'
EPAYCO_P_KEY = '4a1632e025a043f2eac033b1083f27fcdabe7293'

# Modo (False = Production)
EPAYCO_TEST_MODE = True

# URLs de callback (PRODUCCIÓN - Render)
BASE_URL = 'https://petcare-r8tf.onrender.com'
EPAYCO_CONFIRMATION_URL = f'{BASE_URL}/pagos/confirmacion/'
EPAYCO_RESPONSE_URL = f'{BASE_URL}/pagos/respuesta/'

# Precios por tipo de consulta (en COP)
APPOINTMENT_PRICES = {
    'Consulta general': 50000,
    'Vacunación': 30000,
    'Cirugía': 200000,
    'Emergencia': 100000,
    'Chequeo': 40000,
    'Desparasitación': 25000,
    'Baño y peluquería': 35000,
}
DEFAULT_APPOINTMENT_PRICE = 50000

# Moneda
EPAYCO_CURRENCY = 'COP'

# Información del negocio
BUSINESS_NAME = 'Veterinaria PetCare'
BUSINESS_EMAIL = 'santiagotabina@gmail.com'
BUSINESS_NIT = '900123456-7'  # Cambiar por tu NIT real
BUSINESS_PHONE = '3001234567'  # Cambiar por tu teléfono real
BUSINESS_ADDRESS = 'Calle 123 #45-67'  # Cambiar por tu dirección real
BUSINESS_CITY = 'Bogotá'


# Para producción con Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'santiago.mosquerat@uam.edu.co'
EMAIL_HOST_PASSWORD = 'wmck ltkk odqb nxhv'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
