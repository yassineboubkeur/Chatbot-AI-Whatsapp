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

    requests.post(url, json=payload, headers=headers)
