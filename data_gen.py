# import pandas as pd
# import numpy as np
# import json
# import random
# import os

# class UnifiedKPISampleDataGenerator:
#     def __init__(self, kpi_specs_path='data/kpis.json'):
#         """
#         Initialize the sample data generator with KPI specifications
        
#         :param kpi_specs_path: Path to the JSON file containing KPI specifications
#         """
#         # Load KPI specifications
#         with open(kpi_specs_path, 'r') as f:
#             self.kpi_specs = json.load(f)
    
#     def generate_sample_data(self, num_rows=100):
#         """
#         Generate a unified sample dataset for all numerical KPIs
        
#         :param num_rows: Number of rows to generate
#         :return: Unified DataFrame with KPI data
#         """
#         # Collect all columns to be generated
#         all_columns = []

#         example_kpis=[
#         'Energy consumption, total',
#         'GHG emissions, total (scope I,II)',
#         'Total CO²,NOx, SOx, VOC emissions in million tonnes',
#         'Improvement rate of product energy efficiency compared to previous year',
#         'Water consumption in m³',
#         'CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)',
#         'Water consumption in m³',
#         'Total number of fatalities in relation to FTEsS04-04 II Total number of injuries in relation to FTEs',
#         'Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent',
#         'Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent',
#         'Percentage of FTE leaving p.a./total FTE',
#         'Average expenses on training per FTE p.a',
#         'Age structure/distribution (number of FTEs per age group, 10-year intervals)',
#         'Total amount of bonuses, incentives and stock options paid out in â‚¬,$',
#         'Total amount of bonuses, incentives and stock options paid out in â‚¬,$',
#         'Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices',
#         'Percentage of revenues in regions with Transparency International corruptionindex below 6.0',
#         'Percentage of new products or modified products introduced lessproducts than 12 months ago',
#         'Total amount of bonuses, incentives and stock options paid out in â‚¬,$',
#         'Total amount of bonuses, incentives and stock options paid out in â‚¬,$',
#         'Total waste in tonnes',
#         'Percentage of total waste which is recycled',
#         'Contributions to political parties as a percentage of total revenuespolitical parties',
#         'Total cost of relocation in monetary terms i.e. currency incl. Indemnity, pay-off,relocation of jobs outplacement, hiring, training, consulting',
#         'Percentage of total customers surveyed comprising satisfied customers',
#         'Capacity utilisation as a percentage of total available facilities',
#         'Hazardous waste total in tonnes total',
#         'Share of market by product, product line, segment, region or total'
#         ]

#         # Iterate through KPI specifications
#         for kpi_name, kpi_spec in self.kpi_specs.items():
#             if kpi_name not in example_kpis:
#                 # Skip non-numerical KPIs
#                 if not kpi_spec.get('is_numerical', True):
#                     continue
                
#                 # Get required data columns
#                 required_data = kpi_spec.get('required_data', [])
                
#                 # Add columns with a prefix to ensure unique column names
#                 for data_item in required_data:
#                     column_name = f"{kpi_name}__{data_item['name']}"
#                     all_columns.append({
#                         'column_name': column_name,
#                         'original_name': data_item['name'],
#                         'kpi': kpi_name,
#                         'type': data_item.get('type', 'float'),
#                         'mean': data_item.get('mean', 100),
#                         'std': data_item.get('std', 20),
#                         'min': data_item.get('min', 0),
#                         'max': data_item.get('max', 1000)
#                     })
        
#         # Generate data
#         data = {}
#         for col in all_columns:
#             # Generate sample data based on type
#             if col['type'] == 'float':
#                 data[col['column_name']] = np.random.normal(col['mean'], col['std'], num_rows)
            
#             elif col['type'] == 'int':
#                 data[col['column_name']] = np.random.randint(col['min'], col['max'], num_rows)
            
#             elif col['type'] == 'percentage':
#                 data[col['column_name']] = np.random.uniform(0, 100, num_rows)
            
#             elif col['type'] == 'boolean':
#                 data[col['column_name']] = np.random.choice([True, False], num_rows)
        
#         # Create DataFrame
#         sample_df = pd.DataFrame(data)
        
#         # Apply data transformations and cleaning
#         sample_df = self._apply_data_transformations(sample_df)
        
#         return sample_df, all_columns
    
#     def _apply_data_transformations(self, df):
#         """
#         Apply optional data transformations
        
#         :param df: Input DataFrame
#         :return: Transformed DataFrame
#         """
#         # Ensure no negative values
#         df = df.clip(lower=0)
        
#         return df
    
#     def save_sample_dataset(self, df, output_path='session_files/kpi_sample_data.csv'):
#         """
#         Save the unified sample dataset to a CSV file
        
#         :param df: DataFrame to save
#         :param output_path: Path to save the CSV file
#         """
#         # Ensure directory exists
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
#         # Save to CSV
#         df.to_csv(output_path, index=False)
#         print(f"Sample dataset saved to {output_path}")
    
#     def preview_sample_data(self, df, columns_info):
#         """
#         Preview generated sample dataset
        
#         :param df: DataFrame to preview
#         :param columns_info: List of column information
#         """
#         # Print overall dataset info
#         print("\nDataset Overview:")
#         print(f"Total Rows: {len(df)}")
#         print(f"Total Columns: {len(df.columns)}")
        
#         # Print column details
#         print("\nColumn Mapping:")
#         for col_info in columns_info:
#             print(f"- {col_info['column_name']} (KPI: {col_info['kpi']}, Original Name: {col_info['original_name']})")
        
#         # Print first few rows and basic statistics
#         print("\nFirst 5 Rows:")
#         print(df.head())
        
#         print("\nDataset Description:")
#         print(df.describe())

