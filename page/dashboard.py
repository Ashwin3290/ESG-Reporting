import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import DataManager
from config.constants import CUSTOM_CSS
import pandas as pd
from typing import Dict, Any
import numpy as np

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
        
        # Add EDA Section
        st.markdown("---")
        st.markdown(
            """
            <h2 style='color: #6B46C1; font-size: 1.5rem; font-weight: 600;'>
                Exploratory Data Analysis
            </h2>
            """,
            unsafe_allow_html=True
        )
        self._render_eda_section(categorized_data)
    def _organize_kpi_data(self, kpi_data, categorized_kpis):
        """Organize KPI data by ESG category"""
        categorized_data = {}
        for category in categorized_kpis.keys():
            for kpi in categorized_kpis[category]:
                if kpi in kpi_data:
                    category_data = {kpi:kpi_data[kpi]["value"]}
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
    
    def _render_eda_section(self, categorized_data: Dict[str, Dict[str, Any]]):
        """Render the EDA section with various analyses and visualizations"""
        # Convert data to a more analysis-friendly format
        df = self._prepare_eda_dataframe(categorized_data)
        
        if df.empty:
            st.info("No numerical data available for analysis")
            return

        # Statistical Summary
        self._render_statistical_summary(df)
        
        # Distribution Analysis
        self._render_distribution_analysis(df)
        
       
        # Time Series Analysis (if time-based data is available)
        if any('time' in col.lower() or 'date' in col.lower() or 'year' in col.lower() or 'month' in col.lower() for col in df.columns):
            self._render_time_series_analysis(df)
        
        # Category Comparison
        self._render_category_comparison(categorized_data)

    def _prepare_eda_dataframe(self, categorized_data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Prepare a DataFrame for EDA from categorized data"""
        data_dict = {}
        categories_dict = {}
        
        for category, kpis in categorized_data.items():
            for kpi_name, value in kpis.items():
                if isinstance(value, (int, float)):
                    data_dict[kpi_name] = value
                    categories_dict[kpi_name] = category
        
        df = pd.DataFrame(list(data_dict.items()), columns=['KPI', 'Value'])
        df['Category'] = df['KPI'].map(categories_dict)
        return df

    def _render_statistical_summary(self, df: pd.DataFrame):
        """Render statistical summary cards"""
        st.markdown("### Statistical Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._metric_card(
                "Mean Score",
                f"{df['Value'].mean():.1f}",
                "Average across all KPIs",
                "#6B46C1"
            )
        
        with col2:
            self._metric_card(
                "Median Score",
                f"{df['Value'].median():.1f}",
                "Middle value",
                "#2563EB"
            )
        
        with col3:
            self._metric_card(
                "Standard Deviation",
                f"{df['Value'].std():.1f}",
                "Score variation",
                "#059669"
            )
        
        with col4:
            self._metric_card(
                "Score Range",
                f"{df['Value'].max() - df['Value'].min():.1f}",
                f"Min: {df['Value'].min():.1f}, Max: {df['Value'].max():.1f}",
                "#DC2626"
            )

    def _render_distribution_analysis(self, df: pd.DataFrame):
        """Render distribution analysis visualizations"""
        st.markdown("### Score Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Histogram
            fig_hist = px.histogram(
                df,
                x='Value',
                nbins=20,
                title='Score Distribution',
                color='Category',
                marginal='box'
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Box plot by category
            fig_box = px.box(
                df,
                x='Category',
                y='Value',
                title='Score Distribution by Category',
                color='Category'
            )
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, use_container_width=True)

    def _render_correlation_analysis(self, df: pd.DataFrame):
        """Render correlation analysis"""
        st.markdown("### KPI Relationships")
        
        # Pivot the data for correlation analysis
        pivot_df = df.pivot(columns='KPI', values='Value')
        corr_matrix = pivot_df.corr()
        
        # Heatmap of correlations
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(
            title='KPI Correlation Matrix',
            height=600,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_time_series_analysis(self, df: pd.DataFrame):
        """Render time series analysis if temporal data is available"""
        st.markdown("### Temporal Analysis")
        
        # Create a sample time series visualization
        # This assumes data has some sort of temporal component
        fig = go.Figure()
        
        for category in df['Category'].unique():
            category_data = df[df['Category'] == category]
            fig.add_trace(go.Scatter(
                x=category_data.index,
                y=category_data['Value'],
                name=category,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title='KPI Scores Over Time',
            xaxis_title='Time Period',
            yaxis_title='Score',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_category_comparison(self, categorized_data: Dict[str, Dict[str, Any]]):
        """Render category comparison analysis"""
        st.markdown("### Category Performance Comparison")
        
        # Calculate category averages
        category_averages = {
            category: np.mean([v for v in kpis.values() if isinstance(v, (int, float))])
            for category, kpis in categorized_data.items()
            if any(isinstance(v, (int, float)) for v in kpis.values())
        }
        
        if not category_averages:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Radar chart of category averages
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=list(category_averages.values()),
                theta=list(category_averages.keys()),
                fill='toself',
                name='Category Average'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                title='Category Performance Overview',
                height=400
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            # Bar chart of KPI counts by category
            kpi_counts = {
                category: len(kpis)
                for category, kpis in categorized_data.items()
            }
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=list(kpi_counts.keys()),
                    y=list(kpi_counts.values()),
                    marker_color=['#6B46C1', '#2563EB', '#059669']
                )
            ])
            
            fig_bar.update_layout(
                title='KPIs per Category',
                xaxis_title='Category',
                yaxis_title='Number of KPIs',
                height=400
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)