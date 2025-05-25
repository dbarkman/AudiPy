# AudiPy Scripts Organization

## 🎯 Core Production Pipeline

Run these scripts in order to set up and populate your AudiPy system:

### Phase 1: Authentication
```bash
python phase1_authenticate.py
```
- Authenticates with Audible using your credentials
- Stores encrypted authentication tokens in database
- Handles 2FA/OTP authentication
- **Run first** - required for all other phases

### Phase 2: User Profile Setup
```bash
python phase2_user_profile.py
```
- Sets up user preferences (language, marketplace, price thresholds)
- Interactive configuration of recommendation settings
- **Run second** - configures your personal preferences

### Phase 3: Library Sync
```bash
python phase3_fetch_library.py
```
- Fetches your complete Audible library (696 books in your case)
- Stores books, authors, narrators, and series in database
- Applies language filtering based on preferences
- **Run third** - populates the database with your library

### Phase 4: Generate Recommendations
```bash
python phase4_generate_recommendations.py
```
- Analyzes your library to find patterns
- Generates 252 personalized recommendations
- Categories: Series continuations, favorite authors, preferred narrators
- **Run fourth** - creates your recommendation list

## 🔧 Utility Scripts

Located in `utils/` directory:

### View Recommendations
```bash
python utils/view_recommendations.py
```
- Displays all generated recommendations in formatted tables
- Shows breakdown by type (series/author/narrator)
- Includes confidence scores and purchase methods

### Database Cleanup
```bash
python utils/cleanup_database.py
```
- Comprehensive database cleanup tool
- Multiple modes: interactive, force, confirm-each
- Use when you need to reset and start fresh

### Crypto Utilities
```bash
utils/crypto_utils_simple.py
```
- Encryption/decryption utilities for secure token storage
- Used internally by the phase scripts
- Handles user-specific key derivation

## 📚 Legacy Scripts

Located in `legacy/` directory - these are the original monolithic scripts before the database-driven architecture:

- `audipy.py` - Original CLI-only script
- `audipy_with_token_caching.py` - Enhanced with token caching
- `audipy_interactive.py` - Interactive credential prompting

These are kept for reference but not needed for production use.

## 🚀 Quick Start

1. Set up your `.env` file with database credentials
2. Run the phases in order: 1 → 2 → 3 → 4
3. View your recommendations with `python utils/view_recommendations.py`

## 📊 Current Status

Your system is fully functional with:
- ✅ 696 books in library
- ✅ 387 authors, 404 narrators, 158 series cataloged  
- ✅ 252 personalized recommendations generated
- ✅ Database-driven architecture ready for web interface 