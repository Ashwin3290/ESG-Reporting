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
        Run ESG analysis on session data
        
        Args:
            session_id: Session ID
            analysis_type: Type of analysis to run ('full', 'environmental', 'social', 'governance', 'strategy')
            industry: Industry name
            
        Returns:
            Analysis results
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
        """Run complete ESG analysis"""
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
        
        # Combine results
        categories = {
            "environmental": environmental,
            "social": social,
            "governance": governance
        }
        
        # Develop strategy
        strategy = await self._develop_strategy(session_id, categories, industry)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(categories, industry)
        
        # Store complete analysis
        analysis_id = await self._store_analysis_result(
            session_id=session_id,
            analysis_type="full",
            result={
                "environmental": environmental,
                "social": social,
                "governance": governance,
                "strategies": strategy,
                "recommendations": recommendations
            }
        )
        
        # Return combined results
        return {
            "analysis_id": analysis_id,
            "environmental": environmental,
            "social": social,
            "governance": governance,
            "strategies": strategy,
            "recommendations": recommendations
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
        
        Return a JSON object with the processed data and quality assessment.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.1  # Low temperature for more consistent processing
            )
            
            # Try to parse JSON from response
            try:
                # Extract JSON from potentially mixed text
                json_str = self._extract_json(response_text)
                processed_data = json.loads(json_str)
                return processed_data
            except json.JSONDecodeError:
                # If parsing fails, return the original data with a warning
                logger.warning("Failed to parse JSON from data processing response")
                return {
                    "original_data": data,
                    "warning": "Data validation could not be performed"
                }
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            return data
    
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
        
        Please provide a comprehensive analysis of this {category} data:
        1. Current performance assessment
        2. Benchmarking against industry standards
        3. Identification of risks and vulnerabilities
        4. Strengths and areas of excellence
        5. Improvement opportunities
        
        Return your analysis as a detailed JSON object with clear sections.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.2
            )
            
            # Try to parse JSON from response
            try:
                # Extract JSON from potentially mixed text
                json_str = self._extract_json(response_text)
                analysis = json.loads(json_str)
                
                # Store category analysis
                analysis_id = await self._store_analysis_result(
                    session_id=session_id,
                    analysis_type=f"{category}_analysis",
                    result={category: analysis}
                )
                
                analysis["analysis_id"] = analysis_id
                return analysis
            except json.JSONDecodeError:
                # If parsing fails, return a structured analysis from the text
                logger.warning(f"Failed to parse JSON from {category} analysis response")
                structured_analysis = {
                    "raw_analysis": response_text,
                    "parsing_error": "Could not parse structured JSON result"
                }
                
                # Store category analysis
                analysis_id = await self._store_analysis_result(
                    session_id=session_id,
                    analysis_type=f"{category}_analysis",
                    result={category: structured_analysis}
                )
                
                structured_analysis["analysis_id"] = analysis_id
                return structured_analysis
        except Exception as e:
            logger.error(f"Error in {category} analysis: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _develop_strategy(self, session_id: str, categories: Dict[str, Dict[str, Any]], industry: str) -> Dict[str, Any]:
        """Develop comprehensive ESG strategy"""
        # Create prompt for strategy development
        prompt = f"""
        You are an ESG strategy consultant developing improvements for a company in the {industry} industry.
        
        Analysis results:
        {json.dumps(categories, indent=2)}
        
        Based on the analysis above, develop a comprehensive ESG strategy that includes:
        1. Prioritized improvement opportunities for each ESG category
        2. Specific actions to address identified risks
        3. Short-term (1 year) and medium-term (3 year) implementation timeline
        4. Required resources and potential implementation challenges
        5. Expected benefits and impact metrics
        
        Return your strategy as a detailed JSON object with clear sections.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3
            )
            
            # Try to parse JSON from response
            try:
                # Extract JSON from potentially mixed text
                json_str = self._extract_json(response_text)
                strategy = json.loads(json_str)
                
                # Store strategy
                strategy_id = await self._store_analysis_result(
                    session_id=session_id,
                    analysis_type="strategy",
                    result={"strategies": strategy}
                )
                
                strategy["strategy_id"] = strategy_id
                return strategy
            except json.JSONDecodeError:
                # If parsing fails, return a structured strategy from the text
                logger.warning("Failed to parse JSON from strategy development response")
                structured_strategy = {
                    "raw_strategy": response_text,
                    "parsing_error": "Could not parse structured JSON result"
                }
                
                # Store strategy
                strategy_id = await self._store_analysis_result(
                    session_id=session_id,
                    analysis_type="strategy",
                    result={"strategies": structured_strategy}
                )
                
                structured_strategy["strategy_id"] = strategy_id
                return structured_strategy
        except Exception as e:
            logger.error(f"Error in strategy development: {str(e)}")
            return {"error": f"Strategy development failed: {str(e)}"}
    
    async def _generate_recommendations(self, categories: Dict[str, Dict[str, Any]], industry: str) -> List[str]:
        """Generate prioritized recommendations based on analyses"""
        # Create prompt for recommendations
        prompt = f"""
        You are an ESG advisor providing actionable recommendations for a company in the {industry} industry.
        
        Analysis results:
        {json.dumps(categories, indent=2)}
        
        Based on the analysis above, provide a prioritized list of the top 10 most impactful ESG recommendations.
        For each recommendation, include:
        1. The specific action to take
        2. The ESG category it addresses
        3. The expected impact
        4. Implementation difficulty
        
        Return your recommendations as a JSON array.
        """
        
        # Call LLM
        try:
            response_text = await self.gemini_client.generate_text(
                model="gemini-2.0-flash",
                prompt=prompt,
                temperature=0.3
            )
            
            # Try to parse JSON from response
            try:
                # Extract JSON from potentially mixed text
                json_str = self._extract_json(response_text)
                recommendations = json.loads(json_str)
                
                # Ensure it's a list
                if isinstance(recommendations, dict) and "recommendations" in recommendations:
                    return recommendations["recommendations"]
                elif isinstance(recommendations, list):
                    return recommendations
                else:
                    return [str(recommendations)]
            except json.JSONDecodeError:
                # If parsing fails, extract recommendations from text
                logger.warning("Failed to parse JSON from recommendations response")
                # Split by numbers and newlines to extract recommendations
                lines = response_text.split("\n")
                recommendations = []
                for line in lines:
                    if any(line.strip().startswith(str(i) + ".") for i in range(1, 11)):
                        recommendations.append(line.strip())
                
                return recommendations if recommendations else ["No specific recommendations could be extracted"]
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Failed to generate recommendations due to an error"]
    
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
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text response"""
        if not text:
            return "{}"
        
        # Look for JSON object
        json_pattern = r'\{.+\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(0)
        
        # Look for JSON array
        array_pattern = r'\[.+\]'
        match = re.search(array_pattern, text, re.DOTALL)
        if match:
            return match.group(0)
        
        # Alternative approach: look for code block with JSON
        code_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Array in code block
        array_code_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
        match = re.search(array_code_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # If no JSON found, try to convert the text to JSON
        try:
            import re
            # Extract structured content
            lines = text.split('\n')
            structured_content = {}
            current_section = None
            
            for line in lines:
                # Check for section headers
                section_match = re.match(r'^#+\s+(.+)$', line) or re.match(r'^(\d+\.\s+.+):$', line)
                if section_match:
                    current_section = section_match.group(1).strip()
                    structured_content[current_section] = []
                elif current_section and line.strip():
                    structured_content[current_section].append(line.strip())
            
            # Convert lists to strings
            for section, content in structured_content.items():
                structured_content[section] = '\n'.join(content)
            
            return json.dumps(structured_content)
        except:
            # If all else fails, return the text as a JSON string
            return json.dumps({"text": text})
