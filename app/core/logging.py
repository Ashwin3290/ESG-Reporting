import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import settings

def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                logs_dir / "app.log",
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )
    
    # Configure loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # MongoDB driver is quite verbose at DEBUG level
    logging.getLogger("motor").setLevel(logging.INFO)
    logging.getLogger("pymongo").setLevel(logging.INFO)
    
    # Setup API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)
    
    return api_logger
