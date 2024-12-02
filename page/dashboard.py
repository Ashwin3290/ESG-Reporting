import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import DataManager
from config.constants import CUSTOM_CSS
import pandas as pd
from typing import List,Optional
import numpy as np
from scipy.stats import gaussian_kde
from utils.filename_utils import get_original_kpi_name, load_name_mapping
import os
import json

class DashboardPage:
    def __init__(self):
        self.data_manager = DataManager()
        self.categories = ['Environmental', 'Social', 'Governance']
        self.kpi_reference = json.load(open('data/kpi_reference.json', 'r'))

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
        
        st.markdown("""
            <style>
            /* Subtle styling for selectbox */
            .stSelectbox {
                margin-bottom: 1rem;
            }
            
            .stSelectbox > div > div {
                background-color: #f8fafc;  /* Very light blue-gray */
                border: 1px solid #e2e8f0;  /* Light gray border */
                border-radius: 6px;
                padding: 2px 8px;
            }
            
            .stSelectbox > div > div:hover {
                border-color: #cbd5e1;  /* Slightly darker on hover */
            }
            
            /* Style for the dropdown options */
            .stSelectbox > div > div > div {
                color: #334155;  /* Dark gray text */
                font-size: 0.95rem;
            }
            
            /* Arrow icon color */
            .stSelectbox > div > div > div[data-baseweb="select"] > div {
                color: #64748b;  /* Medium gray for the arrow */
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
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
        
        with col3:
            st.markdown("""
                <style>
                .advisor-btn {
                    background-color: #6B46C1;
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    width: 100%;
                    transition: background-color 0.2s;
                }
                .advisor-btn:hover {
                    background-color: #553C9A;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("💬", key="advisor_btn", help="Open KPI Advisor"):
                st.session_state.current_page = "chat"
                st.rerun()

    def _render_overview_cards(self, categorized_data):
        scores = {}
        for category, data in categorized_data.items():
            if len(data):
                category_scores = []
                for kpi_name, value in data.items():
                    normalized_value, _, _ = self._normalize_kpi_value(kpi_name, value, self.kpi_reference)
                    category_scores.append(normalized_value)
                scores[category] = sum(category_scores) / len(category_scores)
        
        overall_score = sum(scores.values()) / len([s for s in scores.values() if s > 0]) if scores else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "#6B46C1"
            if overall_score >= 75:
                status_icon = "↑"
                description = "Strong performance"
            else:
                status_icon = "↓"
                description = "Needs improvement"
                
            self._metric_card(
                "Overall ESG Score",
                f"{overall_score:.1f} {status_icon}",
                description,
                status_color
            )
        
        with col2:
            completed_kpis = sum(len(data) for data in categorized_data.values())
            total_kpis = self.data_manager.get_total_kpi_len(st.session_state.selected_industry)
            completion_rate = (completed_kpis / total_kpis * 100) if total_kpis > 0 else 0
            
            status_color = "#059669"
            if completion_rate >= 75:
                status_icon = "↑"
                description = "Good coverage"
            else:
                status_icon = "↓"
                description = f"{total_kpis - completed_kpis} KPIs remaining"
            
            self._metric_card(
                "Completion Rate",
                f"{completed_kpis}/{total_kpis} {status_icon}",
                f"{completion_rate:.1f}% complete",
                status_color
            )
        
        with col3:
            if scores:
                highest_cat = max(scores.items(), key=lambda x: x[1])
                status_color = "#2563EB" 
                if highest_cat[1] >= 75:
                    status_icon = "↑"
                    description = "Strong leader"
                else:
                    status_icon = "↓"
                    description = "Room for improvement"
                    
                self._metric_card(
                    "Top Category",
                    f"{highest_cat[0]} {status_icon}",
                    f"Score: {highest_cat[1]:.1f}",
                    status_color
                )
            else:
                self._metric_card(
                    "Top Category",
                    "No data",
                    "Add KPIs to see results",
                    "#2563EB"
                )

    def _render_category_tab(self, category, category_data):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            self._render_kpi_comparison_chart(category_data, category,self.kpi_reference)
        
        with col2:
            self._render_category_performance_radar(category_data,category,self.kpi_reference)
        
        self._render_kpi_table(category_data,self.kpi_reference)

    def _normalize_kpi_value(self, kpi_name: str, value: float, kpi_reference: dict) -> tuple[float, float, str]:
        """
        Normalize KPI value to 0-100 scale and determine if inversion is needed
        Returns: (normalized_value, original_value, unit)
        """
        ref = kpi_reference.get(kpi_name, {})
        best = ref.get('best_score', 0)
        worst = ref.get('worst_score', 0)
        unit = ref.get('unit', '')
        
        if best == worst:
            return 50, value, unit
            
        is_higher_better = best > worst
        
        if is_higher_better:
            normalized = ((value - worst) / (best - worst)) * 100
        else:
            normalized = ((value - best) / (worst - best)) * 100
            normalized = 100 - normalized
            
        normalized = max(0, min(100, normalized))
        
        return normalized, value, unit

    def _render_kpi_comparison_chart(self, kpi_data: dict, category: str, kpi_reference: dict):
        st.markdown(f"### {category} KPI Performance")
        
        normalized_values = []
        original_values = []
        units = []
        
        for kpi_name, value in kpi_data.items():
            norm_val, orig_val, unit = self._normalize_kpi_value(kpi_name, value, kpi_reference)
            normalized_values.append(norm_val)
            original_values.append(orig_val)
            units.append(unit)
        
        fig = go.Figure()
        
        # Add bar for current values
        fig.add_trace(go.Bar(
            x=list(kpi_data.keys()),
            y=normalized_values,
            marker_color='#6B46C1',
            name='Current Value',
            hovertemplate='%{x}<br>' +
                        'Normalized Score: %{y:.1f}<br>' +
                        'Original Value: %{customdata[0]:.2f} %{customdata[1]}<extra></extra>',
            customdata=list(zip(original_values, units))
        ))
        
        # Add bar for industry average
        fig.add_trace(go.Bar(
            x=list(kpi_data.keys()),
            y=[75] * len(kpi_data),
            name='Industry Average',
            marker_color='#E5E7EB',
            hovertemplate='Industry Average: 75<extra></extra>'
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
            ),
            yaxis_title="Normalized Score (0-100)"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_category_performance_radar(self, kpi_data: dict, category: str, kpi_reference: dict):
        st.markdown("### Performance Distribution")
        
        # Normalize all values first
        normalized_values = []
        for kpi_name, value in kpi_data.items():
            norm_val, _, _ = self._normalize_kpi_value(kpi_name, value, kpi_reference)
            normalized_values.append(norm_val)
        
        # Create metrics for radar chart
        metrics = ['Average', 'Maximum', 'Minimum', 'Median']
        if normalized_values:
            values = [
                sum(normalized_values) / len(normalized_values),
                max(normalized_values),
                min(normalized_values),
                sorted(normalized_values)[len(normalized_values)//2]
            ]
        else:
            values = [0, 0, 0, 0]
        
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
        
        st.plotly_chart(fig, use_container_width=True, key=hash(category))

    def _render_kpi_table(self, kpi_data: dict, kpi_reference: dict):
        st.markdown("### KPI Details")
        
        rows = []
        for kpi_name, value in kpi_data.items():
            normalized_value, original_value, unit = self._normalize_kpi_value(kpi_name, value, kpi_reference)
            rows.append({
                'KPI': kpi_name,
                'Original Value': f"{original_value:.2f} {unit}",
                'Normalized Score': normalized_value,
                'Status': 'On Track' if normalized_value >= 75 else 'Needs Attention',
                'Trend': '↑' if normalized_value >= 75 else '↓'
            })
        
        df = pd.DataFrame(rows)
        
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                'KPI': 'KPI Name',
                'Original Value': 'Actual Value',
                'Normalized Score': st.column_config.NumberColumn(
                    'Normalized Score',
                    help='Score normalized to 0-100 scale',
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
        
        # Create KPI selector dropdown with original names
        name_mapping = load_name_mapping()
        display_names = {sanitized: original for sanitized, original in name_mapping.items() 
                        if f"{sanitized}_cal_data.csv" in kpi_files}
        
        if not display_names:
            st.info("No mapped KPI data available for analysis")
            return
            
        selected_display_name = st.selectbox(
            "Select KPI for detailed analysis",
            options=list(display_names.values()),
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Find the corresponding sanitized name
        selected_sanitized = next(
            (san for san, orig in display_names.items() 
            if orig == selected_display_name), 
            None
        )
        
        if not selected_sanitized:
            st.error("Could not find corresponding file for selected KPI")
            return

        # Load and analyze selected KPI data
        kpi_data = self._load_kpi_data(selected_sanitized)
        
        if kpi_data is None or kpi_data.empty:
            st.error(f"No data available for {selected_display_name}")
            return
        
        # Render EDA components
        self._render_kpi_data_summary(kpi_data, selected_display_name)
        self._render_kpi_distributions(kpi_data, selected_display_name)
        self._render_kpi_correlations(kpi_data, selected_display_name)
        self._render_time_patterns(kpi_data, selected_display_name)

    def _get_kpi_files(self) -> List[str]:
        """Get list of KPI files from session_files directory"""
        session_files_dir = "session_files"
        if not os.path.exists(session_files_dir):
            return []
        
        return [f for f in os.listdir(session_files_dir) 
                if f.endswith('_cal_data.csv')]

    def _load_kpi_data(self, sanitized_name: str) -> Optional[pd.DataFrame]:
        """Load KPI data from CSV file"""
        try:
            file_path = f"session_files/{sanitized_name}_cal_data.csv"
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                return df
            return None
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