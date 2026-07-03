#!/usr/bin/env python3
"""
AudiPy Phase 3: Fetch Library
Fetches user's Audible library and stores it in the database
"""

import os
import json
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from rich.progress import Progress, track
from utils.crypto_utils_simple import get_crypto_instance

# Initialize rich console
console = Console()

class LibraryFetcher:
    def __init__(self):
        load_dotenv()
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_NAME', 'audipy'),
            'user': os.getenv('DB_USER', 'audipy'),
            'password': os.getenv('DB_PASSWORD'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # Initialize crypto utilities
        self.crypto = get_crypto_instance()
        
        self.user_id = None
        self.user_preferences = {}
        self.client = None
        self.library_books = []

    def connect_db(self):
        """Connect to database"""
        try:
            self.db = mysql.connector.connect(**self.db_config)
            console.print("[green]✅ Connected to database[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Database connection failed: {e}[/]")
            return False

    def load_user_and_preferences(self):
        """Load user and their preferences"""
        cursor = self.db.cursor()
        
        try:
            # Get user
            cursor.execute("""
                SELECT id, display_name FROM users 
                WHERE oauth_provider = 'test' AND oauth_provider_id = 'test_user_001'
            """)
            
            result = cursor.fetchone()
            if not result:
                console.print("[red]❌ No user found. Please run Phase 1 (authentication) first.[/]")
                return False
            
            self.user_id = result[0]
            console.print(f"[green]✅ Found user: {result[1]} (ID: {self.user_id})[/]")
            
            # Get user preferences
            cursor.execute("""
                SELECT preferred_language, marketplace FROM user_preferences 
                WHERE user_id = %s
            """, (self.user_id,))
            
            prefs = cursor.fetchone()
            if not prefs:
                console.print("[red]❌ No user preferences found. Please run Phase 2 (profile setup) first.[/]")
                return False
            
            self.user_preferences = {
                'language': prefs[0] or 'english',
                'marketplace': prefs[1] or 'us'
            }
            
            console.print(f"[blue]📋 Loaded preferences: {self.user_preferences['language']}, {self.user_preferences['marketplace']}[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Database error loading user: {e}[/]")
            return False
        finally:
            cursor.close()

    def load_audible_client(self):
        """Load and decrypt Audible authentication tokens"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT encrypted_auth_data, marketplace FROM user_audible_accounts 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (self.user_id,))
            
            result = cursor.fetchone()
            if not result:
                console.print("[red]❌ No Audible tokens found. Please run Phase 1 (authentication) first.[/]")
                return False
            
            # Consume any remaining results
            cursor.fetchall()
            
            # Decrypt the authentication data for this user
            encrypted_data = result[0]
            decrypted_json = self.crypto.decrypt_for_user(self.user_id, encrypted_data)
            auth_data = json.loads(decrypted_json)
            
            # Debug: Check token expiration
            expires_timestamp = auth_data.get('expires')
            if expires_timestamp:
                from datetime import datetime
                expires_date = datetime.fromtimestamp(expires_timestamp)
                current_time = datetime.now()
                console.print(f"[dim]Debug: Tokens expire at: {expires_date}[/]")
                console.print(f"[dim]Debug: Current time: {current_time}[/]")
                console.print(f"[dim]Debug: Tokens expired: {current_time > expires_date}[/]")
            
            # Recreate the authenticator from stored data
            auth = Authenticator.from_dict(auth_data)
            
            # Try to refresh tokens if they're expired
            try:
                if expires_timestamp and datetime.now().timestamp() > expires_timestamp:
                    console.print("[yellow]🔄 Tokens expired, attempting refresh...[/]")
                    auth.refresh_access_token()
                    console.print("[green]✅ Tokens refreshed successfully[/]")
            except Exception as refresh_error:
                console.print(f"[yellow]⚠️ Token refresh failed: {refresh_error}[/]")
            
            self.client = Client(auth=auth)
            console.print("[green]✅ Audible client authenticated[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load Audible client: {e}[/]")
            return False
        finally:
            cursor.close()

    def fetch_library(self):
        """Fetch user's library from Audible"""
        console.print("\n[bold blue]📚 Fetching your Audible library...[/]")
        
        try:
            library = self.client.get(
                "1.0/library",
                num_results=1000,
                response_groups="series,contributors,product_desc,media,price,category_ladders"
            )
            
            self.library_books = library.get('items', [])
            console.print(f"[bold green]✅ Found {len(self.library_books)} books in your library![/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch library: {e}[/]")
            return False

    def store_book(self, book_data):
        """Store a single book in the database"""
        cursor = self.db.cursor(buffered=True)
        
        try:
            # Extract basic book information
            asin = book_data.get('asin')
            if not asin:
                return None
            
            # Check language filter
            book_language = book_data.get('language', '').lower()
            if book_language != self.user_preferences['language']:
                return None
            
            # Parse publication datetime
            publication_datetime = self._parse_datetime(book_data.get('publication_datetime'))
            
            # Insert/update book
            cursor.execute("""
                INSERT INTO books (
                    asin, title, subtitle, publisher_name, publication_datetime,
                    language, content_type, runtime_length_min, 
                    merchandising_summary, extended_product_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                subtitle = VALUES(subtitle),
                publisher_name = VALUES(publisher_name),
                publication_datetime = VALUES(publication_datetime),
                language = VALUES(language),
                content_type = VALUES(content_type),
                runtime_length_min = VALUES(runtime_length_min),
                merchandising_summary = VALUES(merchandising_summary),
                extended_product_description = VALUES(extended_product_description),
                updated_at = CURRENT_TIMESTAMP
            """, (
                asin,
                book_data.get('title', ''),
                book_data.get('subtitle'),
                book_data.get('publisher_name'),
                publication_datetime,
                book_language,
                book_data.get('content_type'),
                book_data.get('runtime_length_min'),
                book_data.get('merchandising_summary'),
                book_data.get('extended_product_description')
            ))
            
            # Get book ID
            cursor.execute("SELECT id FROM books WHERE asin = %s", (asin,))
            result = cursor.fetchone()
            book_id = result[0]
            
            # Store authors
            authors = book_data.get('authors', []) or []
            for author in authors:
                author_name = author.get('name')
                if author_name:
                    # Insert/get author
                    cursor.execute("""
                        INSERT INTO authors (name, asin) VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE name = VALUES(name)
                    """, (author_name, author.get('asin')))
                    
                    cursor.execute("SELECT id FROM authors WHERE name = %s", (author_name,))
                    result = cursor.fetchone()
                    author_id = result[0]
                    
                    # Link book to author
                    cursor.execute("""
                        INSERT IGNORE INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                    """, (book_id, author_id))
            
            # Store narrators
            narrators = book_data.get('narrators', []) or []
            for narrator in narrators:
                narrator_name = narrator.get('name')
                if narrator_name:
                    # Insert/get narrator
                    cursor.execute("""
                        INSERT INTO narrators (name, asin) VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE name = VALUES(name)
                    """, (narrator_name, narrator.get('asin')))
                    
                    cursor.execute("SELECT id FROM narrators WHERE name = %s", (narrator_name,))
                    result = cursor.fetchone()
                    narrator_id = result[0]
                    
                    # Link book to narrator
                    cursor.execute("""
                        INSERT IGNORE INTO book_narrators (book_id, narrator_id)
                        VALUES (%s, %s)
                    """, (book_id, narrator_id))
            
            # Store series
            series_list = book_data.get('series', []) or []
            for series in series_list:
                series_title = series.get('title')
                if series_title:
                    # Insert/get series
                    cursor.execute("""
                        INSERT INTO series (title, asin) VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE title = VALUES(title)
                    """, (series_title, series.get('asin')))
                    
                    cursor.execute("SELECT id FROM series WHERE title = %s", (series_title,))
                    result = cursor.fetchone()
                    series_id = result[0]
                    
                    # Link book to series
                    sequence = series.get('sequence')
                    cursor.execute("""
                        INSERT IGNORE INTO book_series (book_id, series_id, sequence, sequence_display)
                        VALUES (%s, %s, %s, %s)
                    """, (book_id, series_id, sequence, str(sequence) if sequence else None))
            
            # Store user library entry
            purchase_date = self._parse_datetime(book_data.get('purchase_date'))
            
            cursor.execute("""
                INSERT INTO user_libraries (
                    user_id, book_id, purchase_date, 
                    percent_complete, is_finished
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                purchase_date = VALUES(purchase_date),
                percent_complete = VALUES(percent_complete),
                is_finished = VALUES(is_finished),
                updated_at = CURRENT_TIMESTAMP
            """, (
                self.user_id,
                book_id,
                purchase_date,
                book_data.get('percent_complete', 0),
                book_data.get('is_finished', False)
            ))
            
            return book_id
            
        except Exception as e:
            console.print(f"[red]❌ Error storing book {asin}: {e}[/]")
            return None
        finally:
            cursor.close()

    def _parse_datetime(self, datetime_str):
        """Parse datetime string from Audible API to MySQL-compatible format"""
        if not datetime_str:
            return None
        
        try:
            # Handle ISO format with 'Z' timezone suffix
            if isinstance(datetime_str, str):
                # Replace 'Z' with '+00:00' for proper ISO parsing
                if datetime_str.endswith('Z'):
                    datetime_str = datetime_str[:-1] + '+00:00'
                
                # Parse the datetime
                from datetime import datetime
                dt = datetime.fromisoformat(datetime_str)
                
                # Return in MySQL-compatible format (without timezone info)
                return dt.replace(tzinfo=None)
            
            return datetime_str
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to parse datetime '{datetime_str}': {e}[/]")
            return None

    def store_library(self):
        """Store all library books in database"""
        console.print(f"\n[bold blue]💾 Storing {len(self.library_books)} books in database...[/]")
        
        stored_count = 0
        skipped_count = 0
        
        for book in track(self.library_books, description="Processing books..."):
            book_id = self.store_book(book)
            if book_id:
                stored_count += 1
            else:
                skipped_count += 1
        
        console.print(f"[green]✅ Stored {stored_count} books[/]")
        if skipped_count > 0:
            console.print(f"[yellow]⚠️  Skipped {skipped_count} books (language filter or errors)[/]")
        
        return stored_count > 0

    def update_sync_status(self, status='completed'):
        """Update the sync status in user_audible_accounts"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                UPDATE user_audible_accounts 
                SET sync_status = %s, last_sync = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (status, self.user_id))
            
        except Exception as e:
            console.print(f"[red]❌ Failed to update sync status: {e}[/]")
        finally:
            cursor.close()

    def display_library_stats(self):
        """Display library statistics"""
        cursor = self.db.cursor()
        
        try:
            # Get counts
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ul.book_id) as total_books,
                    COUNT(DISTINCT ba.author_id) as total_authors,
                    COUNT(DISTINCT bn.narrator_id) as total_narrators,
                    COUNT(DISTINCT bs.series_id) as total_series
                FROM user_libraries ul
                LEFT JOIN book_authors ba ON ul.book_id = ba.book_id
                LEFT JOIN book_narrators bn ON ul.book_id = bn.book_id
                LEFT JOIN book_series bs ON ul.book_id = bs.book_id
                WHERE ul.user_id = %s
            """, (self.user_id,))
            
            stats = cursor.fetchone()
            
            console.print("\n[bold green]📊 Library Statistics[/]")
            console.print(f"[cyan]📚 Total Books:[/] {stats[0]}")
            console.print(f"[cyan]👨‍💼 Unique Authors:[/] {stats[1]}")
            console.print(f"[cyan]🎙️ Unique Narrators:[/] {stats[2]}")
            console.print(f"[cyan]📖 Series:[/] {stats[3]}")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get library stats: {e}[/]")
        finally:
            cursor.close()

    def run(self):
        """Main library fetching flow"""
        console.print("[bold cyan]📚 AudiPy Phase 3: Fetch Library[/]")
        console.print("[dim]Fetching your Audible library and storing in database[/]\n")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Load user and preferences
        if not self.load_user_and_preferences():
            return False
        
        # Load Audible client
        if not self.load_audible_client():
            return False
        
        # Fetch library
        if not self.fetch_library():
            self.update_sync_status('failed')
            return False
        
        # Store library in database
        if not self.store_library():
            self.update_sync_status('failed')
            return False
        
        # Update sync status
        self.update_sync_status('completed')
        
        # Display statistics
        self.display_library_stats()
        
        console.print("\n[bold green]🎉 Phase 3 Complete![/]")
        console.print("[green]✅ Library fetched successfully[/]")
        console.print("[green]✅ Books stored in database[/]")
        console.print("[green]✅ Authors, narrators, and series cataloged[/]")
        console.print("\n[dim]You can now run Phase 4 to generate recommendations[/]")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch Audible library for a user')
    parser.add_argument('--user-id', type=int, help='User ID to fetch library for')
    args = parser.parse_args()
    
    fetcher = LibraryFetcher()
    
    # If user ID is provided, override the default user lookup
    if args.user_id:
        fetcher.user_id = args.user_id
        console.print(f"[blue]📋 Using provided user ID: {args.user_id}[/]")
        
        # Skip the user lookup and load preferences directly
        if not fetcher.connect_db():
            exit(1)
            
        # Load preferences for the specified user
        cursor = fetcher.db.cursor()
        try:
            cursor.execute("""
                SELECT preferred_language, marketplace FROM user_preferences 
                WHERE user_id = %s
            """, (args.user_id,))
            
            prefs = cursor.fetchone()
            if prefs:
                fetcher.user_preferences = {
                    'language': prefs[0] or 'english',
                    'marketplace': prefs[1] or 'us'
                }
                console.print(f"[blue]📋 Loaded preferences: {fetcher.user_preferences['language']}, {fetcher.user_preferences['marketplace']}[/]")
            else:
                # Use defaults if no preferences found
                fetcher.user_preferences = {
                    'language': 'english',
                    'marketplace': 'us'
                }
                console.print(f"[yellow]⚠️ No preferences found for user {args.user_id}, using defaults[/]")
                
        except Exception as e:
            console.print(f"[red]❌ Failed to load preferences for user {args.user_id}: {e}[/]")
            exit(1)
        finally:
            cursor.close()
        
        # Load Audible client
        if not fetcher.load_audible_client():
            exit(1)
        
        # Fetch library
        if not fetcher.fetch_library():
            fetcher.update_sync_status('failed')
            exit(1)
        
        # Store library in database
        if not fetcher.store_library():
            fetcher.update_sync_status('failed')
            exit(1)
        
        # Update sync status
        fetcher.update_sync_status('completed')
        
        # Display statistics
        fetcher.display_library_stats()
        
        console.print("\n[bold green]🎉 Phase 3 Complete![/]")
        console.print("[green]✅ Library fetched successfully[/]")
        console.print("[green]✅ Books stored in database[/]")
        console.print("[green]✅ Authors, narrators, and series cataloged[/]")
        
    else:
        # Run the normal flow for interactive use
        success = fetcher.run()
        
        if not success:
            console.print("\n[red]❌ Library fetch failed. Please check the errors above.[/]")
            exit(1)

if __name__ == "__main__":
    main() 