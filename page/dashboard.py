import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import DataManager
from config.constants import CUSTOM_CSS
import pandas as pd
from typing import Dict, Any, List
import numpy as np
from scipy.stats import gaussian_kde

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
        self._render_kpi_eda()
    def _organize_kpi_data(self, kpi_data, categorized_kpis):
        """Organize KPI data by ESG category"""
        categorized_data = {}
        for category in categorized_kpis.keys():
            categorized_data[category]={}
            for kpi in categorized_kpis[category]:
                if kpi in kpi_data:
                    if isinstance(kpi_data[kpi], dict):
                        categorized_data[category][kpi] = kpi_data[kpi]["value"]
                    else:
                        categorized_data[category][kpi] = kpi_data[kpi]
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
        
        scores = {}
        for category, data in categorized_data.items():
            if len(data):
                scores[category] = sum(data.values()) / len(data)
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
        print(kpi_data)
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
        if len(kpi_data):
            values = [
                sum(kpi_data.values()) / len(kpi_data),
                max(kpi_data.values()),
                min(kpi_data.values()),
                sorted(kpi_data.values())[len(kpi_data)//2]
            ]
        else:
            values=[0,0,0,0]
        
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
    def _render_kpi_eda(self):
        """Render independent KPI data analysis section"""
        # Get list of KPI files from session_files directory
        kpi_files = self._get_kpi_files()
        
        if not kpi_files:
            st.info("No KPI calculation data available for analysis")
            return
        
        # Create KPI selector dropdown
        selected_kpi = st.selectbox(
            "Select KPI for detailed analysis",
            options=kpi_files,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Load and analyze selected KPI data
        kpi_data = self._load_kpi_data(selected_kpi)
        
        if kpi_data is None or kpi_data.empty:
            st.error(f"No data available for {selected_kpi}")
            return
        
        # Render EDA components
        self._render_kpi_data_summary(kpi_data, selected_kpi)
        self._render_kpi_distributions(kpi_data, selected_kpi)
        self._render_kpi_correlations(kpi_data, selected_kpi)
        self._render_time_patterns(kpi_data, selected_kpi)

    def _get_kpi_files(self) -> List[str]:
        """Get list of KPI files from session_files directory"""
        import os
        session_files_dir = "session_files"
        if not os.path.exists(session_files_dir):
            return []
        
        return [f.replace('.csv', '') for f in os.listdir(session_files_dir) 
                if f.endswith('.csv')]

    def _load_kpi_data(self, kpi_name: str) -> pd.DataFrame:
        """Load KPI data from CSV file"""
        try:
            file_path = f"session_files/{kpi_name}.csv"
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None

    def _render_kpi_data_summary(self, df: pd.DataFrame, kpi_name: str):
        """Render summary statistics cards for KPI data"""
        st.markdown("#### Data Overview")
        
        # Basic dataset information
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._metric_card(
                "Total Records",
                f"{len(df)}",
                "Number of data points",
                "#6B46C1"
            )
        
        with col2:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            col_info = f"Numeric: {len(numeric_cols)}, Categorical: {len(categorical_cols)}"
            self._metric_card(
                "Data Columns",
                f"{len(df.columns)}",
                col_info,
                "#2563EB"
            )
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            with col3:
                avg_completeness = (1 - df[numeric_cols].isnull().mean().mean()) * 100
                self._metric_card(
                    "Data Completeness",
                    f"{avg_completeness:.1f}%",
                    "Non-null values",
                    "#059669"
                )
            
            with col4:
                std_devs = df[numeric_cols].std()
                highest_std = std_devs.max()
                highest_std_col = std_devs.idxmax()
                self._metric_card(
                    "Highest Variation",
                    f"{highest_std:.2f}",
                    f"in {highest_std_col}",
                    "#DC2626"
                )

    def _render_kpi_distributions(self, df: pd.DataFrame, kpi_name: str):
        """Render distribution visualizations for KPI data"""
        st.markdown("#### Distribution Analysis")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            st.info("No numerical columns available for distribution analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Combined violin and box plot
            fig_violin = go.Figure()
            
            for col in numeric_cols:
                fig_violin.add_trace(go.Violin(
                    y=df[col],
                    name=col,
                    box_visible=True,
                    meanline_visible=True,
                    points="outliers"
                ))
            
            fig_violin.update_layout(
                title="Distribution Overview",
                height=400,
                showlegend=True,
                violingap=0.3
            )
            
            st.plotly_chart(fig_violin, use_container_width=True)
        
        with col2:
            # Enhanced histogram
            selected_col = st.selectbox(
                "Select column for detailed distribution",
                options=numeric_cols
            )
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df[selected_col],
                nbinsx=30,
                name="Distribution"
            ))
            
            kde = gaussian_kde(df[selected_col].dropna())
            x_range = np.linspace(df[selected_col].min(), df[selected_col].max(), 100)
            fig_hist.add_trace(go.Scatter(
                x=x_range,
                y=kde(x_range) * len(df[selected_col]) * (df[selected_col].max() - df[selected_col].min()) / 30,
                name="Density",
                line=dict(color='red')
            ))
            
            fig_hist.update_layout(
                title=f"{selected_col} Distribution with Density Curve",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)

    def _render_kpi_correlations(self, df: pd.DataFrame, kpi_name: str):
        """Render correlation analysis for KPI data if multiple numerical columns exist"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return
        
        st.markdown("#### Feature Relationships")
        
        # Correlation matrix
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(
            title='Feature Correlation Matrix',
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter matrix for datasets with 3-6 columns
        if 2 < len(numeric_df.columns) <= 6:
            fig_scatter = px.scatter_matrix(
                numeric_df,
                dimensions=numeric_df.columns,
                title="Feature Relationships"
            )
            
            fig_scatter.update_layout(
                height=600,
                showlegend=False
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)

    def _render_time_patterns(self, df: pd.DataFrame, kpi_name: str):
        """Render time-based patterns if datetime columns are present"""
        # Check for datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        date_like_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        if len(datetime_cols) == 0 and len(date_like_cols) == 0:
            return
        
        st.markdown("#### Temporal Patterns")
        
        # Convert date-like columns to datetime if needed
        if len(datetime_cols) == 0 and len(date_like_cols) > 0:
            for col in date_like_cols:
                try:
                    df[col] = pd.to_datetime(df[col])
                    datetime_cols = datetime_cols.append(col)
                except:
                    continue
        
        if len(datetime_cols) > 0:
            # Select time column
            time_col = datetime_cols[0] if len(datetime_cols) == 1 else st.selectbox(
                "Select time column",
                options=datetime_cols
            )
            
            # Select value column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            value_col = st.selectbox("Select value to analyze", options=numeric_cols)
            
            # Time series plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[value_col],
                mode='lines+markers',
                name=value_col
            ))
            
            fig.update_layout(
                title=f"{value_col} Over Time",
                height=400,
                xaxis_title=time_col,
                yaxis_title=value_col
            )
            
            st.plotly_chart(fig, use_container_width=True)