import os
import json
import logging
import uuid
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to ensure it's safe for filesystem use
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace problematic characters
    sanitized = filename.replace('/', '_')
    sanitized = sanitized.replace('\\', '_')
    sanitized = sanitized.replace(':', '_')
    sanitized = sanitized.replace('*', '_')
    sanitized = sanitized.replace('?', '_')
    sanitized = sanitized.replace('"', '_')
    sanitized = sanitized.replace('<', '_')
    sanitized = sanitized.replace('>', '_')
    sanitized = sanitized.replace('|', '_')
    sanitized = sanitized.replace('€', 'EUR')
    sanitized = sanitized.replace('$', 'USD')
    sanitized = sanitized.replace(',', '_')
    sanitized = ''.join(char for char in sanitized if ord(char) < 128)
    
    # Truncate if too long
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    sanitized = sanitized.strip()
    
    return sanitized

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Original filename
        
    Returns:
        File extension (lowercase, without the dot)
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()[1:] if ext else ""

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename based on the original filename
    
    Args:
        original_filename: Original filename
        
    Returns:
        Unique filename
    """
    filename, ext = os.path.splitext(original_filename)
    sanitized = sanitize_filename(filename)
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{sanitized}_{unique_id}{ext}"

def sanitize_and_map_kpi_name(kpi_name: str, mapping: Dict[str, str] = None) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize KPI name for use in filenames and maintain mapping to original names
    
    Args:
        kpi_name: Original KPI name
        mapping: Existing mapping dictionary (optional)
        
    Returns:
        Tuple of (sanitized_name, updated_mapping)
    """
    if mapping is None:
        mapping = {}
    
    # Check if this KPI already has a sanitized name
    for sanitized, original in mapping.items():
        if original == kpi_name:
            return sanitized, mapping
    
    # Sanitize the name
    sanitized = sanitize_filename(kpi_name)
    
    # Create unique name if needed
    base_sanitized = sanitized
    counter = 1
    while sanitized in mapping and mapping[sanitized] != kpi_name:
        sanitized = f"{base_sanitized}_{counter}"
        counter += 1
    
    # Update mapping
    mapping[sanitized] = kpi_name
    
    return sanitized, mapping

def get_original_kpi_name(sanitized_name: str, mapping: Dict[str, str]) -> Optional[str]:
    """
    Get original KPI name from sanitized name
    
    Args:
        sanitized_name: Sanitized KPI name
        mapping: Mapping dictionary
        
    Returns:
        Original KPI name or None if not found
    """
    # Remove _cal_data.csv if present
    if sanitized_name.endswith('_cal_data.csv'):
        sanitized_name = sanitized_name[:-13]
    
    return mapping.get(sanitized_name)

def get_kpi_filename(kpi_name: str, mapping: Dict[str, str] = None) -> Tuple[str, Dict[str, str]]:
    """
    Get the full filename for a KPI's calculated data
    
    Args:
        kpi_name: Original KPI name
        mapping: Existing mapping dictionary (optional)
        
    Returns:
        Tuple of (filename, updated_mapping)
    """
    if mapping is None:
        mapping = {}
    
    sanitized_name, updated_mapping = sanitize_and_map_kpi_name(kpi_name, mapping)
    return f"{sanitized_name}_cal_data.csv", updated_mapping

def parse_csv_columns(csv_content: str) -> List[str]:
    """
    Parse the header row from CSV content
    
    Args:
        csv_content: CSV content as string
        
    Returns:
        List of column names
    """
    if not csv_content:
        return []
    
    # Get the first line and split by comma
    lines = csv_content.splitlines()
    if not lines:
        return []
    
    header = lines[0]
    columns = [col.strip('"\'') for col in header.split(',')]
    
    return columns
