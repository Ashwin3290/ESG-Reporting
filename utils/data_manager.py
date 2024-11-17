from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import streamlit as st

class DataManager:
    def __init__(self):
        # Load CSV data
        self.df = pd.read_csv('data\kpi_data.csv')
        # Clean up any null values in KPI Name
        self.df['KPI Name'] = self.df['KPI Name'].fillna('')
        
        # Split KPIs into ESG categories (temporary solution)
        all_kpis = self.df['KPI Name'].unique().tolist()
        n = len(all_kpis)
        self.esg_categories = {
            'Environmental': all_kpis[:n//3],
            'Social': all_kpis[n//3:2*n//3],
            'Governance': all_kpis[2*n//3:]
        }
        
        # Dictionary to store KPI types (can be loaded from a config file later)
        self.kpi_types = {}
        
    def get_industries(self) -> List[str]:
        """Get list of unique industries"""
        return sorted(self.df['Industry'].unique().tolist())
    
    def get_industry_kpis_by_category(self, industry: str) -> Dict[str, List[str]]:
        """Get KPIs for an industry organized by ESG category"""
        industry_kpis = self.df[self.df['Industry'] == industry]['KPI Name'].unique().tolist()
        return {
            category: [kpi for kpi in kpis if kpi in industry_kpis]
            for category, kpis in self.esg_categories.items()
        }
    
    def get_kpi_details(self, kpi_name: str) -> Dict:
        """Get details for a specific KPI"""
        kpi_data = self.df[self.df['KPI Name'] == kpi_name].iloc[0]
        return {
            'specification_id': kpi_data['Specification ID'],
            'scope': kpi_data['Scope'],
            'specification': kpi_data['Specification'],
            'type': self.kpi_types.get(kpi_name, 'qualitative')  # Default to quantitative
        }
    
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
            # Using proper indexing to avoid warning
            return float(df.iloc[0].iloc[0])
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return None
            
    def set_kpi_type(self, kpi_name: str, kpi_type: str):
        """Set KPI type (qualitative/quantitative)"""
        self.kpi_types[kpi_name] = kpi_type