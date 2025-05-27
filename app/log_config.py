import os

from logtail import LogtailHandler
import logging

env = os.getenv("ENV", "dev")

handler = LogtailHandler(
    source_token=os.getenv("LOGTAIL_SOURCE_TOKEN", "default_source_token"),
    host=os.getenv("LOGTAIL_HOST", "logtail.logtail.com"),
)

logger = logging.getLogger(__name__)

if env == "prod":
    logger.setLevel(logging.WARNING)
else:
    logger.setLevel(logging.INFO)

logger.addHandler(handler)