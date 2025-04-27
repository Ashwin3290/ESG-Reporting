from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from ...services.data_manager import DataManagerService
from ..dependencies import get_data_manager

router = APIRouter()

@router.get("/")
async def get_all_industries(
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get all available industries"""
    return await data_manager.get_all_industries()

@router.get("/search")
async def search_industries(
    q: str = Query(..., description="Search query"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Search industries by name"""
    return await data_manager.search_industries(q)

@router.get("/{industry_id}")
async def get_industry(
    industry_id: str,
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get industry details by ID"""
    industry = await data_manager.get_industry(industry_id)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry

@router.get("/{industry_id}/kpis")
async def get_industry_kpis_by_category(
    industry_id: str,
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get KPIs for a specific industry, organized by ESG category"""
    kpis = await data_manager.get_industry_kpis_by_category(industry_id)
    if not kpis:
        raise HTTPException(status_code=404, detail="Industry KPIs not found")
    return kpis
