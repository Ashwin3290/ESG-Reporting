import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ..utils.llm_helpers import GeminiClient

logger = logging.getLogger(__name__)

class ESGAdvisorService:
    """Service for ESG analysis and advisory using LLM"""
    
    def __init__(self, gemini_client: GeminiClient, db: AsyncIOMotorDatabase):
        self.gemini_client = gemini_client
        self.db = db
    
    async def run_analysis(self, session_id: str, analysis_type: str, industry: str) -> Dict[str, Any]:
        """
        Run ESG analysis on session data, returning a markdown report
        
        Args:
            session_id: Session ID
            analysis_type: Type of analysis to run ('full', 'environmental', 'social', 'governance', 'strategy')
            industry: Industry name
            
        Returns:
            Analysis results as markdown
        """
        # Get session KPI data
        kpi_data = await self._get_session_kpis(session_id)
        if not kpi_data:
            return {"error": "No KPI data available for analysis"}
        
        # Run analysis based on type
        try:
            if analysis_type == "full":
                result = await self._run_full_analysis(session_id, kpi_data, industry)
            elif analysis_type in ["environmental", "social", "governance"]:
                result = await self._analyze_category(session_id, analysis_type, kpi_data, industry)
            elif analysis_type == "strategy":
                # For strategy only, develop strategy
                result = await self._develop_strategy_markdown(session_id, kpi_data, industry)
            else:
                return {"error": f"Unknown analysis type: {analysis_type}"}
            
            return result
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def chat(self, session_id: str, message: str, industry: str, context: Dict[str, Any] = None) -> str:
        """
        Chat with the ESG advisor
        
        Args:
            session_id: Session ID
            message: User message
            industry: Industry name
            context: Previous analysis context (optional)
            
        Returns:
            AI response
        """
        # Get KPI data for context
        kpi_data = await self._get_session_kpis(session_id)
        
        # Build prompt
        prompt = self._build_chat_prompt(message, industry, kpi_data, context)
        
        # Call LLM
        try:
            response = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.7  # Higher temperature for more conversational responses
            )
            
            # Store chat history
            await self._store_chat_message(session_id, message, response)
            
            return response
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
    
    async def _run_full_analysis(self, session_id: str, kpi_data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Run complete ESG analysis and return a single markdown report"""
        # Generate the full analysis report in markdown format
        prompt = f"""
        You are an ESG (Environmental, Social, and Governance) analyst creating a comprehensive report for a company in the {industry} industry.
        
        Data:
        {json.dumps(kpi_data, indent=2)}
        
        Please create a complete ESG analysis report in markdown format that includes:
        
        1. Executive Summary
        2. Environmental Analysis
           - Current performance assessment
           - Comparison to industry benchmarks
           - Key risks and vulnerabilities
           - Improvement opportunities
        3. Social Analysis
           - Current performance assessment
           - Comparison to industry benchmarks
           - Key risks and vulnerabilities
           - Improvement opportunities
        4. Governance Analysis
           - Current performance assessment
           - Comparison to industry benchmarks
           - Key risks and vulnerabilities
           - Improvement opportunities
        5. Strategic Recommendations
           - Prioritized improvement opportunities
           - Action plans for addressing identified risks
           - Implementation timeline (short-term and medium-term)
           - Required resources
        6. Implementation Roadmap
        
        Your report should be well-structured with clear markdown headings, bullet points, and formatting.
        Do not use JSON format - provide the report directly in markdown.
        """
        
        # Call LLM
        try:
            markdown_report = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=4096
            )
            
            # Store analysis
            analysis_id = await self._store_analysis_result(
                session_id=session_id,
                analysis_type="full",
                result={"report": markdown_report}
            )
            
            return {
                "analysis_id": analysis_id,
                "report": markdown_report
            }
                
        except Exception as e:
            logger.error(f"Error generating full analysis: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "report": f"# Error Generating Report\n\nAn error occurred while generating the ESG analysis: {str(e)}"
            }
    
    async def _analyze_category(self, session_id: str, category: str, data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Analyze specific ESG category and return markdown"""
        # Extract category-specific data
        category_data = data.get(category, {})
        
        # Create prompt for category analysis in markdown
        prompt = f"""
        You are an ESG analyst specializing in {category} performance analysis for the {industry} industry.
        
        {category.capitalize()} metrics:
        {json.dumps(category_data, indent=2)}
        
        Please provide a comprehensive analysis of this {category} data in markdown format, including:
        
        1. Current Performance Assessment
        2. Comparison to Industry Benchmarks
        3. Key Risks and Vulnerabilities
        4. Strengths and Areas of Excellence
        5. Improvement Opportunities
        
        Format your response as a well-structured markdown document with headings and bullet points.
        Do not use JSON format - provide the analysis directly in markdown.
        """
        
        # Call LLM
        try:
            markdown_analysis = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=2048
            )
            
            # Store category analysis
            analysis_id = await self._store_analysis_result(
                session_id=session_id,
                analysis_type=f"{category}_analysis",
                result={category: markdown_analysis}
            )
            
            return {
                "analysis_id": analysis_id,
                "report": markdown_analysis
            }
                
        except Exception as e:
            logger.error(f"Error in {category} analysis: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "report": f"# Error Analyzing {category.capitalize()}\n\nAn error occurred: {str(e)}"
            }
    
    async def _develop_strategy_markdown(self, session_id: str, data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Develop a comprehensive ESG strategy in markdown format"""
        # Create prompt for strategy development
        prompt = f"""
        You are an ESG strategy consultant developing improvements for a company in the {industry} industry.
        
        ESG data:
        {json.dumps(data, indent=2)}
        
        Please develop a comprehensive ESG strategy in markdown format that includes:
        
        1. Prioritized Improvement Opportunities
           - For environmental performance
           - For social performance
           - For governance performance
        
        2. Action Plans
           - Specific actions to address identified risks
           - Steps for implementing improvements
           
        3. Implementation Timeline
           - Short-term (1 year) actions
           - Medium-term (3 year) actions
           
        4. Resource Requirements
           - Human resources needed
           - Financial resources needed
           - Technology and systems requirements
           
        5. Expected Benefits and Impact Metrics
        
        Format your response as a well-structured markdown document with headings, bullet points, and clear sections.
        Do not use JSON format - provide the strategy directly in markdown.
        """
        
        # Call LLM
        try:
            markdown_strategy = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=2048
            )
            
            # Store strategy
            strategy_id = await self._store_analysis_result(
                session_id=session_id,
                analysis_type="strategy",
                result={"strategy": markdown_strategy}
            )
            
            return {
                "strategy_id": strategy_id,
                "report": markdown_strategy
            }
                
        except Exception as e:
            logger.error(f"Error in strategy development: {str(e)}")
            return {
                "error": f"Strategy development failed: {str(e)}",
                "report": f"# Error Developing Strategy\n\nAn error occurred: {str(e)}"
            }
    
    async def _get_session_kpis(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all KPI data for a session"""
        # Get calculated KPIs from database
        cursor = self.db.calculated_kpis.find(
            {"session_id": session_id},
            sort=[("calculation_date", -1)]
        )
        
        # Group by KPI name and take most recent
        kpi_values = {}
        seen_kpis = set()
        
        async for doc in cursor:
            kpi_name = doc.get("kpi_name")
            if kpi_name and kpi_name not in seen_kpis:
                seen_kpis.add(kpi_name)
                kpi_values[kpi_name] = doc.get("value")
        
        # Get session to determine industry
        session = await self.db.sessions.find_one({"session_id": session_id})
        if not session:
            return {}
            
        industry = session.get("industry")
        if not industry:
            return {"error": "No industry specified for session"}
        
        # Get industry KPIs
        industry_doc = await self.db.industries.find_one({"industry": industry})
        if not industry_doc:
            return {}
        
        # Organize KPIs by category
        categorized_kpis = {
            "environmental": {},
            "social": {},
            "governance": {}
        }
        
        # Map KPIs to categories based on industry document
        for kpi in industry_doc.get("kpis", []):
            spec = kpi.get("specification")
            category = kpi.get("esg_category", "").lower()
            
            if spec and category in categorized_kpis and spec in kpi_values:
                categorized_kpis[category][spec] = kpi_values[spec]
        
        return categorized_kpis
    
    async def _store_analysis_result(self, session_id: str, analysis_type: str, result: Dict[str, Any]) -> str:
        """Store analysis result in database"""
        # Generate ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # Prepare document
        doc = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "analysis_type": analysis_type,
            "created_at": datetime.utcnow()
        }
        
        # Add result fields
        for key, value in result.items():
            doc[key] = value
        
        # Insert into database
        await self.db.analysis_results.insert_one(doc)
        
        return analysis_id
    
    async def _store_chat_message(self, session_id: str, user_message: str, ai_response: str) -> str:
        """Store chat message in database"""
        # Generate ID
        import uuid
        message_id = str(uuid.uuid4())
        
        # Prepare document
        doc = {
            "message_id": message_id,
            "session_id": session_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.utcnow()
        }
        
        # Insert into database
        await self.db.chat_history.insert_one(doc)
        
        return message_id
    
    def _build_chat_prompt(self, message: str, industry: str, kpi_data: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build prompt for chat with context"""
        # Base prompt
        prompt = f"""
        You are an ESG advisor for a company in the {industry} industry. You provide expert guidance on environmental, social, and governance matters.
        
        Current ESG data:
        {json.dumps(kpi_data, indent=2)}
        """
        
        # Add context if available
        if context:
            # Check if the context contains a report or strategy
            if "report" in context:
                prompt += f"""
                Previous analysis report:
                {context["report"]}
                """
            elif "strategy" in context:
                prompt += f"""
                Previous strategy analysis:
                {context["strategy"]}
                """
            elif context.get("analysis_type") == "environmental_analysis" and "environmental" in context:
                prompt += f"""
                Previous environmental analysis:
                {context["environmental"]}
                """
            elif context.get("analysis_type") == "social_analysis" and "social" in context:
                prompt += f"""
                Previous social analysis:
                {context["social"]}
                """
            elif context.get("analysis_type") == "governance_analysis" and "governance" in context:
                prompt += f"""
                Previous governance analysis:
                {context["governance"]}
                """
            else:
                # Fallback to simple JSON for other cases
                prompt += f"""
                Previous analysis:
                {json.dumps(context, indent=2)}
                """
        
        # Add user message
        prompt += f"""
        User question: {message}
        
        Please provide a helpful, informative response based on the ESG data and previous analysis (if available).
        Your response should be conversational and easy to understand while still providing expert ESG guidance.
        """
        
        return prompt
