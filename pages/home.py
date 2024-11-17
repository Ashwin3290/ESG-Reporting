import streamlit as st
from utils.data_manager import DataManager

class HomePage:
    def __init__(self):
        self.data_manager = DataManager()

    def render(self):
        # Custom CSS for larger cards
        st.markdown("""
            <style>
                .industry-card {
                    background-color: white;
                    border: 1px solid #E5E7EB;
                    border-radius: 0.5rem;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    height: 150px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .industry-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .industry-title {
                    color: #6B46C1;
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    line-height: 1.4;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Title
        st.markdown(
            """
            <h1 style='color: #6B46C1; font-size: 2.5rem; font-weight: 600; margin-bottom: 2rem;'>
                ESG Portal
            </h1>
            """,
            unsafe_allow_html=True
        )
        
        # Search box
        search_query = st.text_input(
            "Search industry",
            key="industry_search",
            help="Type to filter industries",
            placeholder="Enter industry name...",
        )
        
        # Create three columns
        cols = st.columns(3)
        
        # Get filtered industries
        filtered_industries = self.data_manager.search_industries(search_query)
        
        # Display industry cards
        for idx, industry in enumerate(filtered_industries):
            with cols[idx % 3]:
                self._render_industry_card(industry, idx)

    def _render_industry_card(self, industry: str, idx: int):
        st.markdown(
            f"""
            <div class='industry-card'>
                <div class='industry-title'>{industry}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button(
            "Select Industry",
            key=f"industry_{idx}",
            use_container_width=True,
        ):
            st.session_state.selected_industry = industry
            st.session_state.current_page = "sector_kpis"
            if "kpi_data" not in st.session_state:
                st.session_state.kpi_data = {}