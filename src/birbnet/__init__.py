import logging

logger = logging.getLogger(__package__)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)
