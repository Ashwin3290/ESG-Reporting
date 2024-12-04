import streamlit as st
import time
import json
from agent.agentic_chatbot import ESGAdvisorSystem
from typing import Dict, Optional,Any

class ChatInterface:
    def __init__(self):
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize all required session state variables"""
        required_states = {
            'messages': [],
            'advisor': ESGAdvisorSystem(),
            'last_analysis': None,
            'kpi_data': {},
            'kpi_reference': self._load_kpi_reference(),
            'current_category': None 
        }
        
        for key, default_value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def render(self):
        """Public method to render the complete chat interface"""
        self._add_styles()
        self._render_header()
        self._render_chat_container()
        self._render_input()
    
    def _load_kpi_reference(self) -> Dict[str, Any]:
        """Load the KPI reference data from a JSON file"""
        with open('data/kpi_reference.json', 'r') as file:
            return json.load(file)

    def _add_styles(self):
        """Add CSS styles for the chat interface"""
        st.markdown("""
            <style>
            /* Container styles */
            .stChatMessage {
                background-color: transparent !important;
            }
            
            [data-testid="stChatMessageContent"] {
                border-radius: 12px !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
                font-size: 16px !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
                padding: 16px !important;
                max-width: 90% !important;
            }

            /* User message styles */
            .user-message [data-testid="stChatMessageContent"] {
                background-color: #F3F4F6 !important;
                color: #1A202C !important;
                float: right !important;
            }
            
            /* Assistant message styles */
            .assistant-message [data-testid="stChatMessageContent"] {
                background-color: #6B46C1 !important;
                color: white !important;
            }
            
            /* Category indicators */
            .category-indicator {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                margin-right: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .environmental {
                background-color: #48BB78;
                color: white;
            }
            
            .social {
                background-color: #4299E1;
                color: white;
            }
            
            .governance {
                background-color: #9F7AEA;
                color: white;
            }
            
            /* Header styles */
            .header {
                position: sticky;
                top: 0;
                background: white;
                padding: 20px;
                border-bottom: 1px solid #E2E8F0;
                z-index: 99;
                margin-bottom: 20px;
            }
            
            .header-content {
                max-width: 800px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .header-title {
                font-size: 24px;
                font-weight: bold;
                color: #1A202C;
                margin: 0;
            }

            /* Chat container styles */
            .main-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 0 20px;
                margin-bottom: 80px;
            }

            /* Input styles */
            .stChatInput {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 20px;
                background: white;
                border-top: 1px solid #E2E8F0;
                z-index: 100;
            }
            
            .stChatInput > div {
                max-width: 760px;
                margin: 0 auto;
            }
            
            .stChatInput input {
                border: 1px solid #E2E8F0 !important;
                border-radius: 24px !important;
                padding: 12px 20px !important;
                background-color: #F8FAFC !important;
                font-size: 16px !important;
            }
            </style>
        """, unsafe_allow_html=True)

    def _render_header(self):
        """Render the header with navigation and category filters"""
        col1, col2, col3, col4 = st.columns([1, 13, 5, 1])
        
        with col1:
            if st.button("← Back"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        
        with col2:
            st.markdown("### ESG KPI Advisor Chat")
        
        with col3:
            # Add category filter
            categories = ['All', 'Environmental', 'Social', 'Governance']
            selected_category = st.selectbox(
                "Filter by category",
                categories,
                key="category_filter"
            )
            if selected_category != "All":
                st.session_state.current_category = selected_category.lower()
            else:
                st.session_state.current_category = None
        
        with col4:
            if st.button("Reset"):
                self.reset_conversation()
                st.rerun()

    def _render_chat_container(self):
        """Render the main chat container with messages"""
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Filter messages based on selected category
        messages_to_display = self._filter_messages_by_category(st.session_state.messages)
        
        for message in messages_to_display:
            with st.chat_message(message["role"]):
                # Add category indicator if present
                if "category" in message:
                    st.markdown(
                        f'<span class="category-indicator {message["category"]}">{message["category"].title()}</span>',
                        unsafe_allow_html=True
                    )
                st.markdown(message["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    def _render_input(self):
        """Render chat input"""
        if prompt := st.chat_input("Ask about your ESG metrics..."):
            self._handle_user_input(prompt)
    def _filter_messages_by_category(self, messages):
        """Filter messages based on selected category"""
        if not st.session_state.current_category:
            return messages
            
        return [msg for msg in messages if 
                "category" not in msg or 
                msg["category"] == st.session_state.current_category]
    def _handle_user_input(self, prompt: str):
            """Process user input and generate response"""
            # Add user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Get assistant response
            response = self._get_response(prompt)
            # Add assistant response
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            
            st.rerun()
            
    def _get_response(self, prompt: str) -> str:
        """Generate response based on prompt type"""
        # Detect prompt type
        prompt_type = self._analyze_prompt(prompt)
        
        try:
            if prompt_type == "data_request":
                return self._handle_data_request()
                
            elif prompt_type == "analysis_request":
                return self._handle_analysis_request()
                
            elif prompt_type == "question":
                return self._handle_question(prompt)
                
            else:  
                return self._handle_chat(prompt)
                
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "I encountered an error while processing your request. Please try again."
            
    def _analyze_prompt(self, prompt: str) -> str:
        """Analyze prompt to determine type"""
        # Simple keyword-based analysis
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["analyze", "analysis", "evaluate", "assess"]):
            return "analysis_request"
            
        if any(word in prompt_lower for word in ["data", "metrics", "kpis", "numbers"]):
            return "data_request"
            
        if any(word in prompt_lower for word in ["why", "how", "what", "when", "where", "who"]):
            return "question"
            
        return "chat"
        
    def _handle_data_request(self) -> str:
        """Handle request for data overview"""
        if not hasattr(st.session_state, 'kpi_data') or not st.session_state.kpi_data:
            return ("I don't see any KPI data loaded yet. Please ensure your ESG metrics "
                "are loaded in the dashboard before requesting an overview.")
                
        return st.session_state.advisor.run_analysis({
            "type": "data_overview",
            "data": st.session_state.kpi_data
        },
        st.session_state.selected_industry)
        
    def _handle_analysis_request(self) -> str:
        """Handle request for ESG analysis"""
        if not hasattr(st.session_state, 'kpi_data') or not st.session_state.kpi_data:
            return ("I don't see any KPI data loaded yet. Please load your ESG metrics "
                "in the dashboard before requesting analysis.")
                
        response = st.session_state.advisor.run_analysis({
            "type": "full_analysis",
            "data": st.session_state.kpi_data
        },
        st.session_state.selected_industry)
        
        st.session_state.current_analysis = response
        return response
        
    def _handle_question(self, prompt: str) -> str:
        """Handle specific questions"""
        if st.session_state.current_analysis:
            return st.session_state.advisor.run_analysis({
                "type": "question",
                "question": prompt,
                "context": st.session_state.current_analysis
            },
            st.session_state.selected_industry)
        else:
            return ("I don't have any recent analysis context. Would you like me to "
                "analyze your ESG metrics first?")
                
    def _handle_chat(self, prompt: str) -> str:
        """Handle general chat"""
        return st.session_state.advisor.run_analysis({
            "type": "chat",
            "message": prompt,
            "has_data": hasattr(st.session_state, 'kpi_data') and bool(st.session_state.kpi_data)
        },st.session_state.selected_industry)
        
    def _reset_chat(self):
        """Reset chat state"""
        st.session_state.messages = []
        st.session_state.current_analysis = None
        
    def _load_kpi_data(self) -> Optional[Dict]:
        """Load KPI data from session state"""
        if hasattr(st.session_state, 'kpi_data'):
            return st.session_state.kpi_data
        return None
    def _process_kpi_data(self, categorized_data, kpi_reference):
        """Process and categorize KPI data"""
        processed_data = {}
        
        for category, category_data in categorized_data.items():
            if isinstance(category_data, dict):
                for kpi_name, kpi_info in category_data.items():
                    if isinstance(kpi_info, dict) and 'value' in kpi_info:
                        value = kpi_info['value']
                        if hasattr(value, 'item'):
                            value = value.item()
                        
                        # Determine ESG category from KPI name
                        esg_category = 'other'
                        if 'environmental' in kpi_name.lower():
                            esg_category = 'environmental'
                        elif 'social' in kpi_name.lower():
                            esg_category = 'social'
                        elif 'governance' in kpi_name.lower():
                            esg_category = 'governance'
                        
                        processed_data[f"{esg_category}_{kpi_name}"] = {
                            'current_value': float(value),
                            'reference_range': kpi_reference.get(kpi_name, {
                                'min': 0,
                                'max': 100,
                                'target': 75
                            }),
                            'category': esg_category
                        }
        
        return processed_data

    def _get_current_kpi_data(self):
        """Get current KPI data from the dashboard"""
        if 'kpi_data' in st.session_state:
            return st.session_state.kpi_data
        
        if hasattr(st.session_state, 'categorized_kpis'):
            return st.session_state.categorized_kpis
        
        st.error("No KPI data available. Please ensure KPIs are loaded in the dashboard.")
        return {}

    def reset_conversation(self):
        """Reset the conversation and analysis state"""
        st.session_state.messages = []
        st.session_state.last_analysis = None
        st.session_state.current_category = None