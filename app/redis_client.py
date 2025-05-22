import redis
import json

from .redis_config import get_conversation_key

from .redis_config import (REDIS_HOST,REDIS_PORT,
                          REDIS_DB, REDIS_PASSWORD,
                          REDIS_KEY_PREFIX, CONVERSATION_KEY_PREFIX,
                          REDIS_SSL, CONVERSATION_EXPIRY,
                           CONVERSATION_MAX_LENGTH)



try:
    redis_client = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )

    redis_client = redis.Redis(connection_pool=redis_client)
    redis_client.ping()
except redis.RedisError as e:
    memory_store = {}


def get_conversation(tenant_id ,client_phone):
    key = get_conversation_key(tenant_id, client_phone)
    try:
        data = redis_client.get(key)

        if hasattr(data, '__await__'):
            import asyncio
            data = asyncio.get_event_loop().run_until_complete(data)
        return json.loads(data) if data else []
    except Exception as e:
        print(f"Error retrieving conversation from Redis: {e}")
        return []

def save_conversation(tenant_id, client_phone, conversation):
    key = get_conversation_key(tenant_id, client_phone)
    try:
        if len(conversation) > CONVERSATION_MAX_LENGTH:
            conversation = conversation[-CONVERSATION_MAX_LENGTH:]

        redis_client.set(key, json.dumps(conversation), ex=CONVERSATION_EXPIRY)
        return True
    except Exception as e:
        print(f"Error saving conversation to Redis: {e}")
        return False




