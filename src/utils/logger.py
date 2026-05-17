"""
Centralized logging configuration using loguru.
"""

import sys
from loguru import logger
from config.settings import LOG_LEVEL, LOG_FILE


def get_logger(module_name: str = None):
    """
    Get a configured logger instance.
    
    Usage:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting data collection...")
    """
    # Remove default handler
    logger.remove()

    # Console handler (colored)
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[module]}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler (detailed)
    logger.add(
        LOG_FILE,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    # Bind module name
    return logger.bind(module=module_name or "main")