import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from textwrap import dedent
import json
import time
import os

class KPIAdvisorSystem:
    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=4096
        )

        # Initialize agents with Groq LLM
        self.summarizer = Agent(
            role='KPI Performance Analyzer',
            goal='Analyze individual KPI performance and identify gaps',
            backstory=dedent("""
                You are an expert KPI analyst who specializes in understanding the nuances 
                of individual performance metrics. You analyze each KPI's current value against 
                its targets and industry standards, providing detailed context about performance gaps.
            """),
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.planner = Agent(
            role='KPI Improvement Strategist',
            goal='Create specific improvement plans for each KPI',
            backstory=dedent("""
                You are a strategic consultant who develops targeted improvement strategies
                for individual KPIs. You understand the technical requirements and business
                context needed to improve specific metrics, and can create detailed
                action plans for each KPI.
            """),
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.plan_combiner = Agent(
            role='Strategic Integration Expert',
            goal='Create cohesive multi-KPI improvement strategy',
            backstory=dedent("""
                You are a senior strategy expert who excels at finding connections between
                different KPI improvement initiatives. You can identify shared resources,
                dependencies, and synergies to create an efficient overall implementation plan.
            """),
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.presenter = Agent(
            role='KPI Strategy Advisor',
            goal='Communicate KPI improvement strategies and answer questions',
            backstory=dedent("""
                You are an expert advisor who helps organizations understand and implement
                KPI improvement strategies. You can explain complex metrics in simple terms,
                provide actionable guidance, and maintain context of how individual KPI
                improvements connect to overall goals.
            """),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def create_tasks(self, kpi_data):
        """Create tasks based on individual KPI data"""
        
        # Enhanced prompts for Groq LLM
        summarize_template = PromptTemplate(
            input_variables=["kpi_data"],
            template=dedent("""
                Analyze each KPI's current performance with this structured approach:
                1. Current Value Analysis:
                   - Review current values
                   - Identify historical trends if available
                   - Compare against industry benchmarks
                
                2. Gap Assessment:
                   - Calculate performance gaps
                   - Prioritize improvements needed
                   - Identify critical underperforming areas
                
                3. Context Analysis:
                   - Evaluate environmental factors
                   - Consider market conditions
                   - Assess organizational impact
                
                4. Urgency Evaluation:
                   - Determine improvement priorities
                   - Assess potential risks
                   - Recommend focus areas
                
                KPI Data to analyze: {kpi_data}
                
                Provide a structured, detailed analysis following these points.
            """)
        )
        
        summarize_task = Task(
            description=summarize_template.format(kpi_data=json.dumps(kpi_data, indent=2)),
            agent=self.summarizer
        )
        
        planning_task = Task(
            description=dedent("""
                Based on the KPI analysis, create detailed improvement plans:
                
                For each KPI:
                1. Action Items:
                   - Specific, measurable steps
                   - Required resources
                   - Implementation approach
                
                2. Timeline:
                   - Short-term actions (0-3 months)
                   - Medium-term goals (3-6 months)
                   - Long-term objectives (6+ months)
                
                3. Resource Planning:
                   - Team requirements
                   - Budget considerations
                   - Technology needs
                
                4. Risk Management:
                   - Potential obstacles
                   - Mitigation strategies
                   - Contingency plans
                
                5. Success Metrics:
                   - Progress indicators
                   - Milestone definitions
                   - Evaluation criteria
            """),
            agent=self.planner,
            dependencies=[summarize_task]
        )
        
        combination_task = Task(
            description=dedent("""
                Create an integrated improvement strategy by:
                
                1. Strategic Alignment:
                   - Identify interdependencies
                   - Find synergies
                   - Optimize resource allocation
                
                2. Implementation Sequence:
                   - Define critical path
                   - Set priorities
                   - Create timeline
                
                3. Resource Optimization:
                   - Share resources effectively
                   - Minimize redundancy
                   - Maximize efficiency
                
                4. Progress Tracking:
                   - Define KPIs
                   - Set milestones
                   - Create reporting structure
                
                5. Change Management:
                   - Communication plan
                   - Stakeholder engagement
                   - Training requirements
            """),
            agent=self.plan_combiner,
            dependencies=[planning_task]
        )
        
        presentation_task = Task(
            description=dedent("""
                Prepare a clear, actionable communication of the strategy:
                
                1. Executive Summary:
                   - Current state
                   - Key recommendations
                   - Expected outcomes
                
                2. Implementation Plan:
                   - Priority actions
                   - Resource requirements
                   - Timeline
                
                3. Success Factors:
                   - Critical requirements
                   - Risk mitigation
                   - Support needed
                
                4. Next Steps:
                   - Immediate actions
                   - Key decisions needed
                   - Resource allocation
                
                Present this information in a clear, engaging manner suitable for all stakeholders.
            """),
            agent=self.presenter,
            dependencies=[combination_task]
        )
        
        return [summarize_task, planning_task, combination_task, presentation_task]

    def get_advice(self, kpi_data):
        """Generate advice based on KPI data"""
        crew = Crew(
            agents=[self.summarizer, self.planner, self.plan_combiner, self.presenter],
            tasks=self.create_tasks(kpi_data),
            verbose=True,
            process=Process.sequential
        )
        
        return crew.kickoff()

    def ask_question(self, question, context):
        """Handle follow-up questions about KPI strategy"""
        question_template = PromptTemplate(
            input_variables=["question", "context"],
            template=dedent("""
                Based on the following context about our KPI strategy:
                {context}
                
                Please answer this specific question:
                {question}
                
                Provide a clear, detailed response that:
                1. Directly addresses the question
                2. References relevant parts of the strategy
                3. Provides actionable guidance if applicable
                4. Maintains context of the overall plan
            """)
        )
        
        question_task = Task(
            description=question_template.format(
                question=question,
                context=context
            ),
            agent=self.presenter
        )
        
        crew = Crew(
            agents=[self.presenter],
            tasks=[question_task],
            verbose=True,
            process=Process.sequential
        )
        
        return crew.kickoff()

