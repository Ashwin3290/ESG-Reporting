import streamlit as st
from streamlit_modal import Modal
from utils.data_manager import DataManager

class KPIsPage:
    def __init__(self):
        self.data_manager = DataManager()
        if "modal_state" not in st.session_state:
            st.session_state.modal_state = False
        if "current_kpi" not in st.session_state:
            st.session_state.current_kpi = None
        if "kpi_data" not in st.session_state:
            st.session_state.kpi_data = {}

    def render(self):
        if "selected_industry" not in st.session_state:
            st.error("No industry selected")
            return

        industry = st.session_state.selected_industry
        
        # Header with back button
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.button("←", key="back_button"):
                st.session_state.current_page = "home"
                st.rerun()
        
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
        categories = ['Environmental', 'Social', 'Governance']
        tabs = st.tabs(categories)
        
        # Style improvements
        st.markdown("""
            <style>
                .stTabs [data-baseweb="tab-list"] {
                    gap: 24px;
                }
                .stTabs [data-baseweb="tab"] {
                    height: 50px;
                    white-space: wrap;
                    color: #6B46C1;
                }
                .kpi-container {
                    margin-top: 20px;
                    max-height: calc(100vh - 300px);
                    overflow-y: auto;
                }
                .kpi-card {
                    background-color: white;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid #E5E7EB;
                    margin-bottom: 1rem;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                }
            </style>
        """, unsafe_allow_html=True)

        # Modal handling
        modal = Modal("KPI Data Input", key="kpi_modal")
        if st.session_state.modal_state:
            with modal.container():
                self._render_data_input_modal()

        # Render tabs
        for tab_idx, (tab, category) in enumerate(zip(tabs, categories)):
            with tab:
                kpis = categorized_kpis.get(category, [])
                if kpis:
                    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
                    self._render_kpi_list(kpis, category, tab_idx)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(f"No {category} KPIs available for this industry")

        # Fixed footer with dashboard button
        st.markdown("""
            <style>
                .footer-container {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: white;
                    padding: 1rem;
                    border-top: 1px solid #E5E7EB;
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([0.4, 0.2, 0.4])
        with col2:
            if st.button("View Dashboard", type="primary", key="view_dashboard", use_container_width=True):
                is_valid, message = self.data_manager.validate_kpi_data(industry)
                if is_valid:
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error(message)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_data_input_modal(self):
        """Render the modal content for data input"""
        if not st.session_state.current_kpi:
            return

        kpi = st.session_state.current_kpi
        kpi_type = self.data_manager.get_kpi_details(kpi)['type']
        
        st.subheader(f"Input Data for {kpi}")
        
        # Data input method selection with unique key
        input_method = st.radio(
            "Select Input Method",
            ["Manual Input", "CSV Upload", "API Integration"],
            horizontal=True,
            key=f"input_method_{hash(kpi)}_modal"
        )
        
        if input_method == "Manual Input":
            if kpi_type == 'qualitative':
                value = st.text_area("Enter your response", key=f"text_input_{hash(kpi)}")
                if st.button("Submit", key=f"submit_{hash(kpi)}"):
                    st.session_state.kpi_data[kpi] = value
                    st.session_state.modal_state = False
                    st.rerun()
            else:
                value = st.number_input("Enter value", min_value=0.0, key=f"num_input_{hash(kpi)}")
                if st.button("Submit", key=f"submit_{hash(kpi)}"):
                    st.session_state.kpi_data[kpi] = value
                    st.session_state.modal_state = False
                    st.rerun()
                    
        elif input_method == "CSV Upload":
            uploaded_file = st.file_uploader("Upload CSV", type="csv", key=f"upload_{hash(kpi)}")
            if uploaded_file:
                value = self.data_manager.process_csv(uploaded_file)
                if value is not None:
                    st.session_state.kpi_data[kpi] = value
                    st.session_state.modal_state = False
                    st.rerun()
                    
        elif input_method == "API Integration":
            st.text_input("API Endpoint", key=f"api_endpoint_{hash(kpi)}")
            st.text_input("API Key", key=f"api_key_{hash(kpi)}")
            if st.button("Connect", key=f"connect_{hash(kpi)}"):
                st.info("API integration coming soon!")

        if st.button("Close", key=f"close_{hash(kpi)}"):
            st.session_state.modal_state = False
            st.rerun()

    def _render_kpi_list(self, kpis: list, category: str, tab_idx: int):
        """Render the list of KPIs with cards"""
        for kpi_idx, kpi in enumerate(kpis):
            # Create a unique key using category, tab index, and KPI index
            unique_key = f"{category}_{tab_idx}_{kpi_idx}_{hash(kpi)}"
            
            st.markdown(
                f"""
                <div class="kpi-card">
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
                if st.button("Add Data", key=f"add_data_{unique_key}"):
                    st.session_state.modal_state = True
                    st.session_state.current_kpi = kpi
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)