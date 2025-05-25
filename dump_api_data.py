#!/usr/bin/env python3

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console

# Initialize rich console
console = Console()

def dump_api_samples():
    """Dump sample API data for model design"""
    load_dotenv()
    
    username = os.getenv('AUDIBLE_USERNAME')
    password = os.getenv('AUDIBLE_PASSWORD')
    marketplace = os.getenv('AUDIBLE_MARKETPLACE', 'us')
    
    console.print("[bold blue]Authenticating with Audible...[/]")
    
    try:
        # Authenticate
        auth = Authenticator.from_login(
            username=username,
            password=password,
            locale=marketplace
        )
        client = Client(auth=auth)
        console.print("[bold green]Authentication successful![/]")
        
    except Exception as e:
        if "OTP" in str(e):
            otp = input("Please enter the OTP code sent to your device: ")
            auth = Authenticator.from_login(
                username=username,
                password=password,
                locale=marketplace,
                otp_code=otp
            )
            client = Client(auth=auth)
            console.print("[bold green]Authentication successful![/]")
        else:
            raise e
    
    # Create samples directory
    Path('api_samples').mkdir(exist_ok=True)
    
    # 1. Sample User Library Books (your owned books)
    console.print("[yellow]Fetching user library samples...[/]")
    library = client.get(
        "1.0/library",
        num_results=10,
        response_groups="series,contributors,product_desc,media,price,customer_rights,library_status"
    )
    
    with open('api_samples/user_library_books.json', 'w') as f:
        json.dump(library, f, indent=2)
    console.print(f"[green]Saved {len(library.get('items', []))} user library book samples[/]")
    
    # 2. Sample Catalog Books (Audible's full catalog)
    console.print("[yellow]Fetching catalog book samples...[/]")
    catalog = client.get(
        "1.0/catalog/products",
        num_results=10,
        response_groups="series,contributors,product_desc,media,price,reviews,category_ladders"
    )
    
    with open('api_samples/catalog_books.json', 'w') as f:
        json.dump(catalog, f, indent=2)
    console.print(f"[green]Saved {len(catalog.get('products', []))} catalog book samples[/]")
    
    # 3. Sample Author Search
    console.print("[yellow]Fetching author-specific books...[/]")
    author_books = client.get(
        "1.0/catalog/products",
        author="John Scalzi",
        num_results=5,
        response_groups="series,contributors,product_desc,media,price"
    )
    
    with open('api_samples/author_books.json', 'w') as f:
        json.dump(author_books, f, indent=2)
    console.print(f"[green]Saved {len(author_books.get('products', []))} author book samples[/]")
    
    # 4. Sample Narrator Search  
    console.print("[yellow]Fetching narrator-specific books...[/]")
    narrator_books = client.get(
        "1.0/catalog/products",
        narrator="R.C. Bray",
        num_results=5,
        response_groups="series,contributors,product_desc,media,price"
    )
    
    with open('api_samples/narrator_books.json', 'w') as f:
        json.dump(narrator_books, f, indent=2)
    console.print(f"[green]Saved {len(narrator_books.get('products', []))} narrator book samples[/]")
    
    # 5. Sample Categories/Genres
    console.print("[yellow]Fetching categories...[/]")
    try:
        categories = client.get("1.0/catalog/categories")
        with open('api_samples/categories.json', 'w') as f:
            json.dump(categories, f, indent=2)
        console.print(f"[green]Saved categories data[/]")
    except Exception as e:
        console.print(f"[yellow]Could not fetch categories: {str(e)}[/]")
    
    # 6. Sample User Account Info
    console.print("[yellow]Fetching user account info...[/]")
    try:
        account = client.get("1.0/customer/information")
        with open('api_samples/user_account.json', 'w') as f:
            json.dump(account, f, indent=2)
        console.print(f"[green]Saved user account info[/]")
    except Exception as e:
        console.print(f"[yellow]Could not fetch account info: {str(e)}[/]")
    
    # 7. Print unique field analysis
    console.print("\n[bold yellow]Analyzing API Response Fields...[/]")
    
    if library.get('items'):
        library_fields = set()
        for book in library['items']:
            library_fields.update(book.keys())
        console.print(f"[cyan]User Library Book Fields ({len(library_fields)}): {sorted(library_fields)}[/]")
    
    if catalog.get('products'):
        catalog_fields = set()
        for book in catalog['products']:
            catalog_fields.update(book.keys())
        console.print(f"[cyan]Catalog Book Fields ({len(catalog_fields)}): {sorted(catalog_fields)}[/]")
    
    console.print(f"\n[bold green]✅ API samples saved to 'api_samples/' directory[/]")

if __name__ == "__main__":
    dump_api_samples() 