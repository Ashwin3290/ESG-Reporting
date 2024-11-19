import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import DataManager
from config.constants import CUSTOM_CSS
import pandas as pd

class DashboardPage:
    def __init__(self):
        self.data_manager = DataManager()
        self.categories = ['Environmental', 'Social', 'Governance']

    def render(self):
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        
        if "selected_industry" not in st.session_state or "kpi_data" not in st.session_state:
            st.error("No data available for dashboard")
            return

        sector = st.session_state.selected_industry
        kpi_data = st.session_state.kpi_data
        
        # Organize KPIs by category
        categorized_kpis = self.data_manager.get_industry_kpis_by_category(sector)
        categorized_data = self._organize_kpi_data(kpi_data, categorized_kpis)

        # Header with navigation
        self._render_header(sector)

        # Overview Cards
        self._render_overview_cards(categorized_data)

        # Create tabs for ESG categories
        tabs = st.tabs(self.categories)
        
        # Render content for each category tab
        for tab, category in zip(tabs, self.categories):
            with tab:
                if category in categorized_data:
                    self._render_category_tab(category, categorized_data[category])
                else:
                    st.info(f"No {category} KPIs available")

    def _organize_kpi_data(self, kpi_data, categorized_kpis):
        """Organize KPI data by ESG category"""
        categorized_data = {}
        for category in self.categories:
            category_kpis = categorized_kpis.get(category, [])
            category_data = {kpi: kpi_data[kpi] for kpi in category_kpis if kpi in kpi_data}
            if category_data:
                categorized_data[category] = category_data
        return categorized_data

    def _render_header(self, sector):
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        with col1:
            if st.button("← Back"):
                st.session_state.current_page = "sector_kpis"
                st.rerun()
        
        with col2:
            st.markdown(
                f"""
                <h1 style='color: #6B46C1; font-size: 2rem; font-weight: 600; text-align: center;'>
                    {sector} ESG Dashboard
                </h1>
                """,
                unsafe_allow_html=True
            )

    def _render_overview_cards(self, categorized_data):
        # Calculate category scores
        scores = {
            category: sum(data.values()) / len(data) if data else 0
            for category, data in categorized_data.items()
        }
        
        overall_score = sum(scores.values()) / len([s for s in scores.values() if s > 0])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._metric_card(
                "Overall ESG Score",
                f"{overall_score:.1f}",
                "Overall performance",
                "#6B46C1"
            )
        
        with col2:
            completed_kpis = sum(len(data) for data in categorized_data.values())
            total_kpis = self.data_manager.get_total_kpi_len(st.session_state.selected_industry)
            self._metric_card(
                "Completion Rate",
                f"{completed_kpis}/{total_kpis}",
                "Mandatory KPIs",
                "#059669"
            )
        
        with col3:
            highest_cat = max(scores.items(), key=lambda x: x[1]) if scores else ("None", 0)
            self._metric_card(
                "Top Category",
                f"{highest_cat[0]}",
                f"Score: {highest_cat[1]:.1f}",
                "#2563EB"
            )

    def _render_category_tab(self, category, category_data):
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            self._render_kpi_comparison_chart(category_data, category)
        
        with col2:
            self._render_category_performance_radar(category_data,category)
        
        self._render_kpi_table(category_data)

    def _render_kpi_comparison_chart(self, kpi_data, category):
        st.markdown(f"### {category} KPI Performance")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(kpi_data.keys()),
            y=list(kpi_data.values()),
            marker_color='#6B46C1',
            name='Current Value'
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

    def _render_category_performance_radar(self, kpi_data,category):
        st.markdown("### Performance Distribution")
        
        # Create metrics for radar chart
        metrics = ['Average', 'Maximum', 'Minimum', 'Median']
        values = [
            sum(kpi_data.values()) / len(kpi_data),
            max(kpi_data.values()),
            min(kpi_data.values()),
            sorted(kpi_data.values())[len(kpi_data)//2]
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
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
        
        st.plotly_chart(fig, use_container_width=True,key=hash(category))

    def _render_kpi_table(self, kpi_data):
        st.markdown("### KPI Details")
        
        df = pd.DataFrame({
            'KPI': kpi_data.keys(),
            'Value': kpi_data.values(),
            'Status': ['On Track' if v >= 75 else 'Needs Attention' for v in kpi_data.values()],
            'Trend': ['↑' if v >= 75 else '↓' for v in kpi_data.values()]
        })
        
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