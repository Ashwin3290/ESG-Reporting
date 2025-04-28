kpi_calculations = {
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
            "Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices": "legal_expenses + fines_paid",
            "Percentage of revenues in regions with low corruption index": 
                "(revenue_by_region / total_revenue) * 100",
            "Percentage of new products introduced in last 12 months": 
                "(new_product_revenue / total_revenue) * 100",
            "CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)": "(esg_investments / total_capex) * 100",
            "Share of market by product/segment": "(product_revenue / total_market_revenue) * 100",
            "Capacity utilisation of facilities": "(actual_capacity_used / total_capacity) * 100",

            # Compliance and Political KPIs
            "Contributions to political parties as percentage of revenue": "(political_contributions / total_revenue) * 100",
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

reference={
    "Energy consumption, total": {
        "best_score": 500,
        "worst_score": 2500,
        "unit": "MWh"
    },
    "GHG emissions, total (scope I,II)": {
        "best_score": 100,
        "worst_score": 5000,
        "unit": "tCO2e"
    },
    "Total CO₂,NOx, SOx, VOC emissions in million tonnes": {
        "best_score": 0.5,
        "worst_score": 10,
        "unit": "Million tonnes"
    },
    "Improvement rate of product energy efficiency compared to previous year": {
        "best_score": 15,
        "worst_score": -5,
        "unit": "Percentage"
    },
    "Water consumption in m³": {
        "best_score": 50000,
        "worst_score": 500000,
        "unit": "Cubic meters"
    },
    "Total waste in tonnes": {
        "best_score": 100,
        "worst_score": 5000,
        "unit": "Tonnes"
    },
    "Percentage of total waste which is recycled": {
        "best_score": 90,
        "worst_score": 10,
        "unit": "Percentage"
    },
    "Percentage of FTE leaving p.a./total FTE": {
        "best_score": 5,
        "worst_score": 35,
        "unit": "Percentage"
    },
    "Average expenses on training per FTE p.a": {
        "best_score": 2000,
        "worst_score": 200,
        "unit": "Currency per FTE"
    },
    "Total number of fatalities in relation to FTEs": {
        "best_score": 0,
        "worst_score": 0.1,
        "unit": "Fatality Ratio"
    },
    "Total number of suppliers": {
        "best_score": 50,
        "worst_score": 5,
        "unit": "Number of Suppliers"
    },
    "Contributions to political parties as percentage of revenue": {
        "best_score": 0,
        "worst_score": 2,
        "unit": "Percentage"
    },
    "Percentage of new products introduced in last 12 months": {
        "best_score": 25,
        "worst_score": 5,
        "unit": "Percentage"
    },
    "CapEx allocation to investments on ESG relevant aspects of business as definedby the company (refered to Introduction 1.8.1. KPIs & Definitions)": {
        "best_score": 20,
        "worst_score": 2,
        "unit": "Percentage"
    },
    "Percentage of revenues in regions with Transparency International corruption index below 6.0": {
        "best_score": 90,
        "worst_score": 10,
        "unit": "Percentage"
    },
    "Total amount of bonuses, incentives and stock options paid out": {
        "best_score": 500000,
        "worst_score": 50000,
        "unit": "Currency"
    },
    "Expenses and fines on filings, law suits related to anti-competitivebehavior, anti-trust and monopoly practices": {
        "best_score": 0,
        "worst_score": 1000000,
        "unit": "Currency"
    },
    "Total cost of relocation": {
        "best_score": 100000,
        "worst_score": 2000000,
        "unit": "Currency"
    },
    "Percentage of total customers surveyed comprising satisfied customers": {
        "best_score": 95,
        "worst_score": 50,
        "unit": "Percentage"
    },
    "Capacity utilisation of facilities": {
        "best_score": 90,
        "worst_score": 40,
        "unit": "Percentage"
    },
    "Hazardous waste total in tonnes": {
        "best_score": 10,
        "worst_score": 500,
        "unit": "Tonnes"
    },
    "Share of market by product/segment": {
        "best_score": 35,
        "worst_score": 5,
        "unit": "Percentage"
    },
    "Total number of FTEs receiving 90% of bonuses": {
        "best_score": 20,
        "worst_score": 80,
        "unit": "Percentage"
    },
    "Total number of FTEs receiving bonuses": {
        "best_score": 50,
        "worst_score": 5,
        "unit": "Percentage of Total FTEs"
    },
    "Key Performance Narrative (Please answer the questions in max. 500 words)How do you ensure that your suppliers adhere to a standard of ESG compliancesimilar to that of your company?V28-05 III Key Performance Narrative (Please answer the questions in max. 500 words)When assessing the performance of your procurement and purchasing functions:Do you incentivise your procurement management for the selection of ESGperforming suppliers even if you might have to carry a premium over lessexpensive suppliers?": {
        "best_response": "Our comprehensive supplier management system includes quarterly ESG audits and real-time monitoring through our digital compliance platform. We maintain detailed scorecards for all suppliers, tracking 50+ ESG metrics across environmental impact, labor practices, and governance standards. Our supplier evaluation process includes both announced and unannounced site visits, third-party verification, and continuous performance monitoring. Our procurement team's compensation structure directly ties 30% of their performance bonuses to ESG-related metrics, with a clear premium threshold of up to 15% for suppliers who demonstrate exceptional ESG performance. This is supported by a sophisticated cost-benefit analysis framework that quantifies long-term value creation from sustainable sourcing. We conduct monthly supplier training sessions, maintain a supplier development program, and provide technical assistance for ESG improvements. Our dedicated supplier portal offers real-time performance tracking, automated compliance reporting, and a collaborative platform for sharing best practices. We've implemented blockchain-based traceability for critical supply chain components. We operate a structured supplier development program with clear improvement targets, quarterly reviews, and dedicated improvement plans. This includes mentorship programs, technology transfer initiatives, and innovation workshops. Suppliers showing consistent improvement receive preferential status and increased business opportunities. Our multi-tier risk assessment framework covers immediate suppliers and their sub-suppliers. We employ predictive analytics to identify potential ESG risks, maintain contingency plans for high-risk scenarios, and conduct regular stress tests of our supply chain resilience. Currently, 95% of our suppliers meet our ESG standards, with 40% exceeding them. We achieve 100% traceability for critical materials and maintain a supplier retention rate of 85%. Our supplier diversity program includes 30% minority-owned businesses.",
        "worst_response": "We check supplier compliance through annual self-reporting questionnaires. Basic environmental and social standards are included in our supplier contracts, and we rely on suppliers to maintain their own ESG standards. Our procurement decisions are primarily based on cost considerations. While we encourage suppliers to maintain good practices, we do not specifically incentivize ESG performance or allocate additional budget for sustainable sourcing. Suppliers receive our ESG guidelines during onboarding, and we maintain email communication for updates on policy changes. Compliance is checked during contract renewal periods. Suppliers are expected to meet minimum standards, and issues are addressed when reported. We review performance during annual contract renewals. We maintain a list of approved suppliers and address issues as they arise. Basic compliance checks are performed during initial supplier selection. Currently, 60% of suppliers meet basic compliance requirements, and we track major violations and address them on a case-by-case basis.",
        "best_score": 1,
        "worst_score": 0
    }
}


import json
import pandas as pd

data=json.load(open('data\kpis.json',"r"))

for k,v in data.items():
    if k in reference:
        for k1,v1 in reference[k].items():
            data[k][k1]=v1
    if k in kpi_calculations:
            data[k]["calculation_logic"]=v1

# print(data)

for k in kpi_calculations:
    if k not in data:
        print(k)

for k in reference:
    if k not in data:
        print(k)
