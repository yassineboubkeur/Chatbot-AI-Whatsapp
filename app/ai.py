import requests
import os
import json
from app import db
from flask import session

from config import OPENAI_API_KEY

api_key = os.getenv("OPEN_AI_API_KEY")

def open_ai_gpt(message, client_phone=None, question_type=None, tenant_id=None):

    # TODO : User message should be embedded  FUNCTION => get_embedding
    # TODO : We should Classify the question type FUNCTION => classify_intent
    # TODO : based on the question type we should search for the product or service or general , the Search will be done using the embedding FUNCTION => search_products_by_embedding or search_services_by_embedding

    messages = context_memory(client_phone, {"role": "user", "content": message})

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
        context_memory(client_phone, {"role": "assistant", "content": ai_response})

        return response_data
    except requests.exceptions.RequestException as e:
        print(">>> Exception while checking if message is a question: ", e)
        return False

# TODO: BUG HERE the Session ID is Changing between requests , which is not expected
# TODO: I need to Setup Redis Database to manage the Context memory
def context_memory(client_phone, message):
    from flask import session

    # Debug: Print session ID to see if it's changing between requests
    print(f"Session ID: {session.sid if hasattr(session, 'sid') else id(session)}")

    # Initialize conversation if it doesn't exist
    if 'conversation' not in session:
        print("Creating new conversation in session")
        session['conversation'] = []
    else:
        print(f"Existing conversation found with {len(session['conversation'])} messages")

    # Add the new message
    session['conversation'].append(message)
    print(f"Added message. Conversation length: {len(session['conversation'])}")

    # Limit conversation size
    if len(session['conversation']) > 50:
        session['conversation'].pop(0)
        print("Removed oldest message")

    # Create complete context
    complete_context = [
        {
            "role": "system",
            "content": "You are a helpful assistant, response with short, clear, direct to the point answer."
        }
    ]

    # Add conversation history
    complete_context.extend(session['conversation'])

    # Force session persistence - CRITICAL!
    session.modified = True

    # Debug: Print the actual messages to verify
    print(f"Complete context: {complete_context}")

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
