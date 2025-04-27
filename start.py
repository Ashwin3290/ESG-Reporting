#!/usr/bin/env python
"""
Startup script for ESG-API Platform

This script performs the necessary setup and starts the FastAPI application.
"""
import asyncio
import logging
import os
import sys
from scripts.init_database import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("esg-api.log")
    ]
)
logger = logging.getLogger("esg-api")

async def setup():
    """Perform initial setup before starting the API"""
    # Create required directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Initialize the database
    try:
        logger.info("Initializing database...")
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)

def start_api():
    """Start the FastAPI application"""
    import uvicorn
    from app.core.config import settings
    
    logger.info(f"Starting ESG API on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    # Run the setup
    asyncio.run(setup())
    
    # Start the API
    start_api()
