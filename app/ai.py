import requests
import os
import json

from sqlalchemy.sql.coercions import expect

api_key = os.getenv("GEMENI_AI_API_KEY")

def is_question(message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{
                "text": f"'{message}'"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        return response_data
    except requests.exceptions.RequestException as e:
        print(">>> Exception while checking if message is a question: ", e)
        return False


