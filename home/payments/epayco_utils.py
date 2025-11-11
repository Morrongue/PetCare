# payments/epayco_utils.py
import time
import hashlib
from datetime import datetime
from django.conf import settings
from bson import ObjectId

# Importar las colecciones de MongoDB
# Asegúrate de importar desde tu módulo correcto
# from tu_app.mongodb_config import payments, citas, pacientes, users

def generate_payment_reference(paciente_id):
    """
    Genera una referencia única para el pago
    Formato: CITA-{paciente_id}-{timestamp}
    """
    timestamp = int(time.time())
    return f"CITA-{paciente_id}-{timestamp}"


def save_pending_payment(payments_collection, ref_payco, cita_data, user_data, precio):
    """
    Guarda un registro de pago pendiente en MongoDB antes del pago
    
    Args:
        payments_collection: Colección de payments de MongoDB
        ref_payco: Referencia única del pago
        cita_data: dict con id_user, id_paciente, id_veterinario, fecha, motivo, duracion
        user_data: dict con email, name, phone, doc_type, document
        precio: float con el monto a cobrar
    
    Returns:
        str: ID del pago insertado
    """
    payment_doc = {
        "ref_payco": ref_payco,
        "x_transaction_id": None,  # Se llenará cuando se confirme
        "x_response": "Pendiente",
        "amount": precio,
        "currency": "COP",
        "email": user_data["email"],
        "customer_name": user_data["name"],
        "customer_phone": user_data.get("phone", ""),
        "customer_doc_type": user_data.get("doc_type", "CC"),
        "customer_document": user_data.get("document", ""),
        "id_user": cita_data["id_user"],
        "id_paciente": cita_data["id_paciente"],
        "id_veterinario": cita_data["id_veterinario"],
        "fecha_cita": cita_data["fecha"],
        "motivo": cita_data["motivo"],
        "duracion": cita_data.get("duracion", 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    result = payments_collection.insert_one(payment_doc)
    return str(result.inserted_id)


def validate_epayco_signature(data, p_cust_id_cliente, p_key):
    """
    Valida la firma de la transacción recibida de ePayco
    
    Formato: MD5(
        x_cust_id_cliente^
        x_ref_payco^
        x_transaction_id^
        x_amount^
        x_currency_code^
        x_signature_key
    )
    
    Args:
        data: dict con los datos recibidos de ePayco
        p_cust_id_cliente: ID del cliente de ePayco
        p_key: Llave P_KEY de ePayco
    
    Returns:
        bool: True si la firma es válida, False si no
    """
    try:
        signature_string = (
            f"{p_cust_id_cliente}^"
            f"{p_key}^"
            f"{data.get('x_ref_payco')}^"
            f"{data.get('x_transaction_id')}^"
            f"{data.get('x_amount')}^"
            f"{data.get('x_currency_code')}"
        )
        
        calculated_signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        received_signature = data.get('x_signature')
        
        return calculated_signature == received_signature
    except Exception as e:
        print(f"❌ Error validando firma: {e}")
        return False


def create_appointment_from_payment(citas_collection, payments_collection, ref_payco):
    """
    Crea la cita en MongoDB cuando el pago es aceptado
    
    Args:
        citas_collection: Colección de citas de MongoDB
        payments_collection: Colección de payments de MongoDB
        ref_payco: Referencia del pago
    
    Returns:
        str: ID de la cita creada o None si hubo error
    """
    try:
        # Buscar el pago
        payment = payments_collection.find_one({"ref_payco": ref_payco})
        
        if not payment:
            print(f"❌ Pago no encontrado: {ref_payco}")
            return None
        
        # Verificar que no exista ya la cita
        existing = citas_collection.find_one({"ref_payco": ref_payco})
        if existing:
            print(f"✅ Cita ya existe: {ref_payco}")
            return str(existing["_id"])
        
        # Crear la cita
        cita_doc = {
            "id_paciente": payment["id_paciente"],
            "id_veterinario": payment["id_veterinario"],
            "fecha": payment["fecha_cita"],
            "motivo": payment["motivo"],
            "duracion": payment.get("duracion", 1),
            "estado": "Pendiente",
            "payment_id": str(payment["_id"]),
            "payment_status": "paid",
            "payment_amount": payment["amount"],
            "payment_date": payment.get("payment_date", datetime.now().isoformat()),
            "ref_payco": ref_payco,
            "created_at": datetime.now().isoformat(),
            "observacion": "",
            "fecha_observacion": "",
            "veterinario_observacion": ""
        }
        
        result = citas_collection.insert_one(cita_doc)
        print(f"✅ Cita creada exitosamente: {ref_payco}")
        
        return str(result.inserted_id)
    
    except Exception as e:
        print(f"❌ Error creando cita desde pago: {e}")
        return None


def get_appointment_price(motivo):
    """
    Obtiene el precio de una cita según el motivo
    
    Args:
        motivo: str con el motivo de la consulta
    
    Returns:
        int: Precio en COP
    """
    return settings.APPOINTMENT_PRICES.get(
        motivo,
        settings.DEFAULT_APPOINTMENT_PRICE
    )