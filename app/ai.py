from os import abort

import requests
import os
import json

from flask import jsonify

from app import db
from app.utils import extract_whatsapp_message

from config import OPENAI_API_KEY
from .redis_config import CONVERSATION_MAX_LENGTH

api_key = os.getenv("OPEN_AI_API_KEY")

def open_ai_gpt(message, client_phone=None, question_type=None, tenant_id=None):

    # TODO : User message should be embedded  FUNCTION => get_embedding
    # TODO : We should Classify the question type FUNCTION => classify_intent
    # TODO : based on the question type we should search for the product or service or general , the Search will be done using the embedding FUNCTION => search_products_by_embedding or search_services_by_embedding

    embedding = get_embedding(message)

    if not question_type:
        question_type = classify_intent(message)

    print(f"Question Type: {question_type}")
    context_info = ""
    if embedding and tenant_id:
        if question_type == 'service':
            services = search_services_by_embedding(embedding, tenant_id)
            if services:
                context_info = "Relevant Services: \n" + "\n".join(f"- {s.name}: {s.description} {s.price} {s.periode}" for s in services)
    user_content = message
    if context_info:
        user_content = f"User question: {message}\n\nContext information (not visible to user):{context_info}"

    messages = context_memory(client_phone, {"role": "user", "content": user_content}, tenant_id=tenant_id)

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    print(messages)
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()

        # Extract AI response
        ai_response = response_data['choices'][0]['message']['content']

        # Store the AI response in context memory
        context_memory(client_phone, {"role": "assistant", "content": ai_response}, tenant_id=tenant_id)

        return response_data
    except requests.exceptions.RequestException as e:
        print(">>> Exception while checking if message is a question: ", e)
        return None


def context_memory(client_phone, message=None, tenant_id=None):
    from .redis_client import get_conversation, save_conversation

    if not tenant_id or not client_phone:
        print("Tenant ID or Client Phone not found in context_memory function")
        return []

    conversation = get_conversation(tenant_id, client_phone)

    if message:
        conversation.append(message)

        while len(conversation) > CONVERSATION_MAX_LENGTH:
            conversation.pop(0)


        save_conversation(tenant_id, client_phone, conversation)

    complete_context = [
        {
            "role": "system",
            "content": "You are a helpful assistant, response with short, clear, direct to the point answer."
        }
    ]

    complete_context.extend(conversation)

    return complete_context


def get_embedding(text):

    """ Convert the user message into embedding using OpenAI API """

    if  not OPENAI_API_KEY:
        print("OpenAI API key not found in environment variables")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "text-embedding-ada-002",
        "input": text
    }

    try:
        response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding']
    except Exception as e:
        print(">>> Exception while getting embedding: ", {str(e)})
        return None


def classify_intent(message):
    """ Classify the intent of the message into 'product', 'service', or 'general' """
    if not OPENAI_API_KEY:
        print("OpenAI API key not found in environment variables")
        return None
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "Classify the intent of the following message strictly into one of the three categories: 'product', 'service', or 'general'. Return only the category name."
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "max_tokens": 10,
        "temperature": 0
    }


    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(">>> Exception while classifying intent: ", {str(e)})
        return None


def search_products_by_embedding(query_embedding, tenant_id, limit=3):
    """Search for products similar to the query embedding."""
    from models import Product

    return (
        db.session.query(Product)
        .filter(Product.tenant_id == tenant_id)
        .order_by(Product.embedding.op('<=>')(query_embedding))
        .limit(limit)
        .all()
    )


def search_services_by_embedding(query_embedding, tenant_id, limit=3):
    """Search for products similar to the query embedding."""
    from models import Service

    return (
        db.session.query(Service)
        .filter(Service.tenant_id == tenant_id)
        .order_by(Service.embedding.op('<=>')(query_embedding))
        .limit(limit)
        .all()
    )
