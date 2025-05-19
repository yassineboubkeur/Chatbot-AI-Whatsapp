import json
import os

from flask import Blueprint, request, jsonify
"""from .whatapp import send_message"""
from .whatapp import send_message
from .ai import is_question
from .utils import extract_whatsapp_message, extract_client_phone
from .product import query_product
from .utils import validate_message, format_response


main = Blueprint('main', __name__)


@main.route('/test-api', methods=['GET'])
def test_api():
    return jsonify(
        {
            "status": "success",
            "message": "Welcome to the WhatApp Bot API"
        }
    )


@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        # You can set a verification token in your .env file
        if mode == 'subscribe' and token == os.getenv("WHATSAPP_VERIFY_TOKEN", "default_verify_token"):
            return challenge
        else:
            return jsonify({"status": "error", "message": "Verification failed"}), 403


    data = request.get_json()
    phone_number = extract_client_phone(data)
    msg = extract_whatsapp_message(data)
    if msg:
        response_data = is_question(msg)
        response_text = response_data['candidates'][0]['content']['parts'][0]['text']
        send_message(phone_number, response_text)
        print(response_text)
        return jsonify({"status": "success"})
    """msg = data['message']['text']
    sender = data['message']['from']

    if not validate_message(msg):
        return jsonify({"status": "Invalid Input"}), 400

    if not is_question(msg):
        send_message(sender, "Please ask questions about Products")
        return jsonify({"status": "Success"})

    product_name = extract_product(msg)
    product = query_product(product_name)

    if not product:
        send_message(sender, "Sorry no product found")
    else:
        response = format_response(product)
        send_message(sender, response)"""

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
