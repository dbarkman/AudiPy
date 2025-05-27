#!/usr/bin/env python3
"""
AudiPy Database Setup Script
Reads .env configuration and creates all database tables
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# Add backend directory to path so we can import from it
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': os.getenv('DB_NAME', 'audipy'),
        'user': os.getenv('DB_USER', 'audipy'),
        'password': os.getenv('DB_PASSWORD'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }

def create_tables():
    """Create all database tables"""
    config = get_db_config()
    
    # Debug: Print config (without password)
    debug_config = config.copy()
    debug_config['password'] = '***' if config['password'] else 'None'
    print(f"Config: {debug_config}")
    
    # SQL statements for all tables
    table_statements = [
        # Users & Authentication Tables
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            oauth_provider VARCHAR(50) NOT NULL,
            oauth_provider_id VARCHAR(255) NOT NULL,
            display_name VARCHAR(255),
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            is_active BOOLEAN DEFAULT TRUE,
            
            UNIQUE KEY unique_oauth_user (oauth_provider, oauth_provider_id),
            INDEX idx_provider (oauth_provider),
            INDEX idx_created_at (created_at),
            INDEX idx_active (is_active),
            INDEX idx_last_login (last_login)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_oauth_tokens (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            provider VARCHAR(50) NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TIMESTAMP NULL,
            scope TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_provider (user_id, provider),
            INDEX idx_user_id (user_id),
            INDEX idx_expires_at (token_expires_at)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_audible_accounts (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            encrypted_auth_data TEXT NOT NULL,
            marketplace VARCHAR(10) DEFAULT 'us',
            last_sync TIMESTAMP NULL,
            sync_status ENUM('pending', 'syncing', 'completed', 'failed') DEFAULT 'pending',
            sync_error TEXT NULL,
            tokens_expires_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_marketplace (user_id, marketplace),
            INDEX idx_last_sync (last_sync),
            INDEX idx_expires_at (tokens_expires_at)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            max_price DECIMAL(10,2) DEFAULT 12.66,
            preferred_language VARCHAR(20) DEFAULT 'english',
            marketplace VARCHAR(10) DEFAULT 'us',
            currency VARCHAR(3) DEFAULT 'USD',
            notifications_enabled BOOLEAN DEFAULT TRUE,
            price_alert_enabled BOOLEAN DEFAULT TRUE,
            new_release_alerts BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_prefs (user_id)
        )
        """,
        
        # Core Book Entities
        """
        CREATE TABLE IF NOT EXISTS books (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            asin VARCHAR(20) UNIQUE NOT NULL,
            amazon_asin VARCHAR(20),
            title TEXT NOT NULL,
            subtitle TEXT,
            publisher_name VARCHAR(500),
            publication_datetime TIMESTAMP NULL,
            publication_name VARCHAR(500),
            issue_date DATE,
            release_date DATE,
            isbn VARCHAR(20),
            language VARCHAR(20),
            content_type VARCHAR(50),
            content_delivery_type VARCHAR(50),
            format_type VARCHAR(50),
            runtime_length_min INT,
            merchandising_summary TEXT,
            merchandising_description TEXT,
            extended_product_description TEXT,
            audible_editors_summary TEXT,
            publisher_summary TEXT,
            is_adult_product BOOLEAN DEFAULT FALSE,
            is_listenable BOOLEAN DEFAULT FALSE,
            is_purchasability_suppressed BOOLEAN DEFAULT FALSE,
            is_vvab BOOLEAN DEFAULT FALSE,
            has_children BOOLEAN DEFAULT FALSE,
            sku VARCHAR(50),
            sku_lite VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_asin (asin),
            INDEX idx_title (title(100)),
            INDEX idx_language (language),
            INDEX idx_publisher (publisher_name(100)),
            INDEX idx_release_date (release_date),
            INDEX idx_runtime (runtime_length_min)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS authors (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            asin VARCHAR(20) UNIQUE,
            name VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_name (name(100)),
            INDEX idx_asin (asin)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS narrators (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            asin VARCHAR(20) UNIQUE,
            name VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_name (name(100)),
            INDEX idx_asin (asin)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS series (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            asin VARCHAR(20) UNIQUE,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_title (title(100)),
            INDEX idx_asin (asin)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS categories (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            audible_category_id VARCHAR(50),
            name VARCHAR(500) NOT NULL,
            parent_id BIGINT NULL,
            level INT DEFAULT 0,
            full_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
            INDEX idx_name (name(100)),
            INDEX idx_parent (parent_id),
            INDEX idx_level (level)
        )
        """,
        
        # Relationship Tables
        """
        CREATE TABLE IF NOT EXISTS book_authors (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            author_id BIGINT NOT NULL,
            role VARCHAR(100) DEFAULT 'author',
            display_order INT DEFAULT 0,
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_author (book_id, author_id),
            INDEX idx_book_id (book_id),
            INDEX idx_author_id (author_id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS book_narrators (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            narrator_id BIGINT NOT NULL,
            display_order INT DEFAULT 0,
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (narrator_id) REFERENCES narrators(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_narrator (book_id, narrator_id),
            INDEX idx_book_id (book_id),
            INDEX idx_narrator_id (narrator_id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS book_series (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            series_id BIGINT NOT NULL,
            sequence DECIMAL(10,2),
            sequence_display VARCHAR(20),
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_series (book_id, series_id),
            INDEX idx_book_id (book_id),
            INDEX idx_series_id (series_id),
            INDEX idx_sequence (sequence)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS book_categories (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            category_id BIGINT NOT NULL,
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_category (book_id, category_id),
            INDEX idx_book_id (book_id),
            INDEX idx_category_id (category_id)
        )
        """,
        
        # User Library & Progress
        """
        CREATE TABLE IF NOT EXISTS user_libraries (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            book_id BIGINT NOT NULL,
            purchase_date TIMESTAMP NULL,
            order_id VARCHAR(100),
            order_item_id VARCHAR(100),
            date_added TIMESTAMP NULL,
            is_pending BOOLEAN DEFAULT FALSE,
            is_preordered BOOLEAN DEFAULT FALSE,
            is_removable BOOLEAN DEFAULT FALSE,
            is_visible BOOLEAN DEFAULT TRUE,
            is_archived BOOLEAN DEFAULT FALSE,
            percent_complete DECIMAL(5,2) DEFAULT 0.00,
            is_finished BOOLEAN DEFAULT FALSE,
            is_downloaded BOOLEAN DEFAULT FALSE,
            is_playable BOOLEAN DEFAULT FALSE,
            is_in_wishlist BOOLEAN DEFAULT FALSE,
            user_rating DECIMAL(3,1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_book (user_id, book_id),
            INDEX idx_user_id (user_id),
            INDEX idx_book_id (book_id),
            INDEX idx_purchase_date (purchase_date),
            INDEX idx_is_finished (is_finished),
            INDEX idx_percent_complete (percent_complete)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_wishlists (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            book_id BIGINT NOT NULL,
            priority INT DEFAULT 0,
            notes TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_wishlist (user_id, book_id),
            INDEX idx_user_id (user_id),
            INDEX idx_priority (priority),
            INDEX idx_added_date (added_date)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_reading_lists (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_name (name)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_reading_list_books (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            reading_list_id BIGINT NOT NULL,
            book_id BIGINT NOT NULL,
            position INT DEFAULT 0,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (reading_list_id) REFERENCES user_reading_lists(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_list_book (reading_list_id, book_id),
            INDEX idx_reading_list_id (reading_list_id),
            INDEX idx_position (position)
        )
        """,
        
        # Pricing & Suggestions
        """
        CREATE TABLE IF NOT EXISTS book_prices (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            marketplace VARCHAR(10) NOT NULL,
            credit_price DECIMAL(10,2),
            list_price DECIMAL(10,2),
            member_price DECIMAL(10,2),
            currency_code VARCHAR(3) DEFAULT 'USD',
            price_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_price_date (book_id, marketplace, price_date),
            INDEX idx_book_id (book_id),
            INDEX idx_price_date (price_date),
            INDEX idx_member_price (member_price)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_recommendations (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            book_id BIGINT NOT NULL,
            suggestion_type ENUM('series', 'author', 'narrator', 'similar') NOT NULL,
            source_book_id BIGINT NULL,
            source_name VARCHAR(500),
            confidence_score DECIMAL(3,2) DEFAULT 0.50,
            purchase_method ENUM('cash', 'credits') DEFAULT 'credits',
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_dismissed BOOLEAN DEFAULT FALSE,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (source_book_id) REFERENCES books(id) ON DELETE SET NULL,
            UNIQUE KEY unique_user_suggestion (user_id, book_id, suggestion_type, source_name),
            INDEX idx_user_id (user_id),
            INDEX idx_suggestion_type (suggestion_type),
            INDEX idx_generated_at (generated_at),
            INDEX idx_confidence (confidence_score)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS price_alerts (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            book_id BIGINT NOT NULL,
            target_price DECIMAL(10,2) NOT NULL,
            alert_type ENUM('below', 'percentage_off') DEFAULT 'below',
            percentage_threshold DECIMAL(5,2),
            is_active BOOLEAN DEFAULT TRUE,
            last_notified TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_book_id (book_id),
            INDEX idx_target_price (target_price),
            INDEX idx_is_active (is_active)
        )
        """,
        
        # Extended Book Data
        """
        CREATE TABLE IF NOT EXISTS book_extended_data (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            book_id BIGINT NOT NULL,
            product_images JSON,
            social_media_images JSON,
            rich_images JSON,
            customer_reviews JSON,
            goodreads_ratings JSON,
            rating DECIMAL(3,1),
            is_ayce BOOLEAN DEFAULT FALSE,
            is_buyable BOOLEAN DEFAULT FALSE,
            is_preorderable BOOLEAN DEFAULT FALSE,
            is_prereleased BOOLEAN DEFAULT FALSE,
            is_released BOOLEAN DEFAULT FALSE,
            is_returnable BOOLEAN DEFAULT FALSE,
            is_searchable BOOLEAN DEFAULT FALSE,
            is_shared BOOLEAN DEFAULT FALSE,
            is_pdf_url_available BOOLEAN DEFAULT FALSE,
            is_ws4v_enabled BOOLEAN DEFAULT FALSE,
            is_ws4v_companion_asin_owned BOOLEAN DEFAULT FALSE,
            date_first_available DATE,
            preorder_release_date DATE,
            new_episode_added_date DATE,
            product_site_launch_date DATE,
            destination_asin VARCHAR(20),
            origin_asin VARCHAR(20),
            origin_id VARCHAR(50),
            origin_marketplace VARCHAR(10),
            origin_type VARCHAR(50),
            ws4v_companion_asin VARCHAR(20),
            copyright TEXT,
            content_level VARCHAR(50),
            content_rating VARCHAR(50),
            narration_accent VARCHAR(100),
            voice_description TEXT,
            episode_count INT,
            episode_number INT,
            episode_type VARCHAR(50),
            season_number INT,
            part_number INT,
            available_codecs JSON,
            ws4v_details JSON,
            product_page_url TEXT,
            sample_url TEXT,
            pdf_url TEXT,
            claim_code_url TEXT,
            image_url TEXT,
            book_tags JSON,
            tags JSON,
            thesaurus_subject_keywords JSON,
            platinum_keywords JSON,
            long_tail_topic_tags JSON,
            spotlight_tags JSON,
            generic_keyword VARCHAR(500),
            text_to_speech JSON,
            read_along_support JSON,
            collection_ids JSON,
            subscription_asins JSON,
            music_id VARCHAR(50),
            
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_book_extended (book_id)
        )
        """,
        
        # System & Analytics
        """
        CREATE TABLE IF NOT EXISTS sync_jobs (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            job_type ENUM('full_sync', 'library_sync', 'suggestions_sync') NOT NULL,
            status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
            started_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            books_processed INT DEFAULT 0,
            books_added INT DEFAULT 0,
            books_updated INT DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_analytics (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50),
            entity_id BIGINT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_action_type (action_type),
            INDEX idx_created_at (created_at)
        )
        """
    ]
    
    try:
        # Connect to database
        print(f"Connecting to database '{config['database']}' as user '{config['user']}'...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("✅ Connected successfully!")
        print("Creating tables...")
        
        # Execute each table creation statement
        for i, statement in enumerate(table_statements, 1):
            try:
                cursor.execute(statement)
                print(f"✅ Created table {i}/{len(table_statements)}")
            except Error as e:
                print(f"❌ Error creating table {i}: {e}")
                return False
        
        # Insert test user
        print("Inserting test user...")
        cursor.execute("""
            INSERT IGNORE INTO users (oauth_provider, oauth_provider_id, display_name) 
            VALUES ('test', '1', 'Test User')
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ All tables created successfully!")
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 AudiPy Database Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path('backend/.env')
    if not env_file.exists():
        print(f"❌ Environment file not found: {env_file}")
        print("Please create backend/.env with database configuration")
        return False
    
    config = get_db_config()
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    print(f"Host: {config['host']}:{config['port']}")
    print()
    
    # Create tables directly with existing user
    if create_tables():
        print()
        print("🎉 Database setup completed successfully!")
        print("You can now test the API connection:")
        print("curl http://localhost:8000/health")
        return True
    else:
        print()
        print("❌ Database setup failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 