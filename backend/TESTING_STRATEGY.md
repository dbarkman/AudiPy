# AudiPy Testing Strategy

## Overview
This document outlines the comprehensive testing strategy for AudiPy, covering all layers of the application from backend services to frontend components.

## Current Test Status ✅

### Backend Tests (Working)
- **Service Tests**: 14/14 passing ✅
  - Authentication service with Audible API integration
  - Token storage and encryption
  - User management and OTP handling
  
- **Crypto Tests**: 6/6 passing ✅
  - User-specific encryption/decryption
  - Master key management
  - Data security validation
  
- **Database Tests**: 6/6 passing ✅
  - Connection management
  - Error handling
  - Configuration validation
  
- **Integration Tests**: 5/5 passing ✅
  - End-to-end authentication flows
  - Service interaction testing
  - Error propagation chains

### API Tests (Needs Fix)
- **Status**: 18 tests with compatibility issues ⚠️
- **Issue**: FastAPI TestClient version incompatibility
- **Solution**: Migrate to httpx or downgrade dependencies

## Testing Layers

### 1. Backend Unit Tests
**Location**: `backend/tests/`
**Framework**: pytest + pytest-asyncio + pytest-mock
**Coverage**: Services, utilities, database connections

**Test Categories**:
- `test_auth_service.py` - Authentication and Audible API integration
- `test_crypto_utils.py` - Encryption and security
- `test_db_connection.py` - Database connectivity
- `test_integration.py` - Cross-service integration

**Running Tests**:
```bash
# All backend tests (excluding API)
python run_tests.py services crypto db

# Individual categories
python run_tests.py services
python run_tests.py crypto
python run_tests.py db
```

### 2. API Integration Tests
**Status**: Needs migration to compatible testing framework
**Current Issue**: TestClient compatibility with FastAPI 0.104.1 + Starlette 0.27.0

**Planned Tests**:
- Authentication endpoints (login, OTP, logout)
- User profile management
- Library management (sync, search, filtering)
- Error handling and validation

**Migration Options**:
1. Use httpx.AsyncClient with ASGI transport
2. Downgrade to compatible FastAPI/Starlette versions
3. Use requests library for integration testing

### 3. Frontend Testing (To Implement)

#### Unit Tests
**Framework**: Jest + React Testing Library
**Location**: `frontend/src/__tests__/`

**Test Categories**:
- Component rendering and props
- User interactions and state changes
- API integration mocking
- Authentication context

**Example Structure**:
```
frontend/src/__tests__/
├── components/
│   ├── Dashboard.test.jsx
│   ├── Library.test.jsx
│   ├── UserProfile.test.jsx
│   └── auth/
│       ├── LoginForm.test.jsx
│       └── OTPDialog.test.jsx
├── contexts/
│   └── AuthContext.test.jsx
├── utils/
│   └── api.test.js
└── App.test.jsx
```

#### Integration Tests
**Framework**: Cypress or Playwright
**Location**: `frontend/cypress/` or `frontend/e2e/`

**Test Scenarios**:
- Complete authentication flow
- Library sync and browsing
- Search and filtering
- Profile management
- Error handling

### 4. End-to-End Testing (To Implement)

#### Full Stack Integration
**Framework**: Playwright or Cypress
**Scope**: Frontend + Backend + Database

**Test Scenarios**:
- User registration and login
- Audible account connection
- Library synchronization
- Book search and filtering
- Profile updates
- Error scenarios

#### Performance Testing
**Framework**: Artillery or k6
**Metrics**: Response times, throughput, resource usage

### 5. Database Testing

#### Schema Testing
**Framework**: pytest + MySQL
**Coverage**: 
- Table creation and relationships
- Data integrity constraints
- Migration scripts

#### Data Testing
**Framework**: pytest-mysql or testcontainers
**Coverage**:
- CRUD operations
- Complex queries
- Transaction handling

## Test Data Management

### Test Fixtures
**Location**: `backend/tests/conftest.py`
**Includes**:
- Mock database connections
- Sample authentication data
- Crypto instances
- Mock Audible clients

### Test Databases
**Strategy**: Separate test database or in-memory SQLite
**Benefits**: Isolation, speed, repeatability

## Continuous Integration

### GitHub Actions (Recommended)
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run backend tests
        run: python run_tests.py services crypto db
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Run frontend tests
        run: npm test
```

## Test Coverage Goals

### Backend Coverage Targets
- **Services**: 90%+ line coverage
- **Utilities**: 95%+ line coverage
- **API Endpoints**: 85%+ line coverage
- **Database Layer**: 80%+ line coverage

### Frontend Coverage Targets
- **Components**: 85%+ line coverage
- **Utilities**: 90%+ line coverage
- **Context/State**: 90%+ line coverage

## Testing Best Practices

### Backend
1. **Mock External Dependencies**: Audible API, database connections
2. **Test Error Scenarios**: Network failures, invalid data, timeouts
3. **Validate Security**: Encryption, authentication, authorization
4. **Performance Testing**: Response times, memory usage

### Frontend
1. **Test User Interactions**: Clicks, form submissions, navigation
2. **Mock API Calls**: Use MSW or similar for consistent testing
3. **Accessibility Testing**: Screen readers, keyboard navigation
4. **Responsive Testing**: Different screen sizes and devices

### Integration
1. **Test Real Workflows**: Complete user journeys
2. **Error Recovery**: How system handles failures
3. **Data Consistency**: Ensure data integrity across layers
4. **Performance Under Load**: Concurrent users, large datasets

## Implementation Roadmap

### Phase 1: Fix API Tests ⚠️
- [ ] Resolve FastAPI TestClient compatibility
- [ ] Migrate to httpx AsyncClient or compatible version
- [ ] Restore API endpoint testing

### Phase 2: Frontend Testing 📋
- [ ] Setup Jest + React Testing Library
- [ ] Create component unit tests
- [ ] Add integration tests with Cypress/Playwright
- [ ] Mock API interactions

### Phase 3: E2E Testing 🔄
- [ ] Setup full-stack testing environment
- [ ] Create user journey tests
- [ ] Add performance testing
- [ ] Implement CI/CD pipeline

### Phase 4: Advanced Testing 🚀
- [ ] Load testing with realistic data
- [ ] Security testing (penetration testing)
- [ ] Accessibility compliance testing
- [ ] Mobile responsiveness testing

## Tools and Dependencies

### Backend Testing
```bash
pip install pytest pytest-asyncio pytest-mock httpx
```

### Frontend Testing
```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
npm install --save-dev cypress  # or playwright
```

### Coverage Reporting
```bash
pip install pytest-cov
npm install --save-dev @testing-library/jest-dom
```

## Running the Complete Test Suite

### Current Working Tests
```bash
# Backend services (31 tests passing)
python run_tests.py services crypto db

# Individual categories
python run_tests.py services  # 14 tests
python run_tests.py crypto    # 6 tests  
python run_tests.py db        # 6 tests
```

### Future Complete Suite
```bash
# Backend
python run_tests.py all

# Frontend
npm test

# E2E
npm run e2e

# Coverage
python run_tests.py coverage
npm run test:coverage
```

## Monitoring and Reporting

### Test Results Dashboard
- Test pass/fail rates
- Coverage metrics
- Performance benchmarks
- Flaky test identification

### Alerts and Notifications
- Failed test notifications
- Coverage drop alerts
- Performance regression warnings

This testing strategy ensures comprehensive coverage across all layers of AudiPy while maintaining development velocity and code quality. 