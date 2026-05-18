"""
Logging configuration for RxAccess AI
"""
import sys
from loguru import logger
from pathlib import Path
from src.config import settings

# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

# Add file handler
log_file = settings.logs_dir / "rxaccess.log"
logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    rotation="10 MB",
    retention="30 days",
    compression="zip",
)

# Add error file handler
error_log_file = settings.logs_dir / "errors.log"
logger.add(
    error_log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB",
    retention="90 days",
    compression="zip",
)


def get_logger(name: str):
    """Get a logger instance with the given name"""
    return logger.bind(name=name)
