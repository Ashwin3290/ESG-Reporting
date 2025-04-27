import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)

class DataManagerService:
    """Service for managing ESG data, adapted from existing DataManager"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    async def get_all_industries(self) -> List[Dict[str, Any]]:
        """Get list of all industries"""
        cursor = self.db.industries.find({}, {"_id": 0})
        industries = []
        async for doc in cursor:
            # Group by sector
            sector = doc.get("sector")
            industry = doc.get("industry")
            
            # Add to list if not already present
            if sector and industry:
                industries.append({
                    "sector": sector,
                    "industry": industry
                })
        
        return industries
    
    async def search_industries(self, query: str) -> List[Dict[str, Any]]:
        """Search industries by name"""
        query = query.lower()
        all_industries = await self.get_all_industries()
        
        # Filter industries that match the query
        return [
            industry for industry in all_industries
            if query in industry["sector"].lower() or query in industry["industry"].lower()
        ]
    
    async def get_industry(self, industry_name: str) -> Optional[Dict[str, Any]]:
        """Get industry details by name"""
        industry = await self.db.industries.find_one({"industry": industry_name}, {"_id": 0})
        return industry
    
    async def get_industry_kpis_by_category(self, industry_name: str) -> Dict[str, List[str]]:
        """Get KPIs for an industry organized by ESG category"""
        industry = await self.get_industry(industry_name)
        if not industry:
            return {}
        
        # Initialize categories
        categorized_kpis = {
            "environmental": [],
            "social": [],
            "governance": []
        }
        
        # Categorize KPIs
        kpis = industry.get("kpis", [])
        for kpi in kpis:
            category = kpi.get("esg_category", "").lower()
            if category in categorized_kpis:
                categorized_kpis[category].append(kpi.get("specification"))
        
        return categorized_kpis
    
    async def get_all_kpi_specs(self) -> Dict[str, Any]:
        """Get all KPI specifications"""
        cursor = self.db.kpi_specifications.find({}, {"_id": 0})
        specs = {}
        async for doc in cursor:
            name = doc.get("name")
            if name:
                specs[name] = doc
        
        return specs
    
    async def get_kpi_spec(self, kpi_name: str) -> Optional[Dict[str, Any]]:
        """Get KPI specification by name"""
        spec = await self.db.kpi_specifications.find_one({"name": kpi_name}, {"_id": 0})
        return spec
    
    async def get_kpi_reference(self, kpi_name: str) -> Optional[Dict[str, Any]]:
        """Get KPI reference values by name"""
        ref = await self.db.kpi_references.find_one({"name": kpi_name}, {"_id": 0})
        return ref
    
    async def get_kpis_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get KPIs by ESG category"""
        cursor = self.db.kpi_specifications.find({"category": category}, {"_id": 0})
        kpis = []
        async for doc in cursor:
            kpis.append(doc)
        
        return kpis
    
    async def create_session(self, industry: str = None, expires_at: datetime = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        if not expires_at:
            expires_at = datetime.utcnow() + timedelta(days=7)
        
        session_doc = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "expires_at": expires_at,
            "industry": industry,
            "uploaded_files": [],
            "column_mappings": {},
            "mapping_status": {}
        }
        
        await self.db.sessions.insert_one(session_doc)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        session = await self.db.sessions.find_one({"session_id": session_id})
        if session:
            # Convert ObjectId to str
            session["_id"] = str(session["_id"])
            return session
        return None
    
    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update session data"""
        # Always update last_updated
        update_data["last_updated"] = datetime.utcnow()
        
        result = await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        result = await self.db.sessions.delete_one({"session_id": session_id})
        return result.deleted_count > 0
    
    async def update_column_mappings(self, session_id: str, kpi_name: str, mappings: Dict[str, str]) -> bool:
        """Update column mappings for a KPI"""
        # Prepare update data
        mapping_key = f"column_mappings.{kpi_name}"
        status_key = f"mapping_status.{kpi_name}"
        
        update_data = {
            mapping_key: mappings,
            status_key: "complete" if mappings else "incomplete",
            "last_updated": datetime.utcnow()
        }
        
        result = await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def get_column_mappings(self, session_id: str, kpi_name: str) -> Optional[Dict[str, str]]:
        """Get column mappings for a KPI"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        mappings = session.get("column_mappings", {}).get(kpi_name, {})
        return mappings
    
    async def store_calculated_kpi(self, session_id: str, kpi_name: str, value: Any, status: str = "calculated") -> str:
        """Store calculated KPI value"""
        kpi_id = str(uuid.uuid4())
        
        kpi_doc = {
            "kpi_id": kpi_id,
            "session_id": session_id,
            "kpi_name": kpi_name,
            "value": value,
            "status": status,
            "calculation_date": datetime.utcnow()
        }
        
        await self.db.calculated_kpis.insert_one(kpi_doc)
        return kpi_id
    
    async def get_calculated_kpi(self, session_id: str, kpi_name: str) -> Optional[Any]:
        """Get calculated KPI value"""
        # Get the most recent calculation
        kpi = await self.db.calculated_kpis.find_one(
            {"session_id": session_id, "kpi_name": kpi_name},
            sort=[("calculation_date", -1)]
        )
        
        if kpi:
            return kpi.get("value")
        return None
    
    async def get_session_kpis(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all calculated KPIs for a session, organized by category"""
        cursor = self.db.calculated_kpis.find(
            {"session_id": session_id},
            sort=[("calculation_date", -1)]
        )
        
        # Group by KPI name and take most recent
        kpi_values = {}
        seen_kpis = set()
        
        async for kpi in cursor:
            kpi_name = kpi.get("kpi_name")
            if kpi_name and kpi_name not in seen_kpis:
                seen_kpis.add(kpi_name)
                kpi_values[kpi_name] = kpi.get("value")
        
        # Organize by category
        categorized_kpis = {
            "environmental": {},
            "social": {},
            "governance": {}
        }
        
        # Get industry to determine KPI categories
        session = await self.get_session(session_id)
        industry = session.get("industry") if session else None
        
        if industry:
            industry_kpis = await self.get_industry_kpis_by_category(industry)
            
            # Assign KPIs to categories
            for category, kpis in industry_kpis.items():
                for kpi_name in kpis:
                    if kpi_name in kpi_values:
                        categorized_kpis[category][kpi_name] = kpi_values[kpi_name]
        else:
            # If no industry, try to categorize based on KPI specifications
            for kpi_name, value in kpi_values.items():
                spec = await self.get_kpi_spec(kpi_name)
                if spec:
                    category = spec.get("category", "").lower()
                    if category in categorized_kpis:
                        categorized_kpis[category][kpi_name] = value
        
        return categorized_kpis
    
    async def calculate_category_score(self, category_kpis: Dict[str, Any]) -> float:
        """Calculate normalized score for a category"""
        if not category_kpis:
            return 0.0
        
        normalized_values = []
        for kpi_name, value in category_kpis.items():
            normalized_value, _, _ = await self.normalize_kpi_value(kpi_name, value)
            normalized_values.append(normalized_value)
        
        if not normalized_values:
            return 0.0
        
        return sum(normalized_values) / len(normalized_values)
    
    async def normalize_kpi_value(self, kpi_name: str, value: Any) -> Tuple[float, Any, str]:
        """
        Normalize KPI value to 0-100 scale
        
        Returns:
            Tuple of (normalized_value, original_value, unit)
        """
        # Get KPI reference values
        ref = await self.get_kpi_reference(kpi_name)
        
        if not ref:
            # Default normalization if no reference found
            return 50.0, value, ""
        
        best = ref.get("best_score", 0)
        worst = ref.get("worst_score", 0)
        unit = ref.get("unit", "")
        
        if best == worst:
            return 50.0, value, unit
        
        # Determine if higher is better
        is_higher_better = best > worst
        
        try:
            value_float = float(value)
            
            if is_higher_better:
                normalized = ((value_float - worst) / (best - worst)) * 100
            else:
                normalized = ((value_float - best) / (worst - best)) * 100
                normalized = 100 - normalized
            
            # Clamp to 0-100 range
            normalized = max(0, min(100, normalized))
            
            return normalized, value, unit
        except (ValueError, TypeError):
            # For non-numeric values
            return 50.0, value, unit
    
    async def store_analysis_result(self, session_id: str, analysis_type: str, result: Dict[str, Any]) -> str:
        """Store analysis result"""
        analysis_id = str(uuid.uuid4())
        
        analysis_doc = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "analysis_type": analysis_type,
            "created_at": datetime.utcnow(),
            "environmental": result.get("environmental", {}),
            "social": result.get("social", {}),
            "governance": result.get("governance", {}),
            "strategies": result.get("strategies", {}),
            "recommendations": result.get("recommendations", [])
        }
        
        await self.db.analysis_results.insert_one(analysis_doc)
        return analysis_id
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result by ID"""
        analysis = await self.db.analysis_results.find_one({"analysis_id": analysis_id})
        if analysis:
            # Convert ObjectId to str
            analysis["_id"] = str(analysis["_id"])
            return analysis
        return None
    
    async def get_session_analyses(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a session"""
        cursor = self.db.analysis_results.find({"session_id": session_id})
        analyses = []
        
        async for analysis in cursor:
            # Convert ObjectId to str
            analysis["_id"] = str(analysis["_id"])
            analyses.append(analysis)
        
        return analyses
