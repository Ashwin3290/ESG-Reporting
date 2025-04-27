import logging
import os
import io
import uuid
import pandas as pd
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
import csv
from bson import ObjectId

from ..utils.filename_utils import sanitize_filename, get_file_extension, generate_unique_filename, parse_csv_columns

logger = logging.getLogger(__name__)

class FileService:
    """Service for managing file uploads and processing"""
    
    def __init__(self, db: AsyncIOMotorDatabase, fs: AsyncIOMotorGridFSBucket):
        self.db = db
        self.fs = fs
        
    async def upload_file(self, session_id: str, file: UploadFile) -> str:
        """
        Upload a file to GridFS and register it with a session
        
        Args:
            session_id: Session ID
            file: FastAPI UploadFile object
            
        Returns:
            File ID
        """
        # Generate a unique file ID
        file_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Get file metadata
        original_filename = file.filename
        file_size = len(content)
        content_type = file.content_type or self._guess_content_type(original_filename)
        
        # Create a unique filename to avoid collisions
        filename = generate_unique_filename(original_filename)
        
        # Store the file in GridFS
        grid_out = await self.fs.upload_from_stream(
            filename=filename,
            source=io.BytesIO(content),
            metadata={
                "file_id": file_id,
                "session_id": session_id,
                "original_filename": original_filename,
                "content_type": content_type,
                "upload_date": datetime.utcnow()
            }
        )
        
        # Create file metadata document
        file_metadata = {
            "file_id": file_id,
            "grid_id": grid_out,
            "filename": original_filename,
            "sanitized_filename": filename,
            "file_size": file_size,
            "content_type": content_type,
            "upload_date": datetime.utcnow(),
            "session_id": session_id
        }
        
        # Store file metadata
        await self.db.file_metadata.insert_one(file_metadata)
        
        # Update session with file reference
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "uploaded_files": {
                        "file_id": file_id,
                        "filename": original_filename,
                        "upload_date": datetime.utcnow(),
                        "file_size": file_size,
                        "content_type": content_type
                    }
                },
                "$set": {"last_updated": datetime.utcnow()}
            }
        )
        
        return file_id
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by ID"""
        metadata = await self.db.file_metadata.find_one({"file_id": file_id})
        if metadata:
            # Convert ObjectId to str
            metadata["_id"] = str(metadata["_id"])
            metadata["grid_id"] = str(metadata["grid_id"])
            return metadata
        return None
    
    async def get_file_content(self, file_id: str) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
        """
        Get file content and metadata by ID
        
        Returns:
            Tuple of (file_content, file_metadata)
        """
        metadata = await self.get_file_metadata(file_id)
        if not metadata:
            return None, None
        
        try:
            # Retrieve file from GridFS
            grid_id = metadata.get("grid_id")
            
            # Check if grid_id is a string and convert to ObjectId if needed
            if isinstance(grid_id, str):
                try:
                    grid_id = ObjectId(grid_id)
                except Exception as e:
                    logger.warning(f"Failed to convert grid_id to ObjectId: {str(e)}")
            
            # Try to get the file using the new GridFS bucket first
            try:
                grid_out = await self.fs.open_download_stream(grid_id)
                
                # Read file content
                chunks = []
                while chunk := await grid_out.readchunk():
                    chunks.append(chunk)
                
                content = b"".join(chunks)
                return content, metadata
            except Exception as e:
                # If that fails, try the legacy method through self.db.fs
                logger.warning(f"Could not retrieve file with new GridFS bucket: {str(e)}. Trying legacy method.")
                grid_out = await self.db.fs.find_one({"_id": grid_id})
                
                if grid_out:
                    # If we find the file through the legacy method, return its content
                    return grid_out.get("data", None), metadata
                else:
                    # If both methods fail, raise the exception
                    raise e
                
        except Exception as e:
            logger.error(f"Error retrieving file content: {str(e)}")
            return None, metadata
    
    async def get_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all files for a session"""
        session = await self.db.sessions.find_one(
            {"session_id": session_id},
            {"uploaded_files": 1}
        )
        
        if not session:
            return []
        
        return session.get("uploaded_files", [])
    
    async def delete_file(self, session_id: str, file_id: str) -> bool:
        """Delete a file"""
        # Get file metadata
        metadata = await self.get_file_metadata(file_id)
        if not metadata:
            return False
        
        # Check if file belongs to session
        if metadata.get("session_id") != session_id:
            return False
        
        try:
            # Delete file from GridFS
            grid_id = metadata.get("grid_id")
            
            # Check if grid_id is a string and convert to ObjectId if needed
            if isinstance(grid_id, str):
                try:
                    grid_id = ObjectId(grid_id)
                except Exception as e:
                    logger.warning(f"Failed to convert grid_id to ObjectId: {str(e)}")
            
            try:
                # Try the new method first
                await self.fs.delete(grid_id)
            except Exception as e:
                # If that fails, try the legacy method
                logger.warning(f"Could not delete file with new GridFS bucket: {str(e)}. Trying legacy method.")
                await self.db.fs.delete_one({"_id": grid_id})
            
            # Delete file metadata
            await self.db.file_metadata.delete_one({"file_id": file_id})
            
            # Update session
            await self.db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$pull": {"uploaded_files": {"file_id": file_id}},
                    "$set": {"last_updated": datetime.utcnow()}
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    async def get_file_columns(self, file_id: str) -> Optional[List[str]]:
        """
        Get CSV file columns
        
        Returns:
            List of column names
        """
        content, metadata = await self.get_file_content(file_id)
        if not content:
            return None
        
        # Check if file is CSV
        content_type = metadata.get("content_type", "")
        filename = metadata.get("filename", "")
        
        if not (content_type == "text/csv" or filename.lower().endswith(".csv")):
            logger.warning(f"File {file_id} is not a CSV file")
            return None
        
        try:
            # Try to parse CSV
            csv_content = content.decode("utf-8")
            return parse_csv_columns(csv_content)
        except Exception as e:
            logger.error(f"Error parsing CSV file: {str(e)}")
            return None
    
    async def load_file_as_dataframe(self, file_id: str, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load file as pandas DataFrame
        
        Returns:
            pandas DataFrame or None if file cannot be loaded
        """
        content, metadata = await self.get_file_content(file_id)
        if not content:
            return None
        
        # Check file type
        filename = metadata.get("filename", "")
        content_type = metadata.get("content_type", "")
        
        try:
            if filename.lower().endswith(".csv") or content_type == "text/csv":
                # Parse CSV
                csv_content = content.decode("utf-8")
                return pd.read_csv(io.StringIO(csv_content), nrows=nrows)
            elif filename.lower().endswith(".xlsx") or content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                # Parse Excel
                return pd.read_excel(io.BytesIO(content), nrows=nrows)
            elif filename.lower().endswith(".xls") or content_type == "application/vnd.ms-excel":
                # Parse Excel
                return pd.read_excel(io.BytesIO(content), nrows=nrows)
            else:
                logger.warning(f"Unsupported file type: {filename} ({content_type})")
                return None
        except Exception as e:
            logger.error(f"Error loading file as DataFrame: {str(e)}")
            return None
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        ext = get_file_extension(filename)
        
        content_types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "json": "application/json",
            "txt": "text/plain",
        }
        
        return content_types.get(ext, "application/octet-stream")
        
    async def get_file_sample(self, file_id: str, max_rows: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get a sample of data from a file to provide context for LLM mapping
        
        Args:
            file_id: File ID
            max_rows: Maximum number of rows to return
            
        Returns:
            List of dictionaries with sample data or None
        """
        try:
            # Load a small sample of the file as DataFrame
            df = await self.load_file_as_dataframe(file_id, nrows=max_rows)
            if df is None or df.empty:
                return None
                
            # Convert to list of dictionaries
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error getting file sample: {str(e)}")
            return None
            
    async def migrate_legacy_file(self, file_id: str) -> bool:
        """
        Migrate a file from the legacy storage format to the new GridFS bucket
        
        Args:
            file_id: File ID
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            # Get file metadata
            metadata = await self.get_file_metadata(file_id)
            if not metadata:
                return False
                
            # Get the file content using legacy method
            grid_id = metadata.get("grid_id")
            if isinstance(grid_id, str):
                try:
                    grid_id = ObjectId(grid_id)
                except Exception:
                    pass
                    
            legacy_file = await self.db.fs.find_one({"_id": grid_id})
            if not legacy_file or "data" not in legacy_file:
                return False
                
            # Upload to new GridFS bucket
            filename = metadata.get("sanitized_filename", f"migrated_{file_id}.bin")
            file_content = legacy_file.get("data")
            
            # Store in new GridFS bucket
            new_grid_id = await self.fs.upload_from_stream(
                filename=filename,
                source=io.BytesIO(file_content),
                metadata={
                    "file_id": file_id,
                    "session_id": metadata.get("session_id"),
                    "original_filename": metadata.get("filename"),
                    "content_type": metadata.get("content_type"),
                    "upload_date": datetime.utcnow(),
                    "migrated": True,
                    "original_grid_id": str(grid_id)
                }
            )
            
            # Update file metadata
            await self.db.file_metadata.update_one(
                {"file_id": file_id},
                {"$set": {
                    "grid_id": new_grid_id,
                    "migrated": True,
                    "migration_date": datetime.utcnow()
                }}
            )
            
            # Optionally, delete the old file
            # await self.db.fs.delete_one({"_id": grid_id})
            
            return True
        except Exception as e:
            logger.error(f"Error migrating legacy file {file_id}: {str(e)}")
            return False
