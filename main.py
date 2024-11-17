import streamlit as st
from pages.home import HomePage
from pages.sector_kpis import KPIsPage
from pages.dashboard import DashboardPage

def main():
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Page routing
    if st.session_state.current_page == "home":
        HomePage().render()
    elif st.session_state.current_page == "sector_kpis":
        KPIsPage().render()
    elif st.session_state.current_page == "dashboard":
        DashboardPage().render()

if __name__ == "__main__":
    st.set_page_config(
        page_title="ESG Analysis Platform",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    main()