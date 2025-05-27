import os

from flask import Blueprint, request, jsonify, g
from time import time
from .whatapp import send_message
from models import Client, Tenant
from .ai import open_ai_gpt, classify_intent
from .utils import extract_whatsapp_message, extract_client_phone, is_audio_message, extract_audio_data, download_whatsapp_media, transcribe_audio
from .log_config import logger


main = Blueprint('main', __name__)


@main.before_request
def start_timer():
    g.start = time()
    logger.info(f"Request started", extra={"path": request.path, "method": request.method, "remote_addr": request.remote_addr})


@main.after_request
def log_response(response):
    duration = time() - g.start
    logger.info(f"Request completed", extra={
        "path": request.path,
        "method": request.method,
        "remote_addr": request.remote_addr,
        "status_code": response.status_code,
        "duration": round(duration, 4)
    })
    return response

@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return handle_verification()
    try:
        data = request.get_json()
        if not data or 'entry' not in data or not data['entry']:
            logger.warning("Invalid data received", extra={"data": data})
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        entry = data['entry'][0]
        if 'changes' not in entry or not entry['changes']:
            logger.warning("No changes found in data", extra={"data": data})
            return jsonify({"status": "success"})

        value = entry['changes'][0]['value']
        if 'metadata' not in value or 'display_phone_number' not in value['metadata']:
            logger.warning("Display phone number not found in data", extra={"data": data})
            return jsonify({"status": "error", "message": "Display phone number not found"}), 400

        display_phone_number = data['entry'][0]['changes'][0]['value']['metadata']['display_phone_number']

        if 'contacts' not in value:
            return jsonify({"status": "success"})

        return process_whatsapp_message(data, display_phone_number)
    except Exception as e:
        logger.error("Error processing webhook", extra={"error": str(e), "data": request.get_json()})
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def handle_verification():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.info("Verification request received", extra={"mode": mode, "token": bool(token), "challenge": bool(challenge)})

    if mode == 'subscribe' and token == os.getenv("WHATSAPP_VERIFY_TOKEN", "default_verify_token"):
        logger.info("Webhook Verification successful")
        return challenge
    else:
        logger.warning("Webhook Verification failed", extra={
            "mode": mode,
            "expected_token": os.getenv("WHATSAPP_VERIFY_TOKEN", "default_verify_token")[:10] + "******",
        })
        return jsonify({"status": "error", "message": "Verification failed"}), 403


def process_whatsapp_message(data, display_phone_number):

    try:
        if 'entry' in data and data['entry'] and 'changes' in data['entry'][0] and data['entry'][0]['changes'] and 'value' in data['entry'][0]['changes'][0] and 'contacts' in data['entry'][0]['changes'][0]['value'] and data['entry'][0]['changes'][0]['value']['contacts']:

            profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
        else:
            logger.warning("No profile name found in data", extra={"data": data})
            profile_name = "Unknown"

        tenant_id = Tenant.get_tenant_id(display_phone_number)
        if not tenant_id:
            logger.warning("Tenant ID not found for display phone number", extra={"display_phone_number": display_phone_number})
            return jsonify({"status": "error", "message": "Tenant ID not found for display phone number"}), 404

        client_phone_number = extract_client_phone(data)
        if not client_phone_number:
            logger.warning("Client phone number not found in data", extra={"data": data})
            return jsonify({"status": "error", "message": "Client phone number not found"}), 400

        try:
            Client.insert_client_data(client_phone_number, profile_name, tenant_id)
            logger.info("Client data inserted successfully", extra={"client_phone_number": client_phone_number[:6] + '*****', "profile_name": profile_name, "tenant_id": tenant_id})
        except Exception as e:
            logger.error("Error inserting client data", extra={"error": str(e), "client_phone_number": client_phone_number[:6] + '*****', "profile_name": profile_name, "tenant_id": tenant_id})
            return jsonify({"status": "error", "message": "Internal server error"}), 500

        if is_audio_message(data):
            logger.info("Audio message received", extra={"data": data})
            return process_audio_message(data, display_phone_number, client_phone_number, tenant_id)
        else:
            logger.info("Text message received", extra={"data": data})
            return process_text_message(data, display_phone_number, client_phone_number, tenant_id)

    except Exception as e:
        logger.error("Error processing WhatsApp message", extra={"error": str(e), "data": data})
        return jsonify({"status": "error", "message": "Internal server error"}), 500



