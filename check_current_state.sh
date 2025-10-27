#!/bin/bash
# AudiPy Current State Diagnostic
# This script helps you understand what's already set up

echo "🔍 AudiPy Current State Diagnostic"
echo "===================================="
echo ""

# Check if .env exists
echo "1️⃣  Checking for .env file..."
if [ -f "/home/david/AudiPy/backend/.env" ]; then
    echo "   ✅ .env file exists"
    echo "   📋 Contents (passwords hidden):"
    grep -v "PASSWORD\|KEY\|SECRET" /home/david/AudiPy/backend/.env | sed 's/^/      /'
    echo ""
else
    echo "   ❌ .env file NOT found at /home/david/AudiPy/backend/.env"
    echo "   👉 You need to create this file first"
    echo ""
fi

# Check Python virtual environment
echo "2️⃣  Checking for Python virtual environment..."
if [ -d "/home/david/AudiPy/backend/venv" ]; then
    echo "   ✅ Virtual environment exists"
else
    echo "   ❌ Virtual environment NOT found"
    echo "   👉 Run: cd /home/david/AudiPy/backend && python3 -m venv venv"
    echo ""
fi

# Check if MySQL is running
echo "3️⃣  Checking if MySQL/MariaDB is running..."
if systemctl is-active --quiet mysql 2>/dev/null; then
    echo "   ✅ MySQL is running"
elif systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "   ✅ MariaDB is running"
else
    echo "   ⚠️  Cannot determine if MySQL/MariaDB is running"
    echo "   👉 Try: systemctl status mysql or systemctl status mariadb"
fi
echo ""

# Try to connect to database and check contents
echo "4️⃣  Attempting to check database contents..."
echo "   (You may be prompted for the database password)"
echo ""

read -p "   Database username [audipy]: " DB_USER
DB_USER=${DB_USER:-audipy}

read -p "   Database name [audipy]: " DB_NAME
DB_NAME=${DB_NAME:-audipy}

echo ""
echo "   Connecting to database '$DB_NAME' as user '$DB_USER'..."

# Try to query the database
if mysql -u "$DB_USER" -p "$DB_NAME" -e "SELECT 1" >/dev/null 2>&1; then
    echo "   ✅ Database connection successful!"
    echo ""
    
    echo "   📊 Database Contents:"
    mysql -u "$DB_USER" -p "$DB_NAME" << 'EOSQL'
SELECT 
    'Users' as Table_Name, 
    COUNT(*) as Count 
FROM users
UNION ALL
SELECT 'Audible Accounts', COUNT(*) FROM user_audible_accounts
UNION ALL
SELECT 'User Preferences', COUNT(*) FROM user_preferences
UNION ALL
SELECT 'Books', COUNT(*) FROM books
UNION ALL
SELECT 'Authors', COUNT(*) FROM authors
UNION ALL
SELECT 'Narrators', COUNT(*) FROM narrators
UNION ALL
SELECT 'Series', COUNT(*) FROM series
UNION ALL
SELECT 'User Library', COUNT(*) FROM user_libraries
UNION ALL
SELECT 'Recommendations', COUNT(*) FROM user_recommendations;
EOSQL
    
    echo ""
    echo "   👤 User Accounts:"
    mysql -u "$DB_USER" -p "$DB_NAME" -e "
    SELECT 
        u.id,
        u.display_name,
        u.oauth_provider,
        uaa.marketplace,
        uaa.sync_status,
        uaa.last_sync,
        CASE 
            WHEN LENGTH(uaa.encrypted_auth_data) > 0 THEN '✅ Has encrypted tokens'
            ELSE '❌ No tokens'
        END as token_status
    FROM users u
    LEFT JOIN user_audible_accounts uaa ON u.id = uaa.user_id
    ORDER BY u.created_at DESC;"
    
else
    echo "   ❌ Could not connect to database"
    echo "   👉 Possible issues:"
    echo "      - Wrong username or password"
    echo "      - Database doesn't exist"
    echo "      - MySQL/MariaDB not running"
fi

echo ""
echo "===================================="
echo "✅ Diagnostic complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. If .env missing: Create /home/david/AudiPy/backend/.env"
echo "   2. If venv missing: cd /home/david/AudiPy/backend && python3 -m venv venv"
echo "   3. If database empty: You'll need to run Phase 1-4 scripts"
echo "   4. If database has data: You may just need to refresh tokens"
echo ""
echo "📖 For detailed instructions, see: /home/david/AudiPy/GETTING_STARTED_CLI.md"

