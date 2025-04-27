# ESG Analysis Platform API

A FastAPI-based backend for the ESG Analysis Platform, providing comprehensive Environmental, Social, and Governance (ESG) metrics tracking, analysis, and AI-powered advisory capabilities.

## Features

- **Industry-specific KPI Management**: Track and analyze industry-specific ESG KPIs tailored to various business sectors
- **Intelligent Column Mapping**: Automatically map uploaded data files to required KPI inputs using Gemini 2.0 Flash LLM
- **Advanced ESG Analysis**: Generate comprehensive ESG analysis and recommendations with AI assistance
- **MongoDB Integration**: Persistent data storage with session-based management for efficient multi-user support
- **AI-Powered Advisory**: Integrated with Gemini 2.0 Flash for intelligent analysis and strategic recommendations
- **Flexible Data Import**: Support for CSV and Excel file formats with automatic header detection
- **RESTful API Design**: Clean, well-documented API endpoints following best practices

## System Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Frontend    │     │  FastAPI       │     │   MongoDB     │
│   (UI Team)   │────▶│  Backend      │────▶│   Database    │
└───────────────┘     └───────────────┘     └───────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │   Gemini 2.0  │
                      │   Flash LLM   │
                      └───────────────┘
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Gemini API key (for AI-powered features)

### Installation

1. Clone the repository or navigate to the existing directory:
```bash
cd D:\Office\esg-api
```

2. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
# Or on Linux/Mac: source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment variables in `.env`:
```
# MongoDB connection
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=esg_platform

# API settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
SECRET_KEY=your-secret-key-for-token-generation

# Gemini API settings
GEMINI_API_KEY=your-gemini-api-key

# CORS settings
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8501"]
```

5. Initialize the database with seed data using the helper script:
```bash
python scripts/init_database.py
```

## Running the API

### Option 1: Using the Start Script

The easiest way to start the API locally is using the provided start script, which performs initial setup and starts the server:

```bash
python start.py
```

### Option 2: Manual Startup

Alternatively, you can start the server directly with uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```


The API will be available at http://localhost:8000, and the interactive documentation is accessible at http://localhost:8000/docs.

## API Endpoints

The ESG Analysis Platform API provides the following endpoint groups:

### Industries Endpoints

```
GET /api/industries                  # Get all industries
GET /api/industries/search?q={query} # Search industries
GET /api/industries/{industry_id}    # Get specific industry
GET /api/industries/{industry_id}/kpis # Get KPIs for industry by category
```

### Session Management

```
POST /api/sessions                   # Create a new session
GET /api/sessions/{session_id}       # Get session data
PUT /api/sessions/{session_id}       # Update session data
DELETE /api/sessions/{session_id}    # End session
```

### File Management

```
POST /api/files/upload               # Upload file(s)
GET /api/files/{file_id}             # Get file metadata
GET /api/files/{file_id}/content     # Get file content
GET /api/files/{file_id}/columns     # Get columns for CSV files
DELETE /api/files/{file_id}          # Delete file
```

### KPI Management

```
GET /api/kpis                        # Get all KPI specifications
GET /api/kpis/{kpi_id}               # Get KPI details
POST /api/kpis/calculate             # Calculate KPI value from input data
GET /api/kpis/session/{session_id}   # Get all KPIs for a session
GET /api/kpis/categories             # Get all ESG categories
GET /api/kpis/category/{category}    # Get KPIs by category
```

### Column Mapping

```
POST /api/mapping/exact              # Map columns using exact match
POST /api/mapping/llm                # Map columns using LLM
POST /api/mapping/manual             # Set manual column mappings
GET /api/mapping/{session_id}/{kpi_name} # Get current mapping status
```

### Dashboard Data

```
GET /api/dashboard/overview/{session_id}         # Get dashboard overview data
GET /api/dashboard/category/{category}/{session_id} # Get data for a specific category
GET /api/dashboard/charts/{chart_type}/{session_id} # Get data for specific chart
```

### AI Advisory System

```
POST /api/advisor/analyze            # Run comprehensive ESG analysis
POST /api/advisor/chat               # Chat with the ESG advisor
GET /api/advisor/recommendations/{session_id} # Get stored recommendations
GET /api/advisor/history/{session_id} # Get analysis history
GET /api/advisor/analysis/{analysis_id} # Get specific analysis
```

## Example Usage

### Basic Flow

1. **Create a session**

```bash
curl -X POST "http://localhost:8000/api/sessions" \
     -H "Content-Type: application/json" \
     -d '{"industry": "Oil & Gas"}'
```

Response:
```json
{"session_id": "78a9021b-9e6d-4eac-8eb9-2964801c1c91", "expires_at": "2025-05-03T14:23:42.123456"}
```

2. **Upload a data file**

```bash
curl -X POST "http://localhost:8000/api/files/upload?session_id=78a9021b-9e6d-4eac-8eb9-2964801c1c91" \
     -F "file=@data.csv"
```

3. **Map columns with LLM**

```bash
curl -X POST "http://localhost:8000/api/mapping/llm" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "78a9021b-9e6d-4eac-8eb9-2964801c1c91", "kpi_name": "Energy consumption, total", "file_id": "file123"}'
```

4. **Calculate KPI values**

```bash
curl -X POST "http://localhost:8000/api/kpis/calculate" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "78a9021b-9e6d-4eac-8eb9-2964801c1c91", "kpi_name": "Energy consumption, total", "file_id": "file123"}'
```

5. **Get AI-powered analysis**

```bash
curl -X POST "http://localhost:8000/api/advisor/analyze" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "78a9021b-9e6d-4eac-8eb9-2964801c1c91", "analysis_type": "full"}'
```

## Running Tests

### API Testing

The project includes a basic API test script that verifies core functionality:

```bash
python scripts/api_test.py
```

### Adding Unit Tests

To run the test suite (once implemented):

```bash
pytest tests/
```

## Development Guidelines

### Code Style

This project follows PEP 8 style guidelines. Run the following to check code style:

```bash
flake8 app/ tests/
```

### Adding New Features

When adding new features:

1. Create appropriate database models in `app/db/models.py`
2. Implement service logic in `app/services/`
3. Add API endpoints in `app/api/endpoints/`
4. Update documentation

## License

MIT
