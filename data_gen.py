import pandas as pd
import numpy as np
import json
import sympy as sp
import re

class EquationDecompositionKPIDataGenerator:
    def __init__(self, 
                kpi_specs_path='data/kpis.json', 
                kpi_reference_path='data/kpi_reference.json'):
        """
        Initialize the KPI data generator with equation decomposition
        
        :param kpi_specs_path: Path to the JSON file containing KPI specifications
        :param kpi_reference_path: Path to the JSON file containing KPI reference values
        """
        # Load KPI specifications
        with open(kpi_specs_path, 'r') as f:
            self.kpi_specs = json.load(f)
        
        # Load KPI reference values
        with open(kpi_reference_path, 'r') as f:
            self.kpi_reference = json.load(f)
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

    def _extract_variables(self, formula):
        """
        Extract unique variables from a formula string
        
        :param formula: Formula string
        :return: List of unique variables
        """
        # Remove any operators and numbers
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
        return list(set(variables))
    
    def _calculate_kpi_range(self, kpi_name):
        """
        Calculate the target range for a KPI between 60-75% of the total range
        
        :param kpi_name: Name of the KPI
        :return: Tuple of (best_score, worst_score, target_min, target_max)
        """
        ref = self.kpi_reference.get(kpi_name, {})
        best_score = ref.get('best_score', 0)
        worst_score = ref.get('worst_score', 100)
        
        total_range = abs(worst_score - best_score)
        
        # Calculate 60-75% point of the range
        range_min = best_score + (0.6 * total_range)
        range_max = best_score + (0.75 * total_range)
        
        return best_score, worst_score, range_min, range_max
    
    def generate_sample_data(self, num_rows=100):
        """
        Generate a unified sample dataset for KPIs
        
        :param num_rows: Number of rows to generate
        :return: Tuple of (DataFrame, column information)
        """
        # Collect all unique variables across KPIs
        all_variables = set()
        for formula in self.kpi_calculations.values():
            all_variables.update(self._extract_variables(formula))
        
        # Collect data and column information
        data = {}
        column_info = []
        
        # Generate data for each unique variable
        for var_name in all_variables:
            # Skip empty or problematic variable names
            if not var_name or var_name in ['x', 'y']:
                continue
            
            # Try to find reference data or use default range
            best_score, worst_score, target_min, target_max = self._calculate_kpi_range(var_name)
            
            # Ensure we have reasonable min and max
            if target_min == target_max:
                target_min, target_max = 0, 100
            
            # Generate column data using normal distribution
            col_data = np.random.normal(
                loc=(target_min + target_max) / 2, 
                scale=(target_max - target_min) / 6, 
                size=num_rows
            )
            
            # Ensure non-negative and within range
            col_data = np.clip(col_data, target_min, target_max)
            
            # Store column data
            data[var_name] = col_data
            
            # Store column information
            column_info.append({
                'column_name': var_name,
                'range': {
                    'min': target_min,
                    'max': target_max,
                    'mean': (target_min + target_max) / 2,
                    'std': (target_max - target_min) / 6
                }
            })
        
        # Create DataFrame
        sample_df = pd.DataFrame(data)
        
        return sample_df, column_info
    
    def preview_sample_data(self, df):
        """
        Preview generated sample dataset and validate KPI calculations
    
        :param df: DataFrame to preview
        """
        # Validate KPI calculations for each KPI type
        print("\nKPI Calculations Validation:")
        for kpi_name, formula in self.kpi_calculations.items():
            try:
                # Calculate KPI using the provided formula
                kpi_values = df.eval(formula)
                
                # Get KPI range information
                best_score, worst_score, target_min, target_max = self._calculate_kpi_range(kpi_name)
                
                mean_kpi = kpi_values.mean()
                std_kpi = kpi_values.std()
                
                print(f"\nKPI: {kpi_name}")
                print(f"Formula: {formula}")
                print(f"Target Range: {target_min:.2f} - {target_max:.2f}")
                print(f"Actual Mean KPI: {mean_kpi:.2f}")
                print(f"Actual KPI Std Dev: {std_kpi:.2f}")
            except Exception as e:
                print(f"Error calculating {kpi_name}: {e}")
        
        # Print dataset overview
        print("\nDataset Overview:")
        print(f"Total Rows: {len(df)}")
        print(f"Total Columns: {len(df.columns)}")
    
        # Print first few rows and basic statistics
        print("\nFirst 5 Rows:")
        print(df.head())
    
        print("\nDataset Description:")
        print(df.describe())
        
        # Save to CSV
        df.to_csv("sample.csv", index=False)

# Example usage
if __name__ == "__main__":
    # Create an instance of the generator
    generator = EquationDecompositionKPIDataGenerator()
    
    # Generate sample data
    sample_df, columns_info = generator.generate_sample_data(num_rows=50)
    
    # Preview the dataset
    generator.preview_sample_data(sample_df)