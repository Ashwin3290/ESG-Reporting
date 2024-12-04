from crewai import Agent, Task, Crew, Process,LLM
from typing import Dict, List, Optional
import json
from agent.progress import ProgressTracker, AnalysisStage
# from agent.llm_config import LLMFactory
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

# os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
# os.environ["GROQ_API_KEY2"] = os.getenv("GROQ_API_KEY2")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
print("Gemini")

def create_llm(model_type: str) -> LLM:
        """Create an LLM instance based on type"""
        
        configs = {
            'analysis': {
                'model': "gemini/gemini-1.5-flash",
                'temperature': 0.1,
                'api_key': os.environ["GEMINI_API_KEY"]
            },
            'strategy': {
                'model': "gemini/gemini-1.5-flash",
                'temperature': 0.2,
                'api_key': os.environ["GEMINI_API_KEY"]
            },
            'chat': {
                'model': "gemini/gemini-1.5-flash",
                'api_key': os.environ["GEMINI_API_KEY"]
            }
        }
        
        if model_type not in configs:
            raise ValueError(f"Unknown model type: {model_type}")
            
        config = configs[model_type]
        return LLM(
            model=config['model'],
            # temperature=config['temperature'],
            # base_url=config['base_url'],
            api_key=config['api_key']
        )

class BaseAgent:
    """Base class for all ESG agents"""
    
    def __init__(self, role: str, goal: str, backstory: str, llm_type: str):
        self.llm = create_llm(llm_type)
        self.agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
    def execute_task(self, task: Task) -> str:
        return self.agent.execute_task(task)

class ESGAdvisorSystem:
    """Main ESG advisor system coordinating multiple agents"""
    
    def __init__(self):
        self.progress = ProgressTracker()
        self.initialize_agents()
        
    def initialize_agents(self):
        """Initialize specialized agents"""
        self.agents = {
            'data': BaseAgent(
                role='ESG Data Processor',
                goal='Process and validate ESG metrics',
                backstory="""Expert in ESG data processing and validation, ensuring 
                        data quality and standardization.""",
                llm_type='analysis'
            ),
            
            'environmental': BaseAgent(
                role='Environmental Analyst',
                goal='Analyze environmental performance',
                backstory="""Specialist in environmental metrics, climate impact, 
                        and sustainability practices.""",
                llm_type='analysis'
            ),
            
            'social': BaseAgent(
                role='Social Impact Analyst',
                goal='Analyze social performance',
                backstory="""Expert in social metrics, workforce analytics, and 
                        community impact assessment.""",
                llm_type='analysis'
            ),
            
            'governance': BaseAgent(
                role='Governance Analyst',
                goal='Analyze governance structure',
                backstory="""Specialist in corporate governance, ethics, and 
                        compliance frameworks.""",
                llm_type='analysis'
            ),
            
            'strategy': BaseAgent(
                role='Strategy Developer',
                goal='Develop improvement strategies',
                backstory="""Expert in ESG strategy development and 
                        implementation planning.""",
                llm_type='strategy'
            ),
            
            'communication': BaseAgent(
                role='Communication Specialist',
                goal='Present findings effectively',
                backstory="""Specialist in presenting ESG information to 
                        different stakeholders.""",
                llm_type='chat'
            )
        }
        
    def process_data(self, data: Dict, industry: str) -> Dict:
        """Process and validate input data"""
        stage = AnalysisStage(
            "Data Processing",
            [
                "Validating data structure",
                "Checking completeness",
                "Normalizing values",
                "Identifying anomalies"
            ],
            self.progress
        )
        
        task = Task(
            description=f"""
                Process and validate this ESG data from the {industry} industry:
                {json.dumps(data, indent=2)}
                
                Steps:
                1. Validate data structure and types
                2. Check for missing or invalid values
                3. Normalize metrics to standard ranges
                4. Flag any anomalies or outliers
                
                Return JSON with:
                - Processed data
                - Data quality metrics
                - Identified issues
                - Completeness score
            """,
            expected_output="Processed and validated ESG data",
            agent=self.agents['data'].agent
        )
        
        return stage.execute(lambda _: self.agents['data'].execute_task(task))
        
    def analyze_category(self, category: str, data: Dict, industry: str) -> Dict:
        """Analyze specific ESG category"""
        stage = AnalysisStage(
            f"{category.title()} Analysis",
            [
                "Analyzing current performance",
                "Comparing benchmarks",
                "Identifying risks",
                "Finding opportunities"
            ],
            self.progress
        )
        
        task = Task(
            description=f"""
                Analyze {category} performance from the {industry} industry:
                {json.dumps(data, indent=2)}
                
                Provide:
                1. Performance assessment
                2. Gap analysis
                3. Risk evaluation
                4. Improvement opportunities
                
                Return detailed JSON analysis.
            """,
            expected_output=f"Detailed {category} analysis",
            agent=self.agents[category].agent
        )
        
        return stage.execute(lambda _: self.agents[category].execute_task(task))
        
    def develop_strategy(self, analyses: Dict, industry: str) -> Dict:
        """Develop comprehensive improvement strategy"""
        stage = AnalysisStage(
            "Strategy Development",
            [
                "Prioritizing improvements",
                "Developing action plans",
                "Creating timeline",
                "Allocating resources"
            ],
            self.progress
        )
        
        task = Task(
            description=f"""
                Develop strategy based on analyses from the {industry} industry:
                {json.dumps(analyses, indent=2)}
                
                Create:
                1. Prioritized improvements
                2. Action plans
                3. Implementation timeline
                4. Resource requirements
                
                Return detailed Markdown strategy.
            """,
            expected_output="Comprehensive ESG strategy",
            agent=self.agents['strategy'].agent
        )
        
        return stage.execute(lambda _: self.agents['strategy'].execute_task(task))
        
    def generate_report(self, 
                    data: Dict, 
                    analyses: Dict, 
                    strategy: Dict,
                    industry: str) -> str:
        """Generate final report"""
        stage = AnalysisStage(
            "Report Generation",
            [
                "Creating executive summary",
                "Organizing findings",
                "Formatting recommendations",
                "Finalizing report"
            ],
            self.progress
        )
        
        task = Task(
            description=f"""
                Create comprehensive report from the {industry} industry using:
                Processed Data: {json.dumps(data, indent=2)}
                Analyses: {json.dumps(analyses, indent=2)}
                Strategy: {json.dumps(strategy, indent=2)}
                
                Include:
                1. Executive summary
                2. Detailed findings by category
                3. Prioritized recommendations
                4. Implementation roadmap
                
                Format as markdown with clear sections.
            """,
            expected_output="Complete ESG advisory report with the appropriate important data in a well structured manner",
            agent=self.agents['communication'].agent
        )
        
        return stage.execute(lambda _: self.agents['communication'].execute_task(task))
        
    def run_analysis(self, input_data: Dict, industry: str) -> str:
        """Run complete ESG analysis pipeline"""
        self.progress.init_tracking()
        
        try:
            processed_data = self.process_data(input_data,industry)
            
            analyses = {
                category: self.analyze_category(category, processed_data,industry)
                for category in ['environmental', 'social', 'governance']
            }
            
            strategy = self.develop_strategy(analyses,industry)
            self.progress.clear()
            return strategy
            
        except Exception as e:
            self.progress.clear()
            st.error(f"Analysis failed: {str(e)}")
            return "Analysis could not be completed due to an error."

