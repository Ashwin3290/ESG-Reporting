import logging
import json
import asyncio
import re
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ..utils.llm_helpers import GeminiClient, extract_json_from_text

logger = logging.getLogger(__name__)

class ESGAdvisorService:
    """Service for ESG analysis and advisory using LLM"""
    
    def __init__(self, gemini_client: GeminiClient, db: AsyncIOMotorDatabase):
        self.gemini_client = gemini_client
        self.db = db
    
    async def run_analysis(self, session_id: str, analysis_type: str, industry: str) -> Dict[str, Any]:
        """
        Run ESG analysis on session data
        
        Args:
            session_id: Session ID
            analysis_type: Type of analysis to run ('full', 'environmental', 'social', 'governance', 'strategy')
            industry: Industry name
            
        Returns:
            Analysis results in a format that matches the agentic chatbot output
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
                # Get the most recent analyses for all categories
                categories = await self._get_latest_category_analyses(session_id)
                if not categories:
                    # If no previous analyses, run analyses for all categories
                    categories = {
                        "environmental": await self._analyze_category(session_id, "environmental", kpi_data, industry),
                        "social": await self._analyze_category(session_id, "social", kpi_data, industry),
                        "governance": await self._analyze_category(session_id, "governance", kpi_data, industry)
                    }
                
                # Develop strategy based on category analyses
                result = await self._develop_strategy(session_id, categories, industry)
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
        """Run complete ESG analysis with the structure matching the agentic chatbot"""
        # First process and validate the data
        processed_data = await self._process_data(kpi_data, industry)
        
        # Run analyses for each category in parallel
        env_task = asyncio.create_task(
            self._analyze_category(session_id, "environmental", processed_data, industry)
        )
        
        soc_task = asyncio.create_task(
            self._analyze_category(session_id, "social", processed_data, industry)
        )
        
        gov_task = asyncio.create_task(
            self._analyze_category(session_id, "governance", processed_data, industry)
        )
        
        # Wait for all analyses to complete
        environmental = await env_task
        social = await soc_task
        governance = await gov_task
        
        # Combine results for analysis
        analyses = {
            "environmental": environmental,
            "social": social,
            "governance": governance
        }
        
        # Develop strategy
        strategy = await self._develop_strategy(session_id, analyses, industry)
        
        # Generate report sections similar to agentic chatbot
        report_sections = await self._generate_report_sections(processed_data, analyses, strategy, industry)
        
        # Store complete analysis
        analysis_id = await self._store_analysis_result(
            session_id=session_id,
            analysis_type="full",
            result={
                "processed_data": processed_data,
                "analyses": analyses,
                "strategy": strategy,
                "report_sections": report_sections
            }
        )
        
        # Return combined results matching the agentic chatbot structure
        return {
            "analysis_id": analysis_id,
            "processed_data": processed_data,
            "analyses": analyses,
            "strategy": strategy,
            "report_sections": report_sections
        }
    
    async def _process_data(self, data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Process and validate input data"""
        # Create prompt for data processing
        prompt = f"""
        You are an ESG data analyst processing and validating data for analysis.
        
        Industry: {industry}
        
        Data:
        {json.dumps(data, indent=2)}
        
        Please process this data by:
        1. Identifying any missing or anomalous values
        2. Normalizing metrics to standard ranges
        3. Checking for data quality issues
        4. Flagging any unusual patterns or outliers
        
        You must return a valid JSON object with:
        - processed_data: The cleaned and normalized data
        - data_quality: Metrics about the quality of data
        - issues: Array of identified issues
        - completeness_score: A number from 0-100
        
        Format your response as a proper JSON object. Do not include any text outside the JSON.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.1  # Low temperature for more consistent processing
            )
            
            # Try to parse JSON from response using our improved function
            processed_data = extract_json_from_text(response_text)
            
            # Check if we got an error
            if "error" in processed_data:
                logger.warning(f"JSON parsing error in data processing: {processed_data['error']}")
                
                # Return original data with warning if parsing failed
                return {
                    "original_data": data,
                    "warning": "Data validation could not be performed - JSON parsing failed",
                    "raw_response": response_text[:1000]  # Limit the size of the raw response
                }
                
            return processed_data
                
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            return {
                "original_data": data,
                "error": f"Processing failed: {str(e)}"
            }
    
    async def _analyze_category(self, session_id: str, category: str, data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Analyze specific ESG category"""
        # Extract category-specific data
        category_data = data.get(category, {})
        
        # Create prompt for category analysis
        prompt = f"""
        You are an ESG analyst specializing in {category} performance analysis.
        
        Industry: {industry}
        
        {category.capitalize()} metrics:
        {json.dumps(category_data, indent=2)}
        
        You must analyze and provide a valid JSON object with:
        - performance: Assessment of current performance metrics
        - gaps: Analysis of gaps compared to industry standards
        - risks: Evaluation of key {category} risks
        - opportunities: Key improvement opportunities
        - score: Overall performance score from 0-100
        
        Format your response as a proper JSON object. Do not include any text outside the JSON.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.2
            )
            
            # Parse JSON from response using our improved function
            analysis = extract_json_from_text(response_text)
            
            # If we got an error parsing JSON
            if "error" in analysis and "raw_text" in analysis:
                logger.warning(f"Failed to parse JSON from {category} analysis response")
                
                # Create a structured analysis from the raw text
                structured_analysis = {
                    "performance": "Could not parse performance analysis",
                    "gaps": "Could not parse gaps analysis",
                    "risks": "Could not parse risks analysis",
                    "opportunities": "Could not parse opportunities",
                    "score": 50,  # Default middle score
                    "raw_analysis": analysis["raw_text"][:1000],  # Truncate long responses
                    "parsing_error": analysis["error"]
                }
                
                analysis = structured_analysis
            
            # Store category analysis
            analysis_id = await self._store_analysis_result(
                session_id=session_id,
                analysis_type=f"{category}_analysis",
                result={category: analysis}
            )
            
            analysis["analysis_id"] = analysis_id
            return analysis
                
        except Exception as e:
            logger.error(f"Error in {category} analysis: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "score": 0
            }
    
    async def _develop_strategy(self, session_id: str, analyses: Dict[str, Dict[str, Any]], industry: str) -> Dict[str, Any]:
        """Develop comprehensive ESG strategy"""
        # Create prompt for strategy development
        prompt = f"""
        You are an ESG strategy consultant developing improvements for a company in the {industry} industry.
        
        Analysis results:
        {json.dumps(analyses, indent=2)}
        
        You must return a valid JSON object with:
        - priorities: Array of prioritized improvements with scores
        - action_plans: Detailed action plans for each priority
        - timeline: Implementation timeline with milestones
        - resources: Required resources by category
        - expected_outcomes: Anticipated results after implementation
        
        Format your response as a proper JSON object. Do not include any text outside the JSON.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3
            )
            
            # Parse JSON using our improved function
            strategy = extract_json_from_text(response_text)
            
            # If we got an error parsing JSON
            if "error" in strategy and "raw_text" in strategy:
                logger.warning("Failed to parse JSON from strategy development response")
                
                # Create a structured strategy from the raw text
                structured_strategy = {
                    "priorities": ["Could not parse priorities"],
                    "action_plans": {"error": "Could not parse action plans"},
                    "timeline": {"error": "Could not parse timeline"},
                    "resources": {"error": "Could not parse resources"},
                    "expected_outcomes": {"error": "Could not parse outcomes"},
                    "raw_strategy": strategy["raw_text"][:1000],  # Truncate long responses
                    "parsing_error": strategy["error"]
                }
                
                strategy = structured_strategy
            
            # Store strategy
            strategy_id = await self._store_analysis_result(
                session_id=session_id,
                analysis_type="strategy",
                result={"strategies": strategy}
            )
            
            strategy["strategy_id"] = strategy_id
            return strategy
                
        except Exception as e:
            logger.error(f"Error in strategy development: {str(e)}")
            return {
                "error": f"Strategy development failed: {str(e)}",
                "priorities": ["Error occurred during analysis"]
            }
    
    async def _generate_report_sections(self, data: Dict[str, Any], analyses: Dict[str, Dict[str, Any]], 
                                     strategy: Dict[str, Any], industry: str) -> Dict[str, str]:
        """Generate final report sections in markdown format"""
        # Create prompt for report generation
        prompt = f"""
        You are an ESG communication specialist creating a comprehensive report for a company in the {industry} industry.
        
        Data:
        {json.dumps(data, indent=2)}
        
        Analyses:
        {json.dumps(analyses, indent=2)}
        
        Strategy:
        {json.dumps(strategy, indent=2)}
        
        You must return a valid JSON object with the following sections as markdown formatted text:
        - executive_summary: Brief overview of key findings (markdown)
        - environmental_section: Details on environmental performance (markdown)
        - social_section: Details on social performance (markdown)
        - governance_section: Details on governance performance (markdown)
        - recommendations: Prioritized recommendations (markdown)
        - implementation: Implementation roadmap (markdown)
        
        Format your response as a proper JSON object with markdown text values for each section.
        Do not include any text outside the JSON.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3
            )
            
            # Parse JSON using our improved function
            report_sections = extract_json_from_text(response_text)
            
            # If we got an error parsing JSON
            if "error" in report_sections and "raw_text" in report_sections:
                logger.warning("Failed to parse JSON from report generation response")
                
                # Create fallback sections from the raw text
                raw_text = report_sections["raw_text"]
                sections = ["executive_summary", "environmental_section", "social_section", 
                           "governance_section", "recommendations", "implementation"]
                
                # Try to split the response into sections
                report_sections = {}
                
                # Default sections with error information
                for section in sections:
                    report_sections[section] = f"*Error: Could not parse {section.replace('_', ' ')} content.*"
                
                # Try to extract sections from headings in the raw text
                lines = raw_text.split("\n")
                current_section = None
                section_content = []
                
                for line in lines:
                    # Check if this line matches a section header
                    for section in sections:
                        section_name = section.replace("_", " ").title()
                        if section_name in line or section.title() in line:
                            # Save previous section if exists
                            if current_section and section_content:
                                report_sections[current_section] = "\n".join(section_content)
                                section_content = []
                            
                            current_section = section
                            break
                    
                    # Add content to current section
                    if current_section and not any(section_name in line for section_name in 
                                                [s.replace("_", " ").title() for s in sections]):
                        section_content.append(line)
                
                # Add the last section
                if current_section and section_content:
                    report_sections[current_section] = "\n".join(section_content)
                
                # Add error notice
                report_sections["error"] = "JSON parsing failed - sections may be incomplete"
            
            return report_sections
                
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}")
            return {
                "error": f"Report generation failed: {str(e)}",
                "executive_summary": "Error generating report.",
                "environmental_section": "Error generating environmental section.",
                "social_section": "Error generating social section.",
                "governance_section": "Error generating governance section.",
                "recommendations": "Error generating recommendations.",
                "implementation": "Error generating implementation plan."
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
    
    async def _get_latest_category_analyses(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get the most recent analysis for each category"""
        categories = ["environmental", "social", "governance"]
        results = {}
        
        for category in categories:
            # Get most recent analysis for this category
            cursor = self.db.analysis_results.find(
                {"session_id": session_id, "analysis_type": f"{category}_analysis"},
                sort=[("created_at", -1)],
                limit=1
            )
            
            async for doc in cursor:
                results[category] = doc.get(category, {})
        
        return results if len(results) == 3 else {}
    
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
