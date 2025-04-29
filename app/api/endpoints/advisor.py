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
    """Run ESG analysis based on session data with markdown output"""
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

@router.get("/report/{analysis_id}")
async def get_report(
    analysis_id: str = Path(..., description="Analysis ID"),
    data_manager: DataManagerService = Depends(get_data_manager)
):
    """Get the markdown report from a specific analysis"""
    analysis = await data_manager.get_analysis_result(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Extract report depending on what fields exist
    if "report" in analysis:
        markdown_report = analysis["report"]
    elif "markdown_report" in analysis:
        markdown_report = analysis["markdown_report"]
    elif "strategy" in analysis:
        markdown_report = analysis["strategy"]
    elif analysis.get("analysis_type") == "environmental_analysis" and "environmental" in analysis:
        markdown_report = analysis["environmental"]
    elif analysis.get("analysis_type") == "social_analysis" and "social" in analysis:
        markdown_report = analysis["social"]
    elif analysis.get("analysis_type") == "governance_analysis" and "governance" in analysis:
        markdown_report = analysis["governance"]
    else:
        # Fallback for old format or if report is missing
        markdown_report = "# Report Not Available\n\nThis analysis does not have a markdown report available."
    
    return {
        "analysis_id": analysis.get("_id") or analysis.get("analysis_id", ""),
        "report": markdown_report
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
        # Determine if analysis has a report
        has_report = any(key in analysis for key in ["report", "markdown_report", "strategy"])
        if not has_report:
            # Check category specific fields
            if analysis.get("analysis_type") == "environmental_analysis" and "environmental" in analysis:
                has_report = True
            elif analysis.get("analysis_type") == "social_analysis" and "social" in analysis:
                has_report = True
            elif analysis.get("analysis_type") == "governance_analysis" and "governance" in analysis:
                has_report = True
        
        analysis_history.append({
            "analysis_id": analysis.get("_id") or analysis.get("analysis_id", ""),
            "analysis_type": analysis.get("analysis_type"),
            "created_at": analysis.get("created_at"),
            "has_report": has_report
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
    
    # Convert MongoDB ObjectId to string if present
    if "_id" in analysis:
        analysis["_id"] = str(analysis["_id"])
        
    return analysis
