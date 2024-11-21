# ESG Analysis Platform

A sophisticated web application built with Streamlit for analyzing Environmental, Social, and Governance (ESG) metrics across different industry sectors.

## Overview

The platform provides real-time ESG analytics through an intuitive interface, enabling users to:
- Select and analyze specific industry sectors
- Input and manage KPI data
- Visualize ESG performance through interactive dashboards
- Generate comprehensive ESG reports

## Features

### 1. Industry Selection
- Dynamic industry filtering and selection
- Sector-specific KPI mapping
- Automated industry categorization

### 2. KPI Management
- Automated KPI data validation
- Support for both quantitative and qualitative KPIs
- Bulk data import capabilities
- Real-time KPI calculation engine

### 3. Dashboard Analytics
- Interactive visualization components
- Category-wise ESG performance metrics
- Comparative analysis tools
- Statistical overview generation
- Time-series analysis capabilities

### 4. Data Processing
- Automated data cleaning and validation
- Column mapping interface
- CSV file processing
- Real-time data transformation

## Technical Architecture

### Core Components
- Frontend: Streamlit
- Data Processing: Pandas, NumPy
- Visualization: Plotly
- Configuration: JSON-based KPI specifications

### Key Modules
1. `DataManager`: Handles data operations and KPI calculations
2. `DashboardPage`: Manages visualization and analytics
3. `KPIsPage`: Handles KPI data input and validation
4. `HomePage`: Main interface and navigation

## Setup and Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
