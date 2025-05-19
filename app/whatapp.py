import requests
from config import WHATSAPP_TOKEN, PHONE_NUMBER_ID

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
        return False
