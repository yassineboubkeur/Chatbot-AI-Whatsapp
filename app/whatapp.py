import requests
from models.tenant import Tenant



def extract_client_access_token(phone):
    tenantObj = Tenant.query.filter_by(phone_number=phone).first()
    if tenantObj:
        whatsapp_token = tenantObj.whatsapp_token
        phone_number_id = tenantObj.phone_number_id
        tenant_id = tenantObj.id
    else:
        whatsapp_token = None
        phone_number_id = None
        tenant_id = None
    return tenant_id, whatsapp_token, phone_number_id


def send_message(sender, to, message):
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
        return True
    except requests.exceptions.RequestException as e:
        print(">>> Exception while sending message: ", e)
        if hasattr(e, 'response') and e.response:
            print(">>> Response: ", e.response.text)
        return False
