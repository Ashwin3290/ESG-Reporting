import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from ..core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    fs: AsyncIOMotorGridFSBucket = None

async def connect_to_mongo():
    """Connect to MongoDB database"""
    logger.info("Connecting to MongoDB...")
    MongoDB.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000
    )
    
    # Verify connection
    try:
        await MongoDB.client.admin.command('ping')
        logger.info("Connected to MongoDB")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    MongoDB.db = MongoDB.client[settings.MONGODB_DATABASE]
    
    # Initialize GridFS bucket
    MongoDB.fs = AsyncIOMotorGridFSBucket(MongoDB.db)
    
    # Setup indexes
    await setup_indexes()
    
    logger.info(f"Using database: {settings.MONGODB_DATABASE}")

async def setup_indexes():
    """Setup necessary indexes for collections"""
    # Sessions collection TTL index
    await MongoDB.db.sessions.create_index(
        "expires_at", 
        expireAfterSeconds=0
    )
    
    # Other indexes as needed
    await MongoDB.db.industries.create_index("industry")
    await MongoDB.db.kpi_specifications.create_index("name", unique=True)
    
    logger.info("MongoDB indexes set up")

async def close_mongo_connection():
    """Close MongoDB connection"""
    if MongoDB.client:
        MongoDB.client.close()
        logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    return MongoDB.db

def get_gridfs() -> AsyncIOMotorGridFSBucket:
    """Get GridFS bucket instance"""
    return MongoDB.fs
