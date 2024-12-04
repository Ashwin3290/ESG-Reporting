# ESG Analysis Platform

An interactive web platform for tracking, analyzing, and improving Environmental, Social, and Governance (ESG) metrics. Features include dynamic dashboards, KPI management, and AI-powered advisory capabilities.

## Features

- **Interactive ESG Dashboards**
  - Real-time performance tracking
  - Category-wise analysis
  - Comparative visualizations

- **KPI Management**
  - Automated data processing
  - Custom KPI calculations
  - Performance tracking

- **AI-Powered Advisor**
  - Real-time ESG guidance
  - Strategy recommendations
  - Performance analysis

- **Data Analysis**
  - Exploratory data analysis
  - Trend visualization
  - Benchmark comparisons

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

## Installation

1. Create and activate virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

1. Required environment variables:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

2. Prepare reference data:
- Place industry KPI data in `data/kpi_data.csv`
- Configure KPI references in `data/kpi_reference.json`
- Set up KPI specifications in `data/kpis.json`

## Running the Application

1. Start the application:
```bash
streamlit run main.py
```

2. Access the platform:
- Open your browser
- Navigate to `http://localhost:8501`

## Usage Guide

1. **Industry Selection**
   - Choose your industry from the home page
   - Use the search function to find specific industries

2. **KPI Management**
   - Upload CSV files with your ESG data
   - Map columns to required KPI inputs
   - View calculated KPI values

3. **Dashboard Navigation**
   - Access overview metrics
   - Explore category-wise performance
   - Analyze trends and patterns

4. **AI Advisor**
   - Chat with the ESG advisor
   - Get performance insights
   - Receive improvement recommendations

## Project Structure

```
├── data/          # Reference data and configurations
├── logs/          # Application logs
├── session_files/ # Temporary session data
├── page/          # Page components
├── utils/         # Utility functions
└── agent/         # AI advisor components
```

## Error Handling

- Check `logs/` directory for detailed error logs
- Verify file permissions for data directories
- Ensure all required environment variables are set
- Validate input data formats