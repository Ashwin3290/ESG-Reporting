import logging
import json
import traceback
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.filename_utils import get_file_extension

logger = logging.getLogger(__name__)

class KPICalculatorService:
    """Service for calculating KPI values"""
    
    def __init__(self, db: AsyncIOMotorDatabase, file_service):
        self.db = db
        self.file_service = file_service
        self.calculation_formulas = {}
        
    async def initialize_formulas(self):
        """Initialize calculation formulas from KPI specifications"""
        # This will be called during startup to load formulas from the database
        cursor = self.db.kpi_specifications.find({}, {"name": 1, "calculation_logic": 1})
        
        async for doc in cursor:
            name = doc.get("name")
            formula = doc.get("calculation_logic")
            if name and formula:
                self.calculation_formulas[name] = formula
    
    async def get_calculation_formula(self, kpi_name: str) -> Optional[str]:
        """Get calculation formula for a KPI"""
        # If formulas are already loaded, return from cache
        if kpi_name in self.calculation_formulas:
            return self.calculation_formulas[kpi_name]
        
        # Otherwise, get from database
        spec = await self.db.kpi_specifications.find_one(
            {"name": kpi_name}, 
            {"calculation_logic": 1}
        )
        
        if spec and "calculation_logic" in spec:
            # Cache the formula
            formula = spec["calculation_logic"]
            self.calculation_formulas[kpi_name] = formula
            return formula
        
        return None
    
    async def calculate_kpi(self, session_id: str, kpi_name: str, file_id: str = None, 
                     mappings: Dict[str, str] = None, is_numeric: bool = True) -> Tuple[Optional[Any], Optional[str]]:
        """
        Calculate KPI value from input data
        
        Args:
            session_id: Session ID
            kpi_name: Name of KPI to calculate
            file_id: ID of file containing the data (optional)
            mappings: Column mappings (optional)
            is_numeric: Whether the KPI should return a numeric value
            
        Returns:
            Tuple of (KPI value, error message)
        """
        try:
            # Get KPI specification
            kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name})
            if not kpi_spec:
                return None, f"No specification found for KPI: {kpi_name}"
            
            # Get calculation formula for numeric KPIs
            calculation = None
            if is_numeric:
                calculation = await self.get_calculation_formula(kpi_name)
                if not calculation:
                    return None, f"No calculation formula found for KPI: {kpi_name}"
            
            # If no file provided, check for stored value
            if not file_id:
                # Get most recent calculated value
                cursor = self.db.calculated_kpis.find(
                    {"session_id": session_id, "kpi_name": kpi_name},
                    sort=[("calculation_date", -1)],
                    limit=1
                )
                
                async for doc in cursor:
                    return doc.get("value"), None
                
                return None, "No data available for calculation"
            
            # Get mappings if not provided
            if not mappings:
                # Get from session
                session = await self.db.sessions.find_one(
                    {"session_id": session_id},
                    {"column_mappings": 1}
                )
                
                if not session or not session.get("column_mappings") or kpi_name not in session["column_mappings"]:
                    return None, "No column mappings found for this KPI"
                
                mappings = session["column_mappings"][kpi_name]
            
            # Get required columns
            required_fields = [field["name"] for field in kpi_spec.get("required_data", [])]
            
            # Check if all required fields are mapped
            missing_fields = [field for field in required_fields if field not in mappings]
            if missing_fields:
                return None, f"Missing mappings for fields: {', '.join(missing_fields)}"
            
            # Load file as DataFrame
            df = await self.file_service.load_file_as_dataframe(file_id)
            if df is None or df.empty:
                return None, "Failed to load file or file is empty"
            
            # Create new DataFrame with mapped columns
            mapped_df = pd.DataFrame()
            for field in required_fields:
                col = mappings[field]
                if col not in df.columns:
                    return None, f"Mapped column '{col}' not found in file"
                
                mapped_df[field] = df[col]
            
            # For non-numeric KPIs, return the text value
            if not is_numeric:
                if len(mapped_df) > 0:
                    # Use the first field (there should be only one for text KPIs)
                    text_field = required_fields[0]
                    value = mapped_df[text_field].iloc[0]
                    
                    # Store the calculated value
                    await self.store_calculation_result(
                        session_id=session_id,
                        kpi_name=kpi_name,
                        value=value,
                        status="calculated"
                    )
                    
                    return value, None
                
                return None, "No data available for non-numeric KPI"
            
            # Calculate the KPI value
            try:
                # Use the calculation formula
                result = mapped_df.apply(
                    lambda row: eval(calculation, {"__builtins__": {}}, row.to_dict()), 
                    axis=1
                )
                
                # Get the mean value (if multiple rows)
                value = float(result.mean())
                
                # Store the calculated value
                await self.store_calculation_result(
                    session_id=session_id,
                    kpi_name=kpi_name,
                    value=value,
                    status="calculated",
                    metadata={
                        "file_id": file_id,
                        "row_count": len(mapped_df),
                        "formula": calculation
                    }
                )
                
                return value, None
            except Exception as e:
                error_msg = f"Calculation error: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return None, error_msg
        
        except Exception as e:
            error_msg = f"Error in KPI calculation: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return None, error_msg
    
    async def store_calculation_result(self, session_id: str, kpi_name: str, 
                               value: Any, status: str = "calculated", 
                               metadata: Dict[str, Any] = None) -> str:
        """
        Store KPI calculation result
        
        Args:
            session_id: Session ID
            kpi_name: KPI name
            value: Calculated value
            status: Calculation status
            metadata: Additional metadata
            
        Returns:
            Calculation ID
        """
        # Generate ID for this calculation
        import uuid
        calculation_id = str(uuid.uuid4())
        
        # Prepare document
        doc = {
            "calculation_id": calculation_id,
            "session_id": session_id,
            "kpi_name": kpi_name,
            "value": value,
            "status": status,
            "calculation_date": pd.Timestamp.now().to_pydatetime(),
            "metadata": metadata or {}
        }
        
        # Insert into database
        await self.db.calculated_kpis.insert_one(doc)
        
        return calculation_id
    
    async def batch_calculate_kpis(self, session_id: str, industry: str = None,
                           category: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate multiple KPIs in batch for a session
        
        Args:
            session_id: Session ID
            industry: Industry filter (optional)
            category: ESG category filter (optional)
            
        Returns:
            Dictionary of calculation results by KPI name
        """
        # Get session
        session = await self.db.sessions.find_one({"session_id": session_id})
        if not session:
            logger.error(f"Session not found: {session_id}")
            return {}
        
        # Get industry if not provided
        if not industry:
            industry = session.get("industry")
            if not industry:
                logger.error(f"No industry specified for session: {session_id}")
                return {}
        
        # Get KPIs for industry
        industry_doc = await self.db.industries.find_one({"industry": industry})
        if not industry_doc:
            logger.error(f"Industry not found: {industry}")
            return {}
        
        # Get KPI list filtered by category if specified
        kpis = []
        for kpi in industry_doc.get("kpis", []):
            if category:
                if kpi.get("esg_category", "").lower() == category.lower():
                    kpis.append(kpi)
            else:
                kpis.append(kpi)
        
        if not kpis:
            logger.warning(f"No KPIs found for industry: {industry}")
            return {}
        
        # Get files for session
        files = session.get("uploaded_files", [])
        if not files:
            logger.warning(f"No files found for session: {session_id}")
            return {}
        
        # Get mappings
        mappings = session.get("column_mappings", {})
        
        # Calculate KPIs
        results = {}
        for kpi in kpis:
            kpi_name = kpi.get("specification")
            if not kpi_name:
                continue
            
            # Check if mappings exist for this KPI
            if kpi_name not in mappings:
                continue
            
            # Use the most recent file
            file_id = files[-1]["file_id"] if files else None
            if not file_id:
                continue
            
            # Calculate KPI
            value, error = await self.calculate_kpi(
                session_id=session_id,
                kpi_name=kpi_name,
                file_id=file_id,
                mappings=mappings[kpi_name]
            )
            
            results[kpi_name] = {
                "value": value,
                "status": "error" if error else "calculated",
                "error": error
            }
        
        return results
