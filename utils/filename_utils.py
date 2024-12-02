import os
import json
import logging
from typing import Dict, Optional, Tuple

def load_name_mapping() -> Dict[str, str]:
    """Load the KPI name mapping file"""
    mapping_file = "session_files/kpi_name_mapping.json"
    try:
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error loading KPI name mapping: {str(e)}")
        return {}

def save_name_mapping(mapping: Dict[str, str]) -> None:
    """Save the KPI name mapping to file"""
    mapping_file = "session_files/kpi_name_mapping.json"
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving KPI name mapping: {str(e)}")

def sanitize_and_map_filename(kpi_name: str) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize filename and maintain mapping to original.
    Returns tuple of (sanitized_name, updated_mapping)
    """
    # Load existing mapping
    mapping = load_name_mapping()
    
    # Check if this KPI already has a sanitized name
    for sanitized, original in mapping.items():
        if original == kpi_name:
            return sanitized, mapping

    # Sanitize the filename
    sanitized = kpi_name.replace('/', '_')
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
    
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    sanitized = sanitized.strip()
    
    # Create unique name if needed
    base_sanitized = sanitized
    counter = 1
    while sanitized in mapping and mapping[sanitized] != kpi_name:
        sanitized = f"{base_sanitized}_{counter}"
        counter += 1
    
    # Update mapping
    mapping[sanitized] = kpi_name
    save_name_mapping(mapping)
    
    return sanitized, mapping

def get_original_kpi_name(sanitized_name: str) -> Optional[str]:
    """Get original KPI name from sanitized filename"""
    mapping = load_name_mapping()
    # Remove _cal_data.csv if present
    if sanitized_name.endswith('_cal_data.csv'):
        sanitized_name = sanitized_name[:-13]
    return mapping.get(sanitized_name)

def get_kpi_filename(kpi_name: str) -> str:
    """Get the full filename for a KPI's calculated data"""
    sanitized_name, _ = sanitize_and_map_filename(kpi_name)
    return f"session_files/{sanitized_name}_cal_data.csv"