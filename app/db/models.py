from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class FileMetadata(BaseModel):
    """File metadata model"""
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    file_size: int
    content_type: str
    grid_id: Optional[str] = None  # GridFS ID

class KPIRequiredData(BaseModel):
    """KPI required data field model"""
    name: str
    description: str
    type: str

class KPISpecification(BaseModel):
    """KPI specification model"""
    name: str
    is_numerical: bool
    required_data: List[KPIRequiredData]
    calculation_logic: str
    unit_of_measurement: str

class KPIReference(BaseModel):
    """KPI reference values model"""
    best_score: float
    worst_score: float
    unit: str
    best_response: Optional[str] = None  # For narrative KPIs
    worst_response: Optional[str] = None  # For narrative KPIs

class IndustryKPI(BaseModel):
    """Industry KPI mapping model"""
    name: str
    specification_id: str
    scope: str
    specification: str
    cluster: int
    esg_category: str

class Industry(BaseModel):
    """Industry model"""
    sector: str
    industry: str
    kpis: List[IndustryKPI]

class Session(BaseModel):
    """Session model"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    industry: Optional[str] = None
    uploaded_files: List[FileMetadata] = []
    column_mappings: Dict[str, Dict[str, str]] = {}  # {kpi_name: {field_name: column_name}}
    mapping_status: Dict[str, str] = {}  # {kpi_name: status}

class CalculatedKPI(BaseModel):
    """Calculated KPI result model"""
    session_id: str
    kpi_name: str
    calculation_date: datetime = Field(default_factory=datetime.utcnow)
    value: Any  # Can be number or text
    status: str
    calculation_metadata: Dict[str, Any] = {}

class AnalysisResult(BaseModel):
    """Analysis result model"""
    session_id: str
    analysis_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    environmental: Dict[str, Any] = {}
    social: Dict[str, Any] = {}
    governance: Dict[str, Any] = {}
    strategies: Dict[str, Any] = {}
    recommendations: List[str] = []
