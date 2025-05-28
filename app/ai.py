import requests
import os
import json
import time

from config import OPENAI_API_KEY
from models import Client, TenantInfo, Service, Product
from .redis_config import CONVERSATION_MAX_LENGTH
from .log_config import logger

api_key = os.getenv("OPEN_AI_API_KEY")


def open_ai_gpt(message, client_phone=None, question_type=None, tenant_id=None):
    # Mask sensitive identifiers for logging
    masked_phone = mask_identifier(client_phone) if client_phone else None

    logger.debug("Processing AI request", extra={
        "client": masked_phone,
        "tenant": tenant_id,
        "question_type": question_type
    })

    embedding = get_embedding(message)
    if not embedding:
        logger.warning("Embedding generation failed", {
            "client": masked_phone,
            "tenant": tenant_id
        })

    if not question_type:
        question_type = classify_intent(message)

    # Build context information based on message type
    context_info = ""
    if embedding and tenant_id:
        if question_type == 'service':
            services = Service.search_services_by_embedding(embedding, tenant_id)
            if services:
                context_info = build_services_context(services)
                logger.debug("Services context added", {"count": len(services)})
        elif question_type == 'product':
            products = Product.search_products_by_embedding(embedding, tenant_id)
            if products:
                context_info = build_products_context(products)
                logger.debug("Products context added", {"count": len(products)})
        elif question_type == 'general':
            tenant_info = TenantInfo.get_tenant_information(embedding, tenant_id)
            if tenant_info:
                context_info = build_tenant_context(tenant_info)
                logger.debug("Tenant context added")

    user_content = message
    if context_info:
        user_content = f"User question: {message}\n\nContext information (not visible to user):{context_info}"

    # Track conversation history
    start_time = time.time()
    messages = context_memory(client_phone, {"role": "user", "content": user_content}, tenant_id=tenant_id)

    # Call OpenAI API
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
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_time = time.time() - start_time

        # Log API metrics
        logger.debug("OpenAI API call completed", {
            "duration_ms": round(response_time * 1000),
            "status_code": response.status_code
        })

        response.raise_for_status()
        response_data = response.json()
        ai_response = response_data['choices'][0]['message']['content']

        # Log usage metrics
        usage = response_data.get('usage', {})
        logger.info("OpenAI request successful", {
            "model": response_data.get('model', 'unknown'),
            "prompt_tokens": usage.get('prompt_tokens', 0),
            "completion_tokens": usage.get('completion_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0),
            "question_type": question_type
        })

        # Save AI response to conversation history
        context_memory(client_phone, {"role": "assistant", "content": ai_response}, tenant_id=tenant_id)
        return response_data

    except requests.exceptions.ConnectionError:
        logger.error("OpenAI API connection failed", {
            "client": masked_phone,
            "error_type": "connection_error"
        })
        return None
    except requests.exceptions.Timeout:
        logger.error("OpenAI API timeout", {
            "client": masked_phone,
            "error_type": "timeout"
        })
        return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        error_info = {}

        # Extract error details from response
        try:
            error_data = e.response.json()
            error_info = {
                "error_type": error_data.get('error', {}).get('type', 'unknown'),
                "error_code": error_data.get('error', {}).get('code', 'unknown')
            }
        except: # TODO: set specific exception type here
            pass

        logger.error("OpenAI API error", {
            "client": masked_phone,
            "status_code": status_code,
            "error_type": "http_error",
            **error_info
        })
        return None
    except Exception as e:
        logger.error("OpenAI API unexpected error", {
            "client": masked_phone,
            "error_type": "unexpected",
            "error": str(e)
        })
        return None


def context_memory(client_phone, message=None, tenant_id=None):
    from .redis_client import get_conversation, save_conversation

    # Mask phone number for logging
    masked_phone = mask_identifier(client_phone) if client_phone else None

    if not tenant_id or not client_phone:
        logger.warning("Missing conversation parameters", {
            "has_tenant_id": tenant_id is not None,
            "has_client_phone": client_phone is not None
        })
        return []

    try:
        conversation = get_conversation(tenant_id, client_phone)

        if message:
            message_type = message.get('role', 'unknown')
            conversation.append(message)

            if len(conversation) > CONVERSATION_MAX_LENGTH:
                logger.debug("Trimming conversation history", {
                    "client": masked_phone,
                    "original_length": len(conversation),
                    "new_length": CONVERSATION_MAX_LENGTH
                })
                while len(conversation) > CONVERSATION_MAX_LENGTH:
                    conversation.pop(0)

            save_conversation(tenant_id, client_phone, conversation)
            logger.debug("Conversation updated", {
                "client": masked_phone,
                "message_type": message_type,
                "conversation_length": len(conversation)
            })

        complete_context = [
            {
                "role": "system",
                "content": "You are an expert marketing consultant representing this business. Your goals are to:\n1. Identify client needs and match them to our products/services\n2. Overcome objections professionally (e.g., if price concerns arise, suggest more affordable alternatives)\n3. Actively sell and recommend our offerings based on client interests\n4. IMPORTANT: Do **not** request the client's personal information (name, email, the offer they like) until they show clear interest in a specific product or service\n5. CRITICAL: Once interest is shown, collect the client's full name, email address and the offer they want\n6. Then identify and confirm which specific pack/service the client wants to purchase\n7. Create detailed lead information including: client name, email, and selected pack/service\n8. Answer only business-related questions and politely redirect other inquiries by saying: 'That's outside my area. I can help you with our services instead.'\n9. Communicate in the same language as the client (French, Arabic, English, or Moroccan Darija)\n10. Analyze sentiment to provide personalized responses\n11. If the conversation stalls or gets off-topic, ask relevant questions to bring focus back\n12. NEVER answer questions unrelated to our business (e.g., AI, politics, programming, personal advice). Politely decline and refocus on business.\n\nMake responses concise, professional and sales-focused. Always guide the conversation toward understanding client needs first, and only collect personal info after they express interest in a product or service."
            }
        ]

        complete_context.extend(conversation)
        return complete_context

    except Exception as e:
        logger.error("Conversation history error", {
            "client": masked_phone,
            "error": str(e),
            "function": "context_memory"
        })
        # Return a basic context without history
        return [{
            "role": "system",
            "content": "You are an expert marketing consultant representing this business."
        }]


def get_embedding(text):
    """ Convert the user message into embedding using OpenAI API """
    start_time = time.time()

    if not OPENAI_API_KEY:
        logger.error("OpenAI API key missing", {
            "function": "get_embedding"
        })
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
        response_time = time.time() - start_time

        logger.debug("Embedding API call completed", {
            "duration_ms": round(response_time * 1000),
            "status_code": response.status_code
        })

        response.raise_for_status()
        data = response.json()

        logger.debug("Embedding generated", {
            "usage": data.get('usage', {}).get('total_tokens', 0)
        })

        return data['data'][0]['embedding']

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        logger.error("Embedding API error", {
            "status_code": status_code,
            "error": str(e)
        })
        return None
    except Exception as e:
        logger.error("Embedding generation failed", {
            "error_type": type(e).__name__,
            "error": str(e)
        })
        return None


def extract_client_info_with_ai(message, client_phone=None, tenant_id=None, client_id=None):
    from models import Order

    masked_phone = mask_identifier(client_phone) if client_phone else None

    logger.info("Extracting client information", {
        "client": masked_phone,
        "tenant": tenant_id
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
        start_time = time.time()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_time = time.time() - start_time

        logger.debug("Client info extraction API call completed", {
            "duration_ms": round(response_time * 1000),
            "status_code": response.status_code
        })

        response.raise_for_status()
        data = response.json()
        ai_response = data['choices'][0]['message']['content'].strip()

        client_data = json.loads(ai_response)

        # Safely log data with PII masked
        log_info = {}
        if client_data.get('client_name'):
            log_info['has_name'] = True
        if client_data.get('client_email'):
            log_info['has_email'] = True
        if client_data.get('pack_name'):
            log_info['pack_name'] = client_data.get('pack_name')

        logger.info("Client data extracted", log_info)

        # Prepare complete client data
        client_data['client_id'] = client_id
        client_data['client_phone'] = client_phone
        client_data['tenant_id'] = tenant_id
        client_data['client_id'] = Client.get_client_id_from_phone(client_phone)

        # Process complete information if available
        if client_data['client_name'] and client_data['client_email'] and client_data['pack_name']:
            logger.info("Complete client information received, creating order", {
                "client": masked_phone,
                "pack": client_data['pack_name']
            })

            order = Order.insert_from_ai_extraction(client_data)

            if order:
                logger.info("Order created successfully", {
                    "client": masked_phone,
                    "order_id": getattr(order, 'id', 'unknown')
                })
            else:
                logger.error("Order creation failed", {
                    "client": masked_phone,
                    "pack": client_data['pack_name']
                })
        else:
            logger.info("Incomplete client information", {
                "client": masked_phone,
                "has_name": client_data['client_name'] is not None,
                "has_email": client_data['client_email'] is not None,
                "has_pack": client_data['pack_name'] is not None
            })

        return client_data

    except json.JSONDecodeError as e:
        logger.error("JSON parsing error in client extraction", {
            "client": masked_phone,
            "error": str(e),
            "response": ai_response if 'ai_response' in locals() else "N/A"
        })
        return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        logger.error("OpenAI API error during client extraction", {
            "client": masked_phone,
            "status_code": status_code,
            "error": str(e)
        })
        return None
    except Exception as e:
        logger.error("Client extraction unexpected error", {
            "client": masked_phone,
            "error_type": type(e).__name__,
            "error": str(e)
        })
        return None


def classify_intent(message):
    """ Classify the intent of the message into 'product', 'service', or 'general' """
    start_time = time.time()

    if not OPENAI_API_KEY:
        logger.error("OpenAI API key missing", {
            "function": "classify_intent"
        })
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
        response_time = time.time() - start_time

        logger.debug("Intent classification API call completed", {
            "duration_ms": round(response_time * 1000),
            "status_code": response.status_code
        })

        response.raise_for_status()
        data = response.json()
        intent = data['choices'][0]['message']['content'].strip()

        logger.debug("Intent classified", {
            "intent": intent,
            "tokens": data.get('usage', {}).get('total_tokens', 0)
        })

        return intent

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        logger.error("Intent classification API error", {
            "status_code": status_code,
            "error": str(e)
        })
        return None
    except Exception as e:
        logger.error("Intent classification failed", {
            "error_type": type(e).__name__,
            "error": str(e)
        })
        return None


# Helper functions for the main code

def mask_identifier(identifier):
    """Mask sensitive identifiers like phone numbers or emails"""
    if not identifier:
        return None
    if isinstance(identifier, str):
        if len(identifier) > 4:
            return f"...{identifier[-4:]}"
        return "***"
    return "***"


def build_services_context(services):
    """Build context info for services"""
    return "Relevant Services: \n" + "\n".join(
        f"- {s.name}: {s.description} {s.price} DH {s.periode}" for s in services
    )


def build_products_context(products):
    """Build context info for products"""
    return "Relevant Products: \n" + "\n".join(
        f"- {p.name}: {p.description} {p.price} {p.periode}" for p in products
    )


def build_tenant_context(tenant_info):
    """Build context info for tenant"""
    return f"Tenant Information: \n" + "\n".join(
        f"- we are {t.name}, we are in {t.address}{t.city}, this Our mail address {t.email} if you want to call us this is our phone {t.phone_number}"
        for t in tenant_info
    )