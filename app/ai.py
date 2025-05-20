import requests
import os
import json

from sqlalchemy.sql.coercions import expect

api_key = os.getenv("OPEN_AI_API_KEY")

def open_ai_gpt(message):
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",  # You can change this to another model like "gpt-4o" if needed
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant, response with short, clear, direct to the point answer."
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        return response_data
    except requests.exceptions.RequestException as e:
        print(">>> Exception while checking if message is a question: ", e)
        return False



