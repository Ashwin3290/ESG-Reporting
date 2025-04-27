from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ...services.auto_processor import AutoProcessorService
from ...services.data_manager import DataManagerService
from ..dependencies import get_auto_processor, get_data_manager

router = APIRouter()

class ProcessingStatusResponse(BaseModel):
    session_id: str
    status: str
    industry: Optional[str] = None
    last_processed: Optional[str] = None

@router.get("/{session_id}/map-columns")
async def map_columns(
    session_id: str = Path(..., description="Session ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    async_mode: bool = Query(True, description="Process in background (true) or wait for completion (false)"),
    auto_processor: AutoProcessorService = Depends(get_auto_processor),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """
    Trigger automatic column mapping for all KPIs based on industry
    
    This will analyze all files in the session and map columns to KPI fields.
    First tries exact matches, then uses LLM for intelligent mapping.
    """
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if industry is set
    industry = session.get("industry")
    if not industry:
        raise HTTPException(status_code=400, detail="No industry assigned to this session")
    
    # Update session status to processing
    await data_manager.update_session(
        session_id=session_id,
        update_data={
            "mapping_status": "processing",
            "mapping_started": datetime.utcnow()
        }
    )
    
    if async_mode:
        # Process in background
        background_tasks.add_task(auto_processor.map_columns, session_id)
        
        return {
            "session_id": session_id,
            "status": "mapping_started",
            "message": "Column mapping started in background"
        }
    else:
        # Process synchronously
        result = await auto_processor.map_columns(session_id)
        return result

@router.get("/{session_id}/calculate-kpis")
async def calculate_kpis(
    session_id: str = Path(..., description="Session ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    async_mode: bool = Query(True, description="Process in background (true) or wait for completion (false)"),
    auto_processor: AutoProcessorService = Depends(get_auto_processor),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """
    Trigger KPI calculation using mapped columns
    
    This will calculate all KPIs for the session based on previously mapped columns.
    """
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if industry is set
    industry = session.get("industry")
    if not industry:
        raise HTTPException(status_code=400, detail="No industry assigned to this session")
    
    # Check if columns are mapped
    column_mappings = session.get("column_mappings", {})
    if not column_mappings:
        raise HTTPException(status_code=400, detail="No column mappings available. Run column mapping first.")
    
    # Update session status to processing
    await data_manager.update_session(
        session_id=session_id,
        update_data={
            "calculation_status": "processing",
            "calculation_started": datetime.utcnow()
        }
    )
    
    if async_mode:
        # Process in background
        background_tasks.add_task(auto_processor.calculate_kpis, session_id)
        
        return {
            "session_id": session_id,
            "status": "calculation_started",
            "message": "KPI calculation started in background"
        }
    else:
        # Process synchronously
        result = await auto_processor.calculate_kpis(session_id)
        return result

@router.get("/{session_id}/mappings")
async def get_column_mappings(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """
    Get all column mappings for a session
    
    Returns the mapping status and details for all KPIs.
    """
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get mapping status
    column_mappings = session.get("column_mappings", {})
    mapping_status = session.get("mapping_status", {})
    
    # Get KPIs for industry
    industry = session.get("industry")
    kpis_by_category = {}
    
    if industry:
        industry_doc = await data_manager.get_industry(industry)
        if industry_doc:
            kpis = industry_doc.get("kpis", [])
            for kpi in kpis:
                category = kpi.get("esg_category", "").lower()
                spec = kpi.get("specification")
                
                if category and spec:
                    if category not in kpis_by_category:
                        kpis_by_category[category] = []
                    kpis_by_category[category].append({
                        "name": spec,
                        "mapping_status": mapping_status.get(spec, "pending"),
                        "mappings": column_mappings.get(spec, {})
                    })
    
    return {
        "session_id": session_id,
        "industry": industry,
        "mapping_status": session.get("mapping_status", "not_started"),
        "last_mapped": session.get("last_column_mapping"),
        "kpis_by_category": kpis_by_category
    }

@router.get("/{session_id}/results")
async def get_kpi_results(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """
    Get all calculated KPI results for a session
    
    Returns the calculation results for all KPIs.
    """
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPI status
    kpi_status = session.get("kpi_status", {})
    
    # Get calculated KPIs
    calculated_kpis = {}
    cursor = data_manager.db.calculated_kpis.find(
        {"session_id": session_id},
        sort=[("calculation_date", -1)]
    )
    
    # Create a map of most recent KPI calculations
    seen_kpis = set()
    async for kpi_doc in cursor:
        kpi_name = kpi_doc.get("kpi_name")
        if kpi_name and kpi_name not in seen_kpis:
            seen_kpis.add(kpi_name)
            # Remove ObjectId for JSON serialization
            kpi_doc["_id"] = str(kpi_doc["_id"])
            calculated_kpis[kpi_name] = kpi_doc
    
    # Organize by category
    kpis_by_category = {}
    industry = session.get("industry")
    
    if industry:
        industry_doc = await data_manager.get_industry(industry)
        if industry_doc:
            kpis = industry_doc.get("kpis", [])
            for kpi in kpis:
                category = kpi.get("esg_category", "").lower()
                spec = kpi.get("specification")
                
                if category and spec:
                    if category not in kpis_by_category:
                        kpis_by_category[category] = []
                    
                    kpi_result = calculated_kpis.get(spec)
                    kpis_by_category[category].append({
                        "name": spec,
                        "status": kpi_status.get(spec, "pending"),
                        "result": kpi_result.get("value") if kpi_result else None,
                        "calculation_date": kpi_result.get("calculation_date") if kpi_result else None
                    })
    
    return {
        "session_id": session_id,
        "industry": industry,
        "calculation_status": session.get("calculation_status", "not_started"),
        "last_calculated": session.get("last_calculation"),
        "kpis_by_category": kpis_by_category
    }

@router.get("/{session_id}/status")
async def get_processing_status(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get the current processing status for a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Count metrics
    mapping_status = session.get("mapping_status", {})
    kpi_status = session.get("kpi_status", {})
    
    # Count mapped KPIs
    mapped_count = sum(1 for status in mapping_status.values() if status == "complete")
    total_kpis = len(mapping_status)
    
    # Count calculated KPIs
    calculated_count = sum(1 for status in kpi_status.values() if status == "calculated")
    
    return {
        "session_id": session_id,
        "industry": session.get("industry"),
        "mapping_status": session.get("mapping_status", "not_started"),
        "calculation_status": session.get("calculation_status", "not_started"),
        "last_mapped": session.get("last_column_mapping"),
        "last_calculated": session.get("last_calculation"),
        "mapped_kpi_count": mapped_count,
        "calculated_kpi_count": calculated_count,
        "total_kpis": total_kpis,
        "file_count": len(session.get("uploaded_files", []))
    }

@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get all files for a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get files
    files = session.get("uploaded_files", [])
    
    return {
        "session_id": session_id,
        "file_count": len(files),
        "files": files
    }

@router.get("/{session_id}/process-all")
async def process_all(
    session_id: str = Path(..., description="Session ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    auto_processor: AutoProcessorService = Depends(get_auto_processor),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """
    Trigger both column mapping and KPI calculation in sequence
    
    This endpoint is provided for convenience to run the full processing pipeline.
    """
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if industry is set
    industry = session.get("industry")
    if not industry:
        raise HTTPException(status_code=400, detail="No industry assigned to this session")
    
    # Update session status
    await data_manager.update_session(
        session_id=session_id,
        update_data={
            "mapping_status": "processing",
            "calculation_status": "pending",
            "processing_started": datetime.utcnow()
        }
    )
    
    # Define background task function
    async def run_full_process(sid: str):
        # Step 1: Map columns
        mapping_result = await auto_processor.map_columns(sid)
        
        # Step 2: Calculate KPIs
        if "error" not in mapping_result:
            await auto_processor.calculate_kpis(sid)
    
    # Run in background
    background_tasks.add_task(run_full_process, session_id)
    
    return {
        "session_id": session_id,
        "status": "processing_started",
        "message": "Full processing pipeline started in background"
    }
