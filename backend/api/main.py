"""
AudiPy FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import jwt
import uuid
from datetime import datetime, timedelta, timezone
import os
import asyncio
import subprocess
import threading

from services.auth_service import AuthService
from utils.db.connection import test_connection, get_db_connection

# Initialize FastAPI app
app = FastAPI(
    title="AudiPy API",
    description="Audible library analyzer and recommendation engine",
    version="1.0.0"
)

# Create API router with /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server (backup port)
        "http://23.239.29.130:5173",  # External access
        "http://23.239.29.130:5174",  # External access (backup port)
        "http://web1",            # Production domain
        "https://web1",           # Production HTTPS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer(auto_error=False)

# Services
auth_service = AuthService()

# In-memory OTP sessions (in production, use Redis or database)
otp_sessions = {}

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str
    marketplace: str = "us"

class OTPRequest(BaseModel):
    session_id: str
    otp_code: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    requires_otp: bool = False
    session_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class AuthResponse(BaseModel):
    authenticated: bool
    user: Optional[Dict[str, Any]] = None

class LibraryBook(BaseModel):
    asin: str
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = []
    narrators: List[str] = []
    series: Optional[str] = None
    series_sequence: Optional[str] = None
    runtime_length_min: Optional[int] = None
    publication_datetime: Optional[str] = None
    purchase_date: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    cover_url: Optional[str] = None

class LibraryResponse(BaseModel):
    books: List[LibraryBook]
    total_count: int
    page: int
    page_size: int
    has_next: bool

class SyncStatusResponse(BaseModel):
    is_syncing: bool
    last_sync: Optional[str] = None
    total_books: int
    status_message: str

class BookDetailResponse(BaseModel):
    book: LibraryBook
    description: Optional[str] = None
    categories: List[str] = []
    publisher: Optional[str] = None

# Per-user sync status tracking
user_sync_status = {}

def get_user_sync_status(user_id: int) -> dict:
    """Get sync status for a specific user"""
    if user_id not in user_sync_status:
        user_sync_status[user_id] = {
            "is_syncing": False,
            "last_sync": None,
            "total_books": 0,
            "status_message": "Ready to sync"
        }
    return user_sync_status[user_id]

def set_user_sync_status(user_id: int, **kwargs) -> None:
    """Update sync status for a specific user"""
    status = get_user_sync_status(user_id)
    status.update(kwargs)

# Helper functions
def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """Create JWT token for user"""
    payload = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "marketplace": user_data["marketplace"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token in cookies"""
    token = request.cookies.get("auth_token")
    if not token:
        return None
    
    user_data = verify_jwt_token(token)
    return user_data

async def ensure_user_exists(username: str, marketplace: str) -> int:
    """Ensure user exists in database, create if not exists"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Check if user exists (using display_name as username for now)
            cursor.execute("""
                SELECT id FROM users WHERE oauth_provider = 'audible' AND oauth_provider_id = %s
            """, (username,))
            user = cursor.fetchone()
            
            if user:
                cursor.close()
                return user["id"]
            
            # Create new user with Audible as OAuth provider
            cursor.execute("""
                INSERT INTO users (oauth_provider, oauth_provider_id, display_name, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, ('audible', username, username))
            
            user_id = cursor.lastrowid
            cursor.close()
            
            return user_id
            
    except Exception as e:
        print(f"Error ensuring user exists: {e}")
        # Fallback to temp user ID
        return 1

# Routes
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

