import logging

logger = logging.getLogger(__package__)
formatter = logging.Formatter(
    datefmt="%Y-%m-%d %H:%M:%S",
    fmt="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(message)s",
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
