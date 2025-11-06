"""
Centralized logging utility.
Replaces scattered print statements with structured logging.
"""

import logging
import sys
from typing import Any

# Configure logger
logger = logging.getLogger("studybuddy")
logger.setLevel(logging.INFO)

# Console handler
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)

# Format: [TIMESTAMP] [LEVEL] [MODULE] Message
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)


def log_info(module: str, message: str, **kwargs: Any):
    """Log info message with module context."""
    extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    full_message = f"[{module}] {message}" + (f" | {extra_info}" if extra_info else "")
    logger.info(full_message)


def log_error(module: str, message: str, error: Exception = None):
    """Log error message with optional exception."""
    if error:
        logger.error(f"[{module}] {message}: {str(error)}", exc_info=True)
    else:
        logger.error(f"[{module}] {message}")


def log_debug(module: str, message: str, **kwargs: Any):
    """Log debug message (only in debug mode)."""
    if logger.level <= logging.DEBUG:
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
        full_message = f"[{module}] {message}" + (f" | {extra_info}" if extra_info else "")
        logger.debug(full_message)
