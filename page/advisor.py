import streamlit as st
import time
from agent.agentic_chatbot import KPIAdvisorSystem

class ChatInterface:
    def __init__(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'advisor' not in st.session_state:
            st.session_state.advisor = KPIAdvisorSystem()
        if 'last_analysis' not in st.session_state:
            st.session_state.last_analysis = None

    def render(self):
        """Public method to render the complete chat interface"""
        self._add_styles()
        self._render_header()
        self._render_chat_container()
        self._render_chat_input()

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
        """Render the header with back button and title"""
        col1, col2 = st.columns([1, 20])
        with col1:
            if st.button("← Back"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with col2:
            st.markdown("### KPI Advisor Chat")

    def _render_chat_container(self):
        """Render the main chat container with messages"""
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)


    def _render_chat_input(self):
        """Render the chat input with enhanced KPI advisor integration"""
        if prompt := st.chat_input("Type your message..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get bot response with KPI advisor integration
            response = self._get_bot_response(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()

    def _get_bot_response(self, prompt):
        """Enhanced response generation using KPI advisor"""
        with st.spinner("Analyzing KPIs and generating response..."):
            # Get current KPI data from session state
            if 'kpi_data' not in st.session_state:
                return "No KPI data available. Please ensure KPI data is loaded first."
            
            kpi_data = st.session_state.kpi_data
            
            # Check if this is a follow-up question
            if "last_analysis" in st.session_state and st.session_state.last_analysis:
                response = st.session_state.advisor.ask_question(
                    prompt, 
                    st.session_state.last_analysis
                )
            else:
                # Generate new analysis
                response = st.session_state.advisor.get_advice(kpi_data)
                st.session_state.last_analysis = response
            
            return response

    def reset_conversation(self):
        """Reset the conversation and analysis state"""
        st.session_state.messages = []
        st.session_state.last_analysis = None