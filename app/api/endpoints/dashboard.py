from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Dict, Any, List, Optional

from ...services.data_manager import DataManagerService
from ..dependencies import get_data_manager

router = APIRouter()

@router.get("/overview/{session_id}")
async def get_dashboard_overview(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get overview data for dashboard"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPI data
    kpi_data = await data_manager.get_session_kpis(session_id)
    if not kpi_data:
        return {
            "overall_score": 0,
            "completion_rate": 0,
            "categories": {
                "environmental": {"score": 0, "kpi_count": 0},
                "social": {"score": 0, "kpi_count": 0},
                "governance": {"score": 0, "kpi_count": 0}
            }
        }
    
    # Get industry KPIs
    industry = session.get("industry")
    if not industry:
        raise HTTPException(status_code=400, detail="Session has no industry assigned")
    
    industry_kpis = await data_manager.get_industry_kpis_by_category(industry)
    
    # Calculate scores
    env_kpis = kpi_data.get("environmental", {})
    soc_kpis = kpi_data.get("social", {})
    gov_kpis = kpi_data.get("governance", {})
    
    env_score = await data_manager.calculate_category_score(env_kpis)
    soc_score = await data_manager.calculate_category_score(soc_kpis)
    gov_score = await data_manager.calculate_category_score(gov_kpis)
    
    # Calculate overall score
    total_score = 0
    score_count = 0
    
    if env_score > 0:
        total_score += env_score
        score_count += 1
    
    if soc_score > 0:
        total_score += soc_score
        score_count += 1
    
    if gov_score > 0:
        total_score += gov_score
        score_count += 1
    
    overall_score = total_score / score_count if score_count > 0 else 0
    
    # Calculate completion rate
    total_kpis = sum(len(kpis) for kpis in industry_kpis.values())
    completed_kpis = sum(len(kpis) for kpis in [env_kpis, soc_kpis, gov_kpis])
    completion_rate = (completed_kpis / total_kpis * 100) if total_kpis > 0 else 0
    
    return {
        "overall_score": overall_score,
        "completion_rate": completion_rate,
        "categories": {
            "environmental": {
                "score": env_score,
                "kpi_count": len(env_kpis)
            },
            "social": {
                "score": soc_score,
                "kpi_count": len(soc_kpis)
            },
            "governance": {
                "score": gov_score,
                "kpi_count": len(gov_kpis)
            }
        }
    }

@router.get("/category/{category}/{session_id}")
async def get_category_data(
    category: str = Path(..., description="ESG category"),
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get data for a specific ESG category"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate category
    if category.lower() not in ["environmental", "social", "governance"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    # Get KPI data
    kpi_data = await data_manager.get_session_kpis(session_id)
    category_kpis = kpi_data.get(category.lower(), {})
    
    # Get KPI details
    kpi_details = []
    for kpi_name, value in category_kpis.items():
        kpi_spec = await data_manager.get_kpi_spec(kpi_name)
        if kpi_spec:
            normalized_value, original_value, unit = await data_manager.normalize_kpi_value(
                kpi_name, value
            )
            
            kpi_details.append({
                "kpi_name": kpi_name,
                "original_value": original_value,
                "normalized_value": normalized_value,
                "unit": unit,
                "status": "On Track" if normalized_value >= 75 else "Needs Attention"
            })
    
    category_score = await data_manager.calculate_category_score(category_kpis)
    
    return {
        "category": category,
        "score": category_score,
        "kpi_count": len(category_kpis),
        "kpi_details": kpi_details
    }

@router.get("/charts/comparison/{session_id}")
async def get_kpi_comparison_chart(
    session_id: str = Path(..., description="Session ID"),
    category: Optional[str] = Query(None, description="ESG category filter"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get data for KPI comparison chart"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPI data
    kpi_data = await data_manager.get_session_kpis(session_id)
    
    # Filter by category if provided
    if category:
        if category.lower() not in ["environmental", "social", "governance"]:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        filtered_data = {category.lower(): kpi_data.get(category.lower(), {})}
    else:
        filtered_data = kpi_data
    
    # Prepare chart data
    chart_data = []
    for cat, kpis in filtered_data.items():
        for kpi_name, value in kpis.items():
            normalized_value, original_value, unit = await data_manager.normalize_kpi_value(
                kpi_name, value
            )
            
            chart_data.append({
                "kpi_name": kpi_name,
                "category": cat,
                "normalized_value": normalized_value,
                "original_value": original_value,
                "unit": unit,
                "industry_avg": 75  # This could be dynamic based on actual industry data
            })
    
    return {
        "chart_data": chart_data
    }

@router.get("/charts/radar/{session_id}")
async def get_category_radar_chart(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get data for category radar chart"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get KPI data
    kpi_data = await data_manager.get_session_kpis(session_id)
    
    # Calculate statistics for each category
    categories = ["environmental", "social", "governance"]
    radar_data = {}
    
    for category in categories:
        category_kpis = kpi_data.get(category, {})
        normalized_values = []
        
        for kpi_name, value in category_kpis.items():
            normalized_value, _, _ = await data_manager.normalize_kpi_value(
                kpi_name, value
            )
            normalized_values.append(normalized_value)
        
        if normalized_values:
            radar_data[category] = {
                "average": sum(normalized_values) / len(normalized_values),
                "maximum": max(normalized_values) if normalized_values else 0,
                "minimum": min(normalized_values) if normalized_values else 0,
                "median": sorted(normalized_values)[len(normalized_values)//2] if normalized_values else 0
            }
        else:
            radar_data[category] = {
                "average": 0,
                "maximum": 0,
                "minimum": 0,
                "median": 0
            }
    
    return {
        "radar_data": radar_data
    }
