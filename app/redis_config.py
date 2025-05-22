import os



REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"


REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'app')
CONVERSATION_KEY_PREFIX = f"{REDIS_KEY_PREFIX}:conversation"


CONVERSATION_EXPIRY = int(os.getenv('CONVERSATION_EXPIRY', 86400))
CONVERSATION_MAX_LENGTH = int(os.getenv('CONVERSATION_MAX_LENGTH', 50))


def get_conversation_key(tenant_id, client_phone):
    clean_phone = client_phone.replace("+", "").replace(" ", "")
    return f"{CONVERSATION_KEY_PREFIX}:{tenant_id}:{clean_phone}"
