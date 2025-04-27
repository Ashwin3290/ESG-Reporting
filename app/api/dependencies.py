from fastapi import Depends
from ..db.mongodb import get_database
from ..services.data_manager import DataManagerService
from ..services.kpi_calculator import KPICalculatorService
from ..services.file_service import FileService
from ..services.advisor import ESGAdvisorService
from ..services.column_mapping import ColumnMappingService
from ..utils.llm_helpers import GeminiClient
from ..core.security import verify_api_key
from motor.motor_asyncio import AsyncIOMotorDatabase

# Database dependency
def get_db():
    return get_database()

# Services dependencies
def get_data_manager(db: AsyncIOMotorDatabase = Depends(get_db)):
    return DataManagerService(db)

def get_file_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    return FileService(db)

def get_kpi_calculator(
    db: AsyncIOMotorDatabase = Depends(get_db),
    file_service: FileService = Depends(get_file_service)
):
    return KPICalculatorService(db, file_service)

def get_gemini_client():
    return GeminiClient()

def get_column_mapping_service(
    gemini_client: GeminiClient = Depends(get_gemini_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return ColumnMappingService(gemini_client, db)

def get_advisor_service(
    gemini_client: GeminiClient = Depends(get_gemini_client),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return ESGAdvisorService(gemini_client, db)

# Authentication dependencies
def get_authenticated_api_key(api_key: str = Depends(verify_api_key)):
    return api_key
