from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Dict, Any, List
from pydantic import BaseModel

from ...services.column_mapping import ColumnMappingService
from ...services.data_manager import DataManagerService
from ...services.file_service import FileService
from ..dependencies import get_column_mapping_service, get_data_manager, get_file_service

router = APIRouter()

class ExactMappingRequest(BaseModel):
    session_id: str
    kpi_name: str
    file_id: str

class LLMMappingRequest(BaseModel):
    session_id: str
    kpi_name: str
    file_id: str
    use_sample_data: bool = True

class ManualMappingRequest(BaseModel):
    session_id: str
    kpi_name: str
    mappings: Dict[str, str]

@router.post("/exact")
async def map_columns_exact(
    request: ExactMappingRequest,
    column_mapping_service: ColumnMappingService = Depends(get_column_mapping_service),
    data_manager: DataManagerService = Depends(get_data_manager),
    file_service: FileService = Depends(get_file_service)
):
    """Map columns using exact matching algorithm"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify file exists
    file_info = await file_service.get_file_metadata(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify KPI exists
    kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
    if not kpi_spec:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    # Get file columns
    columns = await file_service.get_file_columns(request.file_id)
    if not columns:
        raise HTTPException(status_code=404, detail="Failed to get file columns")
    
    # Perform exact mapping
    mappings = await column_mapping_service.perform_exact_matching(
        kpi_name=request.kpi_name,
        file_columns=columns,
        kpi_spec=kpi_spec
    )
    
    # Update session with mappings
    await data_manager.update_column_mappings(
        session_id=request.session_id,
        kpi_name=request.kpi_name,
        mappings=mappings
    )
    
    return {
        "kpi_name": request.kpi_name,
        "mappings": mappings,
        "complete": len(mappings) == len(kpi_spec.get("required_data", []))
    }

@router.post("/llm")
async def map_columns_llm(
    request: LLMMappingRequest,
    column_mapping_service: ColumnMappingService = Depends(get_column_mapping_service),
    data_manager: DataManagerService = Depends(get_data_manager),
    file_service: FileService = Depends(get_file_service)
):
    """Map columns using LLM for semantic matching"""
    """Map columns using LLM for semantic matching"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify file exists
    file_info = await file_service.get_file_metadata(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify KPI exists
    kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
    if not kpi_spec:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    # Get file columns
    columns = await file_service.get_file_columns(request.file_id)
    if not columns:
        raise HTTPException(status_code=404, detail="Failed to get file columns")
    
    # Try exact matching first
    exact_mappings = await column_mapping_service.perform_exact_matching(
        kpi_name=request.kpi_name,
        file_columns=columns,
        kpi_spec=kpi_spec
    )
    
    # Check if all required fields are mapped
    all_mapped = len(exact_mappings) == len(kpi_spec.get("required_data", []))
    if all_mapped:
        # Update session with mappings
        await data_manager.update_column_mappings(
            session_id=request.session_id,
            kpi_name=request.kpi_name,
            mappings=exact_mappings
        )
        
        return {
            "kpi_name": request.kpi_name,
            "mappings": exact_mappings,
            "complete": True,
            "method": "exact"
        }
    
    # Get sample data for context if requested
    sample_data = None
    if request.use_sample_data:
        sample_data = await file_service.get_file_sample(request.file_id, max_rows=5)
    
    # Perform LLM mapping for remaining fields
    mappings = await column_mapping_service.perform_llm_matching(
        kpi_name=request.kpi_name,
        file_columns=columns,
        kpi_spec=kpi_spec,
        existing_mappings=exact_mappings,
        sample_data=sample_data
    )
    
    # Update session with mappings
    await data_manager.update_column_mappings(
        session_id=request.session_id,
        kpi_name=request.kpi_name,
        mappings=mappings
    )
    
    return {
        "kpi_name": request.kpi_name,
        "mappings": mappings,
        "complete": len(mappings) == len(kpi_spec.get("required_data", [])),
        "method": "llm"
    }

@router.post("/manual")
async def set_manual_mappings(
    request: ManualMappingRequest,
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Set manual column mappings"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify KPI exists
    kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
    if not kpi_spec:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    # Update session with mappings
    await data_manager.update_column_mappings(
        session_id=request.session_id,
        kpi_name=request.kpi_name,
        mappings=request.mappings
    )
    
    return {
        "kpi_name": request.kpi_name,
        "mappings": request.mappings,
        "complete": len(request.mappings) == len(kpi_spec.get("required_data", [])),
        "method": "manual"
    }

@router.get("/{session_id}/{kpi_name}")
async def get_column_mappings(
    session_id: str = Path(..., description="Session ID"),
    kpi_name: str = Path(..., description="KPI name"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get column mappings for a KPI in a session"""
    """Get column mappings for a KPI in a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get mappings
    mappings = await data_manager.get_column_mappings(session_id, kpi_name)
    if not mappings:
        return {"kpi_name": kpi_name, "mappings": {}, "complete": False}
    
    # Get KPI spec to check if mapping is complete
    kpi_spec = await data_manager.get_kpi_spec(kpi_name)
    is_complete = False
    if kpi_spec:
        is_complete = len(mappings) == len(kpi_spec.get("required_data", []))
    
    return {
        "kpi_name": kpi_name,
        "mappings": mappings,
        "complete": is_complete
    }
