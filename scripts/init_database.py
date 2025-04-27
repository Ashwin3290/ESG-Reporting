import asyncio
import json
import pandas as pd
import os
import logging
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("db_init")

async def init_database():
    """Initialize the MongoDB database with seed data"""
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Create collections
    collections = [
        "industries", 
        "kpi_specifications",
        "kpi_references",
        "sessions",
        "file_metadata",
        "calculated_kpis",
        "analysis_results",
        "chat_history"
    ]
    
    for collection in collections:
        if collection not in await db.list_collection_names():
            logger.info(f"Creating collection: {collection}")
            await db.create_collection(collection)
    
    # Import KPI data
    await import_kpi_data(db)
    
    # Import KPI specifications
    await import_kpi_specs(db)
    
    # Import KPI references
    await import_kpi_references(db)
    
    # Create indexes
    await create_indexes(db)
    
    logger.info("Database initialization complete")
    return db

async def import_kpi_data(db):
    """Import KPI data from CSV"""
    kpi_csv_path = os.path.join("data", "kpi_data.csv")
    
    if not os.path.exists(kpi_csv_path):
        logger.error(f"KPI data CSV not found at {kpi_csv_path}")
        return
    
    logger.info(f"Importing KPI data from {kpi_csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(kpi_csv_path)
        logger.info(f"Loaded {len(df)} KPI records from CSV")
        
        # Check if data already exists
        count = await db.industries.count_documents({})
        if count > 0:
            logger.info(f"Industries collection already contains {count} records, skipping import")
            return
        
        # Process industries
        industries = {}
        
        for _, row in df.iterrows():
            sector = row["Sector"]
            industry = row["Industry"]
            
            # Create industry key
            key = f"{sector}_{industry}"
            
            if key not in industries:
                industries[key] = {
                    "sector": sector,
                    "industry": industry,
                    "kpis": []
                }
            
            # Add KPI to industry
            industries[key]["kpis"].append({
                "name": row["KPI Name"],
                "specification_id": row["Specification ID"],
                "scope": row["Scope"],
                "specification": row["Specification"],
                "cluster": row["Cluster"],
                "esg_category": row["ESG Category"]
            })
        
        # Insert into database
        for industry in industries.values():
            await db.industries.insert_one(industry)
        
        logger.info(f"Imported {len(industries)} industries with KPIs")
    
    except Exception as e:
        logger.error(f"Error importing KPI data: {e}")

async def import_kpi_specs(db):
    """Import KPI specifications from JSON"""
    specs_json_path = os.path.join("data", "kpis.json")
    
    if not os.path.exists(specs_json_path):
        logger.error(f"KPI specifications JSON not found at {specs_json_path}")
        return
    
    logger.info(f"Importing KPI specifications from {specs_json_path}")
    
    # Read JSON
    try:
        with open(specs_json_path, 'r') as f:
            specs = json.load(f)
        
        # Check if data already exists
        count = await db.kpi_specifications.count_documents({})
        if count > 0:
            logger.info(f"KPI specifications collection already contains {count} records, skipping import")
            return
        
        # Insert into database
        for name, spec in specs.items():
            spec_doc = {
                "name": name,
                **spec
            }
            await db.kpi_specifications.insert_one(spec_doc)
        
        logger.info(f"Imported {len(specs)} KPI specifications")
    
    except Exception as e:
        logger.error(f"Error importing KPI specifications: {e}")

async def import_kpi_references(db):
    """Import KPI references from JSON"""
    refs_json_path = os.path.join("data", "kpi_reference.json")
    
    if not os.path.exists(refs_json_path):
        logger.error(f"KPI references JSON not found at {refs_json_path}")
        return
    
    logger.info(f"Importing KPI references from {refs_json_path}")
    
    # Read JSON
    try:
        with open(refs_json_path, 'r') as f:
            refs = json.load(f)
        
        # Check if data already exists
        count = await db.kpi_references.count_documents({})
        if count > 0:
            logger.info(f"KPI references collection already contains {count} records, skipping import")
            return
        
        # Insert into database
        for name, ref in refs.items():
            ref_doc = {
                "name": name,
                **ref
            }
            await db.kpi_references.insert_one(ref_doc)
        
        logger.info(f"Imported {len(refs)} KPI references")
    
    except Exception as e:
        logger.error(f"Error importing KPI references: {e}")

async def create_indexes(db):
    """Create database indexes"""
    logger.info("Creating database indexes")
    
    # Industry indexes
    await db.industries.create_index("industry")
    await db.industries.create_index("sector")
    
    # KPI specifications indexes
    await db.kpi_specifications.create_index("name", unique=True)
    
    # KPI references indexes
    await db.kpi_references.create_index("name", unique=True)
    
    # Sessions indexes
    await db.sessions.create_index("session_id", unique=True)
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    
    # File metadata indexes
    await db.file_metadata.create_index("file_id", unique=True)
    await db.file_metadata.create_index("session_id")
    
    # Calculated KPIs indexes
    await db.calculated_kpis.create_index([("session_id", 1), ("kpi_name", 1), ("calculation_date", -1)])
    
    # Analysis results indexes
    await db.analysis_results.create_index([("session_id", 1), ("analysis_type", 1), ("created_at", -1)])
    await db.analysis_results.create_index("analysis_id", unique=True)
    
    # Chat history indexes
    await db.chat_history.create_index("session_id")
    await db.chat_history.create_index("message_id", unique=True)
    
    logger.info("Database indexes created")

if __name__ == "__main__":
    # Run initialization
    asyncio.run(init_database())
