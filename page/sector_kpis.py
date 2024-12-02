import streamlit as st
import pandas as pd
import os
import json
from streamlit_modal import Modal
import uuid
from utils.data_manager import DataManager
from utils.kpi_calculator import KPICalculator
from utils.logging import kpi_logger, log_dataframe_info
import logging
from utils.filename_utils import get_kpi_filename
from utils.text_evaluator import score_esg_narrative

class KPIsPage:
    def __init__(self):
        self.data_manager = DataManager()
        self.kpi_calculator = KPICalculator()
        self._initialize_session_state()
        self._setup_directory()
        self._load_kpi_specs()

    def _initialize_session_state(self):
        """Initialize all session state variables"""
        session_vars = {
            "modal_state": False,
            "current_kpi": None,
            "kpi_data": {},
            "uploaded_files": {},
            "column_mappings": {},
            "mapping_status": {},
            "calculated_values": {}  # New: Store calculated KPI values
        }
        
        for var, default in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default

    def render(self):
        if "selected_industry" not in st.session_state:
            st.error("No industry selected")
            return

        industry = st.session_state.selected_industry
        
        # File Management and Column Mapping Section
        with st.expander("Data Source Management", expanded=False):
            self._render_file_management()
            
        if st.session_state.uploaded_files:
            with st.expander("Column Mapping", expanded=False):
                self._render_column_mapping()
        
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

        # Create tabs for ESG categories
        categories = ['Environmental', 'Social', 'Governance']
        tabs = st.tabs(categories)
        
        # Render tabs
        for tab_idx, (tab, category) in enumerate(zip(tabs, categories)):
            with tab:
                kpis = self.data_manager.get_industry_kpis_by_category(industry).get(category, [])
                if kpis:
                    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
                    self._render_kpi_list(kpis, category, tab_idx)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(f"No {category} KPIs available for this industry")

        # Text input modal handling
        modal = Modal("KPI Text Input", key="text_modal")
        if st.session_state.modal_state:
            with modal.container():
                self._render_text_input_modal()

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

    def _render_file_management(self):
        """Render the file management section"""
        st.subheader("Upload Data Files")
        uploaded_files = st.file_uploader(
            "Upload CSV files",
            type="csv",
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            for file in uploaded_files:
                if file.name not in st.session_state.uploaded_files:
                    df = pd.read_csv(file)
                    st.session_state.uploaded_files[file.name] = {
                        'data': df,
                        'columns': df.columns.tolist()
                    }
                    st.success(f"Successfully uploaded: {file.name}")

        if st.session_state.uploaded_files:
            st.subheader("Available Files")
            for filename, file_info in st.session_state.uploaded_files.items():
                st.text(f"📄 {filename} - {len(file_info['columns'])} columns")

    @kpi_logger.log_execution
    def _auto_map_columns(self, available_columns, required_columns):
        mappings_updated = False
        for col_key, col_info in required_columns.items():
            if col_info['name'] in available_columns:
                if st.session_state.column_mappings.get(col_key) != col_info['name']:
                    st.session_state.column_mappings[col_key] = col_info['name']
                    mappings_updated = True        
        return mappings_updated

    def _setup_directory(self):
        """Create necessary directories"""
        os.makedirs("session_files", exist_ok=True)

    def _load_kpi_specs(self):
        """Load KPI specifications from JSON file"""
        with open('data\kpis.json',"rb") as f:
            self.kpi_specs=json.load(f)

    def _get_required_columns(self, kpi_name):
        """Get required columns for a specific KPI"""
        kpi_spec = self.kpi_specs.get(kpi_name, {})
        if not kpi_spec:
            return []
            
        return [
            {
                'name': item['name'],
                'description': item['description']
            }
            for item in kpi_spec.get('required_data', [])
        ]
    
    @kpi_logger.log_execution
    @log_dataframe_info
    def _process_mapped_data(self, filename, kpi_name):
        """Process mapped data for KPI calculation and storage"""
        try:
            df = st.session_state.uploaded_files[filename]['data']
            required_columns = self._get_required_columns(kpi_name)
            
            if not required_columns:
                return False
            
            # Get mappings for this KPI
            mappings = {}
            for col_info in required_columns:
                mapping_key = f"{kpi_name}_{col_info['name']}"
                mapped_column = st.session_state.column_mappings.get(mapping_key)
                if mapped_column:
                    mappings[col_info['name']] = mapped_column
            
            # Validate mappings
            if len(mappings) != len(required_columns):
                missing = [col['name'] for col in required_columns if col['name'] not in mappings]
                st.session_state.mapping_status[kpi_name] = "incomplete"
                return False

            # Create processed DataFrame
            selected_df = df[list(mappings.values())].copy()
            selected_df.columns = list(mappings.keys())
            # Calculate KPI value
            result, error = self.kpi_calculator.calculate_kpi(kpi_name, selected_df)
            
            if result is not None:
                st.session_state.calculated_values[kpi_name] = result
                st.session_state.kpi_data[kpi_name] = result
                st.session_state.mapping_status[kpi_name] = "complete"
                
                # Get proper filename using the utility function
                output_filename = get_kpi_filename(kpi_name)
                
                # Ensure directory exists
                os.makedirs("session_files", exist_ok=True)
                
                # Save processed data
                selected_df.to_csv(output_filename, index=False)
                
                return True
            else:
                st.session_state.mapping_status[kpi_name] = "error"
                return False

        except Exception as e:
            st.session_state.mapping_status[kpi_name] = "error"
            logging.error(f"Error processing data for {kpi_name}: {str(e)}")
            logging.error("Traceback:", exc_info=True)
            return False

    def _render_column_mapping(self):
        """Render improved column mapping interface"""
        st.subheader("Map Data Columns")
        
        selected_file = st.selectbox(
            "Select Data Source",
            list(st.session_state.uploaded_files.keys()),
            key="mapping_file_select"
        )
        
        if not selected_file:
            return
            
        file_info = st.session_state.uploaded_files[selected_file]
        available_columns = file_info['columns']
        
        # Group KPIs by category for organized mapping
        for category in ['Environmental', 'Social', 'Governance']:
            kpis = self.data_manager.get_industry_kpis_by_category(
                st.session_state.selected_industry
            ).get(category, [])
            
            if kpis:
                st.markdown(f"### {category} KPIs")
                
                for kpi in kpis:
                    kpi_details = self.data_manager.get_kpi_details(kpi)
                    kpi_name = kpi_details['specification']
                    
                    
                    if kpi_name in self.kpi_specs:
                        st.markdown(f"#### {kpi}")
                        
                        # Manual mapping interface
                        required_columns = self._get_required_columns(kpi_name)
                        mappings_changed = False
                        
                        # Auto-map columns
                        for col_info in required_columns:
                            mapping_key = f"{kpi_name}_{col_info['name']}"
                            current_mapping = st.session_state.column_mappings.get(mapping_key)
                            
                            # Auto-map if exact match exists
                            if not current_mapping and col_info['name'] in available_columns:
                                st.session_state.column_mappings[mapping_key] = col_info['name']
                                current_mapping = col_info['name']
                                mappings_changed = True
                            
                            # Create selectbox for column mapping
                            index = (available_columns.index(current_mapping) + 1 
                            if current_mapping in available_columns else 0)

                            selected_column = st.selectbox(
                            f"{col_info['description']} ({col_info['name']})",
                            options=['-- Select Column --'] + available_columns,
                            index=index,
                            key=f"mapping_{mapping_key}_{uuid.uuid4()}"
                            )
                            
                            if selected_column != '-- Select Column --':
                                if st.session_state.column_mappings.get(mapping_key) != selected_column:
                                    st.session_state.column_mappings[mapping_key] = selected_column
                                    mappings_changed = True
                        
                        if mappings_changed:
                            self._process_mapped_data(selected_file, kpi_name)
                        
                        # Show mapping status and calculated value
                        status = st.session_state.mapping_status.get(kpi_name, "pending")
                        status_colors = {
                            "complete": "green",
                            "incomplete": "orange",
                            "invalid": "red",
                            "error": "red",
                            "pending": "gray"
                        }
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                f'<p style="color: {status_colors[status]}">Status: {status}</p>',
                                unsafe_allow_html=True
                            )
                        with col2:
                            if status == "complete":
                                value = st.session_state.calculated_values.get(kpi_name)
                                if value is not None:
                                    st.markdown(f"Value: {value:.2f}")
                        
                        st.markdown("---")
                        
    def _render_kpi_list(self, kpis: list, category: str, tab_idx: int):
        for kpi_idx, kpi in enumerate(kpis):
            unique_key = f"{category}_{tab_idx}_{kpi_idx}_{hash(kpi)}"
            
            st.markdown(f'<div class="kpi-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([0.7, 0.3])
            kpi_details = self.data_manager.get_kpi_details(kpi)
            if kpi_details["specification"] in self.kpi_specs.keys():
                with col1:
                    st.markdown(f"**{kpi_details['kpi_name']}**")
                    st.markdown(f"*Specification:* {kpi_details['specification']}")
                    st.markdown(f"*Scope:* {kpi_details['scope']}")
                
                with col2:
                    if not self.kpi_specs[kpi_details['specification']].get('is_numerical', True):
                        # For text-based KPIs
                        if st.button("Add Answer", key=f"text_input_{unique_key}"):
                            st.session_state.modal_state = True
                            st.session_state.current_kpi = kpi
                            st.rerun()
                        if kpi_details["specification"] in st.session_state.calculated_values:
                                result=round(st.session_state.calculated_values[kpi_details['specification']], 2)
                                st.markdown(f"**Value:** {result}")
                                st.session_state.kpi_data[kpi] = {
                                        'value': result,
                                        'status': 'Calculated'
                                    }
                        else:
                            st.markdown(f"**Status:** Pending")
                    else:
                            if kpi_details["specification"] in st.session_state.calculated_values:
                                result=round(st.session_state.calculated_values[kpi_details['specification']], 2)
                                st.markdown(f"**Value:** {result}")
                                st.session_state.kpi_data[kpi] = {
                                        'value': result,
                                        'status': 'Calculated'
                                    }
                            else:
                                st.markdown(f"**Status:** Pending")
                    
                st.markdown("</div>", unsafe_allow_html=True)

    def _render_text_input_modal(self):
        """Render the modal for text input"""
        if not st.session_state.current_kpi:
            return

        kpi = st.session_state.current_kpi
        kpi_details = self.data_manager.get_kpi_details(kpi)
        st.subheader(f"Input Answer for {kpi_details['kpi_name']}")
        
        value = st.text_area(
            "Enter your response",
            key=f"text_input_{hash(kpi)}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", key=f"submit_{hash(kpi)}"):
                if not value:
                    st.error("Please enter a response.")
                else:
                    value=score_esg_narrative(value,kpi)
                    st.session_state.calculated_values[kpi] = value
                    st.session_state.modal_state = False
                    st.rerun()
        with col2:
            if st.button("Cancel", key=f"cancel_{hash(kpi)}"):
                st.session_state.modal_state = False
                st.rerun()