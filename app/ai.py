import requests
import os
import json

api_key = os.getenv("GEMENI_AI_API_KEY")

def is_question(message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{
                "text": f"Analyze if the following text is a question. Only respond with 'yes' if it's a question or 'no' if it's not a question: '{message}'"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_data = response.json()

            if (response_data.get('candidates')) and (response_data['candidates'][0].get('content'))  and  response_data['candidates'][0]['content'].get('parts'):
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text'].strip().lower()
                return 1 if ai_response == "yes" else 0
        print(f"Exception while calling AI: {response.status_code} - {response.text}")
        return 0
    except Exception as e:
        print(f"Exception while calling AI: {e}")
        return 0




def extract_product(message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{
                "text": f"Extract the product name from the following text: '{message}'"
            }]
        }]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_data = response.json()

            if (response_data.get('candidates')) and (response_data['candidates'][0].get('content')) and response_data['candidates'][0]['content'].get('parts'):
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                return ai_response
        print(f"Exception while calling AI: {response.status_code} - {response.text}")
        return ""
    except Exception as e:
        print(f"Exception while calling AI: {e}")
    return 1


