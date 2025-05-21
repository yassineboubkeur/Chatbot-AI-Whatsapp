import json
import os

from flask import Blueprint, request, jsonify
"""from .whatapp import send_message"""
from .whatapp import send_message
from .client import insert_client_data
from .ai import open_ai_gpt, get_embedding, classify_intent
from .utils import extract_whatsapp_message, extract_client_phone, is_audio_message, extract_audio_data, download_whatsapp_media, transcribe_audio, get_tenant_id
from .product import query_product
from .utils import validate_message, format_response


main = Blueprint('main', __name__)

@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == os.getenv("WHATSAPP_VERIFY_TOKEN", "default_verify_token"):
            return challenge
        else:
            return jsonify({"status": "error", "message": "Verification failed"}), 403


    data = request.get_json()

    display_phone_number = data['entry'][0]['changes'][0]['value']['metadata']['display_phone_number']
    if 'contacts' in data['entry'][0]['changes'][0]['value']:
        profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
        tenant_id = get_tenant_id(display_phone_number)
        client_phone_number = extract_client_phone(data)

        insert_client_data(client_phone_number, profile_name, tenant_id) #TODO: handle Errors Here

        if is_audio_message(data):
            audio_data = extract_audio_data(data)
            if audio_data:
                bytesAudio = download_whatsapp_media(audio_data['id'])
                dataText = transcribe_audio(bytesAudio)
                response_data = open_ai_gpt(dataText)
                ai_answer = response_data["choices"][0]["message"]["content"] if response_data and "choices" in response_data else ""
                send_message(display_phone_number, client_phone_number, ai_answer)
                print(response_data) # TODO: send the Message to Client using his phone number
                return jsonify({"status": "success"})
        else:
            msg = extract_whatsapp_message(data)
            if msg:
                question_type = classify_intent(msg)
                response_data = open_ai_gpt(msg, question_type)
                response_text = response_data["choices"][0]["message"]["content"] if response_data and "choices" in response_data else ""
                print(response_text)
                send_message(display_phone_number, client_phone_number, response_text)
                print(response_text)
                return jsonify({"status": "success"})

    return jsonify({"status": "success"})


"""@main.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    print(data)
    if 'message' in data and 'text' in data['message']:
        msg = data['message']['text']
        chat_id = data['message']['chat']['id']

        if not validate_message(msg):
            return jsonify({"status": "Invalid Input"}), 400
        if not is_question(msg):
            send_message(chat_id, "Please ask questions about Products")
            return jsonify({"status": "Success"})

        product_name = extract_product(msg)
        product = query_product(product_name)
        print(product)
        if not product:
            send_message(chat_id, "Sorry no product found")
        else:
            response = format_response(product)
            send_message(chat_id, response)
    return jsonify({"status": "success"})"""
