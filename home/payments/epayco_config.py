# payments/epayco_config.py
"""
Configuración de ePayco sin SDK
Todo se maneja vía Checkout JavaScript y validación de webhooks
"""

from django.conf import settings

def get_epayco_config():
    """
    Retorna la configuración de ePayco para usar en templates
    """
    return {
        'public_key': settings.EPAYCO_PUBLIC_KEY,
        'test_mode': settings.EPAYCO_TEST_MODE,
        'confirmation_url': settings.EPAYCO_CONFIRMATION_URL,
        'response_url': settings.EPAYCO_RESPONSE_URL,
    }

def get_checkout_config():
    """
    Retorna configuración para el checkout de ePayco
    """
    return {
        'key': settings.EPAYCO_PUBLIC_KEY,
        'test': settings.EPAYCO_TEST_MODE
    }