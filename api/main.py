"""
AudiPy FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from services.auth_service import AuthService
from utils.db.connection import test_connection

# Initialize FastAPI app
app = FastAPI(
    title="AudiPy API",
    description="Audible library analyzer and recommendation engine",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
auth_service = AuthService()

# Pydantic models for request/response
class AuthRequest(BaseModel):
    username: str
    password: str
    marketplace: str = "us"
    otp_code: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    requires_otp: bool
    tokens_stored: bool

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Dependency to get current user (placeholder for now)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # TODO: Implement proper JWT token validation
    # For now, return a test user ID
    return 1

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AudiPy API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check with database connection test"""
    db_status = test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }

@app.post("/auth/audible", response_model=AuthResponse)
async def authenticate_audible(
    auth_request: AuthRequest,
    user_id: int = Depends(get_current_user)
):
    """Authenticate with Audible and store tokens"""
    try:
        result = await auth_service.authenticate_user(
            user_id=user_id,
            username=auth_request.username,
            password=auth_request.password,
            marketplace=auth_request.marketplace,
            otp_code=auth_request.otp_code
        )
        
        return AuthResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/test", response_model=ApiResponse)
async def test_audible_access(user_id: int = Depends(get_current_user)):
    """Test Audible API access for current user"""
    try:
        result = await auth_service.test_api_access(user_id)
        return ApiResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Add more endpoints for:
# - User preferences management
# - Library sync operations
# - Recommendation generation
# - Recommendation viewing

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 