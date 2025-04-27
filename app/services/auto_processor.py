import logging
import pandas as pd
import json
import os
import re
import numpy as np
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import io

from ..utils.llm_helpers import GeminiClient
from ..core.config import settings

logger = logging.getLogger(__name__)

class AutoProcessorService:
    """Service for automated processing of ESG data"""
    
    def __init__(self, db: AsyncIOMotorDatabase, gemini_client: GeminiClient):
        self.db = db
        self.gemini_client = gemini_client
        self._load_calculation_formulas()
    
    def _load_calculation_formulas(self):
        """Load KPI calculation formulas"""
        self.kpi_calculations = {
            # Environmental KPIs
            "Energy consumption, total": lambda row: row.get('total_energy_consumption', 0) + row.get('energy_by_source', 0),
            "GHG emissions, total (scope I,II)": lambda row: row.get('scope_1_emissions', 0) + row.get('scope_2_emissions', 0),
            "Total CO²,NOx, SOx, VOC emissions in million tonnes": lambda row: row.get('co2_emissions', 0) + row.get('nox_emissions', 0) + row.get('sox_emissions', 0) + row.get('voc_emissions', 0),
            "Improvement rate of product energy efficiency compared to previous year": lambda row: ((row.get('current_energy_efficiency', 0) - row.get('previous_energy_efficiency', 0)) / max(row.get('previous_energy_efficiency', 1), 1)) * 100,
            "Water consumption in m³": lambda row: row.get('total_water_consumption', 0) + row.get('water_by_source', 0),
            "Total waste in tonnes": lambda row: row.get('scope_1_waste', 0),
            "Percentage of total waste which is recycled": lambda row: (row.get('recycled_waste', 0) / max(row.get('total_waste', 1), 1)) * 100,
            "Hazardous waste total in tonnes total": lambda row: row.get('hazardous_waste', 0),

            # Workforce and HR KPIs
            "Percentage of FTE leaving p.a./total FTE": lambda row: (row.get('fte_leaving', 0) / max(row.get('total_fte_start', 1), 1)) * 100,
            "Average expenses on training per FTE p.a": lambda row: row.get('total_training_expenses', 0) / max(row.get('total_fte', 1), 1),
            "Age structure/distribution (number of FTEs per age group, 10-year intervals)": lambda row: row.get('age_distribution', 0),
            "Total number of fatalities in relation to FTEsS04-04 II Total number of injuries in relation to FTEs": lambda row: row.get('fatalities', 0) / max(row.get('total_fte', 1), 1),

            # Financial and Business KPIs
            "Total amount of bonuses, incentives and stock options paid out in â‚¬,$": lambda row: row.get('innovation_bonuses', 0) + row.get('innovation_incentives', 0),
            "Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices": lambda row: row.get('legal_expenses', 0) + row.get('fines_paid', 0),
            "Percentage of revenues in regions with Transparency International corruptionindex below 6.0": lambda row: (row.get('revenue_by_region', 0) / max(row.get('total_revenue', 1), 1)) * 100,
            "Percentage of new products or modified products introduced lessproducts than 12 months ago": lambda row: (row.get('new_product_revenue', 0) / max(row.get('total_revenue', 1), 1)) * 100,
            "CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)": lambda row: (row.get('esg_investments', 0) / max(row.get('total_capex', 1), 1)) * 100,
            "Share of market by product, product line, segment, region or total": lambda row: (row.get('product_revenue', 0) / max(row.get('total_market_revenue', 1), 1)) * 100,
            "Capacity utilisation as a percentage of total available facilities": lambda row: (row.get('actual_capacity_used', 0) / max(row.get('total_capacity', 1), 1)) * 100,

            # Compliance and Political KPIs
            "Contributions to political parties as a percentage of total revenuespolitical parties": lambda row: (row.get('political_contributions', 0) / max(row.get('total_revenue', 1), 1)) * 100,
            "Percentage of total customers surveyed comprising satisfied customers": lambda row: (row.get('customers_surveyed', 0) / max(row.get('total_customers', 1), 1)) * 100,
            "Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent": lambda row: row.get('total_suppliers', 0),
            "Total number of FTEs who receive 90 % of total amount of bonuses, incentivesand stock options": lambda row: row.get('innovation_compensation_recipients', 0),
            "Total cost of relocation in monetary terms i.e. currency incl. Indemnity, pay-off,relocation of jobs outplacement, hiring, training, consulting": lambda row: row.get('relocation_costs', 0),
        }
        
        # Generic handlers for common patterns
        self.pattern_handlers = {
            "percentage": lambda numerator, denominator, row: (row.get(numerator, 0) / max(row.get(denominator, 1), 1)) * 100,
            "sum": lambda fields, row: sum(row.get(field, 0) for field in fields),
            "ratio": lambda numerator, denominator, row: row.get(numerator, 0) / max(row.get(denominator, 1), 1),
            "single_field": lambda field, row: row.get(field, 0)
        }
    
    async def map_columns(self, session_id: str) -> Dict[str, Any]:
        """
        Map columns from all files in the session to KPI fields
        
        1. Get industry from session
        2. Load relevant KPIs for that industry
        3. Map columns in all uploaded files to KPI fields
        
        Returns:
            Mapping results
        """
        logger.info(f"Starting column mapping for session {session_id}")
        
        # Get session
        session = await self.db.sessions.find_one({"session_id": session_id})
        if not session:
            return {"error": "Session not found"}
        
        # Get industry
        industry = session.get("industry")
        if not industry:
            return {"error": "No industry assigned to session"}
        
        # Get KPIs for industry
        kpis_by_category = await self._get_industry_kpis(industry)
        if not kpis_by_category:
            return {"error": "No KPIs found for industry"}
        
        # Get uploaded files from session
        files = session.get("uploaded_files", [])
        if not files:
            return {"error": "No files found in session"}
        
        logger.info(f"Found {len(files)} files in session {session_id}")
        
        # Process each file to get columns
        file_columns = {}
        for file in files:
            file_id = file.get("file_id")
            if not file_id:
                continue
                
            # Use the file service through direct DB access to get columns
            try:
                # First get file metadata
                file_doc = await self.db.file_metadata.find_one({"file_id": file_id})
                if not file_doc:
                    logger.warning(f"File {file_id} not found in file_metadata")
                    continue
                
                # Get file content from GridFS
                from bson import ObjectId
                grid_id = file_doc.get("grid_id")
                
                # Convert to ObjectId if it's a string
                if isinstance(grid_id, str):
                    grid_id = ObjectId(grid_id)
                
                # Get file content directly from GridFS collection
                grid_out = await self.db.fs.files.find_one({"_id": grid_id})
                if not grid_out:
                    logger.warning(f"GridFS file {grid_id} not found")
                    continue
                
                # Get content from chunks
                chunks = []
                async for chunk in self.db.fs.chunks.find({"files_id": grid_id}).sort("n", 1):
                    chunks.append(chunk["data"])
                
                content = b"".join(chunks)
                
                # Parse CSV
                try:
                    # Write to temp file first
                    temp_file_path = f"{settings.UPLOAD_DIR}/temp_{file_id}.csv"
                    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                    
                    with open(temp_file_path, 'wb') as f:
                        f.write(content)
                    
                    # Read with pandas
                    df = pd.read_csv(temp_file_path)
                    columns = df.columns.tolist()
                    
                    # Delete temp file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                    
                    # Store columns
                    file_columns[file_id] = columns
                    logger.info(f"File {file_id}: Found {len(columns)} columns")
                except Exception as e:
                    logger.error(f"Error parsing CSV file {file_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error getting file columns for {file_id}: {str(e)}")
        
        if not file_columns:
            return {"error": "No valid CSV files found in session"}
        
        # Auto-map columns for all KPIs
        mapping_results = await self._auto_map_columns(
            session_id=session_id,
            kpis_by_category=kpis_by_category,
            file_columns=file_columns
        )
        
        # Update session status
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "last_column_mapping": datetime.utcnow(),
                "mapping_status": "complete"
            }}
        )
        
        return {
            "session_id": session_id,
            "industry": industry,
            "mapping_results": mapping_results,
            "file_count": len(file_columns)
        }
    
    async def calculate_kpis(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate all KPIs for mapped columns
        
        1. Get industry from session
        2. Load relevant KPIs for that industry
        3. Calculate all KPIs using stored column mappings
        
        Returns:
            Calculation results
        """
        logger.info(f"Starting KPI calculation for session {session_id}")
        
        # Get session
        session = await self.db.sessions.find_one({"session_id": session_id})
        if not session:
            return {"error": "Session not found"}
        
        # Get industry
        industry = session.get("industry")
        if not industry:
            return {"error": "No industry assigned to session"}
        
        # Get KPIs for industry
        kpis_by_category = await self._get_industry_kpis(industry)
        if not kpis_by_category:
            return {"error": "No KPIs found for industry"}
        
        # Get file IDs from session
        files = session.get("uploaded_files", [])
        if not files:
            return {"error": "No files found in session"}
        
        file_ids = [file.get("file_id") for file in files if file.get("file_id")]
        
        # Calculate all KPIs
        calculation_results = await self._calculate_all_kpis(
            session_id=session_id,
            kpis_by_category=kpis_by_category,
            file_ids=file_ids
        )
        
        # Update session status
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "last_calculation": datetime.utcnow(),
                "calculation_status": "complete"
            }}
        )
        
        return {
            "session_id": session_id,
            "industry": industry,
            "calculation_results": calculation_results
        }
    
    async def _get_industry_kpis(self, industry: str) -> Dict[str, List[str]]:
        """Get KPIs for an industry by category"""
        industry_doc = await self.db.industries.find_one({"industry": industry})
        if not industry_doc:
            return {}
        
        categorized_kpis = {
            "environmental": [],
            "social": [],
            "governance": []
        }
        
        for kpi in industry_doc.get("kpis", []):
            category = kpi.get("esg_category", "").lower()
            spec = kpi.get("specification")
            
            if category in categorized_kpis and spec:
                categorized_kpis[category].append(spec)
        
        return categorized_kpis
    
    def _sanitize_field_name(self, name: str) -> str:
        """
        Sanitize field name for MongoDB to avoid dots and special characters
        
        MongoDB does not allow dots in field names, and it's good to sanitize for
        other special characters as well.
        """
        # Replace dots, spaces, and special characters with underscores
        sanitized = re.sub(r'[.\s,()]', '_', name)
        # Ensure name starts with a letter or underscore (MongoDB requirement)
        if not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = f"_{sanitized}"
        return sanitized
    
    async def _auto_map_columns(
        self,
        session_id: str,
        kpis_by_category: Dict[str, List[str]],
        file_columns: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Automatically map columns for all KPIs
        
        First tries exact matches, then uses LLM for remaining fields
        """
        mapping_results = {
            "mapped_kpis": [],
            "unmapped_kpis": [],
            "mapping_details": {}
        }
        
        # Flatten KPI list
        all_kpis = []
        for category_kpis in kpis_by_category.values():
            all_kpis.extend(category_kpis)
        
        # Initialize a mapping dictionary for the session
        mapping_dict = {}
        kpi_status_dict = {}
        
        # Process each KPI
        for kpi_name in all_kpis:
            # Get KPI specification
            kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name})
            if not kpi_spec:
                mapping_results["unmapped_kpis"].append(kpi_name)
                continue
            
            required_fields = kpi_spec.get("required_data", [])
            if not required_fields:
                mapping_results["unmapped_kpis"].append(kpi_name)
                continue
            
            # Try exact matching first
            mappings = {}
            
            # Combine columns from all files
            all_columns = []
            for file_cols in file_columns.values():
                all_columns.extend(file_cols)
            
            # Remove duplicates
            all_columns = list(set(all_columns))
            
            # Try exact matching
            for field in required_fields:
                field_name = field.get("name")
                if field_name in all_columns:
                    mappings[field_name] = field_name
            
            # Check if all fields are mapped
            all_mapped = len(mappings) == len(required_fields)
            
            # If not all mapped, use LLM for remaining fields
            if not all_mapped:
                llm_mappings = await self._get_llm_mapping_suggestions(
                    kpi_name=kpi_name,
                    unmapped_fields=[f for f in required_fields if f.get("name") not in mappings],
                    available_columns=all_columns,
                    kpi_description=kpi_spec.get("description", "")
                )
                
                # Update mappings
                for field_name, column_name in llm_mappings.items():
                    if column_name in all_columns:
                        mappings[field_name] = column_name
            
            # Check final mapping status
            if len(mappings) == len(required_fields):
                mapping_results["mapped_kpis"].append(kpi_name)
                kpi_status = "complete"
            else:
                mapping_results["unmapped_kpis"].append(kpi_name)
                kpi_status = "incomplete"
            
            # Store mapping details
            mapping_results["mapping_details"][kpi_name] = {
                "mappings": mappings,
                "complete": len(mappings) == len(required_fields),
                "mapped_count": len(mappings),
                "total_fields": len(required_fields)
            }
            
            # Add to the mapping dictionary
            sanitized_kpi_name = self._sanitize_field_name(kpi_name)
            mapping_dict[sanitized_kpi_name] = mappings
            kpi_status_dict[sanitized_kpi_name] = kpi_status
        
        # Update session with all mappings at once
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "column_mappings": mapping_dict,
                "kpi_mapping_status": kpi_status_dict
            }}
        )
        
        return mapping_results
    
    async def _get_llm_mapping_suggestions(
        self,
        kpi_name: str,
        unmapped_fields: List[Dict[str, str]],
        available_columns: List[str],
        kpi_description: str = ""
    ) -> Dict[str, str]:
        """
        Use LLM to suggest mappings between KPI fields and available columns
        """
        # Create prompt for LLM
        prompt = f"""
        You are an ESG data expert. I need to map CSV columns to required fields for KPI calculations.
        
        KPI Name: {kpi_name}
        KPI Description: {kpi_description}
        
        Available CSV columns:
        {json.dumps(available_columns, indent=2)}
        
        Unmapped fields that need a corresponding column:
        {json.dumps(unmapped_fields, indent=2)}
        
        For each unmapped field, select the most appropriate column from the available columns.
        If there's no good match, leave it as null.
        
        Return your answer as a JSON object with field names as keys and column names as values.
        Format: {{"field_name": "matched_column_name", ...}}
        """
        
        try:
            # Call LLM
            response = await self.gemini_client.generate_text(
                model="gemini-1.5-flash",
                prompt=prompt,
                temperature=0.1
            )
            
            # Extract JSON from response
            import re
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                suggestions = json.loads(json_str)
                return suggestions
            else:
                logger.warning("Could not extract JSON from LLM response")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting LLM mapping suggestions: {str(e)}")
            return {}
    
    async def _calculate_all_kpis(
        self,
        session_id: str,
        kpis_by_category: Dict[str, List[str]],
        file_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate all KPIs for mapped columns
        """
        calculation_results = {
            "calculated": {},
            "errors": {},
            "skipped": []
        }
        
        # Get session
        session = await self.db.sessions.find_one({"session_id": session_id})
        if not session:
            return calculation_results
        
        # Get column mappings
        column_mappings = session.get("column_mappings", {})
        
        # Get file contents and create temp files
        file_paths = {}
        for file_id in file_ids:
            try:
                # Get file metadata
                file_doc = await self.db.file_metadata.find_one({"file_id": file_id})
                if not file_doc:
                    logger.warning(f"File {file_id} not found in file_metadata")
                    continue
                
                # Get GridFS file ID
                from bson import ObjectId
                grid_id = file_doc.get("grid_id")
                
                # Convert to ObjectId if it's a string
                if isinstance(grid_id, str):
                    grid_id = ObjectId(grid_id)
                
                # Get file content
                grid_out = await self.db.fs.files.find_one({"_id": grid_id})
                if not grid_out:
                    logger.warning(f"GridFS file {grid_id} not found")
                    continue
                
                # Get content from chunks
                chunks = []
                async for chunk in self.db.fs.chunks.find({"files_id": grid_id}).sort("n", 1):
                    chunks.append(chunk["data"])
                
                content = b"".join(chunks)
                
                # Create a temporary file
                temp_file_path = f"{settings.UPLOAD_DIR}/temp_{file_id}.csv"
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                
                with open(temp_file_path, 'wb') as f:
                    f.write(content)
                
                file_paths[file_id] = temp_file_path
                
            except Exception as e:
                logger.error(f"Error retrieving file {file_id}: {str(e)}")
        
        # Flatten KPI list
        all_kpis = []
        for category_kpis in kpis_by_category.values():
            all_kpis.extend(category_kpis)
        
        # Initialize dictionaries for storing results
        kpi_results = {}
        kpi_status = {}
        
        # Process each KPI
        for kpi_name in all_kpis:
            try:
                # Get sanitized KPI name for MongoDB field
                sanitized_kpi_name = self._sanitize_field_name(kpi_name)
                
                # Skip if no mapping for this KPI
                if sanitized_kpi_name not in column_mappings or not column_mappings[sanitized_kpi_name]:
                    calculation_results["skipped"].append(kpi_name)
                    kpi_status[sanitized_kpi_name] = "skipped"
                    continue
                
                # Get KPI specification
                kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name})
                if not kpi_spec:
                    calculation_results["errors"][kpi_name] = "KPI specification not found"
                    kpi_status[sanitized_kpi_name] = "error"
                    continue
                
                # Check if KPI is numerical or text-based
                is_numerical = kpi_spec.get("is_numerical", True)
                
                # Find first available file
                selected_file_id = None
                for file_id in file_ids:
                    if file_id in file_paths:
                        selected_file_id = file_id
                        break
                
                if not selected_file_id:
                    calculation_results["errors"][kpi_name] = "No valid files available"
                    kpi_status[sanitized_kpi_name] = "error"
                    continue
                
                # Load data from file
                file_path = file_paths[selected_file_id]
                df = pd.read_csv(file_path)
                
                # Prepare data for calculation
                calculation_df = pd.DataFrame()
                mappings = column_mappings[sanitized_kpi_name]
                
                for field_name, column_name in mappings.items():
                    if column_name in df.columns:
                        calculation_df[field_name] = df[column_name]
                
                # Calculate KPI value
                if is_numerical:
                    # Apply the calculation function to each row
                    result = self._calculate_kpi_value(kpi_name, calculation_df)
                else:
                    # For text-based KPIs, just take the first value
                    field_name = list(mappings.keys())[0]
                    if field_name in calculation_df.columns and len(calculation_df) > 0:
                        result = calculation_df[field_name].iloc[0]
                    else:
                        calculation_results["errors"][kpi_name] = "No data available for calculation"
                        kpi_status[sanitized_kpi_name] = "error"
                        continue
                
                # Store result
                kpi_id = await self._store_kpi_result(session_id, kpi_name, result)
                
                # Add to results
                calculation_results["calculated"][kpi_name] = {
                    "value": result,
                    "unit": kpi_spec.get("unit_of_measurement", ""),
                    "kpi_id": kpi_id
                }
                
                # Add to dictionaries for session update
                kpi_results[sanitized_kpi_name] = result
                kpi_status[sanitized_kpi_name] = "calculated"
            
            except Exception as e:
                sanitized_kpi_name = self._sanitize_field_name(kpi_name)
                logger.error(f"Error calculating KPI {kpi_name}: {str(e)}")
                calculation_results["errors"][kpi_name] = str(e)
                kpi_status[sanitized_kpi_name] = "error"
        
        # Clean up temporary files
        for file_path in file_paths.values():
            try:
                os.remove(file_path)
            except:
                pass
        
        # Update session with all results at once
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "kpi_results": kpi_results,
                "kpi_status": kpi_status
            }}
        )
        
        return calculation_results
    
    def _calculate_kpi_value(self, kpi_name: str, df: pd.DataFrame) -> float:
        """
        Calculate KPI value based on KPI name and dataframe
        """
        # Check if we have a specific handler for this KPI
        if kpi_name in self.kpi_calculations:
            # Apply the handler to each row and take the mean
            try:
                # Convert DataFrame to list of dictionaries
                rows = df.to_dict('records')
                
                # If no rows, return 0
                if not rows:
                    return 0.0
                
                # Apply the calculation function to each row
                results = [self.kpi_calculations[kpi_name](row) for row in rows]
                
                # Return the mean
                return float(sum(results) / len(results))
            except Exception as e:
                logger.error(f"Error in specific handler for {kpi_name}: {str(e)}")
                # Fall back to numeric mean
                return self._fallback_calculation(df)
        
        # If no specific handler, use a generic approach
        return self._fallback_calculation(df)
    
    def _fallback_calculation(self, df: pd.DataFrame) -> float:
        """Fallback calculation method when specific handlers fail"""
        # Use the mean of all numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            # Calculate mean of all means
            return float(numeric_df.mean().mean())
        return 0.0
    
    async def _store_kpi_result(self, session_id: str, kpi_name: str, value: Any) -> str:
        """Store calculated KPI value"""
        # Generate KPI ID
        import uuid
        kpi_id = str(uuid.uuid4())
        
        # Create KPI document
        kpi_doc = {
            "kpi_id": kpi_id,
            "session_id": session_id,
            "kpi_name": kpi_name,
            "value": value,
            "calculation_date": datetime.utcnow()
        }
        
        # Insert into database
        await self.db.calculated_kpis.insert_one(kpi_doc)
        
        return kpi_id
