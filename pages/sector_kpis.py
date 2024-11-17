import streamlit as st
from utils.data_manager import DataManager

class KPIsPage:
    def __init__(self):
        self.data_manager = DataManager()

    def render(self):
        if "selected_industry" not in st.session_state:
            st.error("No industry selected")
            return

        industry = st.session_state.selected_industry
        
        # Header with back button
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.button("←"):
                st.session_state.current_page = "home"
                st.experimental_rerun()
        
        with col2:
            st.markdown(
                f"""
                <h1 style='color: #6B46C1; font-size: 2rem; font-weight: 600;'>
                    {industry} KPIs
                </h1>
                """,
                unsafe_allow_html=True
            )

        # Get KPIs by category for the industry
        categorized_kpis = self.data_manager.get_industry_kpis_by_category(industry)
        
        # Create tabs for ESG categories
        tabs = st.tabs(['Environmental', 'Social', 'Governance'])
        
        # Scrollable container CSS
        st.markdown("""
            <style>
                .scrollable-container {
                    height: calc(100vh - 300px);
                    overflow-y: auto;
                    padding-right: 20px;
                }
                .stTabs [data-baseweb="tab-list"] {
                    gap: 24px;
                }
                .stTabs [data-baseweb="tab"] {
                    height: 50px;
                    white-space: wrap;
                    color: #6B46C1;
                }
                .modal-container {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                }
            </style>
        """, unsafe_allow_html=True)
        
        for tab, (category, kpis) in zip(tabs, categorized_kpis.items()):
            with tab:
                st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                self._render_kpi_list(kpis)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Fixed footer with dashboard button
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([0.4, 0.2, 0.4])
        with col2:
            if st.button("View Dashboard", type="primary", use_container_width=True):
                is_valid, message = self.data_manager.validate_kpi_data(industry)
                if is_valid:
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error(message)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_data_input_modal(self, kpi: str, kpi_type: str):
        st.markdown("""
            <div class="modal-backdrop"></div>
            <div class="modal-container">
        """, unsafe_allow_html=True)
        
        st.subheader(f"Input Data for {kpi}")
        
        # Data input method selection
        input_method = st.radio(
            "Select Input Method",
            ["Manual Input", "CSV Upload", "API Integration"],
            horizontal=True
        )
        
        if input_method == "Manual Input":
            if kpi_type == 'qualitative':
                value = st.text_area("Enter your response")
                if st.button("Submit"):
                    st.session_state.kpi_data[kpi] = value
            else:
                value = st.number_input("Enter value", min_value=0.0)
                if st.button("Submit"):
                    st.session_state.kpi_data[kpi] = value
                    
        elif input_method == "CSV Upload":
            uploaded_file = st.file_uploader("Upload CSV", type="csv")
            if uploaded_file:
                value = self.data_manager.process_csv(uploaded_file)
                if value is not None:
                    st.session_state.kpi_data[kpi] = value
                    
        elif input_method == "API Integration":
            st.text_input("API Endpoint")
            st.text_input("API Key")
            if st.button("Connect"):
                st.info("API integration coming soon!")
        
        if st.button("Close"):
            st.session_state.show_modal = False
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_kpi_list(self, kpis: list):
        for kpi in kpis:
            with st.container():
                st.markdown(
                    f"""
                    <div style='
                        background-color: white;
                        padding: 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid #E5E7EB;
                        margin-bottom: 1rem;
                        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                    '>
                    """,
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns([0.7, 0.3])
                
                with col1:
                    st.markdown(f"**{kpi}**")
                    kpi_details = self.data_manager.get_kpi_details(kpi)
                    st.markdown(f"*Specification:* {kpi_details['specification']}")
                    st.markdown(f"*Scope:* {kpi_details['scope']}")
                    
                    if kpi in st.session_state.get("kpi_data", {}):
                        st.success(f"Value: {st.session_state.kpi_data[kpi]}")
                
                with col2:
                    if st.button("Add Data", key=f"add_data_{kpi}"):
                        st.session_state.show_modal = True
                        st.session_state.current_kpi = kpi
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

        # Show modal if triggered
        if getattr(st.session_state, 'show_modal', False):
            current_kpi = st.session_state.current_kpi
            kpi_type = self.data_manager.get_kpi_details(current_kpi)['type']
            
            self._render_data_input_modal(current_kpi, kpi_type)