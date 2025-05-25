# 🎵 AudiPy Phase Scripts

## Overview

The AudiPy functionality has been broken down into 4 distinct phases for database testing and development. Each script is standalone and focuses on a specific aspect of the system.

## 📋 Prerequisites

1. **Database Setup**: All tables from `database_schema.md` must be created
2. **Environment Variables**: Update your `.env` file with database and encryption settings
3. **Dependencies**: Install required packages

```bash
pip install mysql-connector-python cryptography audible rich
```

## 🔧 Environment Variables

Add these to your `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=audipy
DB_USER=audipy
DB_PASSWORD=your_secure_database_password_here

# Encryption (will be auto-generated on first run)
ENCRYPTION_KEY=your_encryption_key_here

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

## 🚀 Phase Scripts

### Phase 1: Authentication (`phase1_authenticate.py`)

**Purpose**: Authenticate with Audible and store encrypted tokens in database

**What it does**:
- Prompts for Audible credentials (username, password, marketplace)
- Handles OTP/2FA authentication
- Creates a test user in the database
- Encrypts and stores Audible authentication tokens
- Tests API access to verify tokens work

**Run when**: First time setup or when tokens expire

```bash
python phase1_authenticate.py
```

**Output**: 
- User created in `users` table
- Encrypted tokens stored in `user_audible_accounts` table
- Confirmation of successful API access

---

### Phase 2: User Profile (`phase2_user_profile.py`)

**Purpose**: Set up user preferences and profile settings

**What it does**:
- Finds the user created in Phase 1
- Displays current preferences (or defaults)
- Interactively prompts for preference updates
- Stores preferences in `user_preferences` table

**Run when**: After Phase 1, or when you want to update preferences

```bash
python phase2_user_profile.py
```

**Preferences configured**:
- Max credit price threshold ($12.66 default)
- Language preference (english, spanish, etc.)
- Marketplace (us, uk, de, etc.)
- Notification settings

---

### Phase 3: Fetch Library (`phase3_fetch_library.py`)

**Purpose**: Fetch user's Audible library and store in normalized database

**What it does**:
- Loads user and preferences from database
- Decrypts Audible tokens and creates API client
- Fetches complete library from Audible API
- Stores books in normalized database structure:
  - `books` table (main book data)
  - `authors`, `narrators`, `series` tables
  - `book_authors`, `book_narrators`, `book_series` relationship tables
  - `user_libraries` table (user's ownership data)
- Applies language filtering based on user preferences
- Updates sync status

**Run when**: After Phases 1 & 2, or when you want to refresh your library

```bash
python phase3_fetch_library.py
```

**Database impact**:
- Populates all book-related tables
- Creates normalized relationships
- Stores user's library ownership data

---

### Phase 4: Generate Recommendations (`phase4_generate_recommendations.py`)

**Purpose**: Generate static recommendations and store in database

**What it does**:
- Loads user library and preferences
- Identifies top 5 authors, narrators, and series from user's library
- Searches Audible catalog for books by those authors/narrators/series
- Filters out books user already owns (ASIN + title matching)
- Applies language filtering
- Stores recommendations in `user_recommendations` table
- Calculates confidence scores and purchase methods (cash vs credits)

**Run when**: After Phase 3, or when you want to refresh recommendations

```bash
python phase4_generate_recommendations.py
```

**Recommendation types**:
- **Author**: Books by your favorite authors
- **Narrator**: Books by your favorite narrators  
- **Series**: Missing books from your series

---

## 🔄 Execution Order

### Initial Setup:
1. `phase1_authenticate.py` - Authenticate and store tokens
2. `phase2_user_profile.py` - Set up preferences
3. `phase3_fetch_library.py` - Import your library
4. `phase4_generate_recommendations.py` - Generate recommendations

### Ongoing Usage:
- **Phase 1**: Only when tokens expire or authentication fails
- **Phase 2**: When you want to change preferences
- **Phase 3**: When you want to sync new library additions
- **Phase 4**: When you want fresh recommendations (after library updates)

## 🧪 Testing Limits

For database testing, Phase 4 uses reduced limits:
- **5 authors** (vs 50 in production)
- **5 narrators** (vs 50 in production)  
- **5 series** (vs 20 in production)

This prevents API rate limiting during testing while still validating the database structure.

## 🔍 Verification

After running all phases, you can verify the data:

```sql
-- Check user setup
SELECT * FROM users;
SELECT * FROM user_preferences;
SELECT * FROM user_audible_accounts;

-- Check library data
SELECT COUNT(*) FROM books;
SELECT COUNT(*) FROM user_libraries;
SELECT COUNT(*) FROM authors;
SELECT COUNT(*) FROM narrators;
SELECT COUNT(*) FROM series;

-- Check recommendations
SELECT recommendation_type, COUNT(*) 
FROM user_recommendations 
GROUP BY recommendation_type;
```

## 🎯 Next Steps

Once all phases complete successfully:
1. **Database structure validated** ✅
2. **Authentication flow working** ✅  
3. **Library import process tested** ✅
4. **Recommendation generation verified** ✅
5. **Ready for web interface development** 🚀

The database now contains all the normalized data needed to build the React frontend and API endpoints! 