#!/usr/bin/env python3
"""
AudiPy Phase 1: Authentication
Authenticates with Audible and stores encrypted tokens in database
"""

import os
import json
import mysql.connector
import getpass
from pathlib import Path
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from utils.crypto_utils_simple import get_crypto_instance

# Initialize rich console
console = Console()

class AudibleAuthenticator:
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
        
        self.auth = None
        self.client = None
        self.user_id = None

    def connect_db(self):
        """Connect to database"""
        try:
            self.db = mysql.connector.connect(**self.db_config)
            console.print("[green]✅ Connected to database[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Database connection failed: {e}[/]")
            return False

    def get_user_credentials(self):
        """Get Audible credentials from user"""
        console.print("\n[bold blue]🔐 Audible Authentication Setup[/]")
        console.print("[dim]Enter your Audible account credentials[/]")
        
        username = input("Username/Email: ").strip()
        password = getpass.getpass("Password (not saved in our database): ").strip()
        console.print("[dim]Marketplace is required for authentication (you can update it in preferences later)[/]")
        marketplace = input("Marketplace (us/uk/de/fr/etc) [us]: ").strip() or 'us'
        
        return username, password, marketplace

    def authenticate_audible(self, username, password, marketplace):
        """Authenticate with Audible"""
        console.print(f"\n[bold blue]🔑 Authenticating with Audible ({marketplace})...[/]")
        
        try:
            # Create the authenticator
            auth = Authenticator.from_login(
                username=username,
                password=password,
                locale=marketplace
            )
            
            self.auth = auth
            self.client = Client(auth=auth)
            console.print("[bold green]✅ Authentication successful![/]")
            return True
            
        except Exception as e:
            if "OTP" in str(e) or "captcha" in str(e).lower():
                # If OTP is required
                console.print("[yellow]📱 Two-factor authentication required[/]")
                otp = getpass.getpass("Enter OTP code: ").strip()
                
                try:
                    # Retry authentication with OTP
                    auth = Authenticator.from_login(
                        username=username,
                        password=password,
                        locale=marketplace,
                        otp_code=otp
                    )
                    self.auth = auth
                    self.client = Client(auth=auth)
                    console.print("[bold green]✅ Authentication successful![/]")
                    return True
                except Exception as otp_error:
                    console.print(f"[red]❌ Authentication failed: {otp_error}[/]")
                    return False
            else:
                console.print(f"[red]❌ Authentication failed: {e}[/]")
                return False

    def create_test_user(self, marketplace):
        """Create a test user in the database"""
        cursor = self.db.cursor()
        
        # For testing, create a simple OAuth user
        # In production, this would come from actual OAuth flow
        test_user_data = {
            'oauth_provider': 'test',
            'oauth_provider_id': 'test_user_001',
            'display_name': 'Test User',
            'marketplace': marketplace
        }
        
        try:
            # Insert user
            cursor.execute("""
                INSERT INTO users (oauth_provider, oauth_provider_id, display_name)
                VALUES (%(oauth_provider)s, %(oauth_provider_id)s, %(display_name)s)
                ON DUPLICATE KEY UPDATE 
                display_name = VALUES(display_name),
                last_login = CURRENT_TIMESTAMP
            """, test_user_data)
            
            # Get user ID
            cursor.execute("""
                SELECT id FROM users 
                WHERE oauth_provider = %s AND oauth_provider_id = %s
            """, (test_user_data['oauth_provider'], test_user_data['oauth_provider_id']))
            
            result = cursor.fetchone()
            if result:
                self.user_id = result[0]
                console.print(f"[green]✅ Test user created/updated (ID: {self.user_id})[/]")
                return True
            else:
                console.print("[red]❌ Failed to create test user[/]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Database error creating user: {e}[/]")
            return False
        finally:
            cursor.close()

    def _format_expires_date(self, expires):
        """Format expiration date to ISO string, handling different input types"""
        console.print(f"[dim]Debug: expires type: {type(expires)}, value: {expires}[/]")
        
        if expires is None:
            return None
        
        # If it's already a string, return as-is
        if isinstance(expires, str):
            return expires
        
        # If it's a datetime object, convert to ISO format
        if hasattr(expires, 'isoformat'):
            return expires.isoformat()
        
        # If it's a float/int timestamp, convert to datetime then ISO
        if isinstance(expires, (int, float)):
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(expires)
                return dt.isoformat()
            except (ValueError, OSError):
                # If timestamp conversion fails, return None
                return None
        
        # For any other type, try to convert to string
        return str(expires)

    def _make_json_safe(self, obj):
        """Convert object to JSON-safe format"""
        if obj is None:
            return None
        
        # If it's already a basic type, return as-is
        if isinstance(obj, (str, int, float, bool, list, dict)):
            return obj
        
        # If it's a dict-like object, try to convert to dict
        if hasattr(obj, '__dict__'):
            try:
                return obj.__dict__
            except:
                pass
        
        # If it has a to_dict method, use it
        if hasattr(obj, 'to_dict'):
            try:
                return obj.to_dict()
            except:
                pass
        
        # Otherwise convert to string
        return str(obj)

    def store_audible_tokens(self, marketplace):
        """Store encrypted Audible authentication tokens"""
        if not self.auth or not self.user_id:
            console.print("[red]❌ No authentication data or user ID available[/]")
            return False
        
        try:
            # Debug: Check what we have in the auth object
            console.print(f"[dim]Debug: auth.locale type: {type(self.auth.locale)}[/]")
            console.print(f"[dim]Debug: auth.expires type: {type(self.auth.expires)}[/]")
            
            # Extract complete authentication data (all fields needed by Authenticator.from_dict)
            auth_data = {
                'website_cookies': self._make_json_safe(self.auth.website_cookies),
                'adp_token': self.auth.adp_token,
                'access_token': self.auth.access_token,
                'refresh_token': self.auth.refresh_token,
                'device_private_key': self.auth.device_private_key,
                'store_authentication_cookie': self._make_json_safe(self.auth.store_authentication_cookie),
                'device_info': self._make_json_safe(self.auth.device_info),
                'customer_info': self._make_json_safe(self.auth.customer_info),
                'expires': self.auth.expires,
                'locale_code': marketplace,  # Store the marketplace code, not the Locale object
                'with_username': getattr(self.auth, 'with_username', False),
                'activation_bytes': getattr(self.auth, 'activation_bytes', None)
            }
            
            # Debug output
            console.print(f"[dim]Debug: Storing auth data with locale_code: {auth_data['locale_code']}[/]")
            console.print(f"[dim]Debug: Expires at: {auth_data['expires']}[/]")
            
            # Encrypt the authentication data for this specific user
            auth_json = json.dumps(auth_data)
            encrypted_data = self.crypto.encrypt_for_user(self.user_id, auth_json)
            
            # Store in database
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO user_audible_accounts 
                (user_id, encrypted_auth_data, marketplace, tokens_expires_at, sync_status)
                VALUES (%s, %s, %s, %s, 'pending')
                ON DUPLICATE KEY UPDATE
                encrypted_auth_data = VALUES(encrypted_auth_data),
                tokens_expires_at = VALUES(tokens_expires_at),
                sync_status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            """, (
                self.user_id,
                encrypted_data,
                marketplace,
                self._format_expires_date(auth_data.get('expires'))
            ))
            
            cursor.close()
            console.print("[green]✅ Audible tokens stored securely[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to store tokens: {e}[/]")
            return False

    def test_api_access(self):
        """Test that the stored tokens work"""
        console.print("\n[bold blue]🧪 Testing API access...[/]")
        
        try:
            # Make a simple API call to verify authentication
            # Use a basic library call instead of customer info
            library_test = self.client.get(
                "1.0/library",
                num_results=1,
                response_groups="product_desc"
            )
            
            if library_test:
                total_size = library_test.get('total_size', 0)
                console.print(f"[green]✅ API access confirmed! Library has {total_size} books[/]")
                return True
            else:
                console.print("[red]❌ API access test failed[/]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ API access test failed: {e}[/]")
            return False

    def run(self):
        """Main authentication flow"""
        console.print("[bold cyan]🎵 AudiPy Phase 1: Authentication[/]")
        console.print("[dim]This script will authenticate with Audible and store tokens securely[/]\n")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Get credentials from user
        username, password, marketplace = self.get_user_credentials()
        
        # Authenticate with Audible
        if not self.authenticate_audible(username, password, marketplace):
            return False
        
        # Create test user in database
        if not self.create_test_user(marketplace):
            return False
        
        # Store encrypted tokens
        if not self.store_audible_tokens(marketplace):
            return False
        
        # Test API access
        if not self.test_api_access():
            return False
        
        console.print("\n[bold green]🎉 Phase 1 Complete![/]")
        console.print("[green]✅ Audible authentication successful[/]")
        console.print("[green]✅ Tokens stored securely in database[/]")
        console.print("[green]✅ API access verified[/]")
        console.print("\n[dim]You can now run Phase 2 to set up your user preferences[/]")
        
        return True

def main():
    authenticator = AudibleAuthenticator()
    success = authenticator.run()
    
    if not success:
        console.print("\n[red]❌ Authentication failed. Please check your credentials and try again.[/]")
        exit(1)

if __name__ == "__main__":
    main() 