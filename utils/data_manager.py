from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

class DataManager:
    def __init__(self):
        # Load CSV data
        self.df = pd.read_csv('data\kpi_data.csv')
        # Clean up any null values in KPI Name
        self.df['KPI Name'] = self.df['KPI Name'].fillna('')
        
        # Map cluster numbers to ESG categories
        self.cluster_to_category = {
            0: 'Environmental',
            1: 'Social',
            2: 'Governance'
        }
        
        # Dictionary to store KPI types
        self.kpi_types = {}
        
    def get_industries(self) -> List[str]:
        """Get list of unique industries"""
        return sorted(self.df['Industry'].unique().tolist())
    
    def get_industry_kpis_by_category(self, industry: str) -> Dict[str, List[str]]:
        """Get KPIs for an industry organized by ESG category based on cluster_num"""
        industry_data = self.df[self.df['Industry'] == industry]
        
        categorized_kpis = {
            'Environmental': [],
            'Social': [],
            'Governance': []
        }
        
        for _, row in industry_data.iterrows():
            category = self.cluster_to_category.get(row['Cluster'])
            if category:
                categorized_kpis[category].append(row['KPI Name'])
                
        return categorized_kpis
    
    def get_kpi_details(self, kpi_name: str) -> Dict:
        """Get details for a specific KPI"""
        kpi_data = self.df[self.df['KPI Name'] == kpi_name].iloc[0]
        return {
            'specification_id': kpi_data['Specification ID'],
            'scope': kpi_data['Scope'],
            'specification': kpi_data['Specification'],
            'type': self.kpi_types.get(kpi_name, 'quantitative')
        }
    
    def get_total_kpi_len(self, kpi_name: str) -> List[str]:
        """Get total length of KPI"""
        total_len = len(self.df[self.df['Industry'] == kpi_name])
        return total_len
    
    def search_industries(self, query: str) -> List[str]:
        """Search industries based on partial string match"""
        if not query:
            return self.get_industries()
        query = query.lower()
        return sorted([
            industry for industry in self.get_industries()
            if query in industry.lower()
        ])
    
    @staticmethod
    def validate_kpi_data(industry: str) -> tuple[bool, str]:
        """Validate if all required KPIs have data"""
        if not st.session_state.get("kpi_data", {}):
            return False, "Please input data for at least one KPI before viewing the dashboard"
        return True, ""
    
    @staticmethod
    def process_csv(file) -> Optional[float]:
        """Process uploaded CSV file for KPI data"""
        try:
            df = pd.read_csv(file)
            return float(df.iloc[0].iloc[0])
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return None
            
    def set_kpi_type(self, kpi_name: str, kpi_type: str):
        """Set KPI type (qualitative/quantitative)"""
        self.kpi_types[kpi_name] = kpi_type