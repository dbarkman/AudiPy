#!/usr/bin/env python3
"""
Debug script to examine stored authentication data
"""

import os
import json
import mysql.connector
from dotenv import load_dotenv
from rich.console import Console
from crypto_utils_simple import get_crypto_instance

# Initialize rich console
console = Console()

def debug_auth_data():
    """Debug stored authentication data"""
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
            SELECT encrypted_auth_data, marketplace, created_at, updated_at
            FROM user_audible_accounts 
            WHERE user_id = 1
            ORDER BY updated_at DESC
        """)
        
        results = cursor.fetchall()
        if not results:
            console.print("[red]❌ No stored tokens found for user ID 1[/]")
            return False
        
        console.print(f"[green]✅ Found {len(results)} token entries[/]")
        
        for i, (encrypted_data, marketplace, created_at, updated_at) in enumerate(results):
            console.print(f"\n[bold blue]Entry {i+1}:[/]")
            console.print(f"[cyan]Marketplace:[/] {marketplace}")
            console.print(f"[cyan]Created:[/] {created_at}")
            console.print(f"[cyan]Updated:[/] {updated_at}")
            
            try:
                # Decrypt the tokens for user ID 1
                decrypted_json = crypto.decrypt_for_user(1, encrypted_data)
                auth_data = json.loads(decrypted_json)
                
                console.print("[green]✅ Successfully decrypted tokens[/]")
                
                # Show the structure of auth_data
                console.print(f"[cyan]Auth data keys:[/] {list(auth_data.keys())}")
                
                # Show specific fields that might be relevant to Client-ID issues
                if 'device_info' in auth_data:
                    device_info = auth_data['device_info']
                    console.print(f"[cyan]Device info keys:[/] {list(device_info.keys())}")
                    if 'device_type' in device_info:
                        console.print(f"[cyan]Device type:[/] {device_info['device_type']}")
                    if 'device_serial_number' in device_info:
                        console.print(f"[cyan]Device serial:[/] {device_info['device_serial_number']}")
                
                if 'customer_info' in auth_data:
                    customer_info = auth_data['customer_info']
                    console.print(f"[cyan]Customer info keys:[/] {list(customer_info.keys())}")
                    if 'user_id' in customer_info:
                        console.print(f"[cyan]Customer user_id:[/] {customer_info['user_id']}")
                
                # Check for access_token and refresh_token
                if 'access_token' in auth_data:
                    token_preview = auth_data['access_token'][:50] + "..." if len(auth_data['access_token']) > 50 else auth_data['access_token']
                    console.print(f"[cyan]Access token (preview):[/] {token_preview}")
                
                if 'refresh_token' in auth_data:
                    refresh_preview = auth_data['refresh_token'][:50] + "..." if len(auth_data['refresh_token']) > 50 else auth_data['refresh_token']
                    console.print(f"[cyan]Refresh token (preview):[/] {refresh_preview}")
                
                # Check expires
                if 'expires' in auth_data:
                    from datetime import datetime
                    expires_date = datetime.fromtimestamp(auth_data['expires'])
                    console.print(f"[cyan]Expires:[/] {expires_date}")
                
                # Check locale_code
                if 'locale_code' in auth_data:
                    console.print(f"[cyan]Locale code:[/] {auth_data['locale_code']}")
                
            except Exception as e:
                console.print(f"[red]❌ Failed to decrypt entry {i+1}: {e}[/]")
        
        cursor.close()
        db.close()
        
    except Exception as e:
        console.print(f"[red]❌ Debug failed: {e}[/]")
        return False

if __name__ == "__main__":
    console.print("[bold cyan]🔍 Debugging Stored Authentication Data[/]")
    debug_auth_data() 