def process_audio_message(data, display_phone_number, client_phone_number, tenant_id):
    try:
        audio_data = extract_audio_data(data)
        if not audio_data:
            logger.warning("Audio data not found in data", extra={"data": data})
            return jsonify({"status": "success"})

        logger.info("Audio data extracted successfully", extra={"audio_data": audio_data})

        bytesAudio = download_whatsapp_media(audio_data['id'])
        if not bytesAudio:
            logger.error("Failed to download audio", extra={"media_id": audio_data['id']})
            return jsonify({"status": "error", "message": "Failed to download audio"}), 500

        dataText = transcribe_audio(bytesAudio)
        if not dataText:
            logger.error("Failed to transcribe audio", extra={"media_id": audio_data['id']})
            return jsonify({"status": "error", "message": "Failed to transcribe audio"}), 500
    except Exception as e:
        logger.error("Error processing audio message", extra={"error": str(e), "data": data})
        return jsonify({"status": "error", "message": "Internal server error"}), 500


    return generate_and_send_response(dataText, display_phone_number, client_phone_number, tenant_id)


def process_text_message(data, display_phone_number, client_phone_number, tenant_id):
    try:
        msg = extract_whatsapp_message(data)
        if not msg:
            logger.warning("Message text not found in data", extra={"data": data})
            return jsonify({"status": "success"})
        logger.info("Message text extracted successfully", extra={"message_length": len(msg), "client_phone": client_phone_number[:6] + '*****'})

        return generate_and_send_response(msg, display_phone_number, client_phone_number, tenant_id)
    except Exception as e:
        logger.error("Error processing text message", extra={"error": str(e), "data": data})
        return jsonify({"status": "error", "message": "Internal server error"}), 500



def generate_and_send_response(message_text, display_phone_number, client_phone_number, tenant_id):

    try:
        logger.info("Generating and sending response", extra={"message_text": message_text, "display_phone_number": display_phone_number[:6] + "******", "client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})

        question_type = classify_intent(message_text)

        logger.info("Question classified", extra={
            "question_type": question_type,
            "message_text_length": len(message_text),
            "display_phone_number": display_phone_number[:6] + "******",
            "client_phone_number": client_phone_number[:6] + "******",
            "tenant_id": tenant_id
        })

        response_data = open_ai_gpt(message_text, client_phone_number, question_type, tenant_id)
        if not response_data:
            logger.error("Failed to get response from AI", extra={"client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})
            return jsonify({"status": "error", "message": "Failed to get response from AI"}), 500

        if 'choices' in response_data and response_data['choices']:
            response_text = response_data['choices'][0]['message']['content']
            logger.info("Response generated successfully", extra={"response_text_length": len(response_text), "display_phone_number": display_phone_number[:6] + "******", "client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})

            from .ai import extract_client_info_with_ai
            try:
                extract_client_info_with_ai(message_text, client_phone_number, tenant_id)
                extract_client_info_with_ai(response_text, client_phone_number, tenant_id)
                logger.info("Client info extracted successfully")
            except Exception as e:
                logger.warning("Error extracting client info", extra={"error": str(e)})

            send_result =  send_message(display_phone_number, client_phone_number, response_text)

            if not send_result:
                logger.error("Failed to send response", extra={"display_phone_number": display_phone_number[:6] + "******", "client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})
                return jsonify({"status": "error", "message": "Failed to send response"}), 500
        else:
            logger.error("No response generated", extra={"response_text": response_data, "display_phone_number": display_phone_number[:6] + "******", "client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})
            return jsonify({"status": "error", "message": "No response generated"}), 500

        return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Error generating and sending response", extra={"error": str(e), "message_text": message_text, "display_phone_number": display_phone_number[:6] + "******", "client_phone_number": client_phone_number[:6] + "******", "tenant_id": tenant_id})
        return jsonify({"status": "error", "message": "Internal server error"}), 500
