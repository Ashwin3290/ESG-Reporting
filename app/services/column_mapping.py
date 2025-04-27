import logging
import json
import re
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.llm_helpers import GeminiClient

logger = logging.getLogger(__name__)

class ColumnMappingService:
    """Service for mapping CSV columns to KPI fields using exact and LLM-based matching"""
    
    def __init__(self, gemini_client: GeminiClient, db: AsyncIOMotorDatabase):
        self.gemini_client = gemini_client
        self.db = db
    
    async def perform_exact_matching(self, kpi_name: str, file_columns: List[str], kpi_spec: Dict[str, Any] = None) -> Dict[str, str]:
        """"Use rule-based approach to find exact or close matches"""
        """
        Match columns by exact name or simple transformations
        
        Args:
            kpi_name: KPI name
            file_columns: List of column names from the file
            kpi_spec: KPI specification (optional)
            
        Returns:
            Dictionary of {field_name: column_name} mappings
        """
        # Get KPI specification if not provided
        if not kpi_spec:
            kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name}, {"_id": 0})
            if not kpi_spec:
                logger.warning(f"KPI specification not found: {kpi_name}")
                return {}
        
        # Get required fields
        required_fields = kpi_spec.get("required_data", [])
        if not required_fields:
            logger.warning(f"No required fields found for KPI: {kpi_name}")
            return {}
        
        # Initialize mappings
        mappings = {}
        
        # Match by exact name
        for field in required_fields:
            field_name = field.get("name")
            field_desc = field.get("description", "")
            
            if not field_name:
                continue
            
            # Try exact match
            if field_name in file_columns:
                mappings[field_name] = field_name
                continue
            
            # Try case-insensitive match
            for col in file_columns:
                if col.lower() == field_name.lower():
                    mappings[field_name] = col
                    break
            
            # If still not matched, try simplified match (remove spaces, underscores, etc.)
            if field_name not in mappings:
                simplified_field = self._simplify_string(field_name)
                for col in file_columns:
                    simplified_col = self._simplify_string(col)
                    if simplified_field == simplified_col:
                        mappings[field_name] = col
                        break
            
            # Try matching field description with columns
            if field_name not in mappings and field_desc:
                # Extract key terms from description
                key_terms = self._extract_key_terms(field_desc)
                
                # Check if any column contains key terms
                for col in file_columns:
                    if any(term.lower() in col.lower() for term in key_terms):
                        mappings[field_name] = col
                        break
        
        return mappings
    
    async def perform_llm_matching(self, kpi_name: str, file_columns: List[str], 
                           kpi_spec: Dict[str, Any] = None, 
                           existing_mappings: Dict[str, str] = None, 
                           sample_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
        """Use LLM to perform semantic matching for remaining unmatched fields"""
        """
        Use LLM to match columns semantically
        
        Args:
            kpi_name: KPI name
            file_columns: List of column names from the file
            kpi_spec: KPI specification (optional)
            existing_mappings: Existing mappings to skip (optional)
            
        Returns:
            Dictionary of {field_name: column_name} mappings
        """
        # Get KPI specification if not provided
        if not kpi_spec:
            kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name}, {"_id": 0})
            if not kpi_spec:
                logger.warning(f"KPI specification not found: {kpi_name}")
                return {}
        
        # Initialize with existing mappings if provided
        mappings = existing_mappings.copy() if existing_mappings else {}
        
        # Get required fields
        required_fields = kpi_spec.get("required_data", [])
        if not required_fields:
            logger.warning(f"No required fields found for KPI: {kpi_name}")
            return mappings
        
        # Filter out already mapped fields
        mapped_fields = set(mappings.keys())
        unmapped_fields = [f for f in required_fields if f.get("name") not in mapped_fields]
        
        if not unmapped_fields:
            return mappings
        
        # Filter out already mapped columns
        mapped_columns = set(mappings.values())
        unmapped_columns = [c for c in file_columns if c not in mapped_columns]
        
        if not unmapped_columns:
            return mappings
        
        # Use LLM to match remaining fields
        field_descriptions = "\n".join([
            f"- {f.get('name')}: {f.get('description')} (Type: {f.get('type')})"
            for f in unmapped_fields
        ])
        
        columns_list = "\n".join([f"- {col}" for col in unmapped_columns])
        
        # Add sample data if available for better context
        sample_data_str = ""
        if sample_data and len(sample_data) > 0:
            sample_rows = sample_data[:3]  # Limit to first 3 rows
            sample_data_str = "\nSample data (first 3 rows):\n"
            for row in sample_rows:
                # Only include unmapped columns in sample
                filtered_row = {k: v for k, v in row.items() if k in unmapped_columns}
                sample_data_str += f"{filtered_row}\n"
        
        prompt = f"""
        You are a data analyst mapping CSV columns to required fields for a KPI calculation.
        
        KPI Name: {kpi_name}
        
        Required Fields:
        {field_descriptions}
        
        Available CSV Columns:
        {columns_list}
        {sample_data_str}
        
        Your task is to map each required field to the most semantically appropriate column name from the available columns list.
        
        Follow these rules for matching:
        1. First, look for exact matches or close variations (case differences, underscores vs spaces).
        2. Then look for semantic equivalence (e.g., "total_employees" might match "fte_count").
        3. Consider common abbreviations and conventions in business data.
        4. If a field has multiple potential matches, choose the one with the highest confidence.
        5. If there is no reasonable match for a field, assign it null.
        
        Return your answer as a JSON object with the following format:
        ```json
        {{
            "required_field_name": "matched_csv_column",
            "another_required_field": "another_matched_column",
            "field_without_match": null
        }}
        ```
        
        First explain your reasoning for each mapping decision, then provide the JSON object.
        """
        
        try:
            # Call Gemini API
            response = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.1
            )
            
            # Extract JSON from response
            try:
                json_str = self._extract_json_from_text(response)
                llm_mappings = json.loads(json_str)
                
                # Filter out null values
                llm_mappings = {k: v for k, v in llm_mappings.items() if v is not None}
                
                # Validate mappings (ensure columns exist)
                validated_mappings = {
                    k: v for k, v in llm_mappings.items() 
                    if v in unmapped_columns and k not in mappings
                }
                
                # Combine with existing mappings
                mappings.update(validated_mappings)
                
                return mappings
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from LLM response: {e}")
                logger.debug(f"Response text: {response}")
                return mappings
        except Exception as e:
            logger.error(f"Error using LLM for column mapping: {e}")
            return mappings
    
    def _simplify_string(self, s: str) -> str:
        """Simplify string for matching by removing spaces, underscores, etc."""
        if not s:
            return ""
        
        # Convert to lowercase
        s = s.lower()
        
        # Remove special characters and spaces
        return re.sub(r'[^a-z0-9]', '', s)
    
    def _extract_key_terms(self, desc: str) -> List[str]:
        """Extract key terms from a description"""
        if not desc:
            return []
        
        # Split by spaces and punctuation
        terms = re.findall(r'\b\w+\b', desc.lower())
        
        # Filter out common words
        stopwords = {'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to'}
        return [t for t in terms if t not in stopwords and len(t) > 2]
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON object from text response"""
        if not text:
            return "{}"
        
        # Try structured approach first - look for code blocks with JSON
        code_pattern = r'```(?:json)?\s*([\{\[].*?[\}\]])\s*```'
        match = re.search(code_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Look for JSON object
        json_pattern = r'\{[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            # Return the longest match as it's likely the most complete JSON
            return max(matches, key=len)
            
        # Look for array
        array_pattern = r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        matches = re.findall(array_pattern, text, re.DOTALL)
        if matches:
            return max(matches, key=len)
        
        # If no JSON found, try to extract key-value pairs and create JSON
        extracted = {}
        kv_pattern = r'"([^"]+)"\s*:\s*"([^"]+)"'
        for k, v in re.findall(kv_pattern, text):
            extracted[k] = v
            
        if extracted:
            return json.dumps(extracted)
            
        # Last resort - return empty object
        logger.warning(f"Could not extract JSON from text: {text[:100]}...")
        return "{}"
