from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Dict, Any, List
from pydantic import BaseModel

from ...services.kpi_calculator import KPICalculatorService
from ...services.data_manager import DataManagerService
from ..dependencies import get_kpi_calculator, get_data_manager

router = APIRouter()

class KPICalculationRequest(BaseModel):
    session_id: str
    kpi_name: str
    file_id: str = None
    mappings: Dict[str, str] = None

@router.get("/")
async def get_all_kpi_specs(
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get all KPI specifications"""
    specs = await data_manager.get_all_kpi_specs()
    return specs

@router.get("/{kpi_name}")
async def get_kpi_details(
    kpi_name: str = Path(..., description="KPI name"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get KPI details by name"""
    kpi = await data_manager.get_kpi_spec(kpi_name)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    return kpi

@router.post("/calculate")
async def calculate_kpi(
    request: KPICalculationRequest,
    kpi_calculator: KPICalculatorService = Depends(get_kpi_calculator),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Calculate KPI value from input data"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPI specification
    kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
    if not kpi_spec:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    # Calculate KPI
    result, error = await kpi_calculator.calculate_kpi(
        session_id=request.session_id,
        kpi_name=request.kpi_name,
        file_id=request.file_id,
        mappings=request.mappings,
        is_numeric=kpi_spec.get("is_numerical", True)
    )
    
    if error:
        return {"error": error, "status": "error"}
    
    return {
        "kpi_name": request.kpi_name,
        "value": result,
        "status": "success"
    }

@router.get("/session/{session_id}")
async def get_session_kpis(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get all calculated KPIs for a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPIs
    kpis = await data_manager.get_session_kpis(session_id)
    return kpis

@router.get("/categories")
async def get_kpi_categories():
    """Get ESG categories"""
    return {
        "categories": [
            {"id": "environmental", "name": "Environmental"},
            {"id": "social", "name": "Social"},
            {"id": "governance", "name": "Governance"}
        ]
    }

@router.get("/category/{category}")
async def get_kpis_by_category(
    category: str = Path(..., description="ESG category"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get KPIs by ESG category"""
    kpis = await data_manager.get_kpis_by_category(category.lower())
    return kpis
