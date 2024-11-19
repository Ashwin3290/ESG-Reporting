import pandas as pd
import json

class KPICalculator:
    def __init__(self, kpi_specs_path='data/kpis.json'):
        with open(kpi_specs_path, 'r') as f:
            self.kpi_specs = json.load(f)
        
        self.kpi_calculations = kpi_calculations = {
    "Energy consumption, total": "total_energy_consumption + energy_by_source",
    "GHG emissions, total (scope I,II)": "scope_1_emissions + scope_2_emissions",
    "Percentage of FTE leaving p.a./total FTE": "(fte_leaving / total_fte_start) * 100",
    "Average expenses on training per FTE p.a": "total_training_expenses / total_fte",
    "Age structure/distribution (number of FTEs per age group, 10-year intervals)": "age_distribution",
    "Total amount of bonuses, incentives and stock options paid out in €,$": "innovation_bonuses + innovation_incentives",
    r"Total number of FTEs who receive 90 % of total amount of bonuses, incentivesand stock options": "innovation_compensation_recipients",
    "Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices": "legal_expenses + fines_paid",
    "Percentage of revenues in regions with Transparency International corruptionindex below 6.0": "(revenue_by_region / total_revenue) * 100",
    "Percentage of new products or modified products introduced lessproducts than 12 months ago": "(new_product_revenue / total_revenue) * 100",
    "Total CO2,NOx, SOx, VOC emissions in million tonnes": "co2_emissions + nox_emissions + sox_emissions + voc_emissions",
    "Total waste in tonnes": "scope_1_waste",
    "Percentage of total waste which is recycled": "(recycled_waste / total_waste) * 100",
    "Improvement rate of product energy efficiency compared to previous year": "((current_energy_efficiency - previous_energy_efficiency) / previous_energy_efficiency) * 100",
    "Contributions to political parties as a percentage of total revenuespolitical parties": "(political_contributions / total_revenue) * 100",
    "Total number of fatalities in relation to FTEsS04-04 II Total number of injuries in relation to FTEs": "fatalities / total_fte",
    "Total spending on product safety corporateAspects of Products": "safety_spending",
    "Percentage of total products sold or shipped corporate subject to product recallsfor safety or health reasons": "(recalled_products / total_products) * 100",
    "Total cost of relocation in monetary terms i.e. currency incl. Indemnity, pay-off,relocation of jobs outplacement, hiring, training, consulting": "relocation_costs",
    "Average length of customer relationship in years": "customer_relationship_duration",
    "Percentage of total customers surveyed comprising satisfied customers": "(customers_surveyed / total_customers) * 100",
    "CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)": "(esg_investments / total_capex) * 100",
    "Capacity utilisation as a percentage of total available facilities": "(actual_capacity_used / total_capacity) * 100",
    "Total number of suppliersV28-02 II Percentage of sourcing from 3 biggest external suppliersV28-03 II Turnover of suppliers in percent": "total_suppliers",
    "Hazardous waste total in tonnes total": "hazardous_waste",
    "TOP 2 components of waste incl. emissions to soil by environmental importance(according to TRI; PRTR; and EPER) Rank 1E07-02 III TOP 2 components of waste incl. emissions to soil by environmental importance(according to TRI; PRTR; and EPER) Rank 2": "waste_component_1 + waste_component_2",
    "Percentage of material supply of cobalt covered by hedging contractsE17-05 III Percentage of revenue from products that contain cobalt to total revenueE17-06 III Total cobalt purchasedE17-07 III Percentage of material supply of titanium covered by hedging contractsE17-08 III Percentage of revenue from products that contain titanium to total revenueE17-09 III Total titanium purchased": "(cobalt_supply_covered / total_cobalt_needed) * 100",
    "Waste effluent water in cubic meters": "effluent_water",
    "Number of sites with ISO 14001 certification / number of total sitesCompatibility": "(iso_certified_sites / total_sites) * 100",
    "Share of market by product, product line, segment, region or total": "(product_revenue / total_market_revenue) * 100",
    "Water consumption in m³": "total_water_consumption + water_by_source",
    "Percentage of total facilities certificated ac...": "(certified_facilities / total_facilities) * 100",
    "Total spendings in monetary terms i.e. currenc...": "maintenance_costs + safety_costs",
    "Vertical range of manufacturing in Percentmanu...": "(in_house_manufacturing_value / total_manufacturing_value) * 100",
    "Water (in m³) used per amount (e.g. in tonnes)...": "water_consumption / production_volume",
    "Percentage of total suppliers and supply chain...": "(suppliers_with_agreements / total_suppliers) * 100"
}

    def calculate_kpi(self, kpi_name, df):
        """
        Calculate KPI based on the specification and provided DataFrame
        """
        try:
            # Retrieve calculation for specific KPI
            calculation = self.kpi_calculations.get(kpi_name)
            if not calculation:
                return None, f"No calculation found for {kpi_name}"

            # Get required columns from specification
            required_columns = [
                item['name'] for item in 
                self.kpi_specs.get(kpi_name, {}).get('required_data', [])
            ]

            # Check if all required columns are present
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return None, f"Missing columns: {', '.join(missing_columns)}"

            # Perform calculation
            result = df.apply(lambda row: eval(calculation, row.to_dict()), axis=1)
            
            return result.mean(), None
        
        except Exception as e:
            return None, f"Calculation error: {str(e)}"

# Create an instance for easy import
kpi_calculator = KPICalculator()