import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import DataManager
from config.constants import CUSTOM_CSS, SECTORS
import pandas as pd

class DashboardPage:
    def __init__(self):
        self.data_manager = DataManager()

    def render(self):
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        
        if "selected_sector" not in st.session_state or "kpi_data" not in st.session_state:
            st.error("No data available for dashboard")
            return

        sector = st.session_state.selected_sector
        kpi_data = st.session_state.kpi_data

        # Header with navigation
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        with col1:
            if st.button("← Back"):
                st.session_state.current_page = "sector_kpis"
                st.experimental_rerun()
        
        with col2:
            st.markdown(
                f"""
                <h1 style='color: #6B46C1; font-size: 2rem; font-weight: 600; text-align: center;'>
                    {sector} ESG Dashboard
                </h1>
                """,
                unsafe_allow_html=True
            )

        # Overview Cards
        self._render_overview_cards(kpi_data)

        # Detailed KPI Analysis
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            self._render_kpi_comparison_chart(kpi_data)
        
        with col2:
            self._render_category_performance(kpi_data)

        # KPI Details Table
        self._render_kpi_table(kpi_data)

    def _render_overview_cards(self, kpi_data):
        # Calculate overall scores
        env_score = sum(kpi_data.values()) / len(kpi_data)  # Simplified for Phase 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._metric_card(
                "Overall ESG Score",
                f"{env_score:.1f}",
                "↑ 2.1% from last period",
                "#6B46C1"
            )
        
        with col2:
            self._metric_card(
                "Sector Ranking",
                "Top 25%",
                "↑ 5 positions",
                "#2563EB"
            )
        
        with col3:
            self._metric_card(
                "Completion Rate",
                f"{len(kpi_data)}/{len(SECTORS[st.session_state.selected_sector]['mandatory_kpis'])}",
                "Mandatory KPIs",
                "#059669"
            )

    def _render_kpi_comparison_chart(self, kpi_data):
        st.markdown("### KPI Performance")
        
        # Create comparison chart
        fig = go.Figure()
        
        # Add KPI values
        fig.add_trace(go.Bar(
            x=list(kpi_data.keys()),
            y=list(kpi_data.values()),
            marker_color='#6B46C1'
        ))
        
        # Add industry average (dummy data for Phase 1)
        fig.add_trace(go.Bar(
            x=list(kpi_data.keys()),
            y=[75] * len(kpi_data),
            name='Industry Average',
            marker_color='#E5E7EB'
        ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_category_performance(self, kpi_data):
        st.markdown("### Category Performance")
        
        # Dummy data for Phase 1
        categories = ['Environmental', 'Social', 'Governance']
        values = [85, 78, 92]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            marker_color='#6B46C1'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            height=400,
            margin=dict(t=0, b=0, l=30, r=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_kpi_table(self, kpi_data):
        st.markdown("### KPI Details")
        
        # Create DataFrame
        df = pd.DataFrame({
            'KPI': kpi_data.keys(),
            'Value': kpi_data.values(),
            'Status': ['On Track' if v >= 75 else 'Needs Attention' for v in kpi_data.values()],
            'Trend': ['↑' if v >= 75 else '↓' for v in kpi_data.values()]
        })
        
        # Style the DataFrame
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                'KPI': 'KPI Name',
                'Value': st.column_config.NumberColumn(
                    'Score',
                    help='KPI Score out of 100',
                    format='%.1f'
                ),
                'Status': st.column_config.TextColumn(
                    'Status',
                    help='Current status of the KPI'
                ),
                'Trend': 'Trend'
            },
            use_container_width=True
        )

    def _metric_card(self, title, value, delta, color):
        st.markdown(
            f"""
            <div style='
                background-color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #E5E7EB;
            '>
                <h3 style='
                    color: {color};
                    margin: 0;
                    font-size: 2rem;
                    font-weight: 600;
                '>{value}</h3>
                <p style='
                    color: #6B7280;
                    margin: 0;
                    font-size: 0.875rem;
                '>{title}</p>
                <p style='
                    color: #059669;
                    margin: 0;
                    font-size: 0.75rem;
                    margin-top: 0.5rem;
                '>{delta}</p>
            </div>
            """,
            unsafe_allow_html=True
        )