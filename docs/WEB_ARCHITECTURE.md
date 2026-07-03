# AudiPy Web Architecture Guide

## 🏗️ **New Structure Overview**

The project has been refactored from CLI-based phase scripts to a proper web application architecture suitable for a Python backend + React frontend.

### **Directory Structure**
```
AudiPy/
├── api/                    # FastAPI backend
│   └── main.py            # Main FastAPI application
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py    # Authentication & token management
│   ├── library_service.py # Library sync operations (TODO)
│   ├── recommendation_service.py # Recommendation generation (TODO)
│   └── user_service.py    # User management (TODO)
├── models/                # Data models (TODO)
├── utils/                 # Utilities
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py  # Database connection management
│   └── crypto_utils_simple.py
├── legacy/                # Original phase scripts (kept for reference)
├── phase1_authenticate.py # CLI scripts (still functional)
├── phase2_user_profile.py
├── phase3_fetch_library.py
├── phase4_generate_recommendations.py
└── requirements_web.txt   # Additional web dependencies
```

## 🔄 **Migration from Phase Scripts to Services**

### **What Changed:**

1. **Separation of Concerns:**
   - ❌ **Before:** Mixed business logic with CLI presentation (Rich console)
   - ✅ **After:** Clean service layer with no presentation dependencies

2. **Async Support:**
   - ❌ **Before:** Synchronous operations only
   - ✅ **After:** Async/await for better web performance

3. **Database Management:**
   - ❌ **Before:** Direct MySQL connections in each script
   - ✅ **After:** Context managers and connection pooling

4. **Error Handling:**
   - ❌ **Before:** Console output and exit codes
   - ✅ **After:** Structured responses with proper HTTP status codes

5. **User Management:**
   - ❌ **Before:** Hard-coded test user
   - ✅ **After:** Proper user context and JWT tokens (TODO)

## 🚀 **FastAPI Backend Features**

### **Current Endpoints:**
- `GET /` - Health check
- `GET /health` - Database connection test
- `POST /auth/audible` - Audible authentication
- `GET /auth/test` - Test API access

### **Planned Endpoints:**
- `POST /users/preferences` - Update user preferences
- `POST /library/sync` - Trigger library sync
- `GET /library/status` - Get sync status
- `GET /recommendations` - Get user recommendations
- `POST /recommendations/generate` - Generate new recommendations

## 🔧 **React Frontend Considerations**

### **API Integration:**
```javascript
// Example API calls from React
const authenticateAudible = async (credentials) => {
  const response = await fetch('/api/auth/audible', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(credentials)
  });
  return response.json();
};
```

### **State Management:**
- Use React Context or Redux for user authentication state
- Handle loading states for long-running operations (library sync)
- Implement proper error boundaries

### **Real-time Updates:**
- WebSocket support for sync progress
- Server-sent events for recommendation updates
- Background task status monitoring

## 🔐 **Authentication Flow**

### **Current (Simplified):**
1. User provides Audible credentials via React form
2. Frontend sends to `/auth/audible` endpoint
3. Backend authenticates with Audible API
4. Encrypted tokens stored in database
5. Success/failure response to frontend

### **Production (TODO):**
1. OAuth login (Google, GitHub, etc.)
2. JWT token generation
3. Secure session management
4. Audible credentials as secondary authentication

## 📊 **Background Tasks**

### **Long-running Operations:**
- Library sync (can take minutes for large libraries)
- Recommendation generation
- Token refresh operations

### **Implementation with Celery:**
```python
# Example background task
@celery.app.task
async def sync_user_library(user_id: int):
    library_service = LibraryService()
    return await library_service.sync_library(user_id)
```

### **Frontend Integration:**
```javascript
// Poll for task status
const checkSyncStatus = async (taskId) => {
  const response = await fetch(`/api/tasks/${taskId}/status`);
  return response.json();
};
```

## 🗄️ **Database Considerations**

### **Connection Management:**
- Context managers for automatic cleanup
- Connection pooling for better performance
- Proper transaction handling

### **Migration Strategy:**
- Keep existing database schema
- Add new tables for web-specific features (sessions, tasks)
- Maintain backward compatibility with CLI scripts

## 🧪 **Testing Strategy**

### **Backend Testing:**
```python
# Example test
async def test_authenticate_user():
    auth_service = AuthService()
    result = await auth_service.authenticate_user(
        user_id=1,
        username="test@example.com",
        password="password",
        marketplace="us"
    )
    assert result['success'] == True
```

### **API Testing:**
```python
# FastAPI test client
def test_auth_endpoint():
    response = client.post("/auth/audible", json={
        "username": "test@example.com",
        "password": "password",
        "marketplace": "us"
    })
    assert response.status_code == 200
```

## 🚀 **Deployment Considerations**

### **Backend Deployment:**
- Docker containers for easy deployment
- Environment-based configuration
- Health checks and monitoring
- Horizontal scaling with load balancers

### **Frontend Deployment:**
- Static file serving (Nginx, CDN)
- Environment-specific API endpoints
- Build optimization and caching

### **Infrastructure:**
- Redis for Celery task queue
- MySQL database (existing)
- Reverse proxy (Nginx)
- SSL/TLS certificates

## 📈 **Performance Optimizations**

### **Database:**
- Query optimization and indexing
- Connection pooling
- Read replicas for heavy queries

### **API:**
- Response caching
- Pagination for large datasets
- Async operations for I/O bound tasks

### **Frontend:**
- Code splitting and lazy loading
- API response caching
- Optimistic updates

## 🔄 **Migration Path**

### **Phase 1: Service Layer (Current)**
- ✅ Extract business logic to services
- ✅ Create FastAPI application
- ✅ Basic authentication endpoint

### **Phase 2: Core Features**
- 🔄 Library sync service
- 🔄 Recommendation service
- 🔄 User management service

### **Phase 3: Frontend Integration**
- 🔄 React application setup
- 🔄 API integration
- 🔄 User interface components

### **Phase 4: Production Features**
- 🔄 OAuth authentication
- 🔄 Background task processing
- 🔄 Real-time updates

## 🛠️ **Development Workflow**

### **Backend Development:**
```bash
# Install web dependencies
pip install -r requirements_web.txt

# Run FastAPI development server
python api/main.py
# or
uvicorn api.main:app --reload

# API documentation available at:
# http://localhost:8000/docs
```

### **Frontend Development:**
```bash
# In separate terminal/directory
npx create-react-app audipy-frontend
cd audipy-frontend
npm start
```

### **Full Stack Development:**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- CORS configured for local development

This architecture provides a solid foundation for scaling AudiPy into a full web application while maintaining the existing CLI functionality. 