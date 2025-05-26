import os

from flask import Blueprint, request, jsonify
from .whatapp import send_message
from models import Client, Tenant
from .ai import open_ai_gpt, classify_intent
from .utils import extract_whatsapp_message, extract_client_phone, is_audio_message, extract_audio_data, download_whatsapp_media, transcribe_audio


main = Blueprint('main', __name__)


@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return handle_verification()

    # Process POST request
    data = request.get_json()
    display_phone_number = data['entry'][0]['changes'][0]['value']['metadata']['display_phone_number']

    # If there are no contacts, just return success
    if 'contacts' not in data['entry'][0]['changes'][0]['value']:
        return jsonify({"status": "success"})

    # Process the message
    return process_whatsapp_message(data, display_phone_number)


def handle_verification():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == os.getenv("WHATSAPP_VERIFY_TOKEN", "default_verify_token"):
        return challenge
    else:
        return jsonify({"status": "error", "message": "Verification failed"}), 403


def process_whatsapp_message(data, display_phone_number):
    profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
    tenant_id = Tenant.get_tenant_id(display_phone_number)
    client_phone_number = extract_client_phone(data)

    try:
        Client.insert_client_data(client_phone_number, profile_name, tenant_id)
    except Exception as e:
        # Log the error but continue processing
        print(f"Error inserting client data: {e}")

    if is_audio_message(data):
        return process_audio_message(data, display_phone_number, client_phone_number, tenant_id)
    else:
        return process_text_message(data, display_phone_number, client_phone_number, tenant_id)


def process_audio_message(data, display_phone_number, client_phone_number, tenant_id):
    audio_data = extract_audio_data(data)
    if not audio_data:
        return jsonify({"status": "success"})

    bytesAudio = download_whatsapp_media(audio_data['id'])
    dataText = transcribe_audio(bytesAudio)
    return generate_and_send_response(dataText, display_phone_number, client_phone_number, tenant_id)


def process_text_message(data, display_phone_number, client_phone_number, tenant_id):
    msg = extract_whatsapp_message(data)
    if not msg:
        return jsonify({"status": "success"})

    return generate_and_send_response(msg, display_phone_number, client_phone_number, tenant_id)


def generate_and_send_response(message_text, display_phone_number, client_phone_number, tenant_id):
    question_type = classify_intent(message_text)
    response_data = open_ai_gpt(message_text, client_phone_number, question_type, tenant_id)

    if response_data and "choices" in response_data:
        response_text = response_data["choices"][0]["message"]["content"]
        print(response_text)

        from .ai import extract_client_info_with_ai
        extract_client_info_with_ai(message_text, client_phone_number, tenant_id)
        extract_client_info_with_ai(response_text, client_phone_number, tenant_id)

        send_message(display_phone_number, client_phone_number, response_text)

    return jsonify({"status": "success"})