@api_router.post("/auth/login")
async def login(login_request: LoginRequest, response: Response):
    """Login with Audible credentials"""
    try:
        # Ensure user exists in database FIRST
        user_id = await ensure_user_exists(login_request.username, login_request.marketplace)
        
        result = await auth_service.authenticate_user(
            user_id=user_id,
            username=login_request.username,
            password=login_request.password,
            marketplace=login_request.marketplace
        )
        
        if result["requires_otp"]:
            # Create OTP session
            session_id = str(uuid.uuid4())
            otp_sessions[session_id] = {
                "username": login_request.username,
                "password": login_request.password,
                "marketplace": login_request.marketplace,
                "created_at": datetime.now(timezone.utc),
            }
            
            return LoginResponse(
                success=False,
                message="Two-factor authentication required",
                requires_otp=True,
                session_id=session_id
            )
        
        elif result["success"]:
            # Create user data and JWT token
            user_data = {
                "user_id": user_id,
                "username": login_request.username,
                "marketplace": login_request.marketplace,
            }
            
            token = create_jwt_token(user_data)
            
            # Set HTTP-only cookie
            response.set_cookie(
                key="auth_token",
                value=token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=JWT_EXPIRATION_HOURS * 3600,
            )
            
            return LoginResponse(
                success=True,
                message="Login successful",
                user=user_data
            )
        
        else:
            raise HTTPException(status_code=401, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@api_router.post("/auth/verify-otp")
async def verify_otp(otp_request: OTPRequest, response: Response):
    """Verify OTP code and complete authentication"""
    try:
        # Get OTP session
        session = otp_sessions.get(otp_request.session_id)
        if not session:
            raise HTTPException(status_code=400, detail="Invalid or expired session")
        
        # Check session expiration (15 minutes)
        if datetime.now(timezone.utc) - session["created_at"] > timedelta(minutes=15):
            del otp_sessions[otp_request.session_id]
            raise HTTPException(status_code=400, detail="Session expired")
        
        # Ensure user exists in database FIRST
        user_id = await ensure_user_exists(session["username"], session["marketplace"])
        
        # Attempt authentication with OTP using the correct user_id
        result = await auth_service.authenticate_user(
            user_id=user_id,  # Use the actual user ID
            username=session["username"],
            password=session["password"],
            marketplace=session["marketplace"],
            otp_code=otp_request.otp_code
        )
        
        if result["success"]:
            # Clean up session
            del otp_sessions[otp_request.session_id]
            
            # Create user data and JWT token
            user_data = {
                "user_id": user_id,
                "username": session["username"],
                "marketplace": session["marketplace"],
            }
            
            token = create_jwt_token(user_data)
            
            # Set HTTP-only cookie
            response.set_cookie(
                key="auth_token",
                value=token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=JWT_EXPIRATION_HOURS * 3600,
            )
            
            return LoginResponse(
                success=True,
                message="Authentication successful",
                user=user_data
            )
        
        else:
            raise HTTPException(status_code=401, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTP verification failed: {str(e)}")

@api_router.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    user = await get_current_user(request)
    
    if user:
        return AuthResponse(
            authenticated=True,
            user={
                "user_id": user["user_id"],
                "username": user["username"],
                "marketplace": user["marketplace"],
            }
        )
    else:
        return AuthResponse(authenticated=False)

@api_router.post("/auth/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie(key="auth_token")
    return {"success": True, "message": "Logged out successfully"}

@api_router.get("/auth/test")
async def test_audible_access(request: Request):
    """Test Audible API access for current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = await auth_service.test_api_access(user["user_id"])
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Phase 2: User Profile & Preferences endpoints
@api_router.get("/user/profile")
async def get_user_profile(request: Request):
    """Get current user profile information"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Get user profile data
            cursor.execute("""
                SELECT id as user_id, display_name as username, oauth_provider_id as email, created_at, updated_at
                FROM users WHERE id = %s
            """, (user["user_id"],))
            profile = cursor.fetchone()
            
            # Get user preferences
            cursor.execute("""
                SELECT * FROM user_preferences WHERE user_id = %s
            """, (user["user_id"],))
            preferences = cursor.fetchone()
            
            # Get Audible account status
            cursor.execute("""
                SELECT marketplace, sync_status, tokens_expires_at, last_sync
                FROM user_audible_accounts WHERE user_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (user["user_id"],))
            audible_account = cursor.fetchone()
            
            cursor.close()
            
            return {
                "profile": profile,
                "preferences": preferences or {
                    "language": "english",
                    "marketplace": user.get("marketplace", "us"),
                    "max_price": 12.66,
                    "notifications_enabled": True,
                    "price_alert_enabled": True,
                    "new_release_alerts": True
                },
                "audible_account": audible_account
            }
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Profile endpoint error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@api_router.put("/user/preferences")
async def update_user_preferences(preferences: dict, request: Request):
    """Update user preferences"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor()
            
            # Update or insert preferences
            cursor.execute("""
                INSERT INTO user_preferences 
                (user_id, preferred_language, marketplace, max_price,
                 notifications_enabled, price_alert_enabled, new_release_alerts, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                preferred_language = VALUES(preferred_language),
                marketplace = VALUES(marketplace),
                max_price = VALUES(max_price),
                notifications_enabled = VALUES(notifications_enabled),
                price_alert_enabled = VALUES(price_alert_enabled),
                new_release_alerts = VALUES(new_release_alerts),
                updated_at = CURRENT_TIMESTAMP
            """, (
                user["user_id"],
                preferences.get("language", "english"),
                preferences.get("marketplace", "us"),
                preferences.get("max_price", 12.66),
                preferences.get("notifications_enabled", True),
                preferences.get("price_alert_enabled", True),
                preferences.get("new_release_alerts", True)
            ))
            
            cursor.close()
            
            return {"success": True, "message": "Preferences updated successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")

@api_router.get("/user/status")
async def get_user_status(request: Request):
    """Get user account status and statistics"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Get library statistics (handle missing table gracefully)
            try:
                cursor.execute("""
                    SELECT COUNT(*) as total_books,
                           COUNT(CASE WHEN date_added >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as recent_books
                    FROM user_libraries WHERE user_id = %s
                """, (user["user_id"],))
                library_stats = cursor.fetchone()
            except Exception:
                # Table doesn't exist yet (Phase 3 feature)
                library_stats = {"total_books": 0, "recent_books": 0}
            
            # Get sync status (handle missing data gracefully)
            try:
                cursor.execute("""
                    SELECT sync_status, last_sync, tokens_expires_at
                    FROM user_audible_accounts WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (user["user_id"],))
                sync_status = cursor.fetchone()
            except Exception:
                sync_status = None
            
            # Get recommendation statistics (handle missing table gracefully)
            try:
                cursor.execute("""
                    SELECT COUNT(*) as total_recommendations,
                           COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as recent_recommendations
                    FROM recommendations WHERE user_id = %s
                """, (user["user_id"],))
                rec_stats = cursor.fetchone()
            except Exception:
                # Table doesn't exist yet (Phase 4 feature)
                rec_stats = {"total_recommendations": 0, "recent_recommendations": 0}
            
            cursor.close()
            
            return {
                "library": library_stats or {"total_books": 0, "recent_books": 0},
                "sync": sync_status,
                "recommendations": rec_stats or {"total_recommendations": 0, "recent_recommendations": 0}
            }
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Status endpoint error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

# Phase 3: Library Management endpoints
@api_router.get("/library", response_model=LibraryResponse)
async def get_library(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    author: Optional[str] = None,
    narrator: Optional[str] = None,
    series: Optional[str] = None,
    sort_by: str = "title",
    sort_order: str = "asc"
):
    """Get user's library with pagination, search, and filtering"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Build the WHERE clause for filtering
            where_conditions = ["ul.user_id = %s"]
            params = [user["user_id"]]
            
            if search:
                where_conditions.append("(b.title LIKE %s OR b.subtitle LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
            
            if author:
                where_conditions.append("EXISTS (SELECT 1 FROM book_authors ba JOIN authors a ON ba.author_id = a.id WHERE ba.book_id = b.id AND a.name LIKE %s)")
                params.append(f"%{author}%")
            
            if narrator:
                where_conditions.append("EXISTS (SELECT 1 FROM book_narrators bn JOIN narrators n ON bn.narrator_id = n.id WHERE bn.book_id = b.id AND n.name LIKE %s)")
                params.append(f"%{narrator}%")
            
            if series:
                where_conditions.append("EXISTS (SELECT 1 FROM book_series bs JOIN series s ON bs.series_id = s.id WHERE bs.book_id = b.id AND s.title LIKE %s)")
                params.append(f"%{series}%")
            
            where_clause = " AND ".join(where_conditions)
            
            # Build ORDER BY clause
            valid_sort_fields = {
                "title": "b.title",
                "publication_date": "b.publication_datetime",
                "runtime": "b.runtime_length_min",
                "purchase_date": "ul.date_added"
            }
            sort_field = valid_sort_fields.get(sort_by, "b.title")
            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            # Get total count
            count_query = f"""
                SELECT COUNT(DISTINCT b.asin) as total
                FROM user_libraries ul
                JOIN books b ON ul.book_id = b.id
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()["total"]
            
            # Get paginated results
            offset = (page - 1) * page_size
            
            library_query = f"""
                SELECT DISTINCT
                    b.asin, b.title, b.subtitle, b.runtime_length_min,
                    b.publication_datetime, b.language, b.content_type,
                    ul.date_added as purchase_date,
                    GROUP_CONCAT(DISTINCT a.name ORDER BY ba.display_order SEPARATOR ', ') as authors,
                    GROUP_CONCAT(DISTINCT n.name ORDER BY bn.display_order SEPARATOR ', ') as narrators,
                    GROUP_CONCAT(DISTINCT CONCAT(s.title, CASE WHEN bs.sequence IS NOT NULL THEN CONCAT(' #', bs.sequence) ELSE '' END) SEPARATOR ', ') as series
                FROM user_libraries ul
                JOIN books b ON ul.book_id = b.id
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_narrators bn ON b.id = bn.book_id
                LEFT JOIN narrators n ON bn.narrator_id = n.id
                LEFT JOIN book_series bs ON b.id = bs.book_id
                LEFT JOIN series s ON bs.series_id = s.id
                WHERE {where_clause}
                GROUP BY b.asin, b.title, b.subtitle, b.runtime_length_min, 
                         b.publication_datetime, b.language, b.content_type, ul.date_added
                ORDER BY {sort_field} {sort_direction}
                LIMIT %s OFFSET %s
            """
            
            params.extend([page_size, offset])
            cursor.execute(library_query, params)
            books_data = cursor.fetchall()
            
            # Convert to LibraryBook objects
            books = []
            for book in books_data:
                books.append(LibraryBook(
                    asin=book["asin"],
                    title=book["title"],
                    subtitle=book["subtitle"],
                    authors=book["authors"].split(", ") if book["authors"] else [],
                    narrators=book["narrators"].split(", ") if book["narrators"] else [],
                    series=book["series"] if book["series"] else None,
                    runtime_length_min=book["runtime_length_min"],
                    publication_datetime=book["publication_datetime"].isoformat() if book["publication_datetime"] else None,
                    purchase_date=book["purchase_date"].isoformat() if book["purchase_date"] else None,
                    language=book["language"],
                    content_type=book["content_type"]
                ))
            
            cursor.close()
            
            has_next = (page * page_size) < total_count
            
            return LibraryResponse(
                books=books,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next
            )
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Library endpoint error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to get library: {str(e)}")

@api_router.post("/library/sync")
async def sync_library(request: Request):
    """Trigger library sync from Audible"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = user["user_id"]
    sync_status = get_user_sync_status(user_id)
    
    if sync_status["is_syncing"]:
        return {"success": False, "message": "Sync already in progress"}
    
    try:
        # Start sync in background thread
        def run_sync():
            set_user_sync_status(user_id, is_syncing=True, status_message="Starting library sync...")
            
            try:
                # Run the phase3_fetch_library.py script using virtual environment
                result = subprocess.run([
                    "/var/www/html/AudiPy/backend/venv/bin/python3", "phase3_fetch_library.py", 
                    "--user-id", str(user["user_id"])
                ], 
                cwd="/var/www/html/AudiPy/backend",
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    set_user_sync_status(user_id, 
                        status_message="Library sync completed successfully",
                        last_sync=datetime.utcnow().isoformat()
                    )
                    
                    # Update database sync status
                    with get_db_connection() as db:
                        cursor = db.cursor()
                        cursor.execute("""
                            UPDATE user_audible_accounts 
                            SET sync_status = 'completed', last_sync = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                        """, (user_id,))
                        cursor.close()
                        
                else:
                    set_user_sync_status(user_id, status_message=f"Sync failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                set_user_sync_status(user_id, status_message="Sync timed out after 5 minutes")
            except Exception as e:
                set_user_sync_status(user_id, status_message=f"Sync error: {str(e)}")
            finally:
                set_user_sync_status(user_id, is_syncing=False)
        
        # Start sync thread
        sync_thread = threading.Thread(target=run_sync)
        sync_thread.daemon = True
        sync_thread.start()
        
        return {"success": True, "message": "Library sync started"}
        
    except Exception as e:
        set_user_sync_status(user_id, is_syncing=False)
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")

@api_router.get("/library/status", response_model=SyncStatusResponse)
async def get_sync_status(request: Request):
    """Get library sync status"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = user["user_id"]
    sync_status = get_user_sync_status(user_id)
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Get total books count
            try:
                cursor.execute("""
                    SELECT COUNT(*) as total_books FROM user_libraries WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                total_books = result["total_books"] if result else 0
            except Exception:
                total_books = 0
            
            # Get last sync time from database if not in memory
            if not sync_status["last_sync"]:
                try:
                    cursor.execute("""
                        SELECT last_sync FROM user_audible_accounts 
                        WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
                    """, (user_id,))
                    result = cursor.fetchone()
                    if result and result["last_sync"]:
                        set_user_sync_status(user_id, last_sync=result["last_sync"].isoformat())
                        sync_status = get_user_sync_status(user_id)  # Refresh after update
                except Exception:
                    pass
            
            cursor.close()
            
            return SyncStatusResponse(
                is_syncing=sync_status["is_syncing"],
                last_sync=sync_status["last_sync"],
                total_books=total_books,
                status_message=sync_status["status_message"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@api_router.post("/library/reset-sync-status")
async def reset_sync_status(request: Request):
    """Reset sync status to success (for testing/debugging)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = user["user_id"]
    set_user_sync_status(user_id, 
        is_syncing=False,
        status_message="Library sync completed successfully",
        last_sync=datetime.utcnow().isoformat()
    )
    
    return {"success": True, "message": "Sync status reset to success"}

@api_router.get("/books/{book_asin}", response_model=BookDetailResponse)
async def get_book_details(book_asin: str, request: Request):
    """Get detailed information about a specific book"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)
            
            # Get book details with authors, narrators, series, and categories
            cursor.execute("""
                SELECT 
                    b.asin, b.title, b.subtitle, b.publisher_name,
                    b.publication_datetime, b.language, b.content_type,
                    b.runtime_length_min, b.merchandising_summary,
                    b.extended_product_description,
                    ul.date_added as purchase_date,
                    GROUP_CONCAT(DISTINCT a.name ORDER BY ba.display_order SEPARATOR ', ') as authors,
                    GROUP_CONCAT(DISTINCT n.name ORDER BY bn.display_order SEPARATOR ', ') as narrators,
                    GROUP_CONCAT(DISTINCT CONCAT(s.title, CASE WHEN bs.sequence IS NOT NULL THEN CONCAT(' #', bs.sequence) ELSE '' END) SEPARATOR ', ') as series,
                    GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') as categories
                FROM books b
                LEFT JOIN user_libraries ul ON b.id = ul.book_id AND ul.user_id = %s
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_narrators bn ON b.id = bn.book_id
                LEFT JOIN narrators n ON bn.narrator_id = n.id
                LEFT JOIN book_series bs ON b.id = bs.book_id
                LEFT JOIN series s ON bs.series_id = s.id
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.id
                WHERE b.asin = %s
                GROUP BY b.asin, b.title, b.subtitle, b.publisher_name,
                         b.publication_datetime, b.language, b.content_type,
                         b.runtime_length_min, b.merchandising_summary,
                         b.extended_product_description, ul.date_added
            """, (user["user_id"], book_asin))
            
            book_data = cursor.fetchone()
            cursor.close()
            
            if not book_data:
                raise HTTPException(status_code=404, detail="Book not found")
            
            book = LibraryBook(
                asin=book_data["asin"],
                title=book_data["title"],
                subtitle=book_data["subtitle"],
                authors=book_data["authors"].split(", ") if book_data["authors"] else [],
                narrators=book_data["narrators"].split(", ") if book_data["narrators"] else [],
                series=book_data["series"] if book_data["series"] else None,
                runtime_length_min=book_data["runtime_length_min"],
                publication_datetime=book_data["publication_datetime"].isoformat() if book_data["publication_datetime"] else None,
                purchase_date=book_data["purchase_date"].isoformat() if book_data["purchase_date"] else None,
                language=book_data["language"],
                content_type=book_data["content_type"]
            )
            
            return BookDetailResponse(
                book=book,
                description=book_data["extended_product_description"] or book_data["merchandising_summary"],
                categories=book_data["categories"].split(", ") if book_data["categories"] else [],
                publisher=book_data["publisher_name"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get book details: {str(e)}")

# Include API router
app.include_router(api_router)

# Legacy endpoints (keeping for backward compatibility)
@app.post("/auth/audible")
async def authenticate_audible_legacy(
    auth_request: dict,
    user_id: int = 1  # Default user for legacy endpoint
):
    """Legacy authentication endpoint"""
    try:
        result = await auth_service.authenticate_user(
            user_id=user_id,
            username=auth_request.get("username"),
            password=auth_request.get("password"),
            marketplace=auth_request.get("marketplace", "us"),
            otp_code=auth_request.get("otp_code")
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 