#!/usr/bin/env python3

import os
import json
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
import asyncio

# Initialize rich console
console = Console()

class AudibleLibraryAnalyzer:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('AUDIBLE_USERNAME')
        self.password = os.getenv('AUDIBLE_PASSWORD')
        self.marketplace = os.getenv('AUDIBLE_MARKETPLACE', 'us')
        self.max_price = float(os.getenv('MAX_PRICE', '12.66'))
        self.language = os.getenv('LANGUAGE', 'english').lower()
        
        if not all([self.username, self.password]):
            raise ValueError("Please set AUDIBLE_USERNAME and AUDIBLE_PASSWORD in .env file")
        
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

    def authenticate(self):
        """Authenticate with Audible"""
        console.print("[bold blue]Authenticating with Audible...[/]")
        
        try:
            # Create the authenticator using the correct method
            auth = Authenticator.from_login(
                username=self.username,
                password=self.password,
                locale=self.marketplace
            )
            
            self.auth = auth
            self.client = Client(auth=auth)
            console.print("[bold green]Authentication successful![/]")
            
        except Exception as e:
            if "OTP" in str(e):
                # If OTP is required, the error message will contain "OTP"
                otp = input("Please enter the OTP code sent to your device: ")
                # Retry authentication with OTP
                auth = Authenticator.from_login(
                    username=self.username,
                    password=self.password,
                    locale=self.marketplace,
                    otp_code=otp
                )
                self.auth = auth
                self.client = Client(auth=auth)
                console.print("[bold green]Authentication successful![/]")
            else:
                raise e

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
                    num_results=100,  # Increased from 50
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
                                if member_price is not None and member_price < self.max_price:
                                    purchase_method = "cash"
                                
                                # Always add books (we'll filter in display if needed)
                                if author_name not in self.suggestions['authors']:
                                    self.suggestions['authors'][author_name] = []
                                
                                self.suggestions['authors'][author_name].append({
                                    'title': book.get('title'),
                                    'asin': asin,
                                    'price': member_price,
                                    'purchase_method': purchase_method,
                                    'series_info': self._extract_series_info(book)
                                })
                                found_suggestions += 1
                    
                    console.print(f"[green]Found {found_suggestions} new suggestions by {author_name} (filtered out {filtered_out} owned books)[/]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not fetch suggestions for author '{author_name}': {str(e)}[/]")
                continue
        
        # Search for books by narrators
        console.print("[yellow]Searching by narrators...[/]")
        narrator_count = 0
        for narrator_name in sorted(self.narrators.keys()):  # Search all narrators, sorted alphabetically
            narrator_count += 1
            if narrator_count > 50:  # Reasonable limit to avoid overwhelming the API
                console.print(f"[dim]Stopping narrator search at {narrator_count-1} narrators to avoid API limits[/]")
                break
                
            try:
                console.print(f"[blue]Searching for books narrated by: {narrator_name} ({narrator_count}/{min(50, len(self.narrators))})[/]")
                
                results = self.client.get(
                    "1.0/catalog/products",
                    narrator=narrator_name,
                    num_results=100,  # Increased from 50
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
                                if member_price is not None and member_price < self.max_price:
                                    purchase_method = "cash"
                                
                                # Always add books (we'll filter in display if needed)
                                if narrator_name not in self.suggestions['narrators']:
                                    self.suggestions['narrators'][narrator_name] = []
                                
                                self.suggestions['narrators'][narrator_name].append({
                                    'title': book.get('title'),
                                    'asin': asin,
                                    'price': member_price,
                                    'purchase_method': purchase_method,
                                    'series_info': self._extract_series_info(book)
                                })
                                found_suggestions += 1
                    
                    console.print(f"[green]Found {found_suggestions} new suggestions by narrator {narrator_name} (filtered out {filtered_out} owned books)[/]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not fetch suggestions for narrator '{narrator_name}': {str(e)}[/]")
                continue
        
        # Search for books by series (if any series exist)
        if self.series:
            console.print("[yellow]Searching by series...[/]")
            series_count = 0
            for series_name in sorted(self.series.keys()):  # Search all series, sorted alphabetically
                series_count += 1
                if series_count > 20:  # Reasonable limit for series
                    console.print(f"[dim]Stopping series search at {series_count-1} series to avoid API limits[/]")
                    break
                    
                try:
                    console.print(f"[blue]Searching for books in series: {series_name} ({series_count}/{min(20, len(self.series))})[/]")
                    
                    results = self.client.get(
                        "1.0/catalog/products",
                        keywords=series_name,  # Use keywords instead of title
                        num_results=100,  # Increased from 50
                        response_groups="series,contributors,product_desc,media,price"
                    )
                    
                    if results and 'products' in results and results['products']:
                        found_suggestions = 0
                        filtered_out = 0
                        for book in results['products']:
                            asin = book.get('asin')
                            title = book.get('title', '').lower().strip()
                            
                            # Check if this book is actually part of the series
                            book_series = book.get('series', []) or []
                            is_in_series = any(s.get('title', '').lower() == series_name.lower() for s in book_series)
                            
                            if is_in_series:
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
                                    if member_price is not None and member_price < self.max_price:
                                        purchase_method = "cash"
                                    
                                    # Always add books (we'll filter in display if needed)
                                    if series_name not in self.suggestions['series']:
                                        self.suggestions['series'][series_name] = []
                                    
                                    self.suggestions['series'][series_name].append({
                                        'title': book.get('title'),
                                        'asin': asin,
                                        'price': member_price,
                                        'purchase_method': purchase_method,
                                        'series_info': self._extract_series_info(book)
                                    })
                                    found_suggestions += 1
                        
                        console.print(f"[green]Found {found_suggestions} new suggestions in series {series_name} (filtered out {filtered_out} owned books)[/]")
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not fetch suggestions for series '{series_name}': {str(e)}[/]")
                    continue

    def save_reports(self):
        """Save analysis results to plain text files"""
        console.print("[bold blue]Saving reports...[/]")
        
        # Report 1: Books in my library by authors
        with open('reports/my_library_by_authors.txt', 'w') as f:
            f.write("MY LIBRARY BY AUTHORS\n")
            f.write("=" * 50 + "\n\n")
            for author_name, books in sorted(self.authors.items()):
                f.write(f"{author_name}:\n")
                for book in books:
                    # Find series info from original library
                    original_book = next((b for b in self.library if b.get('asin') == book['asin']), None)
                    series_info = ""
                    if original_book:
                        series_data = self._extract_series_info(original_book)
                        if series_data:
                            series_info = f" ({', '.join(series_data)})"
                    f.write(f"- {book['title']}{series_info}\n")
                f.write("\n")
        
        # Report 2: Books in my library by narrators
        with open('reports/my_library_by_narrators.txt', 'w') as f:
            f.write("MY LIBRARY BY NARRATORS\n")
            f.write("=" * 50 + "\n\n")
            for narrator_name, books in sorted(self.narrators.items()):
                f.write(f"{narrator_name}:\n")
                for book in books:
                    # Find series info from original library
                    original_book = next((b for b in self.library if b.get('asin') == book['asin']), None)
                    series_info = ""
                    if original_book:
                        series_data = self._extract_series_info(original_book)
                        if series_data:
                            series_info = f" ({', '.join(series_data)})"
                    f.write(f"- {book['title']}{series_info}\n")
                f.write("\n")
        
        # Report 3: Books in my library by series
        with open('reports/my_library_by_series.txt', 'w') as f:
            f.write("MY LIBRARY BY SERIES\n")
            f.write("=" * 50 + "\n\n")
            for series_name, books in sorted(self.series.items()):
                f.write(f"{series_name}:\n")
                # Sort by series position
                sorted_books = sorted(books, key=lambda x: x.get('position', 0))
                for book in sorted_books:
                    position = f" #{book['position']}" if book.get('position') else ""
                    f.write(f"- {book['title']}{position}\n")
                f.write("\n")
        
        # Report 4: Missing books in my series (MOST IMPORTANT)
        with open('reports/missing_books_in_my_series.txt', 'w') as f:
            f.write("MISSING BOOKS IN MY SERIES (MOST IMPORTANT)\n")
            f.write("=" * 50 + "\n\n")
            for series_name, books in sorted(self.suggestions['series'].items()):
                f.write(f"{series_name}:\n")
                for book in books:
                    series_info = ""
                    if book.get('series_info'):
                        series_info = f" ({', '.join(book['series_info'])})"
                    price_info = ""
                    if book.get('price'):
                        method = "💰 cash" if book.get('purchase_method') == 'cash' else "🎫 credits"
                        price_info = f" - ${book['price']:.2f} ({method})"
                    f.write(f"- {book['title']}{series_info}{price_info}\n")
                f.write("\n")
        
        # Report 5: Missing books by my authors (2ND MOST IMPORTANT)
        with open('reports/missing_books_by_my_authors.txt', 'w') as f:
            f.write("MISSING BOOKS BY MY AUTHORS (2ND MOST IMPORTANT)\n")
            f.write("=" * 50 + "\n\n")
            for author_name, books in sorted(self.suggestions['authors'].items()):
                f.write(f"{author_name}:\n")
                for book in books:
                    series_info = ""
                    if book.get('series_info'):
                        series_info = f" ({', '.join(book['series_info'])})"
                    price_info = ""
                    if book.get('price'):
                        method = "💰 cash" if book.get('purchase_method') == 'cash' else "🎫 credits"
                        price_info = f" - ${book['price']:.2f} ({method})"
                    f.write(f"- {book['title']}{series_info}{price_info}\n")
                f.write("\n")
        
        # Report 6: Missing books by my narrators (DISCOVERY)
        with open('reports/missing_books_by_my_narrators.txt', 'w') as f:
            f.write("MISSING BOOKS BY MY NARRATORS (DISCOVERY)\n")
            f.write("=" * 50 + "\n\n")
            for narrator_name, books in sorted(self.suggestions['narrators'].items()):
                f.write(f"{narrator_name}:\n")
                for book in books:
                    series_info = ""
                    if book.get('series_info'):
                        series_info = f" ({', '.join(book['series_info'])})"
                    price_info = ""
                    if book.get('price'):
                        method = "💰 cash" if book.get('purchase_method') == 'cash' else "🎫 credits"
                        price_info = f" - ${book['price']:.2f} ({method})"
                    f.write(f"- {book['title']}{series_info}{price_info}\n")
                f.write("\n")
        
        console.print("[bold green]Reports saved successfully![/]")
        console.print(f"[dim]📁 6 text reports saved in 'reports/' directory[/]")

    def display_summary(self):
        """Display a summary of the analysis"""
        console.print("\n[bold yellow]Library Analysis Summary[/]")
        
        # Create summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category")
        table.add_column("Count")
        
        table.add_row("Series", str(len(self.series)))
        table.add_row("Authors", str(len(self.authors)))
        table.add_row("Narrators", str(len(self.narrators)))
        
        console.print(table)
        
        # Count cash vs credit recommendations
        cash_books = []
        credit_books = []
        
        for category, suggestions in self.suggestions.items():
            for name, books in suggestions.items():
                for book in books:
                    if book.get('purchase_method') == 'cash':
                        cash_books.append(book)
                    else:
                        credit_books.append(book)
        
        # Display purchase method summary
        console.print(f"\n[bold cyan]Purchase Recommendations:[/]")
        console.print(f"💰 [green]Buy with Cash (< ${self.max_price:.2f}): {len(cash_books)} books[/]")
        console.print(f"🎫 [yellow]Use Credits (≥ ${self.max_price:.2f}): {len(credit_books)} books[/]")
        
        # Display cash purchase suggestions first (most valuable)
        if cash_books:
            console.print(f"\n[bold green]💰 Best Cash Deals (< ${self.max_price:.2f}):[/]")
            # Sort by price, lowest first
            cash_books_sorted = sorted(cash_books, key=lambda x: x.get('price', 999) if x.get('price') is not None else 999)
            for book in cash_books_sorted[:10]:  # Show top 10 cash deals
                price = f"${book['price']:.2f}" if book.get('price') is not None else "Price N/A"
                console.print(f"  💰 {book['title']} ({price})")
        
        # Display some suggestions by category
        console.print("\n[bold yellow]Top Suggestions by Category[/]")
        for category, suggestions in self.suggestions.items():
            if suggestions:
                console.print(f"\n[bold blue]{category.title()}[/]")
                for name, books in list(suggestions.items())[:3]:
                    console.print(f"\n{name}:")
                    for book in books[:3]:  # Show up to 3 books per author/narrator/series
                        if book.get('price') is not None:
                            price = f"${book['price']:.2f}"
                        else:
                            price = "Price N/A"
                        
                        # Add purchase method indicator
                        method_icon = "💰" if book.get('purchase_method') == 'cash' else "🎫"
                        console.print(f"  {method_icon} {book['title']} ({price})")
        
        # Display total suggestion counts
        total_suggestions = sum(len(books) for category in self.suggestions.values() for books in category.values())
        console.print(f"\n[bold green]Total suggestions found: {total_suggestions}[/]")
        console.print(f"[dim]Language filter: {self.language}[/]")

    def _extract_series_info(self, book):
        """Extract series information from a book"""
        series = book.get('series', []) or []
        series_info = []
        for s in series:
            series_name = s.get('title', 'Unknown Series')
            sequence = s.get('sequence', '')
            if sequence:
                series_info.append(f"{series_name} #{sequence}")
            else:
                series_info.append(series_name)
        return series_info if series_info else None

def main():
    analyzer = AudibleLibraryAnalyzer()
    try:
        analyzer.authenticate()
        analyzer.fetch_library()
        analyzer.analyze_library()
        analyzer.find_suggestions()
        analyzer.save_reports()
        analyzer.display_summary()
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")

if __name__ == "__main__":
    main() 