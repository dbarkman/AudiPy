# 🚀 Getting AudiPy CLI Working - Step by Step

## Current Status
- ✅ Code resurrected from GitHub
- ✅ Database still exists on server
- ✅ Previously connected to Audible (CLI and web)
- ❌ Need to set up .env configuration
- ❌ Need to test everything

## Step 1: Set Up Database Configuration

### 1.1 - Find Your Database Credentials
You mentioned the database is still on the server. We need:
- Database name (likely: `audipy`)
- Database user (likely: `audipy`)
- Database password
- Host (likely: `localhost`)
- Port (likely: `3306`)

**Action:** Check if you have these credentials saved somewhere, or we can query the database.

### 1.2 - Check What's in the Database
Run this command to see what data already exists:
```bash
mysql -u audipy -p audipy -e "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM user_libraries;"
```
This will tell us if you have existing data we can work with.

## Step 2: Set Up Encryption Key

### 2.1 - Check for Existing Encryption Key
If you've run this before, there may already be data encrypted with a key. We need to find that key.

**Action:** Check if there's an old .env file backed up anywhere.

### 2.2 - Generate New Key (if needed)
If this is a fresh start or you can't find the old key, generate a new one:
```bash
cd /home/david/AudiPy/backend
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

⚠️ **IMPORTANT:** If you have existing encrypted data in the database, using a new key will make that data unreadable!

## Step 3: Create .env File

Copy the example and fill in your values:
```bash
cd /home/david/AudiPy/backend
cp .env.example .env
nano .env  # or use your preferred editor
```

Required fields for CLI usage:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=audipy
DB_USER=audipy
DB_PASSWORD=your_actual_password_here

# Encryption Key
AUDIPY_MASTER_KEY=your_generated_key_here
```

## Step 4: Install Python Dependencies

```bash
cd /home/david/AudiPy/backend

# Create virtual environment if it doesn't exist
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Test Database Connection

```bash
cd /home/david/AudiPy/backend
source venv/bin/activate
python3 -c "from utils.db.connection import test_connection; print('✅ Connected!' if test_connection() else '❌ Failed')"
```

## Step 6: Run Phase Scripts (In Order)

### Phase 1: Authentication
**What it does:** Connects to your Audible account and stores encrypted tokens.
```bash
cd /home/david/AudiPy/backend
source venv/bin/activate
python3 phase1_authenticate.py
```

You'll need:
- Your Audible email/username
- Your Audible password
- Your marketplace (us, uk, de, etc.)
- OTP code (if 2FA is enabled)

### Phase 2: User Preferences
**What it does:** Sets up your preferences (language, price threshold, etc.)
```bash
python3 phase2_user_profile.py
```

### Phase 3: Fetch Library
**What it does:** Downloads your entire Audible library into the database.
```bash
python3 phase3_fetch_library.py
```
This may take a few minutes depending on library size.

### Phase 4: Generate Recommendations
**What it does:** Analyzes your library and generates book recommendations.
```bash
python3 phase4_generate_recommendations.py
```

## Step 7: View Your Recommendations

Check the generated reports:
```bash
cd /home/david/AudiPy/reports
ls -lh
```

You should see:
- `my_library_by_authors.txt`
- `my_library_by_narrators.txt`
- `my_library_by_series.txt`
- `missing_books_in_my_series.txt` ⭐ **PRIORITY 1**
- `missing_books_by_my_authors.txt` ⭐ **PRIORITY 2**
- `missing_books_by_my_narrators.txt` 🔍 **DISCOVERY**

Or view recommendations from database:
```bash
cd /home/david/AudiPy/backend
source venv/bin/activate
python3 utils/view_recommendations.py
```

## Troubleshooting

### Database Connection Failed
- Check credentials in .env
- Ensure MySQL is running: `systemctl status mysql` or `systemctl status mariadb`
- Test connection: `mysql -u audipy -p audipy`

### Encryption Key Error
- If you see "Master key not found", add AUDIPY_MASTER_KEY to .env
- If you have existing data, you MUST use the original key

### Audible Authentication Failed
- Double-check username/password
- Make sure you're using the correct marketplace
- If OTP fails, request a new code

### Import Errors
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Quick Status Check Commands

Check database contents:
```bash
mysql -u audipy -p audipy -e "
SELECT 
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM books) as books,
    (SELECT COUNT(*) FROM user_libraries) as library_items,
    (SELECT COUNT(*) FROM user_recommendations) as recommendations;
"
```

Check if authenticated:
```bash
mysql -u audipy -p audipy -e "
SELECT u.display_name, uaa.marketplace, uaa.last_sync, uaa.sync_status 
FROM users u 
JOIN user_audible_accounts uaa ON u.id = uaa.user_id 
ORDER BY u.created_at DESC LIMIT 5;
"
```

---

## Next Steps After Getting It Working

Once the CLI is working, you can:
1. Browse your recommendations to find a good book
2. Run sync/recommendations periodically to stay updated
3. Later: Consider setting up the web interface
