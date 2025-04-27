from fastapi import APIRouter, Depends, HTTPException, Path, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...services.advisor import ESGAdvisorService
from ...services.data_manager import DataManagerService
from ..dependencies import get_advisor_service, get_data_manager

router = APIRouter()

class AnalysisRequest(BaseModel):
    session_id: str
    analysis_type: str = "full"  # 'full', 'environmental', 'social', 'governance', 'strategy'
    industry: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str
    analysis_id: Optional[str] = None

@router.post("/analyze")
async def run_analysis(
    request: AnalysisRequest,
    advisor_service: ESGAdvisorService = Depends(get_advisor_service),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Run ESG analysis based on session data"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get industry if not provided
    industry = request.industry
    if not industry:
        industry = session.get("industry")
        if not industry:
            raise HTTPException(status_code=400, detail="No industry specified for analysis")
    
    # Run analysis
    try:
        result = await advisor_service.run_analysis(
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            industry=industry
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/chat")
async def chat_with_advisor(
    request: ChatRequest,
    advisor_service: ESGAdvisorService = Depends(get_advisor_service),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Chat with the ESG advisor"""
    # Verify session exists
    session = await data_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get session info
    industry = session.get("industry")
    if not industry:
        raise HTTPException(status_code=400, detail="No industry assigned to session")
    
    # Get latest analysis if available
    context = None
    if request.analysis_id:
        analysis = await data_manager.get_analysis_result(request.analysis_id)
        if analysis:
            context = analysis
    else:
        # Try to get most recent analysis
        analyses = await data_manager.get_session_analyses(request.session_id)
        if analyses:
            # Sort by created_at and take the most recent
            analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            context = analyses[0]
    
    # Chat with advisor
    try:
        response = await advisor_service.chat(
            session_id=request.session_id,
            message=request.message,
            industry=industry,
            context=context
        )
        
        return {
            "response": response,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/recommendations/{session_id}")
async def get_recommendations(
    session_id: str = Path(..., description="Session ID"),
    analysis_id: Optional[str] = None,
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get recommendations from a specific analysis or the most recent one"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get analysis
    if analysis_id:
        analysis = await data_manager.get_analysis_result(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
    else:
        # Get most recent analysis
        analyses = await data_manager.get_session_analyses(session_id)
        if not analyses:
            raise HTTPException(status_code=404, detail="No analyses found for session")
        
        # Sort by created_at and take the most recent
        analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        analysis = analyses[0]
    
    # Extract recommendations
    recommendations = analysis.get("recommendations", [])
    strategies = analysis.get("strategies", {})
    
    return {
        "analysis_id": analysis.get("_id"),
        "recommendations": recommendations,
        "strategies": strategies
    }

@router.get("/history/{session_id}")
async def get_analysis_history(
    session_id: str = Path(..., description="Session ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get analysis history for a session"""
    # Verify session exists
    session = await data_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get analyses
    analyses = await data_manager.get_session_analyses(session_id)
    if not analyses:
        return {"analyses": []}
    
    # Sort by created_at
    analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Format response
    analysis_history = []
    for analysis in analyses:
        analysis_history.append({
            "analysis_id": analysis.get("_id"),
            "analysis_type": analysis.get("analysis_type"),
            "created_at": analysis.get("created_at"),
            "has_recommendations": bool(analysis.get("recommendations", []))
        })
    
    return {"analyses": analysis_history}

@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: str = Path(..., description="Analysis ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get a specific analysis by ID"""
    analysis = await data_manager.get_analysis_result(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis
