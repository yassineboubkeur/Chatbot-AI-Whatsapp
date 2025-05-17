from flask import Blueprint, request, jsonify
"""from .whatapp import send_message"""
from .telegram import send_message
from .ai import is_question, extract_product
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


@main.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    msg = data['message']['text']
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
        send_message(sender, response)

    return jsonify({"status": "success"})


@main.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()

    if 'message' in data and 'text' in data['message']:
        msg = data['message']['text']
        chat_id = data['message']['chat']['id']

        """if not validate_message(msg):
            return jsonify({"status": "Invalid Input"}), 400"""
        if not is_question(msg):
            """send_message(chat_id, "Please ask questions about Products")
            return jsonify({"status": "Success"})"""

        product_name = extract_product(msg)
        product = query_product(product_name)
        print(product)
        if not product:
            send_message(chat_id, "Sorry no product found")
        else:
            response = format_response(product)
            send_message(chat_id, response)
    return jsonify({"status": "success"})
