import requests
from config import WHATSAPP_TOKEN, PHONE_NUMBER_ID
from models.tenant import Tenant



def extract_client_access_token(phone):
    tenantObj = Tenant.query.filter_by(phone=phone).first()
    if tenantObj:
        whatsapp_token = tenantObj.whatsapp_token
        phone_number_id = tenantObj.phone_number_id
    else:
        whatsapp_token = None
        phone_number_id = None
    return whatsapp_token, phone_number_id


# TODO: add from parameter contain the tenant phone number so we can dynamically get his whatsapp token, phone number id
def send_message(to, message):
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
