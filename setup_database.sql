-- AudiPy Database Schema Setup
-- This script creates all tables for the AudiPy web application

USE audipy;

-- 1. Users & Authentication Tables

-- Core user accounts for AudiPy (OAuth/OIDC based)
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    oauth_provider VARCHAR(50) NOT NULL, -- 'google', 'github', 'microsoft', etc.
    oauth_provider_id VARCHAR(255) NOT NULL, -- Provider's unique user ID
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
);

-- OAuth provider tokens (for accessing external APIs if needed)
CREATE TABLE user_oauth_tokens (
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
);

-- Audible authentication tokens (encrypted, user-uploaded)
CREATE TABLE user_audible_accounts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    encrypted_auth_data TEXT NOT NULL, -- Encrypted Audible auth tokens
    marketplace VARCHAR(10) DEFAULT 'us',
    last_sync TIMESTAMP NULL,
    sync_status ENUM('pending', 'syncing', 'completed', 'failed') DEFAULT 'pending',
    sync_error TEXT NULL,
    tokens_expires_at TIMESTAMP NULL, -- When Audible tokens expire
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_marketplace (user_id, marketplace),
    INDEX idx_last_sync (last_sync),
    INDEX idx_expires_at (tokens_expires_at)
);

-- User preferences and settings
CREATE TABLE user_preferences (
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
);

-- 2. Core Book Entities

-- Master book catalog (combination of user library + catalog data)
CREATE TABLE books (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asin VARCHAR(20) UNIQUE NOT NULL,
    amazon_asin VARCHAR(20),
    title TEXT NOT NULL,
    subtitle TEXT,
    
    -- Publishing Information
    publisher_name VARCHAR(500),
    publication_datetime TIMESTAMP NULL,
    publication_name VARCHAR(500),
    issue_date DATE,
    release_date DATE,
    isbn VARCHAR(20),
    language VARCHAR(20),
    
    -- Content Information
    content_type VARCHAR(50),
    content_delivery_type VARCHAR(50),
    format_type VARCHAR(50),
    runtime_length_min INT,
    
    -- Descriptions
    merchandising_summary TEXT,
    merchandising_description TEXT,
    extended_product_description TEXT,
    audible_editors_summary TEXT,
    publisher_summary TEXT,
    
    -- Status Flags
    is_adult_product BOOLEAN DEFAULT FALSE,
    is_listenable BOOLEAN DEFAULT FALSE,
    is_purchasability_suppressed BOOLEAN DEFAULT FALSE,
    is_vvab BOOLEAN DEFAULT FALSE,
    has_children BOOLEAN DEFAULT FALSE,
    
    -- Media & Technical
    sku VARCHAR(50),
    sku_lite VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_asin (asin),
    INDEX idx_title (title(100)),
    INDEX idx_language (language),
    INDEX idx_publisher (publisher_name(100)),
    INDEX idx_release_date (release_date),
    INDEX idx_runtime (runtime_length_min),
    FULLTEXT idx_title_subtitle (title, subtitle),
    FULLTEXT idx_descriptions (merchandising_summary, extended_product_description)
);

-- Authors
CREATE TABLE authors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asin VARCHAR(20) UNIQUE,
    name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name(100)),
    INDEX idx_asin (asin)
);

-- Narrators
CREATE TABLE narrators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asin VARCHAR(20) UNIQUE,
    name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name(100)),
    INDEX idx_asin (asin)
);

-- Series
CREATE TABLE series (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asin VARCHAR(20) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_title (title(100)),
    INDEX idx_asin (asin)
);

-- Categories/Genres
CREATE TABLE categories (
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
);

-- 3. Relationship Tables

-- Book-Author relationships
CREATE TABLE book_authors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    role VARCHAR(100) DEFAULT 'author', -- author, co-author, editor, etc.
    display_order INT DEFAULT 0,
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_author (book_id, author_id),
    INDEX idx_book_id (book_id),
    INDEX idx_author_id (author_id)
);

-- Book-Narrator relationships
CREATE TABLE book_narrators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    narrator_id BIGINT NOT NULL,
    display_order INT DEFAULT 0,
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (narrator_id) REFERENCES narrators(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_narrator (book_id, narrator_id),
    INDEX idx_book_id (book_id),
    INDEX idx_narrator_id (narrator_id)
);

-- Book-Series relationships
CREATE TABLE book_series (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    series_id BIGINT NOT NULL,
    sequence DECIMAL(10,2), -- Allow decimals for books like 1.5, 2.5
    sequence_display VARCHAR(20), -- For display like "1.5", "Prequel"
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_series (book_id, series_id),
    INDEX idx_book_id (book_id),
    INDEX idx_series_id (series_id),
    INDEX idx_sequence (sequence)
);

-- Book-Category relationships
CREATE TABLE book_categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_category (book_id, category_id),
    INDEX idx_book_id (book_id),
    INDEX idx_category_id (category_id)
);

-- 4. User Library & Progress

