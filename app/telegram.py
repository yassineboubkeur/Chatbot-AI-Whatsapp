import os

import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_CHAT_ID}:{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response)
