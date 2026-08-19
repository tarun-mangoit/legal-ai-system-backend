# Minimal logging boilerplate
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Application startup")
    return logger
