import pandas as pd
import json
import numpy as np
import traceback

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
        
        self.kpi_calculations = {
            # Environmental KPIs
            "Energy consumption, total": "total_energy_consumption + energy_by_source",
            "GHG emissions, total (scope I,II)": "scope_1_emissions + scope_2_emissions",
            "Total CO²,NOx, SOx, VOC emissions in million tonnes": "co2_emissions + nox_emissions + sox_emissions + voc_emissions",
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
            "Total number of fatalities in relation to FTEsS04-04 II Total number of injuries in relation to FTEs": "fatalities / total_fte",

            # Financial and Business KPIs
            "Total amount of bonuses, incentives and stock options paid out in â‚¬,$": 
                "innovation_bonuses + innovation_incentives",
            "Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices": "legal_expenses + fines_paid",
            "Percentage of revenues in regions with low corruption index": 
                "(revenue_by_region / total_revenue) * 100",
            "Percentage of new products introduced in last 12 months": 
                "(new_product_revenue / total_revenue) * 100",
            "CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)": "(esg_investments / total_capex) * 100",
            "Share of market by product/segment": "(product_revenue / total_market_revenue) * 100",
            "Capacity utilisation as a percentage of total available facilities": "(actual_capacity_used / total_capacity) * 100",

            # Compliance and Political KPIs
            "Contributions to political parties as percentage of revenue": "(political_contributions / total_revenue) * 100",
            "Customer satisfaction percentage": "(customers_surveyed / total_customers) * 100",
            "CapEx allocation to investments on ESG relevant aspects": "(esg_investments / total_capex) * 100",
            "Total number of fatalities in relation to FTEs": "fatalities / total_fte",
            "Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent": "total_suppliers",
            "Total number of FTEs who receive 90 % of total amount of bonuses, incentivesand stock options": "innovation_compensation_recipients",
            "Expenses and fines on anti-competitive behavior": "legal_expenses + fines_paid",
            "Percentage of revenues in regions with Transparency International corruptionindex below 6.0": "(revenue_by_region / total_revenue) * 100",
            "Percentage of new products introduced less than 12 months ago": "(new_product_revenue / total_revenue) * 100",
            "Contributions to political parties as percentage of revenue": "(political_contributions / total_revenue) * 100",
            "Total cost of relocation in monetary terms i.e. currency incl. Indemnity, pay-off,relocation of jobs outplacement, hiring, training, consulting": "relocation_costs",
            "Percentage of total customers surveyed comprising satisfied customers": "(customers_surveyed / total_customers) * 100",
            "Capacity utilisation as percentage of total facilities": "(actual_capacity_used / total_capacity) * 100",
            "Share of market by product, product line, segment, region or total": "(product_revenue / total_market_revenue) * 100"
        }

    def calculate_kpi(self, kpi_name, df, is_numeric=True):
        """
        Calculate KPI based on specifications and provided DataFrame

        Args:
            kpi_name (str): Name of KPI to calculate
            df (pd.DataFrame): DataFrame containing required columns
            is_numeric (bool): Whether the KPI should return a numeric value

        Returns:
            tuple: (KPI value, error message with traceback)
        """
        try:
            kpi_spec = self.kpi_specs.get(kpi_name)
            if not kpi_spec:
                return None, f"No specification found for KPI: {kpi_name}\n{traceback.format_exc()}"

            calculation = self.kpi_calculations.get(kpi_name)
            if not calculation:
                return None, f"No calculation formula found for KPI: {kpi_name}\n{traceback.format_exc()}"

            # Get required columns
            required_columns = [item['name'] for item in kpi_spec.get('required_data', [])]
        
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return None, f"Missing columns: {', '.join(missing_columns)}\n{traceback.format_exc()}"

            if not is_numeric:
                if len(df) > 0:
                    return df[required_columns[0]].iloc[0], None
                print(traceback.format_exc())
                return None, f"No data available\n{traceback.format_exc()}"

            try:
                result = df.apply(lambda row: eval(calculation, row.to_dict()), axis=1)
                return float(result.mean()), None
            except Exception as calc_error:
                print(traceback.format_exc())
                return None, f"Calculation error: {str(calc_error)}\n{traceback.format_exc()}"
        
        except Exception as e:
            return None, f"General error: {str(e)}\n{traceback.format_exc()}"
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

