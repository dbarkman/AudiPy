#!/usr/bin/env python3

import os
import json
import getpass
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
import asyncio

# Initialize rich console
console = Console()

class AudibleLibraryAnalyzer:
    def __init__(self):
        # Load .env for optional settings only (not credentials)
        load_dotenv()
        
        # Get optional settings from .env (with defaults)
        self.marketplace = os.getenv('AUDIBLE_MARKETPLACE', 'us')
        self.max_price = float(os.getenv('MAX_PRICE', '12.66'))
        self.language = os.getenv('LANGUAGE', 'english').lower()
        
        # Credentials will be prompted for (not from .env)
        self.username = None
        self.password = None
        
        # Token cache file path
        self.auth_cache_file = Path('.audible_auth_cache')
        
        self.auth = None
        self.client = None
        self.library = {}
        self.series = {}
        self.authors = {}
        self.narrators = {}
        self.suggestions = {
            'series': {},
            'authors': {},
            'narrators': {}
        }
        
        # Create reports directory if it doesn't exist
        Path('reports').mkdir(exist_ok=True)

    def get_credentials(self):
        """Prompt user for Amazon/Audible credentials"""
        console.print(Panel.fit(
            "[bold green]🔐 AudiPy - Audible Library Analyzer[/]\n\n"
            "[yellow]This tool will analyze your Audible library and find book suggestions[/]\n"
            "[yellow]based on your existing series, authors, and narrators.[/]\n\n"
            "[blue]Please enter your Amazon/Audible credentials to continue.[/]",
            title="Welcome to AudiPy"
        ))
        
        console.print("\n[bold blue]📝 Amazon/Audible Credentials:[/]")
        
        # Get username/email
        self.username = input("Email/Username: ").strip()
        if not self.username:
            raise ValueError("Username/email is required")
        
        # Get password (hidden input)
        self.password = getpass.getpass("Password: ")
        if not self.password:
            raise ValueError("Password is required")
        
        # Get marketplace (with default)
        console.print(f"\n[blue]Marketplace options: us, uk, de, fr, ca, au, in, it, es, jp[/]")
        marketplace_input = input(f"Marketplace [{self.marketplace}]: ").strip().lower()
        if marketplace_input:
            self.marketplace = marketplace_input
        
        console.print(f"[dim]Using marketplace: {self.marketplace}[/]")

    def authenticate(self):
        """Authenticate with Audible using cached tokens when possible"""
        
        # Try to load cached authentication first
        if self.auth_cache_file.exists():
            console.print("[bold blue]Attempting to use cached authentication...[/]")
            try:
                auth = Authenticator.from_file(str(self.auth_cache_file))
                
                # Check if access token is still valid
                if not auth.access_token_expired:
                    console.print("[bold green]✅ Using cached authentication (no OTP needed)![/]")
                    self.auth = auth
                    self.client = Client(auth=auth)
                    return
                else:
                    console.print("[yellow]🔄 Access token expired, refreshing...[/]")
                    try:
                        # Try to refresh the access token
                        auth.refresh_access_token()
                        console.print("[bold green]✅ Token refreshed successfully (no OTP needed)![/]")
                        self.auth = auth
                        self.client = Client(auth=auth)
                        
                        # Save refreshed token
                        auth.to_file(str(self.auth_cache_file), encryption=False)
                        console.print("[dim]💾 Updated cached authentication[/]")
                        return
                    except Exception as refresh_error:
                        console.print(f"[yellow]⚠️ Token refresh failed: {refresh_error}[/]")
                        console.print("[blue]🔑 Fresh login required...[/]")
                        
            except Exception as cache_error:
                console.print(f"[yellow]⚠️ Cached auth failed: {cache_error}[/]")
                console.print("[blue]🔑 Fresh login required...[/]")
        
        # Fresh authentication required - get credentials if we don't have them
        if not self.username or not self.password:
            self.get_credentials()
        
        console.print(f"\n[bold blue]🔑 Authenticating with Audible ({self.marketplace})...[/]")
        
        try:
            # Create the authenticator using the credentials
            auth = Authenticator.from_login(
                username=self.username,
                password=self.password,
                locale=self.marketplace
            )
            
            self.auth = auth
            self.client = Client(auth=auth)
            
            # Save authentication for future use
            auth.to_file(str(self.auth_cache_file), encryption=False)
            console.print("[bold green]✅ Authentication successful and cached![/]")
            console.print(f"[dim]💾 Saved to: {self.auth_cache_file}[/]")
            console.print(f"[dim]⏰ Access token expires: {auth.access_token_expires}[/]")
            
            # Clear credentials from memory for security
            self.username = None
            self.password = None
            
        except Exception as e:
            if "OTP" in str(e) or "captcha" in str(e).lower():
                # If OTP is required, prompt for it
                console.print("[yellow]📱 OTP code required...[/]")
                console.print("[dim]Check your phone/email for the 6-digit code from Amazon[/]")
                otp = input("OTP Code: ").strip()
                
                if not otp:
                    raise ValueError("OTP code is required")
                
                # Retry authentication with OTP
                auth = Authenticator.from_login(
                    username=self.username,
                    password=self.password,
                    locale=self.marketplace,
                    otp_code=otp
                )
                self.auth = auth
                self.client = Client(auth=auth)
                
                # Save authentication for future use
                auth.to_file(str(self.auth_cache_file), encryption=False)
                console.print("[bold green]✅ Authentication successful and cached![/]")
                console.print(f"[dim]💾 Saved to: {self.auth_cache_file}[/]")
                console.print(f"[dim]⏰ Access token expires: {auth.access_token_expires}[/]")
                
                # Clear credentials from memory for security
                self.username = None
                self.password = None
            else:
                # Clear credentials from memory even on error
                self.username = None
                self.password = None
                raise e

    def show_auth_status(self):
        """Display current authentication status"""
        if self.auth:
            console.print("\n[bold blue]🔐 Authentication Status:[/]")
            console.print(f"[green]✅ Authenticated as: {self.auth.user_name if hasattr(self.auth, 'user_name') else 'Unknown User'}[/]")
            console.print(f"[blue]🌍 Marketplace: {self.auth.locale.domain}[/]")
            
            if hasattr(self.auth, 'access_token_expires'):
                if self.auth.access_token_expired:
                    console.print(f"[red]⚠️ Access token: EXPIRED[/]")
                else:
                    console.print(f"[green]⏰ Access token expires: {self.auth.access_token_expires}[/]")
            
            console.print(f"[dim]💾 Cache file: {self.auth_cache_file}[/]")
            console.print()

    def clear_auth_cache(self):
        """Clear the authentication cache (force fresh login next time)"""
        if self.auth_cache_file.exists():
            self.auth_cache_file.unlink()
            console.print("[yellow]🗑️ Authentication cache cleared[/]")
        else:
            console.print("[dim]ℹ️ No authentication cache to clear[/]")

    def fetch_library(self):
        """Fetch user's library"""
        console.print("[bold blue]Fetching your library...[/]")
        library = self.client.get(
            "1.0/library",
            num_results=1000,
            response_groups="series,contributors,product_desc,media,price"
        )
        
        self.library = library.get('items', [])
        console.print(f"[bold green]Found {len(self.library)} books in your library![/]")

    def analyze_library(self):
        """Analyze library and organize by series, authors, and narrators"""
        console.print("[bold blue]Analyzing your library...[/]")
        
        for book in self.library:
            # Extract basic info
            title = book.get('title', 'Unknown Title')
            asin = book.get('asin')
            
            # Process series (if available)
            series = book.get('series', []) or []
            for s in series:
                series_name = s.get('title', 'Unknown Series')
                if series_name not in self.series:
                    self.series[series_name] = []
                self.series[series_name].append({
                    'title': title,
                    'asin': asin,
                    'position': s.get('sequence', 0)
                })
            
            # Process authors (if available)
            authors = book.get('authors', []) or []
            for author in authors:
                author_name = author.get('name', 'Unknown Author')
                if author_name not in self.authors:
                    self.authors[author_name] = []
                self.authors[author_name].append({
                    'title': title,
                    'asin': asin
                })
            
            # Process narrators (if available)
            narrators = book.get('narrators', []) or []
            for narrator in narrators:
                narrator_name = narrator.get('name', 'Unknown Narrator')
                if narrator_name not in self.narrators:
                    self.narrators[narrator_name] = []
                self.narrators[narrator_name].append({
                    'title': title,
                    'asin': asin
                })

    def find_suggestions(self):
        """Find book suggestions based on series, authors, and narrators"""
        console.print("[bold blue]Finding book suggestions...[/]")
        
        # Get user's book ASINs for comparison
        user_books = {book.get('asin') for book in self.library if book.get('asin')}
        console.print(f"[dim]User library contains {len(user_books)} books with ASINs[/]")
        
        # Also get user book titles for additional filtering
        user_titles = {book.get('title', '').lower().strip() for book in self.library if book.get('title')}
        console.print(f"[dim]User library contains {len(user_titles)} book titles[/]")
        
        # Search for books by authors
        console.print("[yellow]Searching by authors...[/]")
        author_count = 0
        for author_name in sorted(self.authors.keys()):  # Search all authors, sorted alphabetically
            author_count += 1
            if author_count > 50:  # Reasonable limit to avoid overwhelming the API
                console.print(f"[dim]Stopping author search at {author_count-1} authors to avoid API limits[/]")
                break
                
            try:
                console.print(f"[blue]Searching for books by: {author_name} ({author_count}/{min(50, len(self.authors))})[/]")
                
                results = self.client.get(
                    "1.0/catalog/products",
                    author=author_name,
                    num_results=50,  # Fixed: API max is 50 per page
                    response_groups="contributors,product_desc,media,price"
                )
                
                if results and 'products' in results and results['products']:
                    found_suggestions = 0
                    filtered_out = 0
                    for book in results['products']:
                        asin = book.get('asin')
                        title = book.get('title', '').lower().strip()
                        
                        # Check if this book is actually by the author we're searching for
                        book_authors = book.get('authors', []) or []
                        author_match = any(author.get('name', '').lower() == author_name.lower() for author in book_authors)
                        
                        if author_match:
                            # Check language filter
                            book_language = book.get('language', '').lower()
                            if book_language != self.language:
                                continue
                            
                            # Enhanced filtering - check both ASIN and title
                            already_owned = False
                            if asin and asin in user_books:
                                already_owned = True
                                filtered_out += 1
                            elif title and title in user_titles:
                                already_owned = True
                                filtered_out += 1
                            
                            if not already_owned:
                                # Extract member price correctly
                                price_info = book.get('price', {})
                                member_price = None
                                
                                if price_info and 'lowest_price' in price_info:
                                    lowest_price = price_info['lowest_price']
                                    if lowest_price.get('type') == 'member':
                                        member_price = lowest_price.get('base')
                                
                                # Determine purchase recommendation
                                purchase_method = "credits"
                                recommendation = "🎫"
                                if member_price and member_price < self.max_price:
                                    purchase_method = "cash"
                                    recommendation = "💰"
                                
                                self.suggestions['authors'][author_name] = self.suggestions['authors'].get(author_name, [])
                                self.suggestions['authors'][author_name].append({
                                    'title': book.get('title', 'Unknown Title'),
                                    'asin': asin,
                                    'price': member_price,
                                    'purchase_method': purchase_method,
                                    'recommendation': recommendation
                                })
                                found_suggestions += 1
                    
                    if found_suggestions > 0 or filtered_out > 0:
                        console.print(f"[green]  → Found {found_suggestions} new books, filtered out {filtered_out} owned[/]")
                        
            except Exception as e:
                console.print(f"[red]Error searching for {author_name}: {e}[/]")
                continue
        
        # Search for books by narrators
        console.print("[yellow]Searching by narrators...[/]")
        narrator_count = 0
        for narrator_name in sorted(self.narrators.keys()):
            narrator_count += 1
            if narrator_count > 50:  # Reasonable limit
                console.print(f"[dim]Stopping narrator search at {narrator_count-1} narrators to avoid API limits[/]")
                break
                
            try:
                console.print(f"[blue]Searching for books narrated by: {narrator_name} ({narrator_count}/{min(50, len(self.narrators))})[/]")
                
                results = self.client.get(
                    "1.0/catalog/products",
                    narrator=narrator_name,
                    num_results=50,  # Fixed: API max is 50 per page
                    response_groups="contributors,product_desc,media,price"
                )
                
                if results and 'products' in results and results['products']:
                    found_suggestions = 0
                    filtered_out = 0
                    for book in results['products']:
                        asin = book.get('asin')
                        title = book.get('title', '').lower().strip()
                        
                        # Check if this book is actually narrated by the narrator we're searching for
                        book_narrators = book.get('narrators', []) or []
                        narrator_match = any(narrator.get('name', '').lower() == narrator_name.lower() for narrator in book_narrators)
                        
                        if narrator_match:
                            # Check language filter
                            book_language = book.get('language', '').lower()
                            if book_language != self.language:
                                continue
                            
                            # Enhanced filtering - check both ASIN and title
                            already_owned = False
                            if asin and asin in user_books:
                                already_owned = True
                                filtered_out += 1
                            elif title and title in user_titles:
                                already_owned = True
                                filtered_out += 1
                            
                            if not already_owned:
                                # Extract member price correctly
                                price_info = book.get('price', {})
                                member_price = None
                                
                                if price_info and 'lowest_price' in price_info:
                                    lowest_price = price_info['lowest_price']
                                    if lowest_price.get('type') == 'member':
                                        member_price = lowest_price.get('base')
                                
                                # Determine purchase recommendation
                                purchase_method = "credits"
                                recommendation = "🎫"
                                if member_price and member_price < self.max_price:
                                    purchase_method = "cash"
                                    recommendation = "💰"
                                
                                self.suggestions['narrators'][narrator_name] = self.suggestions['narrators'].get(narrator_name, [])
                                self.suggestions['narrators'][narrator_name].append({
                                    'title': book.get('title', 'Unknown Title'),
                                    'asin': asin,
                                    'price': member_price,
                                    'purchase_method': purchase_method,
                                    'recommendation': recommendation
                                })
                                found_suggestions += 1
                    
                    if found_suggestions > 0 or filtered_out > 0:
                        console.print(f"[green]  → Found {found_suggestions} new books, filtered out {filtered_out} owned[/]")
                        
            except Exception as e:
                console.print(f"[red]Error searching for {narrator_name}: {e}[/]")
                continue
        
        # Search for missing books in series
        console.print("[yellow]Searching for missing books in your series...[/]")
        series_count = 0
        for series_name in sorted(self.series.keys()):
            series_count += 1
            if series_count > 20:  # Limit to avoid API overload
                console.print(f"[dim]Stopping series search at {series_count-1} series to avoid API limits[/]")
                break
                
            try:
                console.print(f"[blue]Searching series: {series_name} ({series_count}/{min(20, len(self.series))})[/]")
                
                results = self.client.get(
                    "1.0/catalog/products",
                    title=series_name,
                    num_results=50,
                    response_groups="series,contributors,product_desc,media,price"
                )
                
                if results and 'products' in results and results['products']:
                    found_suggestions = 0
                    filtered_out = 0
                    for book in results['products']:
                        asin = book.get('asin')
                        title = book.get('title', '').lower().strip()
                        
                        # Check if this book is in the series we're looking for
                        book_series = book.get('series', []) or []
                        series_match = any(s.get('title', '').lower() == series_name.lower() for s in book_series)
                        
                        if series_match:
                            # Check language filter
                            book_language = book.get('language', '').lower()
                            if book_language != self.language:
                                continue
                            
                            # Enhanced filtering - check both ASIN and title
                            already_owned = False
                            if asin and asin in user_books:
                                already_owned = True
                                filtered_out += 1
                            elif title and title in user_titles:
                                already_owned = True
                                filtered_out += 1
                            
                            if not already_owned:
                                # Extract member price correctly
                                price_info = book.get('price', {})
                                member_price = None
                                
                                if price_info and 'lowest_price' in price_info:
                                    lowest_price = price_info['lowest_price']
                                    if lowest_price.get('type') == 'member':
                                        member_price = lowest_price.get('base')
                                
                                # Determine purchase recommendation
                                purchase_method = "credits"
                                recommendation = "🎫"
                                if member_price and member_price < self.max_price:
                                    purchase_method = "cash"
                                    recommendation = "💰"
                                
                                # Extract series info
                                series_info = self._extract_series_info(book)
                                
                                self.suggestions['series'][series_name] = self.suggestions['series'].get(series_name, [])
                                self.suggestions['series'][series_name].append({
                                    'title': book.get('title', 'Unknown Title'),
                                    'asin': asin,
                                    'price': member_price,
                                    'purchase_method': purchase_method,
                                    'recommendation': recommendation,
                                    'series_info': series_info
                                })
                                found_suggestions += 1
                    
                    if found_suggestions > 0 or filtered_out > 0:
                        console.print(f"[green]  → Found {found_suggestions} missing books, filtered out {filtered_out} owned[/]")
                        
            except Exception as e:
                console.print(f"[red]Error searching series {series_name}: {e}[/]")
                continue

    def save_reports(self):
        """Save analysis reports to text files"""
        console.print("[bold blue]Saving reports...[/]")
        
        # Report 1: My Library by Authors
        with open('reports/my_library_by_authors.txt', 'w', encoding='utf-8') as f:
            for author, books in sorted(self.authors.items()):
                f.write(f"{author}:\n")
                for book in sorted(books, key=lambda x: x['title']):
                    f.write(f"  - {book['title']}\n")
                f.write("\n")
        
        # Report 2: My Library by Narrators
        with open('reports/my_library_by_narrators.txt', 'w', encoding='utf-8') as f:
            for narrator, books in sorted(self.narrators.items()):
                f.write(f"{narrator}:\n")
                for book in sorted(books, key=lambda x: x['title']):
                    f.write(f"  - {book['title']}\n")
                f.write("\n")
        
        # Report 3: My Library by Series
        with open('reports/my_library_by_series.txt', 'w', encoding='utf-8') as f:
            for series, books in sorted(self.series.items()):
                f.write(f"{series}:\n")
                # Sort by position if available
                sorted_books = sorted(books, key=lambda x: (x.get('position', 0), x['title']))
                for book in sorted_books:
                    position = f" (#{book.get('position', '?')})" if book.get('position') else ""
                    f.write(f"  - {book['title']}{position}\n")
                f.write("\n")
        
        # Report 4: Missing Books in My Series (Priority 1)
        with open('reports/missing_books_in_my_series.txt', 'w', encoding='utf-8') as f:
            f.write("Missing Books in Your Series (Priority 1)\n")
            f.write("="*50 + "\n\n")
            for series_name, books in sorted(self.suggestions['series'].items()):
                if books:  # Only include series with missing books
                    f.write(f"{series_name}:\n")
                    for book in sorted(books, key=lambda x: x['title']):
                        price_str = f" (${book['price']:.2f})" if book['price'] else ""
                        f.write(f"  {book['recommendation']} {book['title']}{price_str}\n")
                    f.write("\n")
        
        # Report 5: Missing Books by My Authors (Priority 2)
        with open('reports/missing_books_by_my_authors.txt', 'w', encoding='utf-8') as f:
            f.write("Missing Books by Your Authors (Priority 2)\n")
            f.write("="*50 + "\n\n")
            for author_name, books in sorted(self.suggestions['authors'].items()):
                if books:  # Only include authors with new books
                    f.write(f"{author_name}:\n")
                    for book in sorted(books, key=lambda x: x['title']):
                        price_str = f" (${book['price']:.2f})" if book['price'] else ""
                        f.write(f"  {book['recommendation']} {book['title']}{price_str}\n")
                    f.write("\n")
        
        # Report 6: Missing Books by My Narrators (Discovery)
        with open('reports/missing_books_by_my_narrators.txt', 'w', encoding='utf-8') as f:
            f.write("Missing Books by Your Narrators (Discovery)\n")
            f.write("="*50 + "\n\n")
            for narrator_name, books in sorted(self.suggestions['narrators'].items()):
                if books:  # Only include narrators with new books
                    f.write(f"{narrator_name}:\n")
                    for book in sorted(books, key=lambda x: x['title']):
                        price_str = f" (${book['price']:.2f})" if book['price'] else ""
                        f.write(f"  {book['recommendation']} {book['title']}{price_str}\n")
                    f.write("\n")
        
        console.print("[bold green]📊 Reports saved to 'reports/' directory:[/]")
        console.print("[green]  ✓ my_library_by_authors.txt[/]")
        console.print("[green]  ✓ my_library_by_narrators.txt[/]")
        console.print("[green]  ✓ my_library_by_series.txt[/]")
        console.print("[yellow]  ⭐ missing_books_in_my_series.txt (Priority 1)[/]")
        console.print("[blue]  📚 missing_books_by_my_authors.txt (Priority 2)[/]")
        console.print("[cyan]  🎯 missing_books_by_my_narrators.txt (Discovery)[/]")

    def display_summary(self):
        """Display a summary of the analysis"""
        self.show_auth_status()
        
        console.print(f"[bold green]📚 Library Summary:[/]")
        console.print(f"[green]Total Books: {len(self.library)}[/]")
        console.print(f"[blue]Unique Series: {len(self.series)}[/]")
        console.print(f"[yellow]Unique Authors: {len(self.authors)}[/]")
        console.print(f"[cyan]Unique Narrators: {len(self.narrators)}[/]")
        
        # Count suggestions
        series_suggestions = sum(len(books) for books in self.suggestions['series'].values())
        author_suggestions = sum(len(books) for books in self.suggestions['authors'].values())
        narrator_suggestions = sum(len(books) for books in self.suggestions['narrators'].values())
        
        console.print(f"\n[bold blue]📖 Book Suggestions:[/]")
        console.print(f"[yellow]⭐ Missing in Series: {series_suggestions} books[/]")
        console.print(f"[blue]📚 By Your Authors: {author_suggestions} books[/]")
        console.print(f"[cyan]🎯 By Your Narrators: {narrator_suggestions} books[/]")
        
        total_suggestions = series_suggestions + author_suggestions + narrator_suggestions
        console.print(f"[bold magenta]🎉 Total New Discoveries: {total_suggestions} books![/]")
        
        # Price breakdown
        cash_deals = 0
        credit_deals = 0
        for category in self.suggestions.values():
            for books in category.values():
                for book in books:
                    if book['purchase_method'] == 'cash':
                        cash_deals += 1
                    else:
                        credit_deals += 1
        
        console.print(f"\n[bold green]💰 Purchase Recommendations:[/]")
        console.print(f"[green]💰 Cash Deals (<${self.max_price}): {cash_deals} books[/]")
        console.print(f"[blue]🎫 Credit Deals (≥${self.max_price}): {credit_deals} books[/]")

    def _extract_series_info(self, book):
        """Extract series information from a book"""
        series_list = book.get('series', [])
        if not series_list:
            return None
        
        # Get the first series (most books are in one series)
        series = series_list[0]
        return {
            'title': series.get('title'),
            'sequence': series.get('sequence')
        }

def main():
    try:
        analyzer = AudibleLibraryAnalyzer()
        
        # Check if user wants to clear cache
        if len(os.sys.argv) > 1 and os.sys.argv[1] == '--clear-cache':
            analyzer.clear_auth_cache()
            return
            
        # Check if user wants to see auth status only
        if len(os.sys.argv) > 1 and os.sys.argv[1] == '--auth-status':
            if analyzer.auth_cache_file.exists():
                analyzer.authenticate()
                analyzer.show_auth_status()
            else:
                console.print("[yellow]No cached authentication found[/]")
            return
        
        analyzer.authenticate()
        analyzer.fetch_library()
        analyzer.analyze_library()
        analyzer.find_suggestions()
        analyzer.save_reports()
        analyzer.display_summary()
        
        console.print(f"\n[bold green]🎉 Analysis complete! Check the 'reports/' directory for detailed results.[/]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/]")
        raise

if __name__ == "__main__":
    main() 