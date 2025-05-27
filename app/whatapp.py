import requests
from models.tenant import Tenant
from .log_config import logger



def mask_identifier(identifier):
    """
    Masks the given identifier (e.g., phone number) by showing the first 6 characters
    and replacing the rest with asterisks. Handles edge cases for short strings.
    """
    if len(identifier) <= 6:
        return identifier + "******"
    return identifier[:6] + "******"

def extract_client_access_token(phone):
    logger.info("Extracting client access token for phone: ", extra={
        "phone": mask_identifier(phone)
    })

    tenantObj = Tenant.query.filter_by(phone_number=phone).first()
    if tenantObj:
        logger.info("Tenant found for phone: ", extra={
            "tenant_id": tenantObj.id,
        })
        whatsapp_token = tenantObj.whatsapp_token
        phone_number_id = tenantObj.phone_number_id
        tenant_id = tenantObj.id
    else:
        logger.warning("Tenant not found for phone: ", extra={
            "phone": phone[:6] + "******"
        })
        whatsapp_token = None
        phone_number_id = None
        tenant_id = None
    return tenant_id, whatsapp_token, phone_number_id


def send_message(sender, to, message):
    logger.info("Sending message to: ", extra={
        "to": to[:6] + "******",
        "sender": sender[:6] + "******"
    })

    TENANT_ID, WHATSAPP_TOKEN, PHONE_NUMBER_ID =  extract_client_access_token(sender)

    url  = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Message sent successfully", extra={
            "to": to[:6] + "******",
        })
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Error sending message", extra={
            "error": str(e)
        })
        return False
