from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from .config import settings

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    session_id: Optional[str] = None

def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """Verify API key for authentication"""
    # In a real system, you should check this against database of valid keys
    # This is a placeholder implementation
    if api_key != "test-api-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API key"},
        )
    return api_key

def create_session_token(session_id: str) -> str:
    """Create a JWT token for a session"""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {"exp": expire, "sub": session_id}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_session_token(token: str) -> Optional[str]:
    """Verify a session token and return the session ID"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        session_id = payload.get("sub")
        if session_id is None:
            return None
        token_data = TokenData(session_id=session_id)
        return token_data.session_id
    except JWTError:
        return None
