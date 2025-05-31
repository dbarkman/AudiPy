#!/usr/bin/env python3
"""
AudiPy Phase 4: Generate Recommendations
Generates static recommendations based on user's library and stores them in database
"""

import os
import json
import mysql.connector
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table
from utils.crypto_utils_simple import get_crypto_instance

# Initialize rich console
console = Console()

class RecommendationGenerator:
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
        self.user_books = set()  # ASINs of books user owns
        self.user_titles = set()  # Titles of books user owns (for duplicate detection)
        
        # Recommendation limits for testing
        self.limits = {
            'authors': 5,
            'narrators': 5,
            'series': 5
        }

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
            # Get first available user (for testing - later this will be passed as parameter)
            cursor.execute("""
                SELECT u.id, u.display_name FROM users u
                JOIN user_audible_accounts uaa ON u.id = uaa.user_id
                WHERE u.oauth_provider = 'audible' 
                ORDER BY u.created_at DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if not result:
                console.print("[red]❌ No user found. Please run Phase 1 (authentication) first.[/]")
                return False
            
            self.user_id = result[0]
            console.print(f"[green]✅ Found user: {result[1]} (ID: {self.user_id})[/]")
            
            # Get user preferences (create default if not exists)
            cursor.execute("""
                SELECT preferred_language, marketplace, max_price FROM user_preferences 
                WHERE user_id = %s
            """, (self.user_id,))
            
            prefs = cursor.fetchone()
            if not prefs:
                console.print("[yellow]⚠️ No user preferences found. Creating defaults...[/]")
                # Create default preferences
                cursor.execute("""
                    INSERT INTO user_preferences (user_id, preferred_language, marketplace, max_price)
                    VALUES (%s, 'english', 'us', 12.66)
                    ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
                """, (self.user_id,))
                
                self.user_preferences = {
                    'language': 'english',
                    'marketplace': 'us', 
                    'max_price': 12.66
                }
            else:
                self.user_preferences = {
                    'language': prefs[0] or 'english',
                    'marketplace': prefs[1] or 'us',
                    'max_price': float(prefs[2]) if prefs[2] else 12.66
                }
            
            console.print(f"[blue]📋 Loaded preferences: {self.user_preferences}[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Database error loading user: {e}[/]")
            return False
        finally:
            cursor.close()

    def load_audible_client(self):
        """Load and decrypt Audible authentication tokens"""
        cursor = self.db.cursor(buffered=True)
        
        try:
            cursor.execute("""
                SELECT encrypted_auth_data FROM user_audible_accounts 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (self.user_id,))
            
            result = cursor.fetchone()
            if not result:
                console.print("[red]❌ No Audible tokens found. Please run Phase 1 (authentication) first.[/]")
                return False
            
            # Decrypt the authentication data for this user
            encrypted_data = result[0]
            decrypted_json = self.crypto.decrypt_for_user(self.user_id, encrypted_data)
            auth_data = json.loads(decrypted_json)
            
            # Recreate the authenticator from stored data
            auth = Authenticator.from_dict(auth_data)
            
            self.client = Client(auth=auth)
            console.print("[green]✅ Audible client authenticated[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load Audible client: {e}[/]")
            return False
        finally:
            cursor.close()

    def load_user_library(self):
        """Load user's existing library for duplicate detection"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT b.asin, b.title 
                FROM user_libraries ul
                JOIN books b ON ul.book_id = b.id
                WHERE ul.user_id = %s
            """, (self.user_id,))
            
            results = cursor.fetchall()
            
            self.user_books = {row[0] for row in results if row[0]}
            self.user_titles = {row[1].lower().strip() for row in results if row[1]}
            
            console.print(f"[blue]📚 Loaded {len(self.user_books)} owned books for duplicate detection[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load user library: {e}[/]")
            return False
        finally:
            cursor.close()

    def get_user_authors(self):
        """Get top authors from user's library"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT a.name, COUNT(*) as book_count
                FROM user_libraries ul
                JOIN book_authors ba ON ul.book_id = ba.book_id
                JOIN authors a ON ba.author_id = a.id
                WHERE ul.user_id = %s
                GROUP BY a.id, a.name
                ORDER BY book_count DESC, a.name
                LIMIT %s
            """, (self.user_id, self.limits['authors']))
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get user authors: {e}[/]")
            return []
        finally:
            cursor.close()

    def get_user_narrators(self):
        """Get top narrators from user's library"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT n.name, COUNT(*) as book_count
                FROM user_libraries ul
                JOIN book_narrators bn ON ul.book_id = bn.book_id
                JOIN narrators n ON bn.narrator_id = n.id
                WHERE ul.user_id = %s
                GROUP BY n.id, n.name
                ORDER BY book_count DESC, n.name
                LIMIT %s
            """, (self.user_id, self.limits['narrators']))
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get user narrators: {e}[/]")
            return []
        finally:
            cursor.close()

    def get_user_series(self):
        """Get series from user's library"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT s.title, COUNT(*) as book_count
                FROM user_libraries ul
                JOIN book_series bs ON ul.book_id = bs.book_id
                JOIN series s ON bs.series_id = s.id
                WHERE ul.user_id = %s
                GROUP BY s.id, s.title
                ORDER BY book_count DESC, s.title
                LIMIT %s
            """, (self.user_id, self.limits['series']))
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get user series: {e}[/]")
            return []
        finally:
            cursor.close()

    def search_books_by_author(self, author_name):
        """Search for books by a specific author"""
        try:
            results = self.client.get(
                "1.0/catalog/products",
                author=author_name,
                num_results=50,
                response_groups="contributors,product_desc,media,price"
            )
            
            return results.get('products', []) if results else []
            
        except Exception as e:
            console.print(f"[red]❌ Failed to search books by {author_name}: {e}[/]")
            return []

    def search_books_by_narrator(self, narrator_name):
        """Search for books by a specific narrator"""
        try:
            results = self.client.get(
                "1.0/catalog/products",
                narrator=narrator_name,
                num_results=50,
                response_groups="contributors,product_desc,media,price"
            )
            
            return results.get('products', []) if results else []
            
        except Exception as e:
            console.print(f"[red]❌ Failed to search books by narrator {narrator_name}: {e}[/]")
            return []

    def search_books_in_series(self, series_name):
        """Search for books in a specific series"""
        try:
            results = self.client.get(
                "1.0/catalog/products",
                title=series_name,
                num_results=50,
                response_groups="series,contributors,product_desc,media,price"
            )
            
            # Filter to only books that are actually in the series
            series_books = []
            for book in results.get('products', []):
                book_series = book.get('series', []) or []
                for series in book_series:
                    if series.get('title', '').lower() == series_name.lower():
                        series_books.append(book)
                        break
            
            return series_books
            
        except Exception as e:
            console.print(f"[red]❌ Failed to search books in series {series_name}: {e}[/]")
            return []

    def is_book_owned(self, book):
        """Check if user already owns this book"""
        asin = book.get('asin')
        title = book.get('title', '').lower().strip()
        
        # Check ASIN match
        if asin and asin in self.user_books:
            return True
        
        # Check title match
        if title and title in self.user_titles:
            return True
        
        return False

    def calculate_confidence_score(self, recommendation_type, source_name):
        """Calculate confidence score for recommendation"""
        # For testing, use simple confidence scores
        if recommendation_type == 'series':
            return 1.0  # High confidence for series continuations
        elif recommendation_type == 'author':
            return 0.8  # Good confidence for favorite authors
        elif recommendation_type == 'narrator':
            return 0.6  # Medium confidence for narrators
        else:
            return 0.5

    def store_book_if_needed(self, book_data):
        """Store book in database if it doesn't exist, return book_id"""
        cursor = self.db.cursor()
        
        try:
            asin = book_data.get('asin')
            if not asin:
                return None
            
            # Check if book exists
            cursor.execute("SELECT id FROM books WHERE asin = %s", (asin,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Insert new book
            cursor.execute("""
                INSERT INTO books (
                    asin, title, subtitle, publisher_name,
                    language, content_type, runtime_length_min,
                    merchandising_summary, extended_product_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                asin,
                book_data.get('title', ''),
                book_data.get('subtitle'),
                book_data.get('publisher_name'),
                book_data.get('language', '').lower(),
                book_data.get('content_type'),
                book_data.get('runtime_length_min'),
                book_data.get('merchandising_summary'),
                book_data.get('extended_product_description')
            ))
            
            # Get the new book ID
            cursor.execute("SELECT id FROM books WHERE asin = %s", (asin,))
            return cursor.fetchone()[0]
            
        except Exception as e:
            console.print(f"[red]❌ Error storing book {asin}: {e}[/]")
            return None
        finally:
            cursor.close()

    def store_recommendation(self, book_asin, recommendation_type, source_name, confidence_score, price):
        """Store a recommendation in the database"""
        cursor = self.db.cursor()
        
        try:
            # Get book_id
            cursor.execute("SELECT id FROM books WHERE asin = %s", (book_asin,))
            result = cursor.fetchone()
            if not result:
                return False
            
            book_id = result[0]
            
            # Determine purchase method
            purchase_method = "cash" if price and price < self.user_preferences['max_price'] else "credits"
            
            # Store recommendation
            cursor.execute("""
                INSERT INTO user_recommendations (
                    user_id, book_id, suggestion_type, source_name,
                    confidence_score, purchase_method
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                confidence_score = VALUES(confidence_score),
                purchase_method = VALUES(purchase_method),
                generated_at = CURRENT_TIMESTAMP
            """, (
                self.user_id, book_id, recommendation_type, source_name,
                confidence_score, purchase_method
            ))
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error storing recommendation: {e}[/]")
            return False
        finally:
            cursor.close()

    def generate_author_recommendations(self, authors):
        """Generate recommendations based on user's favorite authors"""
        console.print(f"\n[bold blue]👨‍💼 Generating author recommendations for {len(authors)} authors...[/]")
        
        recommendations = []
        
        for author_name in track(authors, description="Processing authors..."):
            console.print(f"[blue]Searching books by: {author_name}[/]")
            
            books = self.search_books_by_author(author_name)
            found_count = 0
            
            for book in books:
                # Check language filter
                book_language = book.get('language', '').lower()
                if book_language != self.user_preferences['language']:
                    continue
                
                # Check if user already owns this book
                if self.is_book_owned(book):
                    continue
                
                # Verify this book is actually by the author we're searching for
                book_authors = book.get('authors', []) or []
                author_match = any(author.get('name', '').lower() == author_name.lower() for author in book_authors)
                
                if not author_match:
                    continue
                
                # Store book and recommendation
                book_id = self.store_book_if_needed(book)
                if book_id:
                    # Extract price
                    price_info = book.get('price', {})
                    member_price = None
                    if price_info and 'lowest_price' in price_info:
                        lowest_price = price_info['lowest_price']
                        if lowest_price.get('type') == 'member':
                            member_price = lowest_price.get('base')
                    
                    confidence = self.calculate_confidence_score('author', author_name)
                    
                    if self.store_recommendation(book.get('asin'), 'author', author_name, confidence, member_price):
                        recommendations.append({
                            'title': book.get('title'),
                            'author': author_name,
                            'price': member_price
                        })
                        found_count += 1
            
            console.print(f"[green]  Found {found_count} new books by {author_name}[/]")
        
        return recommendations

    def generate_narrator_recommendations(self, narrators):
        """Generate recommendations based on user's favorite narrators"""
        console.print(f"\n[bold blue]🎙️ Generating narrator recommendations for {len(narrators)} narrators...[/]")
        
        recommendations = []
        
        for narrator_name in track(narrators, description="Processing narrators..."):
            console.print(f"[blue]Searching books by narrator: {narrator_name}[/]")
            
            books = self.search_books_by_narrator(narrator_name)
            found_count = 0
            
            for book in books:
                # Check language filter
                book_language = book.get('language', '').lower()
                if book_language != self.user_preferences['language']:
                    continue
                
                # Check if user already owns this book
                if self.is_book_owned(book):
                    continue
                
                # Verify this book is actually narrated by the narrator we're searching for
                book_narrators = book.get('narrators', []) or []
                narrator_match = any(narrator.get('name', '').lower() == narrator_name.lower() for narrator in book_narrators)
                
                if not narrator_match:
                    continue
                
                # Store book and recommendation
                book_id = self.store_book_if_needed(book)
                if book_id:
                    # Extract price
                    price_info = book.get('price', {})
                    member_price = None
                    if price_info and 'lowest_price' in price_info:
                        lowest_price = price_info['lowest_price']
                        if lowest_price.get('type') == 'member':
                            member_price = lowest_price.get('base')
                    
                    confidence = self.calculate_confidence_score('narrator', narrator_name)
                    
                    if self.store_recommendation(book.get('asin'), 'narrator', narrator_name, confidence, member_price):
                        recommendations.append({
                            'title': book.get('title'),
                            'narrator': narrator_name,
                            'price': member_price
                        })
                        found_count += 1
            
            console.print(f"[green]  Found {found_count} new books by narrator {narrator_name}[/]")
        
        return recommendations

    def generate_series_recommendations(self, series_list):
        """Generate recommendations based on user's series"""
        console.print(f"\n[bold blue]📖 Generating series recommendations for {len(series_list)} series...[/]")
        
        recommendations = []
        
        for series_name in track(series_list, description="Processing series..."):
            console.print(f"[blue]Searching books in series: {series_name}[/]")
            
            books = self.search_books_in_series(series_name)
            found_count = 0
            
            for book in books:
                # Check language filter
                book_language = book.get('language', '').lower()
                if book_language != self.user_preferences['language']:
                    continue
                
                # Check if user already owns this book
                if self.is_book_owned(book):
                    continue
                
                # Store book and recommendation
                book_id = self.store_book_if_needed(book)
                if book_id:
                    # Extract price
                    price_info = book.get('price', {})
                    member_price = None
                    if price_info and 'lowest_price' in price_info:
                        lowest_price = price_info['lowest_price']
                        if lowest_price.get('type') == 'member':
                            member_price = lowest_price.get('base')
                    
                    confidence = self.calculate_confidence_score('series', series_name)
                    
                    if self.store_recommendation(book.get('asin'), 'series', series_name, confidence, member_price):
                        recommendations.append({
                            'title': book.get('title'),
                            'series': series_name,
                            'price': member_price
                        })
                        found_count += 1
            
            console.print(f"[green]  Found {found_count} new books in {series_name}[/]")
        
        return recommendations

    def display_recommendation_summary(self):
        """Display summary of generated recommendations"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    suggestion_type,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM user_recommendations 
                WHERE user_id = %s
                GROUP BY suggestion_type
                ORDER BY count DESC
            """, (self.user_id,))
            
            results = cursor.fetchall()
            
            table = Table(title="Recommendation Summary")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="green")
            table.add_column("Avg Confidence", style="yellow")
            
            total_recommendations = 0
            for row in results:
                table.add_row(
                    row[0].title(),
                    str(row[1]),
                    f"{row[2]:.2f}"
                )
                total_recommendations += row[1]
            
            console.print(f"\n[bold green]📊 Generated {total_recommendations} total recommendations[/]")
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get recommendation summary: {e}[/]")
        finally:
            cursor.close()

    def run(self):
        """Main recommendation generation flow"""
        console.print("[bold cyan]🎯 AudiPy Phase 4: Generate Recommendations[/]")
        console.print("[dim]Generating static recommendations based on your library[/]\n")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Load user and preferences
        if not self.load_user_and_preferences():
            return False
        
        # Load Audible client
        if not self.load_audible_client():
            return False
        
        # Load user's existing library
        if not self.load_user_library():
            return False
        
        # Get user's favorite authors, narrators, and series
        authors = self.get_user_authors()
        narrators = self.get_user_narrators()
        series_list = self.get_user_series()
        
        console.print(f"[blue]📋 Found {len(authors)} authors, {len(narrators)} narrators, {len(series_list)} series[/]")
        
        # Generate recommendations
        author_recs = self.generate_author_recommendations(authors)
        narrator_recs = self.generate_narrator_recommendations(narrators)
        series_recs = self.generate_series_recommendations(series_list)
        
        # Display summary
        self.display_recommendation_summary()
        
        console.print("\n[bold green]🎉 Phase 4 Complete![/]")
        console.print("[green]✅ Static recommendations generated[/]")
        console.print("[green]✅ Recommendations stored in database[/]")
        console.print("[green]✅ Ready for web interface integration[/]")
        
        return True

def main():
    generator = RecommendationGenerator()
    success = generator.run()
    
    if not success:
        console.print("\n[red]❌ Recommendation generation failed. Please check the errors above.[/]")
        exit(1)

if __name__ == "__main__":
    main() 