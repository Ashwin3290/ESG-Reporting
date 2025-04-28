import logging
import json
import os
import re
import aiohttp
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> dict:
    """
    Extract JSON from text that might contain markdown or other formats.
    Handles both complete JSON objects and fixing malformed JSON if needed.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Parsed JSON as a dictionary, or an error dictionary if parsing fails
    """
    if not text:
        return {"error": "Empty response"}
    
    # First, try to find JSON objects enclosed in ```json or ``` blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)
    
    if matches:
        for json_str in matches:
            try:
                # Test if valid JSON
                return json.loads(json_str.strip())
            except json.JSONDecodeError:
                continue
    
    # Try to parse the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Look for objects enclosed in curly braces
    brace_pattern = r'\{[\s\S]*?\}'
    potential_jsons = re.findall(brace_pattern, text, re.DOTALL)
    
    for potential_json in potential_jsons:
        try:
            return json.loads(potential_json)
        except json.JSONDecodeError:
            # Try to fix common JSON issues and try again
            try:
                # Replace single quotes with double quotes
                fixed_json = potential_json.replace("'", '"')
                # Fix trailing commas in objects and arrays
                fixed_json = re.sub(r',\s*}', '}', fixed_json)
                fixed_json = re.sub(r',\s*\]', ']', fixed_json)
                # Fix missing quotes around property names
                fixed_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', fixed_json)
                
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                continue
    
    # Look for arrays
    array_pattern = r'\[[\s\S]*?\]'
    array_matches = re.findall(array_pattern, text, re.DOTALL)
    
    for array_json in array_matches:
        try:
            return json.loads(array_json)
        except json.JSONDecodeError:
            continue
    
    # If structured extraction fails, try to create a structured object from markdown
    try:
        # Extract structured content from markdown sections
        lines = text.split('\n')
        structured_content = {}
        current_section = "main"
        section_content = []
        
        for line in lines:
            # Check for section headers (markdown headings)
            header_match = re.match(r'^#{1,6}\s+(.+)$', line)
            if header_match:
                # Save previous section
                if section_content:
                    structured_content[current_section] = '\n'.join(section_content)
                    section_content = []
                
                current_section = header_match.group(1).strip()
            elif line.strip():
                section_content.append(line.strip())
        
        # Add the last section
        if section_content:
            structured_content[current_section] = '\n'.join(section_content)
        
        # If we found structured content, return it
        if len(structured_content) > 1 or current_section != "main":
            return structured_content
        
        # If not, try to extract key-value pairs
        key_value_dict = {}
        for line in lines:
            # Look for lines like "Key: Value" or "Key - Value"
            kv_match = re.match(r'^([^:]+)[:|-]\s*(.+)$', line)
            if kv_match:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                key_value_dict[key] = value
        
        if key_value_dict:
            return key_value_dict
        
    except Exception as e:
        logger.error(f"Error in structured extraction: {str(e)}")
    
    # If all parsing fails, return a formatted error with the original text
    return {
        "error": "Could not parse valid JSON from response",
        "raw_text": text
    }

class GeminiClient:
    """Client for the Gemini API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        
    async def generate_text(self, model: str = "gemini-2.0-flash", 
                     prompt: str = None,
                     max_output_tokens: int = 1024, 
                     temperature: float = 0.2) -> str:
        """Generate text using Gemini API"""
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
        
        try:
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
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {str(e)}")
            raise Exception(f"HTTP request failed: {str(e)}")
            
    async def generate_structured_output(self, 
                                 prompt: str,
                                 schema: Dict[str, Any],
                                 model: str = "gemini-2.0-flash", 
                                 temperature: float = 0.2) -> Dict[str, Any]:
        """Generate structured output using Gemini API with JSON mode"""
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
            
        model_url = f"{self.base_url}/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Construct prompt with JSON schema
        schema_str = json.dumps(schema, indent=2)
        structured_prompt = f"""
        {prompt}
        
        You must respond with a valid JSON object matching this schema:
        {schema_str}
        
        Important: Your response must be valid JSON with no additional text before or after.
        """
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": structured_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        url = f"{model_url}?key={self.api_key}"
        
        try:
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
                        
                        # Parse JSON using our enhanced extraction method
                        return extract_json_from_text(response_text)
                    except (KeyError, IndexError) as e:
                        logger.error(f"Error extracting JSON from response: {e}")
                        logger.error(f"Response text: {response_text}")
                        raise Exception(f"Failed to extract JSON response: {str(e)}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {str(e)}")
            raise Exception(f"HTTP request failed: {str(e)}")