# # Example usage
# if __name__ == "__main__":
#     # Create an instance of the generator
#     generator = UnifiedKPISampleDataGenerator()
    
#     # Generate sample data
#     sample_df, columns_info = generator.generate_sample_data(num_rows=50)
    
#     # Preview the dataset
#     generator.preview_sample_data(sample_df, columns_info)
    
#     # Save the dataset
#     generator.save_sample_dataset(sample_df)

import pandas as pd
import numpy as np
import json
import random
import os

class UnifiedKPISampleDataGenerator:
    def __init__(self, kpi_specs_path='data/kpis.json'):
        """
        Initialize the sample data generator with KPI specifications
        
        :param kpi_specs_path: Path to the JSON file containing KPI specifications
        """
        # Load KPI specifications
        with open(kpi_specs_path, 'r') as f:
            self.kpi_specs = json.load(f)
    
    def generate_sample_data(self, num_rows=100):
        """
        Generate a unified sample dataset for specific KPIs
        
        :param num_rows: Number of rows to generate
        :return: Unified DataFrame with KPI data
        """
        # Specific KPIs to generate
        example_kpis = [
            'Energy consumption, total',
            'GHG emissions, total (scope I,II)',
            'Total CO²,NOx, SOx, VOC emissions in million tonnes',
            'Improvement rate of product energy efficiency compared to previous year',
            'Water consumption in m³',
            'CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)',
            'Total number of fatalities in relation to FTEsS04-04 II Total number of injuries in relation to FTEs',
            'Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent',
            'Percentage of FTE leaving p.a./total FTE',
            'Average expenses on training per FTE p.a',
            'Age structure/distribution (number of FTEs per age group, 10-year intervals)',
            'Total amount of bonuses, incentives and stock options paid out in â‚¬,$',
            'Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices',
            'Percentage of revenues in regions with Transparency International corruptionindex below 6.0',
            'Percentage of new products or modified products introduced lessproducts than 12 months ago',
            'Total waste in tonnes',
            'Percentage of total waste which is recycled',
            'Contributions to political parties as a percentage of total revenuespolitical parties',
            'Total cost of relocation in monetary terms i.e. currency incl. Indemnity, pay-off,relocation of jobs outplacement, hiring, training, consulting',
            'Percentage of total customers surveyed comprising satisfied customers',
            'Capacity utilisation as a percentage of total available facilities',
            'Hazardous waste total in tonnes total',
            'Share of market by product, product line, segment, region or total'
        ]

        # Collect all columns to be generated
        all_columns = []

        # Iterate through specified KPIs
        for kpi_name in example_kpis:
            # Check if KPI exists in specifications
            if kpi_name not in self.kpi_specs:
                print(f"Warning: KPI '{kpi_name}' not found in specifications")
                continue

            kpi_spec = self.kpi_specs[kpi_name]
            
            # Skip non-numerical KPIs
            if not kpi_spec.get('is_numerical', True):
                continue
            
            # Get required data columns
            required_data = kpi_spec.get('required_data', [])
            
            # Add columns with a prefix to ensure unique column names
            for data_item in required_data:
                column_name = f"{data_item['name']}"
                all_columns.append({
                    'column_name': column_name,
                    'original_name': data_item['name'],
                    'kpi': kpi_name,
                    'type': 'float',
                    'mean': random.randint(10,30),
                    'std': random.randint(10,30),
                })
        
        # Generate data
        data = {}
        for col in all_columns:
            # Generate sample data based on type
            if col['type'] == 'float':
                data[col['column_name']] = np.random.normal(col['mean'], col['std'], num_rows)
            
            elif col['type'] == 'int':
                data[col['column_name']] = np.random.randint(col['min'], col['max'], num_rows)
            
            elif col['type'] == 'percentage':
                data[col['column_name']] = np.random.uniform(0, 100, num_rows)
            
            elif col['type'] == 'boolean':
                data[col['column_name']] = np.random.choice([True, False], num_rows)
        
        # Create DataFrame
        sample_df = pd.DataFrame(data)
        
        # Apply data transformations and cleaning
        sample_df = self._apply_data_transformations(sample_df)
        
        return sample_df, all_columns
    
    def _apply_data_transformations(self, df):
        """
        Apply optional data transformations
        
        :param df: Input DataFrame
        :return: Transformed DataFrame
        """
        # Ensure no negative values
        df = df.clip(lower=0)
        
        return df
    
    def save_sample_dataset(self, df, output_path='kpi_data.csv'):
        """
        Save the unified sample dataset to a CSV file
        
        :param df: DataFrame to save
        :param output_path: Path to save the CSV file
        """
        # Ensure directory exists
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Sample dataset saved to {output_path}")
    
    def preview_sample_data(self, df, columns_info):
        """
        Preview generated sample dataset
        
        :param df: DataFrame to preview
        :param columns_info: List of column information
        """
        # Print overall dataset info
        print("\nDataset Overview:")
        print(f"Total Rows: {len(df)}")
        print(f"Total Columns: {len(df.columns)}")
        
        # Print column details
        print("\nColumn Mapping:")
        for col_info in columns_info:
            print(f"- {col_info['column_name']} (KPI: {col_info['kpi']}, Original Name: {col_info['original_name']})")
        
        # Print first few rows and basic statistics
        print("\nFirst 5 Rows:")
        print(df.head())
        
        print("\nDataset Description:")
        print(df.describe())

# Example usage
if __name__ == "__main__":
    # Create an instance of the generator
    generator = UnifiedKPISampleDataGenerator()
    
    # Generate sample data
    sample_df, columns_info = generator.generate_sample_data(num_rows=50)
    
    # Preview the dataset
    generator.preview_sample_data(sample_df, columns_info)
    
    # Save the dataset
    generator.save_sample_dataset(sample_df)