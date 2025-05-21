import redis
import json

from redis_config import (REDIS_HOST,REDIS_PORT,
                          REDIS_DB, REDIS_PASSWORD,
                          REDIS_KEY_PREFIX, CONVERSATION_KEY_PREFIX, REDIS_SSL)



try:
    redis_client = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        ssl=REDIS_SSL,
        decode_responses=True
    )

    redis_client = redis.Redis(connection_pool=redis_client)
    redis_client.ping()
except redis.RedisError as e:
    memory_store = {}



