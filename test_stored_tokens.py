#!/usr/bin/env python3
"""
Test script to verify stored Audible tokens work
"""

import os
import json
import mysql.connector
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from crypto_utils_simple import get_crypto_instance

# Initialize rich console
console = Console()

def test_stored_tokens():
    """Test that stored tokens work"""
    load_dotenv()
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'audipy'),
        'user': os.getenv('DB_USER', 'audipy'),
        'password': os.getenv('DB_PASSWORD'),
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    # Initialize crypto utilities
    crypto = get_crypto_instance()
    
    try:
        # Connect to database
        db = mysql.connector.connect(**db_config)
        console.print("[green]✅ Connected to database[/]")
        
        # Get stored tokens for user ID 1
        cursor = db.cursor()
        cursor.execute("""
            SELECT encrypted_auth_data, marketplace 
            FROM user_audible_accounts 
            WHERE user_id = 1
        """)
        
        result = cursor.fetchone()
        if not result:
            console.print("[red]❌ No stored tokens found for user ID 1[/]")
            return False
        
        encrypted_data, marketplace = result
        console.print(f"[green]✅ Found stored tokens for marketplace: {marketplace}[/]")
        
        # Decrypt the tokens for user ID 1
        decrypted_json = crypto.decrypt_for_user(1, encrypted_data)
        auth_data = json.loads(decrypted_json)
        
        console.print("[green]✅ Successfully decrypted tokens[/]")
        
        # Create authenticator from stored data
        auth = Authenticator.from_dict(auth_data)
        client = Client(auth=auth)
        
        console.print("[green]✅ Created Audible client from stored tokens[/]")
        
        # Test API access
        console.print("\n[bold blue]🧪 Testing API access...[/]")
        library_test = client.get(
            "1.0/library",
            num_results=1,
            response_groups="product_desc"
        )
        
        if library_test:
            total_size = library_test.get('total_size', 0)
            console.print(f"[bold green]🎉 API access confirmed! Library has {total_size} books[/]")
            return True
        else:
            console.print("[red]❌ API access test failed[/]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/]")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    console.print("[bold cyan]🧪 Testing Stored Audible Tokens[/]")
    success = test_stored_tokens()
    
    if success:
        console.print("\n[bold green]✅ Phase 1 authentication is working perfectly![/]")
        console.print("[green]You can now proceed to Phase 2[/]")
    else:
        console.print("\n[red]❌ Token test failed[/]") 