-- User's owned books (from their Audible library)
CREATE TABLE user_libraries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    
    -- Purchase Information
    purchase_date TIMESTAMP NULL,
    order_id VARCHAR(100),
    order_item_id VARCHAR(100),
    
    -- Library Status (from library_status field)
    date_added TIMESTAMP NULL,
    is_pending BOOLEAN DEFAULT FALSE,
    is_preordered BOOLEAN DEFAULT FALSE,
    is_removable BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,
    
    -- Listening Progress
    percent_complete DECIMAL(5,2) DEFAULT 0.00,
    is_finished BOOLEAN DEFAULT FALSE,
    
    -- Download Status
    is_downloaded BOOLEAN DEFAULT FALSE,
    is_playable BOOLEAN DEFAULT FALSE,
    
    -- User Actions
    is_in_wishlist BOOLEAN DEFAULT FALSE,
    user_rating DECIMAL(3,1), -- 1.0 to 5.0
    
    -- Metadata
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
);

-- User's wishlist (books they want to buy)
CREATE TABLE user_wishlists (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    priority INT DEFAULT 0, -- 1=highest, 5=lowest
    notes TEXT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_wishlist (user_id, book_id),
    INDEX idx_user_id (user_id),
    INDEX idx_priority (priority),
    INDEX idx_added_date (added_date)
);

-- User's reading lists (custom collections)
CREATE TABLE user_reading_lists (
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
);

-- Books in user's reading lists
CREATE TABLE user_reading_list_books (
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
);

-- 5. Pricing & Suggestions

-- Price history tracking
CREATE TABLE book_prices (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    marketplace VARCHAR(10) NOT NULL,
    
    -- Price Information (from API price field)
    credit_price DECIMAL(10,2),
    list_price DECIMAL(10,2),
    member_price DECIMAL(10,2),
    currency_code VARCHAR(3) DEFAULT 'USD',
    
    -- Timestamps
    price_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_price_date (book_id, marketplace, price_date),
    INDEX idx_book_id (book_id),
    INDEX idx_price_date (price_date),
    INDEX idx_member_price (member_price)
);

-- Generated recommendations for users
CREATE TABLE user_recommendations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    suggestion_type ENUM('series', 'author', 'narrator', 'similar') NOT NULL,
    source_book_id BIGINT NULL, -- What book/author/narrator triggered this suggestion
    source_name VARCHAR(500), -- Author name, narrator name, or series name
    confidence_score DECIMAL(3,2) DEFAULT 0.50, -- 0.00 to 1.00
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
);

-- Price alerts for wishlist items
CREATE TABLE price_alerts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    target_price DECIMAL(10,2) NOT NULL,
    alert_type ENUM('below', 'percentage_off') DEFAULT 'below',
    percentage_threshold DECIMAL(5,2), -- For percentage-based alerts
    is_active BOOLEAN DEFAULT TRUE,
    last_notified TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_book_id (book_id),
    INDEX idx_target_price (target_price),
    INDEX idx_is_active (is_active)
);

-- 6. Extended Book Data (All 142 Fields)

-- Extended book metadata (stores all remaining fields from API)
CREATE TABLE book_extended_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    book_id BIGINT NOT NULL,
    
    -- Social & Media
    product_images JSON, -- Store image URLs as JSON
    social_media_images JSON,
    rich_images JSON,
    
    -- Review & Rating Data
    customer_reviews JSON,
    goodreads_ratings JSON,
    rating DECIMAL(3,1), -- Overall rating
    
    -- Content Flags & Status
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
    
    -- Dates & Times
    date_first_available DATE,
    preorder_release_date DATE,
    new_episode_added_date DATE,
    product_site_launch_date DATE,
    
    -- IDs & References
    destination_asin VARCHAR(20),
    origin_asin VARCHAR(20),
    origin_id VARCHAR(50),
    origin_marketplace VARCHAR(10),
    origin_type VARCHAR(50),
    ws4v_companion_asin VARCHAR(20),
    
    -- Content Details
    copyright TEXT,
    content_level VARCHAR(50),
    content_rating VARCHAR(50),
    narration_accent VARCHAR(100),
    voice_description TEXT,
    
    -- Series & Episode Data
    episode_count INT,
    episode_number INT,
    episode_type VARCHAR(50),
    season_number INT,
    part_number INT,
    
    -- Technical Data
    available_codecs JSON,
    ws4v_details JSON,
    
    -- URLs & Links
    product_page_url TEXT,
    sample_url TEXT,
    pdf_url TEXT,
    claim_code_url TEXT,
    image_url TEXT,
    
    -- Tags & Keywords
    book_tags JSON,
    tags JSON,
    thesaurus_subject_keywords JSON,
    platinum_keywords JSON,
    long_tail_topic_tags JSON,
    spotlight_tags JSON,
    
    -- Other Data
    generic_keyword VARCHAR(500),
    text_to_speech JSON,
    read_along_support JSON,
    collection_ids JSON,
    subscription_asins JSON,
    music_id VARCHAR(50),
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_extended (book_id)
);

-- 7. System & Analytics

-- Sync job tracking
CREATE TABLE sync_jobs (
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
);

-- Analytics and usage tracking
CREATE TABLE user_analytics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'login', 'search', 'view_book', etc.
    entity_type VARCHAR(50), -- 'book', 'author', 'series', etc.
    entity_id BIGINT,
    metadata JSON, -- Additional context data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
);

-- Insert a test user for development
INSERT INTO users (oauth_provider, oauth_provider_id, display_name) 
VALUES ('test', '1', 'Test User'); 