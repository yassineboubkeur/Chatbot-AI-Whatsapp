from os import abort

import requests
import os
import json

from app import db

from config import OPENAI_API_KEY
from models import Client, TenantInfo, Service, Product
from .redis_config import CONVERSATION_MAX_LENGTH
from .log_config import logger

api_key = os.getenv("OPEN_AI_API_KEY")

def open_ai_gpt(message, client_phone=None, question_type=None, tenant_id=None):

    logger.info("Processing message for the client", extra={
        "message": message,
        "client_phone": client_phone[:6] + "******" ,
        "question_type": question_type,
        "tenant_id": tenant_id
    })

    embedding = get_embedding(message)
    if not embedding:
        logger.warning("Embedding not found for the message")

    if not question_type:
        logger.debug("Question type not provided, checking if message is a question")
        question_type = classify_intent(message)
        logger.info("Classified intent as", extra={"question_type": question_type})

    context_info = ""
    if embedding and tenant_id:
        logger.debug("Getting context info for question type", extra={"question_type": question_type})
        if question_type == 'service':
            services = Service.search_services_by_embedding(embedding, tenant_id)
            if services:
                logger.info("Found relevant services", extra={"services_length": len(services)})
                context_info = "Relevant Services: \n" + "\n".join(f"- {s.name}: {s.description} {s.price} DH {s.periode}" for s in services)
        if question_type == 'product':
            products = Product.search_products_by_embedding(embedding, tenant_id)
            if products:
                logger.info("Found relevant Products", extra={"product_length": len(products)})
                context_info = "Relevant Products: \n" + "\n".join(f"- {p.name}: {p.description} {p.price} {p.periode}" for p in products)
        if question_type == 'general':
            logger.info("Found tenant information for tenant ID", extra={"tenant_id": tenant_id})
            tenant_info = TenantInfo.get_tenant_information(embedding, tenant_id)
            context_info = f"Tenant Information: \n" + "\n".join(f"- we are {t.name}, we are in {t.address}{t.city}, this Our mail address {t.email} if you want to call us this is our phone {t.phone_number}" for t in tenant_info)
    user_content = message
    if context_info:
        logger.debug("User content with context info", extra={"user_content": user_content})
        user_content = f"User question: {message}\n\nContext information (not visible to user):{context_info}"

    messages = context_memory(client_phone, {"role": "user", "content": user_content}, tenant_id=tenant_id)

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }

    try:
        logger.info("Making API request to OpenAI GPT for AI response")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()

        # Extract AI response
        ai_response = response_data['choices'][0]['message']['content']
        logger.info("AI response received", extra={"ai_response": ai_response})
        logger.debug("Response Tokens", extra={"response_tokens": response_data['usage']['total_tokens']})


        # Store the AI response in context memory
        context_memory(client_phone, {"role": "assistant", "content": ai_response}, tenant_id=tenant_id)

        return response_data
    except requests.exceptions.RequestException as e:
        logger.error("Error while making API request to OpenAI GPT", extra={"error": str(e)})
        return None


