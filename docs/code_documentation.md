# ESG-API Code Execution Flow Documentation

This document provides a detailed explanation of the code execution flow for each API endpoint in the ESG Analysis Platform API, showing how requests flow from endpoints through services and interact with data models.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Core Data Flow Pattern](#core-data-flow-pattern)
3. [Industries Endpoints Flow](#industries-endpoints-flow)
4. [Sessions Endpoints Flow](#sessions-endpoints-flow)
5. [Files Endpoints Flow](#files-endpoints-flow)
6. [KPIs Endpoints Flow](#kpis-endpoints-flow)
7. [Column Mapping Endpoints Flow](#column-mapping-endpoints-flow)
8. [Dashboard Endpoints Flow](#dashboard-endpoints-flow)
9. [Advisor Endpoints Flow](#advisor-endpoints-flow)
10. [Common Service Flow Patterns](#common-service-flow-patterns)

---

## System Architecture Overview

The ESG-API follows a layered architecture with clear separation of concerns:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  API Endpoints  │────▶│    Services     │────▶│  Data Models    │────▶│    Database     │
│  (FastAPI)      │     │  (Business      │     │  (Pydantic)     │     │  (MongoDB)      │
└─────────────────┘     │   Logic)        │     └─────────────────┘     └─────────────────┘
                        └─────────────────┘                 │                    ▲
                               ▲  │                         │                    │
                               │  │                         ▼                    │
                               │  │               ┌─────────────────┐           │
                               │  └──────────────▶│  External APIs  │───────────┘
                               │                  │  (Gemini LLM)   │
                               └──────────────────┐─────────────────┘
```

## Core Data Flow Pattern

Most API endpoints follow this general execution flow pattern:

1. **Request Handling**: FastAPI endpoint receives and validates the request
2. **Service Layer**: Request is passed to appropriate service for business logic processing
3. **Data Model Interaction**: Service interacts with Pydantic models for data validation
4. **Database Operations**: Service performs database operations using MongoDB
5. **External Service Calls**: If needed, service makes calls to external services (e.g., Gemini LLM)
6. **Response Generation**: Service returns processed data, which is formatted and returned by the endpoint

---

## Industries Endpoints Flow

### GET `/api/industries`

**Execution Flow:**

1. **Endpoint**: `industries.py/get_industries()`
   ```python
   @router.get("/")
   async def get_industries(
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Request handling
       industries = await data_manager.get_industries()
       return industries
   ```

2. **Service**: `data_manager.py/get_industries()`
   ```python
   async def get_industries(self):
       # Fetch industries from database
       cursor = self.db.industries.find({}, {"_id": 0})
       industries = await cursor.to_list(length=100)
       return industries
   ```

3. **Data Model**: Uses `Industry` model from `models.py`
   ```python
   class Industry(BaseModel):
       sector: str
       industry: str
       kpis: List[IndustryKPI]
   ```

4. **Database**: Retrieves documents from the `industries` collection in MongoDB

### GET `/api/industries/{industry_id}/kpis`

**Execution Flow:**

1. **Endpoint**: `industries.py/get_industry_kpis()`
   ```python
   @router.get("/{industry_id}/kpis")
   async def get_industry_kpis(
       industry_id: str = Path(..., description="Industry ID"),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Request handling and validation
       industry = await data_manager.get_industry(industry_id)
       if not industry:
           raise HTTPException(status_code=404, detail="Industry not found")
       
       # Organize KPIs by category
       kpis_by_category = await data_manager.get_industry_kpis_by_category(industry_id)
       return kpis_by_category
   ```

2. **Service**: `data_manager.py/get_industry_kpis_by_category()`
   ```python
   async def get_industry_kpis_by_category(self, industry_id: str):
       # Get industry document
       industry = await self.get_industry(industry_id)
       if not industry:
           return {}
       
       # Group KPIs by ESG category
       kpis_by_category = {
           "environmental": [],
           "social": [],
           "governance": []
       }
       
       for kpi in industry.get("kpis", []):
           category = kpi.get("esg_category", "").lower()
           if category in kpis_by_category:
               # Get KPI specification for additional details
               kpi_spec = await self.get_kpi_spec(kpi.get("specification"))
               if kpi_spec:
                   kpi_with_details = {**kpi, "details": kpi_spec}
                   kpis_by_category[category].append(kpi_with_details)
       
       return kpis_by_category
   ```

3. **Data Models**: Uses `Industry` and `IndustryKPI` models
   ```python
   class IndustryKPI(BaseModel):
       name: str
       specification_id: str
       scope: str
       specification: str
       cluster: int
       esg_category: str
   ```

4. **Database**: Retrieves and processes documents from both `industries` and `kpi_specifications` collections

---

## Sessions Endpoints Flow

### POST `/api/sessions`

**Execution Flow:**

1. **Endpoint**: `sessions.py/create_session()`
   ```python
   @router.post("/")
   async def create_session(
       request: SessionCreate,
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Request validation using Pydantic model
       session = await data_manager.create_session(
           industry=request.industry
       )
       
       return {
           "session_id": session.get("session_id"),
           "expires_at": session.get("expires_at")
       }
   ```

2. **Service**: `data_manager.py/create_session()`
   ```python
   async def create_session(self, industry: str = None) -> Dict[str, Any]:
       # Generate session ID
       session_id = str(uuid.uuid4())
       
       # Calculate expiration time (24 hours from now)
       expires_at = datetime.utcnow() + timedelta(hours=24)
       
       # Create session document
       session = {
           "session_id": session_id,
           "created_at": datetime.utcnow(),
           "last_updated": datetime.utcnow(),
           "expires_at": expires_at,
           "industry": industry,
           "uploaded_files": [],
           "column_mappings": {},
           "mapping_status": {}
       }
       
       # Insert into database
       await self.db.sessions.insert_one(session)
       
       return session
   ```

3. **Data Model**: Uses `Session` model from `models.py`
   ```python
   class Session(BaseModel):
       session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       created_at: datetime = Field(default_factory=datetime.utcnow)
       last_updated: datetime = Field(default_factory=datetime.utcnow)
       expires_at: datetime
       industry: Optional[str] = None
       uploaded_files: List[FileMetadata] = []
       column_mappings: Dict[str, Dict[str, str]] = {}
       mapping_status: Dict[str, str] = {}
   ```

4. **Database**: Creates a new document in the `sessions` collection with TTL index on `expires_at`

---

## Files Endpoints Flow

### POST `/api/files/upload`

**Execution Flow:**

1. **Endpoint**: `files.py/upload_file()`
   ```python
   @router.post("/upload")
   async def upload_file(
       session_id: str = Query(..., description="Session ID"),
       file: UploadFile = File(...),
       file_service: FileService = Depends(get_file_service),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Validate session exists
       session = await data_manager.get_session(session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Upload file
       file_id = await file_service.upload_file(session_id, file)
       
       # Get file metadata
       file_info = await file_service.get_file_metadata(file_id)
       
       return file_info
   ```

2. **Service**: `file_service.py/upload_file()`
   ```python
   async def upload_file(self, session_id: str, file: UploadFile) -> str:
       # Generate a unique file ID
       file_id = str(uuid.uuid4())
       
       # Read file content
       content = await file.read()
       
       # Get file metadata
       original_filename = file.filename
       file_size = len(content)
       content_type = file.content_type or self._guess_content_type(original_filename)
       
       # Create a unique filename to avoid collisions
       filename = generate_unique_filename(original_filename)
       
       # Store the file in GridFS
       grid_out = await self.db.fs.upload_from_stream(
           filename=filename,
           source=io.BytesIO(content),
           metadata={
               "file_id": file_id,
               "session_id": session_id,
               "original_filename": original_filename,
               "content_type": content_type,
               "upload_date": datetime.utcnow()
           }
       )
       
       # Create file metadata document
       file_metadata = {
           "file_id": file_id,
           "grid_id": grid_out,
           "filename": original_filename,
           "sanitized_filename": filename,
           "file_size": file_size,
           "content_type": content_type,
           "upload_date": datetime.utcnow(),
           "session_id": session_id
       }
       
       # Store file metadata
       await self.db.file_metadata.insert_one(file_metadata)
       
       # Update session with file reference
       await self.db.sessions.update_one(
           {"session_id": session_id},
           {
               "$push": {
                   "uploaded_files": {
                       "file_id": file_id,
                       "filename": original_filename,
                       "upload_date": datetime.utcnow(),
                       "file_size": file_size,
                       "content_type": content_type
                   }
               },
               "$set": {"last_updated": datetime.utcnow()}
           }
       )
       
       return file_id
   ```

3. **Data Model**: Uses `FileMetadata` model from `models.py`
   ```python
   class FileMetadata(BaseModel):
       file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       filename: str
       upload_date: datetime = Field(default_factory=datetime.utcnow)
       file_size: int
       content_type: str
       grid_id: Optional[str] = None  # GridFS ID
   ```

4. **Database**: 
   - Stores file content in GridFS (`fs.files` and `fs.chunks` collections)
   - Stores metadata in `file_metadata` collection
   - Updates the session document in `sessions` collection

### GET `/api/files/{file_id}/columns`

**Execution Flow:**

1. **Endpoint**: `files.py/get_file_columns()`
   ```python
   @router.get("/{file_id}/columns")
   async def get_file_columns(
       file_id: str = Path(..., description="File ID"),
       file_service: FileService = Depends(get_file_service)
   ):
       # Get file columns
       columns = await file_service.get_file_columns(file_id)
       if not columns:
           raise HTTPException(status_code=404, detail="Failed to get file columns")
       
       return {"columns": columns}
   ```

2. **Service**: `file_service.py/get_file_columns()`
   ```python
   async def get_file_columns(self, file_id: str) -> Optional[List[str]]:
       # Get file content
       content, metadata = await self.get_file_content(file_id)
       if not content:
           return None
       
       # Check if file is CSV
       content_type = metadata.get("content_type", "")
       filename = metadata.get("filename", "")
       
       if not (content_type == "text/csv" or filename.lower().endswith(".csv")):
           logger.warning(f"File {file_id} is not a CSV file")
           return None
       
       try:
           # Try to parse CSV
           csv_content = content.decode("utf-8")
           return parse_csv_columns(csv_content)
       except Exception as e:
           logger.error(f"Error parsing CSV file: {str(e)}")
           return None
   ```

3. **Utility Function**: `filename_utils.py/parse_csv_columns()`
   ```python
   def parse_csv_columns(csv_content: str) -> List[str]:
       # Parse CSV and extract headers
       reader = csv.reader(io.StringIO(csv_content))
       header_row = next(reader)
       
       # Clean column names
       columns = [col.strip() for col in header_row if col.strip()]
       return columns
   ```

4. **Database**: Retrieves file content from GridFS

---

## KPIs Endpoints Flow

### POST `/api/kpis/calculate`

**Execution Flow:**

1. **Endpoint**: `kpis.py/calculate_kpi()`
   ```python
   @router.post("/calculate")
   async def calculate_kpi(
       request: KPICalculationRequest,
       kpi_calculator: KPICalculatorService = Depends(get_kpi_calculator),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(request.session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get KPI specification
       kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
       if not kpi_spec:
           raise HTTPException(status_code=404, detail="KPI not found")
       
       # Calculate KPI
       result, error = await kpi_calculator.calculate_kpi(
           session_id=request.session_id,
           kpi_name=request.kpi_name,
           file_id=request.file_id,
           mappings=request.mappings,
           is_numeric=kpi_spec.get("is_numerical", True)
       )
       
       if error:
           return {"error": error, "status": "error"}
       
       return {
           "kpi_name": request.kpi_name,
           "value": result,
           "status": "success"
       }
   ```

2. **Request Model**:
   ```python
   class KPICalculationRequest(BaseModel):
       session_id: str
       kpi_name: str
       file_id: str = None
       mappings: Dict[str, str] = None
   ```

3. **Service**: `kpi_calculator.py/calculate_kpi()`
   ```python
   async def calculate_kpi(
       self, 
       session_id: str, 
       kpi_name: str, 
       file_id: str = None, 
       mappings: Dict[str, str] = None,
       is_numeric: bool = True
   ) -> Tuple[Any, Optional[str]]:
       # Get session
       session = await self.data_manager.get_session(session_id)
       if not session:
           return None, "Session not found"
       
       # Get file_id if not provided
       if not file_id:
           uploaded_files = session.get("uploaded_files", [])
           if not uploaded_files:
               return None, "No files available for KPI calculation"
           # Use most recent file
           file_id = uploaded_files[-1].get("file_id")
       
       # Get column mappings if not provided
       if not mappings:
           mappings = await self.data_manager.get_column_mappings(session_id, kpi_name)
           if not mappings:
               return None, f"No column mappings found for KPI: {kpi_name}"
       
       # Get KPI specification
       kpi_spec = await self.data_manager.get_kpi_spec(kpi_name)
       if not kpi_spec:
           return None, f"KPI specification not found: {kpi_name}"
       
       # Load data from file
       df = await self.file_service.load_file_as_dataframe(file_id)
       if df is None:
           return None, "Failed to load file data"
       
       try:
           # Extract required data using mappings
           required_data = {}
           for field_name, column_name in mappings.items():
               if column_name in df.columns:
                   required_data[field_name] = df[column_name].values
               else:
                   return None, f"Column not found in file: {column_name}"
           
           # Calculate KPI value
           result = self._calculate_value(required_data, kpi_spec, is_numeric)
           
           # Store calculated KPI
           await self._store_kpi_result(
               session_id=session_id,
               kpi_name=kpi_name,
               value=result
           )
           
           return result, None
       except Exception as e:
           logger.error(f"Error calculating KPI: {str(e)}")
           return None, f"Calculation error: {str(e)}"
   ```

4. **Data Model**: Uses `CalculatedKPI` model
   ```python
   class CalculatedKPI(BaseModel):
       session_id: str
       kpi_name: str
       calculation_date: datetime = Field(default_factory=datetime.utcnow)
       value: Any  # Can be number or text
       status: str
       calculation_metadata: Dict[str, Any] = {}
   ```

5. **Database**: 
   - Retrieves data from the `sessions` and `kpi_specifications` collections
   - Retrieves file data from GridFS
   - Stores result in the `calculated_kpis` collection

---

## Column Mapping Endpoints Flow

### POST `/api/mapping/llm`

**Execution Flow:**

1. **Endpoint**: `column_mapping.py/map_columns_llm()`
   ```python
   @router.post("/llm")
   async def map_columns_llm(
       request: LLMMappingRequest,
       column_mapping_service: ColumnMappingService = Depends(get_column_mapping_service),
       data_manager: DataManagerService = Depends(get_data_manager),
       file_service: FileService = Depends(get_file_service)
   ):
       # Verify session exists
       session = await data_manager.get_session(request.session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Verify file exists
       file_info = await file_service.get_file_metadata(request.file_id)
       if not file_info:
           raise HTTPException(status_code=404, detail="File not found")
       
       # Verify KPI exists
       kpi_spec = await data_manager.get_kpi_spec(request.kpi_name)
       if not kpi_spec:
           raise HTTPException(status_code=404, detail="KPI not found")
       
       # Get file columns
       columns = await file_service.get_file_columns(request.file_id)
       if not columns:
           raise HTTPException(status_code=404, detail="Failed to get file columns")
       
       # Try exact matching first
       exact_mappings = await column_mapping_service.perform_exact_matching(
           kpi_name=request.kpi_name,
           file_columns=columns,
           kpi_spec=kpi_spec
       )
       
       # Check if all required fields are mapped
       all_mapped = len(exact_mappings) == len(kpi_spec.get("required_data", []))
       if all_mapped:
           # Update session with mappings
           await data_manager.update_column_mappings(
               session_id=request.session_id,
               kpi_name=request.kpi_name,
               mappings=exact_mappings
           )
           
           return {
               "kpi_name": request.kpi_name,
               "mappings": exact_mappings,
               "complete": True,
               "method": "exact"
           }
       
       # Get sample data for context if requested
       sample_data = None
       if request.use_sample_data:
           sample_data = await file_service.get_file_sample(request.file_id, max_rows=5)
       
       # Perform LLM mapping for remaining fields
       mappings = await column_mapping_service.perform_llm_matching(
           kpi_name=request.kpi_name,
           file_columns=columns,
           kpi_spec=kpi_spec,
           existing_mappings=exact_mappings,
           sample_data=sample_data
       )
       
       # Update session with mappings
       await data_manager.update_column_mappings(
           session_id=request.session_id,
           kpi_name=request.kpi_name,
           mappings=mappings
       )
       
       return {
           "kpi_name": request.kpi_name,
           "mappings": mappings,
           "complete": len(mappings) == len(kpi_spec.get("required_data", [])),
           "method": "llm"
       }
   ```

2. **Request Model**:
   ```python
   class LLMMappingRequest(BaseModel):
       session_id: str
       kpi_name: str
       file_id: str
       use_sample_data: bool = True
   ```

3. **Service**: `column_mapping.py/perform_llm_matching()`
   ```python
   async def perform_llm_matching(self, kpi_name: str, file_columns: List[str], 
                           kpi_spec: Dict[str, Any] = None, 
                           existing_mappings: Dict[str, str] = None, 
                           sample_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
       # Get KPI specification if not provided
       if not kpi_spec:
           kpi_spec = await self.db.kpi_specifications.find_one({"name": kpi_name}, {"_id": 0})
           if not kpi_spec:
               logger.warning(f"KPI specification not found: {kpi_name}")
               return {}
       
       # Initialize with existing mappings if provided
       mappings = existing_mappings.copy() if existing_mappings else {}
       
       # Get required fields
       required_fields = kpi_spec.get("required_data", [])
       if not required_fields:
           logger.warning(f"No required fields found for KPI: {kpi_name}")
           return mappings
       
       # Filter out already mapped fields
       mapped_fields = set(mappings.keys())
       unmapped_fields = [f for f in required_fields if f.get("name") not in mapped_fields]
       
       if not unmapped_fields:
           return mappings
       
       # Filter out already mapped columns
       mapped_columns = set(mappings.values())
       unmapped_columns = [c for c in file_columns if c not in mapped_columns]
       
       if not unmapped_columns:
           return mappings
       
       # Use LLM to match remaining fields
       field_descriptions = "\n".join([
           f"- {f.get('name')}: {f.get('description')} (Type: {f.get('type')})"
           for f in unmapped_fields
       ])
       
       columns_list = "\n".join([f"- {col}" for col in unmapped_columns])
       
       # Add sample data if available for better context
       sample_data_str = ""
       if sample_data and len(sample_data) > 0:
           sample_rows = sample_data[:3]  # Limit to first 3 rows
           sample_data_str = "\nSample data (first 3 rows):\n"
           for row in sample_rows:
               # Only include unmapped columns in sample
               filtered_row = {k: v for k, v in row.items() if k in unmapped_columns}
               sample_data_str += f"{filtered_row}\n"
       
       prompt = f"""
       You are a data analyst mapping CSV columns to required fields for a KPI calculation.
       
       KPI Name: {kpi_name}
       
       Required Fields:
       {field_descriptions}
       
       Available CSV Columns:
       {columns_list}
       {sample_data_str}
       
       Your task is to map each required field to the most semantically appropriate column name from the available columns list.
       
       Follow these rules for matching:
       1. First, look for exact matches or close variations (case differences, underscores vs spaces).
       2. Then look for semantic equivalence (e.g., "total_employees" might match "fte_count").
       3. Consider common abbreviations and conventions in business data.
       4. If a field has multiple potential matches, choose the one with the highest confidence.
       5. If there is no reasonable match for a field, assign it null.
       
       Return your answer as a JSON object with the following format:
       ```json
       {{
           "required_field_name": "matched_csv_column",
           "another_required_field": "another_matched_column",
           "field_without_match": null
       }}
       ```
       
       First explain your reasoning for each mapping decision, then provide the JSON object.
       """
       
       try:
           # Call Gemini API
           response = await self.gemini_client.generate_text(
               model="gemini-2.0-flash",
               prompt=prompt,
               temperature=0.1
           )
           
           # Extract JSON from response
           try:
               json_str = self._extract_json_from_text(response)
               llm_mappings = json.loads(json_str)
               
               # Filter out null values
               llm_mappings = {k: v for k, v in llm_mappings.items() if v is not None}
               
               # Validate mappings (ensure columns exist)
               validated_mappings = {
                   k: v for k, v in llm_mappings.items() 
                   if v in unmapped_columns and k not in mappings
               }
               
               # Combine with existing mappings
               mappings.update(validated_mappings)
               
               return mappings
           except json.JSONDecodeError as e:
               logger.error(f"Error parsing JSON from LLM response: {e}")
               logger.debug(f"Response text: {response}")
               return mappings
       except Exception as e:
           logger.error(f"Error using LLM for column mapping: {e}")
           return mappings
   ```

4. **External API Call**: Uses `GeminiClient` to call Gemini LLM API
   ```python
   # In llm_helpers.py
   async def generate_text(self, model: str = "gemini-2.0-flash", 
                     prompt: str = None,
                     max_output_tokens: int = 1024, 
                     temperature: float = 0.2) -> str:
       # Call Google's Generative Language API
       if not self.api_key:
           raise ValueError("Gemini API key not provided")
           
       model_url = f"{self.base_url}/models/{model}:generateContent"
       headers = {
           "Content-Type": "application/json"
       }
       
       data = {
           "contents": [
               {
                   "parts": [
                       {
                           "text": prompt
                       }
                   ]
               }
           ],
           "generationConfig": {
               "temperature": temperature,
               "maxOutputTokens": max_output_tokens,
               "topP": 0.95,
               "topK": 40
           }
       }
       
       url = f"{model_url}?key={self.api_key}"
       
       # Make async HTTP request
       async with aiohttp.ClientSession() as session:
           async with session.post(url, headers=headers, json=data) as response:
               if response.status != 200:
                   error_text = await response.text()
                   logger.error(f"Gemini API error: {error_text}")
                   raise Exception(f"API request failed with status {response.status}: {error_text}")
                   
               result = await response.json()
               
               # Extract text from response
               try:
                   response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                   return response_text
               except (KeyError, IndexError) as e:
                   logger.error(f"Error extracting text from response: {e}")
                   logger.error(f"Response structure: {json.dumps(result, indent=2)}")
                   raise Exception("Failed to extract text from API response")
   ```

5. **Database**: Updates column mappings in the session document in the `sessions` collection

---

## Advisor Endpoints Flow

### POST `/api/advisor/analyze`

**Execution Flow:**

1. **Endpoint**: `advisor.py/run_analysis()`
   ```python
   @router.post("/analyze")
   async def run_analysis(
       request: AnalysisRequest,
       advisor_service: ESGAdvisorService = Depends(get_advisor_service),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(request.session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get industry if not provided
       industry = request.industry
       if not industry:
           industry = session.get("industry")
           if not industry:
               raise HTTPException(status_code=400, detail="No industry specified for analysis")
       
       # Run analysis
       try:
           result = await advisor_service.run_analysis(
               session_id=request.session_id,
               analysis_type=request.analysis_type,
               industry=industry
           )
           
           if "error" in result:
               raise HTTPException(status_code=400, detail=result["error"])
           
           return result
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
   ```

2. **Request Model**:
   ```python
   class AnalysisRequest(BaseModel):
       session_id: str
       analysis_type: str = "full"  # 'full', 'environmental', 'social', 'governance', 'strategy'
       industry: Optional[str] = None
   ```

3. **Service**: `advisor.py/run_analysis()` and `_run_full_analysis()`
   ```python
   async def run_analysis(self, session_id: str, analysis_type: str, industry: str) -> Dict[str, Any]:
       # Get session KPI data
       kpi_data = await self._get_session_kpis(session_id)
       if not kpi_data:
           return {"error": "No KPI data available for analysis"}
       
       # Run analysis based on type
       try:
           if analysis_type == "full":
               result = await self._run_full_analysis(session_id, kpi_data, industry)
           elif analysis_type in ["environmental", "social", "governance"]:
               result = await self._analyze_category(session_id, analysis_type, kpi_data, industry)
           elif analysis_type == "strategy":
               # Get the most recent analyses for all categories
               categories = await self._get_latest_category_analyses(session_id)
               if not categories:
                   # If no previous analyses, run analyses for all categories
                   categories = {
                       "environmental": await self._analyze_category(session_id, "environmental", kpi_data, industry),
                       "social": await self._analyze_category(session_id, "social", kpi_data, industry),
                       "governance": await self._analyze_category(session_id, "governance", kpi_data, industry)
                   }
               
               # Develop strategy based on category analyses
               result = await self._develop_strategy(session_id, categories, industry)
           else:
               return {"error": f"Unknown analysis type: {analysis_type}"}
           
           return result
       except Exception as e:
           logger.error(f"Error in analysis: {str(e)}")
           return {"error": f"Analysis failed: {str(e)}"}
   
   async def _run_full_analysis(self, session_id: str, kpi_data: Dict[str, Any], industry: str) -> Dict[str, Any]:
       # First process and validate the data
       processed_data = await self._process_data(kpi_data, industry)
       
       # Run analyses for each category in parallel
       env_task = asyncio.create_task(
           self._analyze_category(session_id, "environmental", processed_data, industry)
       )
       
       soc_task = asyncio.create_task(
           self._analyze_category(session_id, "social", processed_data, industry)
       )
       
       gov_task = asyncio.create_task(
           self._analyze_category(session_id, "governance", processed_data, industry)
       )
       
       # Wait for all analyses to complete
       environmental = await env_task
       social = await soc_task
       governance = await gov_task
       
       # Combine results
       categories = {
           "environmental": environmental,
           "social": social,
           "governance": governance
       }
       
       # Develop strategy
       strategy = await self._develop_strategy(session_id, categories, industry)
       
       # Generate recommendations
       recommendations = await self._generate_recommendations(categories, industry)
       
       # Store complete analysis
       analysis_id = await self._store_analysis_result(
           session_id=session_id,
           analysis_type="full",
           result={
               "environmental": environmental,
               "social": social,
               "governance": governance,
               "strategies": strategy,
               "recommendations": recommendations
           }
       )
       
       # Return combined results
       return {
           "analysis_id": analysis_id,
           "environmental": environmental,
           "social": social,
           "governance": governance,
           "strategies": strategy,
           "recommendations": recommendations
       }
   ```

4. **LLM Integration**: Uses Gemini API for analysis via `_analyze_category()`, `_develop_strategy()`, and `_generate_recommendations()`
   ```python
   async def _analyze_category(self, session_id: str, category: str, data: Dict[str, Any], industry: str) -> Dict[str, Any]:
       # Extract category-specific data
       category_data = data.get(category, {})
       
       # Create prompt for category analysis
       prompt = f"""
       You are an ESG analyst specializing in {category} performance analysis.
       
       Industry: {industry}
       
       {category.capitalize()} metrics:
       {json.dumps(category_data, indent=2)}
       
       Please provide a comprehensive analysis of this {category} data:
       1. Current performance assessment
       2. Benchmarking against industry standards
       3. Identification of risks and vulnerabilities
       4. Strengths and areas of excellence
       5. Improvement opportunities
       
       Return your analysis as a detailed JSON object with clear sections.
       """
       
       # Call LLM
       try:
           response_text = await self.gemini_client.generate_text(
               model="gemini-2.0-flash",
               prompt=prompt,
               temperature=0.2
           )
           
           # Try to parse JSON from response
           try:
               json_str = self._extract_json(response_text)
               analysis = json.loads(json_str)
               
               # Store category analysis
               analysis_id = await self._store_analysis_result(
                   session_id=session_id,
                   analysis_type=f"{category}_analysis",
                   result={category: analysis}
               )
               
               analysis["analysis_id"] = analysis_id
               return analysis
           except json.JSONDecodeError:
               # If parsing fails, return a structured analysis from the text
               logger.warning(f"Failed to parse JSON from {category} analysis response")
               structured_analysis = {
                   "raw_analysis": response_text,
                   "parsing_error": "Could not parse structured JSON result"
               }
               
               # Store category analysis
               analysis_id = await self._store_analysis_result(
                   session_id=session_id,
                   analysis_type=f"{category}_analysis",
                   result={category: structured_analysis}
               )
               
               structured_analysis["analysis_id"] = analysis_id
               return structured_analysis
       except Exception as e:
           logger.error(f"Error in {category} analysis: {str(e)}")
           return {"error": f"Analysis failed: {str(e)}"}
   ```

5. **Data Model**: Uses `AnalysisResult` model from `models.py`
   ```python
   class AnalysisResult(BaseModel):
       session_id: str
       analysis_type: str
       created_at: datetime = Field(default_factory=datetime.utcnow)
       environmental: Dict[str, Any] = {}
       social: Dict[str, Any] = {}
       governance: Dict[str, Any] = {}
       strategies: Dict[str, Any] = {}
       recommendations: List[str] = []
   ```

6. **Database**: 
   - Retrieves KPI data from the `calculated_kpis` collection
   - Stores analysis results in the `analysis_results` collection

### POST `/api/advisor/chat`

**Execution Flow:**

1. **Endpoint**: `advisor.py/chat_with_advisor()`
   ```python
   @router.post("/chat")
   async def chat_with_advisor(
       request: ChatRequest,
       advisor_service: ESGAdvisorService = Depends(get_advisor_service),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(request.session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get session info
       industry = session.get("industry")
       if not industry:
           raise HTTPException(status_code=400, detail="No industry assigned to session")
       
       # Get latest analysis if available
       context = None
       if request.analysis_id:
           analysis = await data_manager.get_analysis_result(request.analysis_id)
           if analysis:
               context = analysis
       else:
           # Try to get most recent analysis
           analyses = await data_manager.get_session_analyses(request.session_id)
           if analyses:
               # Sort by created_at and take the most recent
               analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
               context = analyses[0]
       
       # Chat with advisor
       try:
           response = await advisor_service.chat(
               session_id=request.session_id,
               message=request.message,
               industry=industry,
               context=context
           )
           
           return {
               "response": response,
               "session_id": request.session_id
           }
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
   ```

2. **Request Model**:
   ```python
   class ChatRequest(BaseModel):
       session_id: str
       message: str
       analysis_id: Optional[str] = None
   ```

3. **Service**: `advisor.py/chat()`
   ```python
   async def chat(self, session_id: str, message: str, industry: str, context: Dict[str, Any] = None) -> str:
       # Get KPI data for context
       kpi_data = await self._get_session_kpis(session_id)
       
       # Build prompt
       prompt = self._build_chat_prompt(message, industry, kpi_data, context)
       
       # Call LLM
       try:
           response = await self.gemini_client.generate_text(
               model="gemini-2.0-flash",
               prompt=prompt,
               temperature=0.7  # Higher temperature for more conversational responses
           )
           
           # Store chat history
           await self._store_chat_message(session_id, message, response)
           
           return response
       except Exception as e:
           logger.error(f"Error in chat: {str(e)}")
           return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
   ```

4. **Prompt Building**: `_build_chat_prompt()` method
   ```python
   def _build_chat_prompt(self, message: str, industry: str, kpi_data: Dict[str, Any], context: Dict[str, Any] = None) -> str:
       # Base prompt
       prompt = f"""
       You are an ESG advisor for a company in the {industry} industry. You provide expert guidance on environmental, social, and governance matters.
       
       Current ESG data:
       {json.dumps(kpi_data, indent=2)}
       """
       
       # Add context if available
       if context:
           prompt += f"""
           Previous analysis:
           {json.dumps(context, indent=2)}
           """
       
       # Add user message
       prompt += f"""
       User question: {message}
       
       Please provide a helpful, informative response based on the ESG data and previous analysis (if available).
       Your response should be conversational and easy to understand while still providing expert ESG guidance.
       """
       
       return prompt
   ```

5. **Database**: 
   - Retrieves session and analysis data
   - Stores chat history in the `chat_history` collection

### GET `/api/advisor/recommendations/{session_id}`

**Execution Flow:**

1. **Endpoint**: `advisor.py/get_recommendations()`
   ```python
   @router.get("/recommendations/{session_id}")
   async def get_recommendations(
       session_id: str = Path(..., description="Session ID"),
       analysis_id: Optional[str] = None,
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get analysis
       if analysis_id:
           analysis = await data_manager.get_analysis_result(analysis_id)
           if not analysis:
               raise HTTPException(status_code=404, detail="Analysis not found")
       else:
           # Get most recent analysis
           analyses = await data_manager.get_session_analyses(session_id)
           if not analyses:
               raise HTTPException(status_code=404, detail="No analyses found for session")
           
           # Sort by created_at and take the most recent
           analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
           analysis = analyses[0]
       
       # Extract recommendations
       recommendations = analysis.get("recommendations", [])
       strategies = analysis.get("strategies", {})
       
       return {
           "analysis_id": analysis.get("_id"),
           "recommendations": recommendations,
           "strategies": strategies
       }
   ```

2. **Database**: Retrieves analysis data from the `analysis_results` collection

## Dashboard Endpoints Flow

### GET `/api/dashboard/overview/{session_id}`

**Execution Flow:**

1. **Endpoint**: `dashboard.py/get_dashboard_overview()`
   ```python
   @router.get("/overview/{session_id}")
   async def get_dashboard_overview(
       session_id: str = Path(..., description="Session ID"),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get industry
       industry = session.get("industry")
       if not industry:
           raise HTTPException(status_code=400, detail="No industry assigned to session")
       
       # Get all KPIs for the session
       kpis = await data_manager.get_session_kpis(session_id)
       
       # Calculate overview metrics
       overall_score, category_scores = await data_manager.calculate_esg_scores(session_id, kpis)
       
       # Get latest analysis if available
       latest_analysis = await data_manager.get_latest_analysis(session_id)
       
       # Generate summary data
       summary = {
           "overall_score": overall_score,
           "category_scores": category_scores,
           "kpi_count": len(kpis),
           "industry": industry,
           "latest_analysis_date": latest_analysis.get("created_at") if latest_analysis else None,
           "has_recommendations": bool(latest_analysis and latest_analysis.get("recommendations", []))
       }
       
       return summary
   ```

2. **Service**: `data_manager.py/calculate_esg_scores()`
   ```python
   async def calculate_esg_scores(self, session_id: str, kpis: List[Dict[str, Any]]) -> Tuple[float, Dict[str, float]]:
       # Group KPIs by category
       category_kpis = {
           "environmental": [],
           "social": [],
           "governance": []
       }
       
       for kpi in kpis:
           # Get KPI specification to determine category
           kpi_name = kpi.get("kpi_name")
           if not kpi_name:
               continue
               
           # Get industry KPI mapping to determine category
           industry_doc = await self.db.sessions.find_one({"session_id": session_id})
           if not industry_doc:
               continue
               
           industry_name = industry_doc.get("industry")
           if not industry_name:
               continue
               
           # Find industry KPI mapping
           industry = await self.db.industries.find_one({"industry": industry_name})
           if not industry:
               continue
               
           # Find category for this KPI
           for industry_kpi in industry.get("kpis", []):
               if industry_kpi.get("specification") == kpi_name:
                   category = industry_kpi.get("esg_category", "").lower()
                   if category in category_kpis:
                       category_kpis[category].append(kpi)
                       break
       
       # Calculate category scores (0-100 scale)
       category_scores = {}
       for category, category_kpis_list in category_kpis.items():
           if not category_kpis_list:
               category_scores[category] = 0
               continue
               
           # Calculate score based on KPI values and reference ranges
           category_score = self._calculate_category_score(category_kpis_list)
           category_scores[category] = category_score
       
       # Calculate overall score as weighted average
       weights = {
           "environmental": 0.34,
           "social": 0.33,
           "governance": 0.33
       }
       
       overall_score = 0
       for category, score in category_scores.items():
           overall_score += score * weights.get(category, 0)
       
       return overall_score, category_scores
   ```

3. **Database**: 
   - Retrieves KPIs from the `calculated_kpis` collection
   - Retrieves industry data from the `industries` collection
   - Retrieves session data from the `sessions` collection

### GET `/api/dashboard/category/{category}/{session_id}`

**Execution Flow:**

1. **Endpoint**: `dashboard.py/get_category_data()`
   ```python
   @router.get("/category/{category}/{session_id}")
   async def get_category_data(
       category: str = Path(..., description="ESG category"),
       session_id: str = Path(..., description="Session ID"),
       data_manager: DataManagerService = Depends(get_data_manager)
   ):
       # Verify session exists
       session = await data_manager.get_session(session_id)
       if not session:
           raise HTTPException(status_code=404, detail="Session not found")
       
       # Get category KPIs
       category_kpis = await data_manager.get_category_kpis(session_id, category.lower())
       
       # Get industry benchmarks
       industry = session.get("industry")
       benchmarks = await data_manager.get_industry_benchmarks(industry, category.lower())
       
       # Get latest category analysis if available
       analysis = await data_manager.get_latest_category_analysis(session_id, category.lower())
       
       return {
           "kpis": category_kpis,
           "benchmarks": benchmarks,
           "score": await data_manager.calculate_category_score(session_id, category.lower()),
           "analysis": analysis
       }
   ```

2. **Service**: `data_manager.py/get_category_kpis()` and `calculate_category_score()`
   ```python
   async def get_category_kpis(self, session_id: str, category: str) -> List[Dict[str, Any]]:
       # Get all session KPIs
       all_kpis = await self.get_session_kpis(session_id)
       
       # Get industry
       session = await self.db.sessions.find_one({"session_id": session_id})
       if not session:
           return []
           
       industry_name = session.get("industry")
       if not industry_name:
           return []
           
       # Get industry KPI mappings
       industry = await self.db.industries.find_one({"industry": industry_name})
       if not industry:
           return []
           
       # Filter KPIs by category
       category_kpis = []
       for kpi in all_kpis:
           kpi_name = kpi.get("kpi_name")
           
           # Find category for this KPI
           for industry_kpi in industry.get("kpis", []):
               if industry_kpi.get("specification") == kpi_name:
                   if industry_kpi.get("esg_category", "").lower() == category:
                       # Add KPI specification details
                       kpi_spec = await self.get_kpi_spec(kpi_name)
                       if kpi_spec:
                           kpi["specification"] = kpi_spec
                       category_kpis.append(kpi)
                       break
       
       return category_kpis
   
   async def calculate_category_score(self, session_id: str, category: str) -> float:
       # Get category KPIs
       category_kpis = await self.get_category_kpis(session_id, category)
       
       if not category_kpis:
           return 0
       
       # Calculate score based on KPI values and reference ranges
       return self._calculate_category_score(category_kpis)
   ```

3. **Database**: 
   - Retrieves KPIs from the `calculated_kpis` collection
   - Retrieves industry data from the `industries` collection
   - Retrieves analysis data from the `analysis_results` collection

## Common Service Flow Patterns

### Data Manager Service

The DataManagerService is a central component that handles data access and processing, following these common patterns:

1. **Session Management**:
   ```
   API Endpoint ─► DataManagerService.get_session() ─► MongoDB.sessions collection ─► Session object
   ```

2. **KPI Management**:
   ```
   API Endpoint ─► DataManagerService.get_kpi_spec() ─► MongoDB.kpi_specifications collection ─► KPI specification
   ```
   
   ```
   API Endpoint ─► DataManagerService.get_session_kpis() ─► MongoDB.calculated_kpis collection ─► Calculated KPI values
   ```

3. **Industry Data Access**:
   ```
   API Endpoint ─► DataManagerService.get_industry() ─► MongoDB.industries collection ─► Industry data
   ```

### File Management Flow

For file uploads and processing, the typical flow is:

```
API Endpoint ─► FileService.upload_file() ─► GridFS storage ─► FileMetadata object ─► Session update
```

For file analysis:

```
API Endpoint ─► FileService.load_file_as_dataframe() ─► GridFS retrieval ─► Pandas DataFrame processing ─► Structured data
```

### Column Mapping Flow

The column mapping process involves several services working together:

1. **Initial Column Detection**:
   ```
   FileService.get_file_columns() ─► CSV parsing ─► List of column names
   ```

2. **Exact Matching**:
   ```
   ColumnMappingService.perform_exact_matching() ─► String normalization and comparison ─► Initial mappings
   ```

3. **LLM-Based Matching** (for unmatched fields):
   ```
   ColumnMappingService.perform_llm_matching() ─► Gemini API prompt ─► JSON response parsing ─► Complete mappings
   ```

4. **Mapping Persistence**:
   ```
   DataManagerService.update_column_mappings() ─► MongoDB.sessions update ─► Updated session object
   ```

### KPI Calculation Flow

The KPI calculation process follows this pattern:

```
API Endpoint ─► KPICalculatorService.calculate_kpi() ─► FileService.load_file_as_dataframe() ─► 
Data extraction using mappings ─► Calculation logic application ─► Result storage in MongoDB.calculated_kpis
```

### ESG Analysis Flow

The AI-powered ESG analysis follows a multi-step process:

1. **Data Collection**:
   ```
   ESGAdvisorService._get_session_kpis() ─► MongoDB.calculated_kpis ─► Categorized KPI data
   ```

2. **Category Analysis** (Environmental, Social, Governance):
   ```
   ESGAdvisorService._analyze_category() ─► Gemini API prompt ─► JSON parsing ─► Category insights
   ```

3. **Strategy Development**:
   ```
   ESGAdvisorService._develop_strategy() ─► Gemini API with category analyses ─► Strategy recommendations
   ```

4. **Recommendations Generation**:
   ```
   ESGAdvisorService._generate_recommendations() ─► Gemini API with strategy context ─► Prioritized actions
   ```

5. **Result Persistence**:
   ```
   ESGAdvisorService._store_analysis_result() ─► MongoDB.analysis_results ─► Persisted analysis
   ```

## Conclusion

The ESG-API codebase follows a well-structured architecture with clear separation of concerns between API endpoints, service layers, and data models. The execution flow patterns show how requests are processed from the initial HTTP request through various services to database operations and external API calls, before returning structured responses to clients.

Key patterns observed in the codebase include:

1. **Dependency Injection**: Services are provided to endpoints using FastAPI's dependency injection system
2. **Asynchronous Processing**: Asynchronous functions (using `async/await`) are used throughout for non-blocking I/O
3. **Service-Oriented Architecture**: Business logic is encapsulated in dedicated service classes
4. **Data Validation**: Pydantic models for request and response validation
5. **Error Handling**: Consistent exception handling and HTTP error response patterns
6. **Parallel Processing**: Certain operations use `asyncio.create_task()` for concurrent execution
7. **AI Integration**: Structured prompting and response parsing for LLM-based features

This architecture provides a maintainable and extensible foundation for the ESG Analysis Platform, allowing for future enhancements and additional features.