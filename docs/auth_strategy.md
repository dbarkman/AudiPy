# AudiPy Authentication Strategy

## 🔐 Current State (CLI Tool)

### How Authentication Currently Works:
1. **Direct Login**: Username + Password → Audible API
2. **2FA/OTP**: Amazon's 2FA system requires OTP on each login
3. **Session-based**: No token persistence between runs
4. **Manual Process**: User enters OTP every time

### Why OTP Every Time?
- **Amazon Security**: Audible uses Amazon's authentication (Amazon owns Audible)
- **No Token Storage**: Current script doesn't store refresh tokens
- **Session Expiry**: Authentication doesn't persist between script runs

## 🎯 Web Application Authentication Strategy

### Phase 1: Enhanced CLI Authentication
**Goal**: Reduce OTP frequency for development

```python
# Enhanced authentication with token caching
class AudibleAuth:
    def __init__(self):
        self.token_file = '.audible_tokens.json'  # Add to .gitignore!
        self.auth = None
        
    def authenticate(self):
        # Try to load existing tokens first
        if self.load_cached_tokens():
            return True
            
        # Fall back to fresh login with OTP
        return self.fresh_login()
        
    def load_cached_tokens(self):
        """Load and validate cached authentication tokens"""
        if Path(self.token_file).exists():
            # Load tokens and test if still valid
            # Return True if valid, False if expired
            pass
            
    def fresh_login(self):
        """Perform fresh login with OTP and cache tokens"""
        # Current login process + save tokens
        pass
```

### Phase 2: Web Application OAuth Strategy

#### Option A: Direct Audible/Amazon OAuth (Recommended)
```
User → AudiPy Web App → Amazon/Audible OAuth → Access Tokens
```

**Pros:**
- Official authentication flow
- Better security (no credential storage)
- Standard OAuth2 implementation
- Automatic token refresh

**Cons:**
- Need to register as Amazon/Audible developer
- More complex initial setup
- Subject to Amazon's app approval process

#### Option B: Credential Proxy (Fallback)
```
User → AudiPy Web App → Encrypted Credential Storage → Audible API
```

**Pros:**
- Can implement immediately
- Full control over authentication flow
- No external app approval needed

**Cons:**
- Storing user credentials (even encrypted)
- Still need to handle OTP somehow
- Security responsibility on us

### Phase 3: Production Authentication Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend │    │  Amazon/Audible │
│                 │    │                  │    │     OAuth       │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │                 │
│ │Login Button │────→ │ │OAuth Handler │────→ │                 │
│ └─────────────┘ │    │ └──────────────┘ │    │                 │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │                 │
│ │JWT Token    │←──── │ │Token Manager │←──── │                 │
│ │Storage      │ │    │ └──────────────┘ │    │                 │
│ └─────────────┘ │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Implementation Plan

### Immediate (CLI Enhancement)
1. **Token Caching**: Store authentication tokens locally
2. **Token Refresh**: Automatically refresh when possible
3. **Graceful Degradation**: Fall back to OTP when tokens expire

### Short Term (Web MVP)
1. **User Registration**: Basic account system for AudiPy users
2. **Credential Encryption**: Secure storage of Audible credentials
3. **Background Sync**: Automated library updates
4. **Session Management**: Web session handling

### Long Term (Production)
1. **Amazon OAuth Integration**: Official OAuth flow
2. **Multi-user Support**: Proper tenant isolation
3. **Token Management**: Automatic refresh, revocation
4. **Rate Limiting**: Respect Audible API limits per user

## 🗄️ Database Models for Authentication

```sql
-- Core user table
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Audible account credentials (encrypted)
CREATE TABLE user_audible_accounts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    encrypted_username TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    marketplace VARCHAR(10) DEFAULT 'us',
    last_sync TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- OAuth tokens (when we get there)
CREATE TABLE user_oauth_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    provider VARCHAR(50) NOT NULL, -- 'amazon', 'audible'
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    scope TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User preferences
CREATE TABLE user_preferences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    max_price DECIMAL(10,2) DEFAULT 12.66,
    preferred_language VARCHAR(20) DEFAULT 'english',
    marketplace VARCHAR(10) DEFAULT 'us',
    currency VARCHAR(3) DEFAULT 'USD',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## 🚦 Next Steps

1. **Run the data dump script** to understand all API fields
2. **Design complete database schema** with all models
3. **Implement token caching** in CLI tool to reduce OTP frequency
4. **Research Amazon/Audible OAuth** requirements and registration process
5. **Start basic web application** with user registration

## 🔒 Security Considerations

- **Credential Encryption**: Use strong encryption for stored credentials
- **Token Security**: Secure storage and transmission of OAuth tokens
- **Rate Limiting**: Respect Audible API limits to avoid account suspension
- **Audit Logging**: Track authentication events and API calls
- **Session Management**: Proper session handling and timeout
- **2FA Support**: Eventually support 2FA for AudiPy accounts themselves 