def context_memory(client_phone, message=None, tenant_id=None):
    from .redis_client import get_conversation, save_conversation

    if not tenant_id or not client_phone:
        logger.warning("Missing parameters in Context Memory", extra={"tenant_id": tenant_id, "client_phone": client_phone[:6] + "******" if client_phone else "None"})
        return []

    logger.debug("Getting conversation", extra={
        "tenant_id": tenant_id,
        "client_phone": client_phone[:6] + "******" if client_phone else "None"
    })

    conversation = get_conversation(tenant_id, client_phone)

    if message:
        logger.debug("Adding message to conversation", extra={"message_length": len(message)})
        conversation.append(message)

        if len(conversation) > CONVERSATION_MAX_LENGTH:
            logger.debug("Trimming the conversaiton", extra={
                "conversation_length": len(conversation),
                "conversation_max_length": CONVERSATION_MAX_LENGTH
            })
            while len(conversation) > CONVERSATION_MAX_LENGTH:
                conversation.pop(0)

        logger.debug(f"Saving conversation with {len(conversation)} messages")
        save_conversation(tenant_id, client_phone, conversation)


    complete_context = [
        {
            "role": "system",
            "content": "You are an expert marketing consultant representing this business. Your goals are to:\n1. Identify client needs and match them to our products/services\n2. Overcome objections professionally (e.g., if price concerns arise, suggest more affordable alternatives)\n3. Actively sell and recommend our offerings based on client interests\n4. IMPORTANT: Do **not** request the client's personal information (name, email, the offer they like) until they show clear interest in a specific product or service\n5. CRITICAL: Once interest is shown, collect the client’s full name, email address and the offer they want\n6. Then identify and confirm which specific pack/service the client wants to purchase\n7. Create detailed lead information including: client name, email, and selected pack/service\n8. Answer only business-related questions and politely redirect other inquiries by saying: 'That’s outside my area. I can help you with our services instead.'\n9. Communicate in the same language as the client (French, Arabic, English, or Moroccan Darija)\n10. Analyze sentiment to provide personalized responses\n11. If the conversation stalls or gets off-topic, ask relevant questions to bring focus back\n12. NEVER answer questions unrelated to our business (e.g., AI, politics, programming, personal advice). Politely decline and refocus on business.\n\nMake responses concise, professional and sales-focused. Always guide the conversation toward understanding client needs first, and only collect personal info after they express interest in a product or service."
        }
    ]

    complete_context.extend(conversation)

    return complete_context


def get_embedding(text):

    """ Convert the user message into embedding using OpenAI API """

    logger.info("Getting embedding text")
    if  not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
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
        logger.debug("Making API request to OpenAI GPT for Embedding")
        response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info("Successfully received embedding from OpenAI GPT")
        return data['data'][0]['embedding']
    except Exception as e:
        logger.error("Error while making API request to OpenAI GPT for Embedding", extra={"error": str(e)})
        return None

# TODO: FIX the BUG , THE AI EXTRACTION IS NOT WORKING PROPERLY SOMETIMES IT WORKS AND SOMETIMES IT DOES NOT WORK
def extract_client_info_with_ai(message, client_phone=None, tenant_id=None, client_id=None):
    from models import Order

    logger.info("Extracting client info with AI", extra={
        "message_length": len(message),
        "client_phone": client_phone[:6] + "******" if client_phone else "None",
        "tenant_id": tenant_id,
        "client_id": client_id
    })
    system_prompt = """
    Extract the following information from the message if present:
    1. Client's full name
    2. Client's email address
    3. Selected pack/service name (this is the specific product or service the client wants to purchase)
    
    the phone number is already provided, so you don't need to ask for it or  extract it.

    Look for explicit mentions like:
    - "My name is [Name]" or "I am [Name]"
    - Email addresses that follow standard format
    - "I want the [Pack Name]" or "I'd like to purchase [Service]"

    Respond ONLY with a JSON object in this exact format:
    {"client_name": "extracted name or null", "client_email": "extracted email or null", "pack_name": "extracted pack or null"}

    If information is not found, use null for that field. DO NOT explain or add any other text.
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
    }

    try:
        logger.debug("Making API request to OpenAI GPT for AI extraction")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        ai_response = data['choices'][0]['message']['content'].strip()
        logger.debug("AI response received", extra={"ai_response_length": len(ai_response)})


        client_data = json.loads(ai_response)
        logger.info("Successfully extracted client info from AI", extra={
            "client_data_len": len(client_data),
        })

        client_data['client_id'] = client_id
        client_data['client_phone'] = client_phone
        client_data['tenant_id'] = tenant_id
        client_data['client_id'] = Client.get_client_id_from_phone(client_phone)

        if client_data['client_name'] and client_data['client_email'] and client_data['pack_name']:
            logger.info("Client info extracted from AI", extra={
                "client_name": client_data['client_name'],
                "client_email": client_data['client_email'],
                "pack_name": client_data['pack_name']
            })
            order = Order.insert_from_ai_extraction(client_data)
            if order:
                logger.info("Successfully created order from AI extraction")
                return client_data
            else:
                logger.error("Failed to create order from AI extraction")
                return None
        return client_data
    except json.JSONDecodeError as e:
        logger.error("Error while parsing AI response as JSON", extra={"error": str(e)})
        return None
    except Exception as e:
        logger.error("Error while making API request to OpenAI GPT for AI extraction", extra={"error": str(e)})
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
