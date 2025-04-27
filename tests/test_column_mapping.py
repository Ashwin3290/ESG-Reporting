import pytest
import pandas as pd
import json
import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.column_mapping import ColumnMappingService

# Sample test data
SAMPLE_KPI_SPEC = {
    "name": "Energy consumption, total",
    "is_numerical": True,
    "required_data": [
        {
            "name": "total_energy_consumption",
            "description": "Total energy consumed across all operations and facilities",
            "type": "number"
        },
        {
            "name": "energy_by_source",
            "description": "Breakdown of energy consumption by source (electricity, fuel, etc.)",
            "type": "number"
        }
    ],
    "calculation_logic": "total_energy_consumption + energy_by_source",
    "unit_of_measurement": "Megawatt hours (MWh)"
}

SAMPLE_FILE_COLUMNS = [
    "date", 
    "facility_name", 
    "energy_consumption", 
    "electricity_usage",
    "fuel_consumption",
    "notes"
]

SAMPLE_DATA = [
    {
        "date": "2024-01-01",
        "facility_name": "Plant A",
        "energy_consumption": 1250.5,
        "electricity_usage": 800.2,
        "fuel_consumption": 450.3,
        "notes": "Regular operation"
    },
    {
        "date": "2024-01-01",
        "facility_name": "Plant B",
        "energy_consumption": 980.1,
        "electricity_usage": 620.5,
        "fuel_consumption": 359.6,
        "notes": "Partial shutdown for maintenance"
    }
]

# Expected LLM response for mapping
MOCK_LLM_RESPONSE = """
I'll analyze the required fields and available columns to find the best matches.

For the required fields:
1. total_energy_consumption: This needs a column that represents the total energy used across operations.
2. energy_by_source: This needs columns that break down energy by different sources.

Looking at the available columns:
- "energy_consumption" appears to directly match "total_energy_consumption"
- "electricity_usage" and "fuel_consumption" together represent energy by source, but we need to pick one for mapping.

```json
{
  "total_energy_consumption": "energy_consumption",
  "energy_by_source": "electricity_usage"
}
```

I've chosen "electricity_usage" for energy_by_source because it's likely the larger component, but "fuel_consumption" would also be valid.
"""

@pytest.fixture
async def column_mapping_service():
    """Create a ColumnMappingService with mocked dependencies"""
    # Mock the LLM client
    mock_llm = AsyncMock()
    mock_llm.generate_text.return_value = MOCK_LLM_RESPONSE
    
    # Mock the database
    mock_db = AsyncMock()
    mock_db.kpi_specifications.find_one.return_value = SAMPLE_KPI_SPEC
    
    # Create the service with mocks
    service = ColumnMappingService(mock_llm, mock_db)
    return service

@pytest.mark.asyncio
async def test_exact_matching(column_mapping_service):
    """Test exact matching functionality"""
    result = await column_mapping_service.perform_exact_matching(
        kpi_name="Energy consumption, total",
        file_columns=["total_energy_consumption", "other_column", "energy_by_source"]
    )
    
    assert "total_energy_consumption" in result
    assert "energy_by_source" in result
    assert result["total_energy_consumption"] == "total_energy_consumption"
    assert result["energy_by_source"] == "energy_by_source"

@pytest.mark.asyncio
async def test_simplified_matching(column_mapping_service):
    """Test matching with simplified column names"""
    result = await column_mapping_service.perform_exact_matching(
        kpi_name="Energy consumption, total",
        file_columns=["total energy consumption", "other_column", "energy by source"]
    )
    
    assert "total_energy_consumption" in result
    assert "energy_by_source" in result

@pytest.mark.asyncio
async def test_llm_matching(column_mapping_service):
    """Test LLM-based matching"""
    # Mock the LLM response
    column_mapping_service.gemini_client.generate_text.return_value = MOCK_LLM_RESPONSE
    
    result = await column_mapping_service.perform_llm_matching(
        kpi_name="Energy consumption, total",
        file_columns=SAMPLE_FILE_COLUMNS,
        kpi_spec=SAMPLE_KPI_SPEC,
        sample_data=SAMPLE_DATA
    )
    
    assert "total_energy_consumption" in result
    assert "energy_by_source" in result
    assert result["total_energy_consumption"] == "energy_consumption"
    assert result["energy_by_source"] == "electricity_usage"

@pytest.mark.asyncio
async def test_extract_json_from_text(column_mapping_service):
    """Test the JSON extraction from text function"""
    # Test with code block format
    text_with_code_block = """
    Here's the mapping:
    
    ```json
    {
        "field1": "column1",
        "field2": "column2"
    }
    ```
    
    This is the best mapping based on my analysis.
    """
    
    result = column_mapping_service._extract_json_from_text(text_with_code_block)
    parsed = json.loads(result)
    assert "field1" in parsed
    assert parsed["field1"] == "column1"
    
    # Test with inline JSON
    inline_json = 'The mapping is: {"field1": "column1", "field2": "column2"}'
    result = column_mapping_service._extract_json_from_text(inline_json)
    parsed = json.loads(result)
    assert "field2" in parsed
    assert parsed["field2"] == "column2"

if __name__ == "__main__":
    # Run the tests manually
    asyncio.run(pytest.main(["-xvs", __file__]))
