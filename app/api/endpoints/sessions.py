from fastapi import APIRouter, Depends, HTTPException, Path, Body
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ...services.data_manager import DataManagerService
from ..dependencies import get_data_manager

router = APIRouter()

class SessionCreate(BaseModel):
    industry: Optional[str] = None
    session_duration_days: int = 7

class SessionUpdate(BaseModel):
    industry: Optional[str] = None
    last_updated: Optional[datetime] = None
    extends_expiry: bool = False
    extension_days: int = 7

@router.post("/")
async def create_session(
    session_data: SessionCreate = Body(...),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Create a new session, optionally with an industry"""
    expires_at = datetime.utcnow() + timedelta(days=session_data.session_duration_days)
    session_id = await data_manager.create_session(session_data.industry, expires_at)
    return {"session_id": session_id, "expires_at": expires_at}

@router.get("/{session_id}")
async def get_session(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get session data by ID"""
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/{session_id}")
async def update_session(
    session_id: str = Path(..., description="Session ID"),
    update_data: SessionUpdate = Body(...),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Update session data"""
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Prepare update data
    update_dict = {}
    
    if update_data.industry is not None:
        update_dict["industry"] = update_data.industry
        
    # Always update last_updated
    update_dict["last_updated"] = datetime.utcnow()
    
    # Extend expiry if requested
    if update_data.extends_expiry:
        update_dict["expires_at"] = datetime.utcnow() + timedelta(days=update_data.extension_days)
    
    # Update session
    success = await data_manager.update_session(session_id, update_dict)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update session")
    
    # Get updated session
    updated_session = await data_manager.get_session(session_id)
    return updated_session

@router.delete("/{session_id}")
async def delete_session(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """End and delete a session"""
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = await data_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    
    return {"success": True, "message": "Session deleted successfully"}
