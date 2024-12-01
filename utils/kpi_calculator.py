import pandas as pd
import json
import numpy as np
from utils.text_evaluator import score_esg_narrative

class KPICalculator:
    def __init__(self, kpi_specs_path="data\kpis.json"):
        """
        Initialize KPI Calculator with specifications from JSON
        
        Args:
            kpi_specs_path (str): Path to JSON file with KPI specifications
        """
        with open(kpi_specs_path, 'r') as f:
            self.kpi_specs = json.load(f)
        with open("data\kpi_reference.json", 'r') as f:
            self.kpi_reference = json.load(f)
        
        # Comprehensive KPI calculation logic
        self.kpi_calculations = {
            # Environmental KPIs
            "Energy consumption, total": "total_energy_consumption + energy_by_source",
            "GHG emissions, total (scope I,II)": "scope_1_emissions + scope_2_emissions",
            "Total CO₂,NOx, SOx, VOC emissions in million tonnes": "co2_emissions + nox_emissions + sox_emissions + voc_emissions",
            "Improvement rate of product energy efficiency compared to previous year": 
                "((current_energy_efficiency - previous_energy_efficiency) / previous_energy_efficiency) * 100",
            "Water consumption in m³": "total_water_consumption + water_by_source",
            "Total waste in tonnes": "scope_1_waste",
            "Percentage of total waste which is recycled": "(recycled_waste / total_waste) * 100",
            "Hazardous waste total in tonnes total": "hazardous_waste",

            # Workforce and HR KPIs
            "Percentage of FTE leaving p.a./total FTE": "(fte_leaving / total_fte_start) * 100",
            "Average expenses on training per FTE p.a": "total_training_expenses / total_fte",
            "Age structure/distribution (number of FTEs per age group, 10-year intervals)": "age_distribution",
            "Total number of fatalities in relation to FTEs": "fatalities / total_fte",

            # Financial and Business KPIs
            "Total amount of bonuses, incentives and stock options paid out in €,$": 
                "innovation_bonuses + innovation_incentives",
            "Expenses and fines on anti-competitive behavior": "legal_expenses + fines_paid",
            "Percentage of revenues in regions with low corruption index": 
                "(revenue_by_region / total_revenue) * 100",
            "Percentage of new products introduced in last 12 months": 
                "(new_product_revenue / total_revenue) * 100",
            "CapEx allocation to ESG investments": "(esg_investments / total_capex) * 100",
            "Share of market by product/segment": "(product_revenue / total_market_revenue) * 100",
            "Capacity utilisation of facilities": "(actual_capacity_used / total_capacity) * 100",

            # Compliance and Political KPIs
            "Contributions to political parties as percentage of revenue": 
                "(political_contributions / total_revenue) * 100",
            "Customer satisfaction percentage": "(customers_surveyed / total_customers) * 100",
            "CapEx allocation to investments on ESG relevant aspects": "(esg_investments / total_capex) * 100",
            "Total number of fatalities in relation to FTEs": "fatalities / total_fte",
            "Total number of suppliers": "total_suppliers",
            "Total amount of bonuses, incentives and stock options paid": "innovation_bonuses + innovation_incentives",
            "Total number of FTEs receiving 90% of bonuses": "innovation_compensation_recipients",
            "Expenses and fines on anti-competitive behavior": "legal_expenses + fines_paid",
            "Percentage of revenues in regions with corruption index below 6.0": "(revenue_by_region / total_revenue) * 100",
            "Percentage of new products introduced less than 12 months ago": "(new_product_revenue / total_revenue) * 100",
            "Contributions to political parties as percentage of revenue": "(political_contributions / total_revenue) * 100",
            "Total cost of relocation": "relocation_costs",
            "Percentage of total customers surveyed comprising satisfied customers": "(customers_surveyed / total_customers) * 100",
            "Capacity utilisation as percentage of total facilities": "(actual_capacity_used / total_capacity) * 100",
            "Share of market by product/segment/region": "(product_revenue / total_market_revenue) * 100"
        }

    def calculate_kpi(self, kpi_name, df,is_numeric=True):
        """
        Calculate KPI based on specifications and provided DataFrame
        
        Args:
            kpi_name (str): Name of KPI to calculate
            df (pd.DataFrame): DataFrame containing required columns
        
        Returns:
            tuple: (KPI value, error message)
        """
        try:
            # Retrieve calculation for specific KPI
            calculation = self.kpi_calculations.get(kpi_name)
            if not calculation:
                return None, f"No calculation found for {kpi_name}"

            # Get required columns from specification
            kpi_spec = self.kpi_specs.get(kpi_name, {})
            required_columns = [
                item['name'] for item in kpi_spec.get('required_data', [])
            ]

            # Validate required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return None, f"Missing columns: {', '.join(missing_columns)}"

            # Perform calculation
            result = df.apply(lambda row: eval(calculation, row.to_dict()), axis=1)
            
            # Return mean and no error
            return result.mean(), None
            
        except Exception as e:
            return None, f"Calculation error: {str(e)}"

    def evaluate_answer(self, kpi_name: str, answer: str) -> tuple[float, str | None]:
        """
        Evaluate an ESG narrative answer against reference scores.
        
        Args:
            kpi_name (str): The name of the KPI to evaluate
            answer (str): The ESG narrative answer to evaluate
            
        Returns:
            tuple[float, str | None]: A tuple containing:
                - float: The calculated score
                - str | None: Error message if any, None if successful
                
        Example:
            score, error = calculator.evaluate_answer("Energy consumption, total", "Our company reduced...")
        """
        try:
            if not isinstance(kpi_name, str) or not isinstance(answer, str):
                return 0.0, "Invalid input types. Both kpi_name and answer must be strings"
                
            if not kpi_name in self.kpi_reference:
                return 0.0, f"KPI '{kpi_name}' not found in reference data"
                
            reference = self.kpi_reference[kpi_name]
            best_score = reference['best_score']
            worst_score = reference['worst_score']
            
            score = score_esg_narrative(answer, best_score, worst_score)
            return score, None
            
        except Exception as e:
            return 0.0, f"Evaluation error: {str(e)}"

    def validate_kpi_data(self, df, kpi_name):
        """
        Validate data for a specific KPI
        
        Args:
            df (pd.DataFrame): Input DataFrame
            kpi_name (str): Name of KPI to validate
        
        Returns:
            bool: Whether data is valid for KPI calculation
        """
        kpi_spec = self.kpi_specs.get(kpi_name, {})
        required_columns = [
            item['name'] for item in kpi_spec.get('required_data', [])
        ]
        
        # Check column existence and data types
        for col in required_columns:
            if col not in df.columns:
                return False
            if not np.issubdtype(df[col].dtype, np.number):
                return False
        
        return True

    def get_kpi_details(self, kpi_name):
        """
        Retrieve detailed specifications for a specific KPI
        
        Args:
            kpi_name (str): Name of KPI
        
        Returns:
            dict: KPI specification details
        """
        return self.kpi_specs.get(kpi_name, {})

