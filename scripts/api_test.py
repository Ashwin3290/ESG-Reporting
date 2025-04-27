#!/usr/bin/env python
"""
Basic test script for the ESG API

This script tests the basic functionality of the ESG API by making a series of API calls.
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings

# Base URL for API
BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

async def test_api():
    """Test the API by making a series of API calls"""
    print(f"Testing ESG API at {BASE_URL}")
    
    # Define test steps
    test_steps = [
        test_health_check,
        test_get_industries,
        test_search_industries,
        test_session_creation,
        test_file_operations,
    ]
    
    # Run test steps
    results = {}
    for step in test_steps:
        step_name = step.__name__
        print(f"\n--- Running test: {step_name} ---")
        
        try:
            result = await step()
            success = True
            results[step_name] = {"success": True, "result": result}
            print(f"✅ {step_name} - Success")
        except Exception as e:
            success = False
            results[step_name] = {"success": False, "error": str(e)}
            print(f"❌ {step_name} - Failed: {str(e)}")
    
    # Print summary
    print("\n=== Test Summary ===")
    for step_name, result in results.items():
        status = "✅ Passed" if result["success"] else "❌ Failed"
        print(f"{status} - {step_name}")
    
    # Overall result
    total = len(results)
    passed = sum(1 for result in results.values() if result["success"])
    print(f"\nOverall: {passed}/{total} tests passed")
    
    return results

async def test_health_check():
    """Test the health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        response.raise_for_status()
        return response.json()

async def test_get_industries():
    """Test getting all industries"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/industries")
        response.raise_for_status()
        industries = response.json()
        
        if not industries:
            raise ValueError("No industries returned")
        
        return industries

async def test_search_industries():
    """Test searching industries"""
    # Get a list of industries first
    all_industries = await test_get_industries()
    
    # Use the first industry to test search
    if all_industries:
        first_industry = all_industries[0]
        search_term = first_industry["industry"][:3]  # Use first 3 chars as search term
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/industries/search?q={search_term}")
            response.raise_for_status()
            search_results = response.json()
            
            if not search_results:
                raise ValueError(f"No search results found for term: {search_term}")
            
            return search_results
    else:
        raise ValueError("No industries available for search test")

async def test_session_creation():
    """Test creating a new session"""
    # Get a list of industries first
    all_industries = await test_get_industries()
    
    # Use the first industry for the session
    if all_industries:
        first_industry = all_industries[0]["industry"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/sessions",
                json={"industry": first_industry}
            )
            response.raise_for_status()
            session_data = response.json()
            
            if not session_data.get("session_id"):
                raise ValueError("No session ID returned")
            
            return session_data
    else:
        raise ValueError("No industries available for session creation test")

async def test_file_operations():
    """Test file upload and operations"""
    # Create test CSV file
    test_file_path = Path("test_data.csv")
    with open(test_file_path, "w") as f:
        f.write("col1,col2,col3\n")
        f.write("1,2,3\n")
        f.write("4,5,6\n")
    
    try:
        # First, create a session
        session_data = await test_session_creation()
        session_id = session_data["session_id"]
        
        # Upload file
        async with httpx.AsyncClient() as client:
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_data.csv", f, "text/csv")}
                response = await client.post(
                    f"{BASE_URL}/api/files/upload?session_id={session_id}",
                    files=files
                )
                response.raise_for_status()
                file_data = response.json()
                
                if not file_data.get("file_id"):
                    raise ValueError("No file ID returned")
                
                file_id = file_data["file_id"]
                
                # Get file columns
                columns_response = await client.get(f"{BASE_URL}/api/files/{file_id}/columns")
                columns_response.raise_for_status()
                columns_data = columns_response.json()
                
                if "columns" not in columns_data:
                    raise ValueError("No columns returned")
                
                return {
                    "file_upload": file_data,
                    "columns": columns_data
                }
    finally:
        # Clean up test file
        if test_file_path.exists():
            os.unlink(test_file_path)

if __name__ == "__main__":
    asyncio.run(test_api())
