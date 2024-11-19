import streamlit as st
import pandas as pd
import os
import json
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
        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = {}
        if "column_mappings" not in st.session_state:
            st.session_state.column_mappings = {}
        
        # Create session_files directory if it doesn't exist
        os.makedirs("session_files", exist_ok=True)
        
        # Load KPI specifications
        with open('data/kpis.json', 'rb') as f:
            self.kpi_specs = json.load(f)

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

    def _auto_map_columns(self, available_columns, required_columns):
        """Automatically map columns if exact matches are found"""
        mappings_updated = False
        for col_key, col_info in required_columns.items():
            # Check if the required column name exists in available columns
            if col_info['name'] in available_columns:
                if st.session_state.column_mappings.get(col_key) != col_info['name']:
                    st.session_state.column_mappings[col_key] = col_info['name']
                    mappings_updated = True
        return mappings_updated

    def _render_column_mapping(self):
        """Render the column mapping interface with auto-mapping"""
        st.subheader("Map Data Columns")
        
        # File selection
        selected_file = st.selectbox(
            "Select Data Source",
            list(st.session_state.uploaded_files.keys()),
            key="mapping_file_select"
        )
        
        if not selected_file:
            return
            
        file_info = st.session_state.uploaded_files[selected_file]
        available_columns = file_info['columns']
        
        # Collect all required numerical columns across KPIs
        required_columns = {}
        for kpi_name, kpi_spec in self.kpi_specs.items():
            if kpi_spec.get('is_numerical', True):
                for data_item in kpi_spec.get('required_data', []):
                    column_key = f"{kpi_name} || {data_item['name']}"
                    required_columns[column_key] = {
                        'kpi': kpi_name,
                        'description': data_item['description'],
                        'name': data_item['name']
                    }
        
        # Auto-map columns when file is selected or changed
        mappings_updated = self._auto_map_columns(available_columns, required_columns)
        if mappings_updated:
            self._process_mapped_data(selected_file)
            st.success("Some columns were automatically mapped based on matching names!")
        
        st.subheader("Map Required Columns")
        
        # Create column mappings with pre-selected values from auto-mapping
        mappings_changed = False
        for col_key, col_info in required_columns.items():
            current_mapping = st.session_state.column_mappings.get(col_key)
            
            # Determine the index for the selectbox
            if current_mapping is None:
                index = 0
            else:
                try:
                    index = available_columns.index(current_mapping) + 1
                except ValueError:
                    index = 0
            
            selected_column = st.selectbox(
                f"{col_info['kpi']} - {col_info['description']} ({col_info['name']})",
                options=['-- Select Column --'] + available_columns,
                index=index,
                key=f"mapping_{col_key}"
            )
            
            if selected_column != '-- Select Column --':
                if st.session_state.column_mappings.get(col_key) != selected_column:
                    st.session_state.column_mappings[col_key] = selected_column
                    mappings_changed = True
        
        if mappings_changed:
            self._process_mapped_data(selected_file)

    def _process_mapped_data(self, filename):
        """Process and save data based on column mappings with enhanced error handling"""
        try:
            df = st.session_state.uploaded_files[filename]['data']
            
            # Group mappings by KPI
            kpi_mappings = {}
            for col_key, mapped_column in st.session_state.column_mappings.items():
                if mapped_column:
                    kpi_name, col_name = col_key.split('||')
                    if kpi_name not in kpi_mappings:
                        kpi_mappings[kpi_name] = {}
                    kpi_mappings[kpi_name][col_name] = mapped_column
            
            # Process each KPI's data
            for kpi_name, mappings in kpi_mappings.items():
                try:
                    # Validate KPI specifications exist
                    if kpi_name not in self.kpi_specs:
                        st.warning(f"KPI {kpi_name} not found in specifications")
                        continue
                    
                    # Check required columns
                    required_columns = self.kpi_specs[kpi_name].get('required_data', [])
                    
                    # Validate all required columns are mapped
                    if len(mappings) != len(required_columns):
                        missing_columns = [
                            item['name'] for item in required_columns 
                            if item['name'] not in mappings
                        ]
                        st.warning(f"Incomplete mapping for {kpi_name}. Missing: {', '.join(missing_columns)}")
                        continue
                    
                    # Prepare DataFrame with mapped columns
                    selected_columns = list(mappings.values())
                    
                    # Validate all selected columns exist in the DataFrame
                    missing_df_columns = [col for col in selected_columns if col not in df.columns]
                    if missing_df_columns:
                        st.warning(f"Columns not found in DataFrame: {', '.join(missing_df_columns)}")
                        continue
                    
                    # Create DataFrame with selected columns
                    selected_df = df[selected_columns].copy()
                    selected_df.columns = list(mappings.keys())
                    
                    # Save processed data
                    output_filename = f"session_files/{kpi_name}_cal_data.csv"
                    selected_df.to_csv(output_filename, index=False)
                    
                    # Update KPI data status
                    st.session_state.kpi_data[kpi_name] = "Data complete"
                    st.success(f"Processed data for {kpi_name}")
                
                except Exception as kpi_error:
                    st.error(f"Error processing KPI {kpi_name}: {str(kpi_error)}")
        
        except Exception as overall_error:
            st.error(f"Critical error in data processing: {str(overall_error)}")

    def _render_kpi_list(self, kpis: list, category: str, tab_idx: int):
        """Render the list of KPIs with cards"""
        for kpi_idx, kpi in enumerate(kpis):
            unique_key = f"{category}_{tab_idx}_{kpi_idx}_{hash(kpi)}"
            
            st.markdown(f'<div class="kpi-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([0.7, 0.3])
            kpi_details = self.data_manager.get_kpi_details(kpi)
            if kpi_details["specification"] in self.kpi_specs.keys():
                print(kpi_details["specification"])
                with col1:
                    st.markdown(f"**{kpi}**")
                    st.markdown(f"*Specification:* {kpi_details['specification']}")
                    st.markdown(f"*Scope:* {kpi_details['scope']}")
                
                with col2:
                    if not self.kpi_specs[kpi_details['specification']].get('is_numerical', True):
                        # For text-based KPIs
                        if st.button("Add Answer", key=f"text_input_{unique_key}"):
                            st.session_state.modal_state = True
                            st.session_state.current_kpi = kpi
                            st.rerun()
                    else:
                        # For numerical KPIs
                        status = st.session_state.kpi_data.get(kpi, "Data incomplete")
                        st.markdown(f"**Status:** {status}")
                
                st.markdown("</div>", unsafe_allow_html=True)

    def _render_text_input_modal(self):
        """Render the modal for text input"""
        if not st.session_state.current_kpi:
            return

        kpi = st.session_state.current_kpi
        st.subheader(f"Input Answer for {kpi}")
        
        value = st.text_area(
            "Enter your response",
            key=f"text_input_{hash(kpi)}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", key=f"submit_{hash(kpi)}"):
                st.session_state.kpi_data[kpi] = value
                st.session_state.modal_state = False
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"cancel_{hash(kpi)}"):
                st.session_state.modal_state = False
                st.rerun()