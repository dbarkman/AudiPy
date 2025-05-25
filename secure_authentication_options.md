#!/usr/bin/env python3

import os
import json
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from dotenv import load_dotenv
from audible import Authenticator, Client
from rich.console import Console
from rich.panel import Panel
import getpass

console = Console()

class SecureTokenGenerator:
    def __init__(self):
        self.auth = None
        
    def generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Generate encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_data(self, data: dict, password: str) -> dict:
        """Encrypt authentication data"""
        # Generate random salt
        salt = os.urandom(16)
        
        # Generate key from password
        key = self.generate_key_from_password(password, salt)
        
        # Create Fernet cipher
        f = Fernet(key)
        
        # Encrypt the data
        encrypted_data = f.encrypt(json.dumps(data).encode())
        
        return {
            'salt': base64.b64encode(salt).decode(),
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'version': '1.0'
        }

    def authenticate_and_generate_tokens(self):
        """Authenticate with Audible and generate token file"""
        
        console.print(Panel.fit(
            "[bold green]🔐 AudiPy Secure Token Generator[/]\n\n"
            "[yellow]This tool authenticates with Amazon/Audible locally and generates[/]\n"
            "[yellow]an encrypted token file for use with the AudiPy web application.[/]\n\n"
            "[red]⚠️  Your Amazon credentials never leave this computer![/]",
            title="Security Notice"
        ))
        
        # Get credentials
        console.print("\n[bold blue]📝 Enter your Amazon/Audible credentials:[/]")
        username = input("Username/Email: ").strip()
        password = getpass.getpass("Password: ")
        marketplace = input("Marketplace (us/uk/de/fr/etc.) [us]: ").strip() or 'us'
        
        console.print(f"\n[bold blue]🔑 Authenticating with Audible ({marketplace})...[/]")
        
        try:
            # Create the authenticator
            auth = Authenticator.from_login(
                username=username,
                password=password,
                locale=marketplace
            )
            
            self.auth = auth
            console.print("[bold green]✅ Authentication successful![/]")
            
        except Exception as e:
            if "OTP" in str(e) or "captcha" in str(e).lower():
                # If OTP is required, prompt for it
                console.print("[yellow]📱 OTP code required...[/]")
                otp = input("OTP Code: ").strip()
                
                # Retry authentication with OTP
                auth = Authenticator.from_login(
                    username=username,
                    password=password,
                    locale=marketplace,
                    otp_code=otp
                )
                self.auth = auth
                console.print("[bold green]✅ Authentication successful![/]")
            else:
                console.print(f"[bold red]❌ Authentication failed: {e}[/]")
                return False
                
        # Test the authentication by fetching basic library info
        try:
            client = Client(auth=self.auth)
            library = client.get("1.0/library", num_results=1)
            console.print(f"[green]✅ Verified access to library ({len(library.get('items', []))} books found)[/]")
        except Exception as e:
            console.print(f"[red]❌ Failed to access library: {e}[/]")
            return False
            
        return True

    def export_encrypted_tokens(self):
        """Export encrypted token file"""
        if not self.auth:
            console.print("[red]❌ No authentication data available[/]")
            return False
            
        console.print("\n[bold blue]🔒 Creating encrypted token file...[/]")
        
        # Get encryption password
        while True:
            encrypt_password = getpass.getpass("Enter password to encrypt token file: ")
            confirm_password = getpass.getpass("Confirm password: ")
            
            if encrypt_password == confirm_password:
                if len(encrypt_password) < 8:
                    console.print("[red]❌ Password must be at least 8 characters[/]")
                    continue
                break
            else:
                console.print("[red]❌ Passwords don't match[/]")
        
        # Extract authentication data
        auth_data = self.auth.to_dict()
        
        # Add metadata
        export_data = {
            'auth_data': auth_data,
            'marketplace': self.auth.locale.country_code,
            'username': getattr(self.auth, 'user_name', 'Unknown'),
            'generated_at': str(self.auth.access_token_expires) if hasattr(self.auth, 'access_token_expires') else None,
            'expires_at': str(self.auth.access_token_expires) if hasattr(self.auth, 'access_token_expires') else None
        }
        
        # Encrypt the data
        encrypted_export = self.encrypt_data(export_data, encrypt_password)
        
        # Save to file
        output_file = Path('audipy_tokens.enc')
        with open(output_file, 'w') as f:
            json.dump(encrypted_export, f, indent=2)
            
        console.print(f"\n[bold green]🎉 Token file created successfully![/]")
        console.print(f"[green]📁 File: {output_file.absolute()}[/]")
        console.print(f"[green]📊 Size: {output_file.stat().st_size} bytes[/]")
        
        # Show usage instructions
        console.print(Panel.fit(
            "[bold yellow]📋 Next Steps:[/]\n\n"
            "[green]1. Upload this file to the AudiPy web application[/]\n"
            "[green]2. Enter the same password you used to encrypt it[/]\n"
            "[green]3. The web app will use these tokens to access your library[/]\n\n"
            "[red]⚠️  Keep this password safe - you'll need it to use the tokens![/]\n"
            "[red]⚠️  Don't share this file without the password![/]",
            title="Usage Instructions"
        ))
        
        return True

    def show_token_info(self):
        """Show information about the generated tokens"""
        if not self.auth:
            return
            
        console.print("\n[bold blue]📋 Token Information:[/]")
        console.print(f"[green]🌍 Marketplace: {self.auth.locale.domain}[/]")
        if hasattr(self.auth, 'access_token_expires'):
            if self.auth.access_token_expired:
                console.print(f"[red]⚠️ Access token: EXPIRED[/]")
            else:
                console.print(f"[green]⏰ Access token expires: {self.auth.access_token_expires}[/]")
        
        console.print("\n[bold yellow]🔄 Token Refresh Capability:[/]")
        console.print("[green]✅ These tokens can be automatically refreshed[/]")
        console.print("[green]✅ No re-authentication needed for ~1 month[/]")
        console.print("[green]✅ Web app can refresh tokens in background[/]")

def main():
    try:
        generator = SecureTokenGenerator()
        
        # Authenticate
        if not generator.authenticate_and_generate_tokens():
            return 1
            
        # Show token info
        generator.show_token_info()
        
        # Export encrypted tokens
        if not generator.export_encrypted_tokens():
            return 1
            
        console.print("\n[bold green]🎉 Token generation complete![/]")
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Token generation cancelled by user.[/]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/]")
        return 1

if __name__ == "__main__":
    exit(main()) 