import logging
import json
import os
import aiohttp
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

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
                    
                    # Extract JSON from response
                    try:
                        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Clean up response to ensure it's valid JSON
                        # Remove markdown code block markers if present
                        response_text = response_text.strip()
                        if response_text.startswith("```json"):
                            response_text = response_text[7:]
                        elif response_text.startswith("```"):
                            response_text = response_text[3:]
                            
                        if response_text.endswith("```"):
                            response_text = response_text[:-3]
                            
                        response_text = response_text.strip()
                        
                        # Parse JSON
                        json_response = json.loads(response_text)
                        return json_response
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        logger.error(f"Error parsing JSON response: {e}")
                        logger.error(f"Response text: {response_text}")
                        raise Exception(f"Failed to parse JSON response: {str(e)}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {str(e)}")
            raise Exception(f"HTTP request failed: {str(e)}")
