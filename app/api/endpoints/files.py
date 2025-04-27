from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Query
from fastapi.responses import StreamingResponse
from typing import List
import io

from ...services.file_service import FileService
from ...services.data_manager import DataManagerService
from ..dependencies import get_file_service, get_data_manager

router = APIRouter()

@router.post("/upload")
async def upload_file(
    session_id: str = Query(..., description="Session ID"),
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Upload a file to a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Upload file
    try:
        file_id = await file_service.upload_file(session_id, file)
        return {"file_id": file_id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.get("/{file_id}")
async def get_file_metadata(
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service)
):
    """Get file metadata by ID"""
    file_info = await file_service.get_file_metadata(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info

@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service)
):
    """Get file content by ID"""
    file_content, file_metadata = await file_service.get_file_content(file_id)
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file content as streaming response
    return StreamingResponse(
        io.BytesIO(file_content), 
        media_type=file_metadata.get("content_type", "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={file_metadata.get('filename', 'file')}"}
    )

@router.get("/session/{session_id}")
async def get_session_files(
    session_id: str = Path(..., description="Session ID"),
    file_service: FileService = Depends(get_file_service),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get all files for a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get files
    files = await file_service.get_session_files(session_id)
    return files

@router.delete("/{file_id}")
async def delete_file(
    file_id: str = Path(..., description="File ID"),
    session_id: str = Query(..., description="Session ID"),
    file_service: FileService = Depends(get_file_service),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Delete a file"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete file
    success = await file_service.delete_file(session_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found or already deleted")
    
    return {"success": True, "message": "File deleted successfully"}

@router.get("/{file_id}/columns")
async def get_file_columns(
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service)
):
    """Get CSV file columns"""
    columns = await file_service.get_file_columns(file_id)
    if not columns:
        raise HTTPException(status_code=404, detail="File not found or not a valid CSV")
    
    return {"file_id": file_id, "columns": columns}
