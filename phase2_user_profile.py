#!/usr/bin/env python3
"""
AudiPy Phase 2: User Profile Setup
Sets up user preferences and profile settings
"""

import os
import mysql.connector
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Initialize rich console
console = Console()

class UserProfileSetup:
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
        
        self.user_id = None
        self.current_preferences = {}

    def connect_db(self):
        """Connect to database"""
        try:
            self.db = mysql.connector.connect(**self.db_config)
            console.print("[green]✅ Connected to database[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Database connection failed: {e}[/]")
            return False

    def find_user(self):
        """Find the test user created in Phase 1"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT id, oauth_provider, oauth_provider_id, display_name, last_login
                FROM users 
                WHERE oauth_provider = 'test' AND oauth_provider_id = 'test_user_001'
            """)
            
            result = cursor.fetchone()
            if result:
                self.user_id = result[0]
                console.print(f"[green]✅ Found user: {result[3]} (ID: {self.user_id})[/]")
                return True
            else:
                console.print("[red]❌ No user found. Please run Phase 1 (authentication) first.[/]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Database error finding user: {e}[/]")
            return False
        finally:
            cursor.close()

    def load_current_preferences(self):
        """Load existing user preferences if any"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT max_price, preferred_language, marketplace, currency,
                       notifications_enabled, price_alert_enabled, new_release_alerts
                FROM user_preferences 
                WHERE user_id = %s
            """, (self.user_id,))
            
            result = cursor.fetchone()
            if result:
                self.current_preferences = {
                    'max_price': float(result[0]) if result[0] else 12.66,
                    'preferred_language': result[1] or 'english',
                    'marketplace': result[2] or 'us',
                    'currency': result[3] or 'USD',
                    'notifications_enabled': bool(result[4]) if result[4] is not None else True,
                    'price_alert_enabled': bool(result[5]) if result[5] is not None else True,
                    'new_release_alerts': bool(result[6]) if result[6] is not None else True
                }
                console.print("[blue]📋 Found existing preferences[/]")
                return True
            else:
                # Set defaults
                self.current_preferences = {
                    'max_price': 12.66,
                    'preferred_language': 'english',
                    'marketplace': 'us',
                    'currency': 'USD',
                    'notifications_enabled': True,
                    'price_alert_enabled': True,
                    'new_release_alerts': True
                }
                console.print("[blue]📋 No existing preferences found, using defaults[/]")
                return True
                
        except Exception as e:
            console.print(f"[red]❌ Database error loading preferences: {e}[/]")
            return False
        finally:
            cursor.close()

    def display_current_preferences(self):
        """Display current preferences in a nice table"""
        table = Table(title="Current User Preferences")
        table.add_column("Setting", style="cyan")
        table.add_column("Current Value", style="green")
        table.add_column("Description", style="dim")
        
        table.add_row(
            "Max Credit Price",
            f"${self.current_preferences['max_price']:.2f}",
            "Books under this price will be recommended for cash purchase"
        )
        table.add_row(
            "Language",
            self.current_preferences['preferred_language'].title(),
            "Preferred audiobook language"
        )
        table.add_row(
            "Marketplace",
            self.current_preferences['marketplace'].upper(),
            "Audible marketplace region"
        )
        table.add_row(
            "Currency",
            self.current_preferences['currency'],
            "Currency for price display"
        )
        table.add_row(
            "Notifications",
            "✅ Enabled" if self.current_preferences['notifications_enabled'] else "❌ Disabled",
            "General app notifications"
        )
        table.add_row(
            "Price Alerts",
            "✅ Enabled" if self.current_preferences['price_alert_enabled'] else "❌ Disabled",
            "Alerts when wishlist books go on sale"
        )
        table.add_row(
            "New Release Alerts",
            "✅ Enabled" if self.current_preferences['new_release_alerts'] else "❌ Disabled",
            "Alerts for new books by favorite authors"
        )
        
        console.print(table)

    def get_user_preferences(self):
        """Interactively get user preferences"""
        console.print("\n[bold blue]⚙️  User Preferences Setup[/]")
        console.print("[dim]Configure your AudiPy preferences[/]\n")
        
        # Display current preferences
        self.display_current_preferences()
        
        # Ask if user wants to update
        if not Confirm.ask("\nWould you like to update these preferences?", default=False):
            console.print("[yellow]Keeping current preferences[/]")
            return self.current_preferences
        
        console.print("\n[bold]Let's update your preferences:[/]")
        
        # Max price for credit recommendations
        console.print(f"\n[cyan]💰 Credit Price Threshold[/]")
        console.print("[dim]Books under this price will be recommended for cash purchase instead of credits[/]")
        max_price = Prompt.ask(
            "Max credit price",
            default=str(self.current_preferences['max_price']),
            show_default=True
        )
        
        # Language preference
        console.print(f"\n[cyan]🌍 Language Preference[/]")
        console.print("[dim]Filter books by language[/]")
        language_options = ["english", "spanish", "french", "german", "italian", "portuguese"]
        language = Prompt.ask(
            "Preferred language",
            choices=language_options,
            default=self.current_preferences['preferred_language'],
            show_default=True
        )
        
        # Marketplace
        console.print(f"\n[cyan]🏪 Marketplace[/]")
        console.print("[dim]Your Audible marketplace region[/]")
        marketplace_options = ["us", "uk", "de", "fr", "au", "ca", "in", "it", "jp"]
        marketplace = Prompt.ask(
            "Marketplace",
            choices=marketplace_options,
            default=self.current_preferences['marketplace'],
            show_default=True
        )
        
        # Currency (auto-set based on marketplace)
        currency_map = {
            'us': 'USD', 'ca': 'CAD', 'uk': 'GBP', 'de': 'EUR', 
            'fr': 'EUR', 'it': 'EUR', 'au': 'AUD', 'in': 'INR', 'jp': 'JPY'
        }
        currency = currency_map.get(marketplace, 'USD')
        
        # Notification preferences
        console.print(f"\n[cyan]🔔 Notification Preferences[/]")
        notifications_enabled = Confirm.ask(
            "Enable general notifications?",
            default=self.current_preferences['notifications_enabled']
        )
        
        price_alert_enabled = Confirm.ask(
            "Enable price drop alerts?",
            default=self.current_preferences['price_alert_enabled']
        )
        
        new_release_alerts = Confirm.ask(
            "Enable new release alerts?",
            default=self.current_preferences['new_release_alerts']
        )
        
        # Return updated preferences
        return {
            'max_price': float(max_price),
            'preferred_language': language,
            'marketplace': marketplace,
            'currency': currency,
            'notifications_enabled': notifications_enabled,
            'price_alert_enabled': price_alert_enabled,
            'new_release_alerts': new_release_alerts
        }

    def save_preferences(self, preferences):
        """Save user preferences to database"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO user_preferences 
                (user_id, max_price, preferred_language, marketplace, currency,
                 notifications_enabled, price_alert_enabled, new_release_alerts)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                max_price = VALUES(max_price),
                preferred_language = VALUES(preferred_language),
                marketplace = VALUES(marketplace),
                currency = VALUES(currency),
                notifications_enabled = VALUES(notifications_enabled),
                price_alert_enabled = VALUES(price_alert_enabled),
                new_release_alerts = VALUES(new_release_alerts),
                updated_at = CURRENT_TIMESTAMP
            """, (
                self.user_id,
                preferences['max_price'],
                preferences['preferred_language'],
                preferences['marketplace'],
                preferences['currency'],
                preferences['notifications_enabled'],
                preferences['price_alert_enabled'],
                preferences['new_release_alerts']
            ))
            
            console.print("[green]✅ Preferences saved successfully[/]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to save preferences: {e}[/]")
            return False
        finally:
            cursor.close()

    def display_summary(self, preferences):
        """Display final preferences summary"""
        console.print("\n[bold green]📋 Final Preferences Summary[/]")
        
        table = Table()
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Max Credit Price", f"${preferences['max_price']:.2f}")
        table.add_row("Language", preferences['preferred_language'].title())
        table.add_row("Marketplace", preferences['marketplace'].upper())
        table.add_row("Currency", preferences['currency'])
        table.add_row("Notifications", "✅ Enabled" if preferences['notifications_enabled'] else "❌ Disabled")
        table.add_row("Price Alerts", "✅ Enabled" if preferences['price_alert_enabled'] else "❌ Disabled")
        table.add_row("New Release Alerts", "✅ Enabled" if preferences['new_release_alerts'] else "❌ Disabled")
        
        console.print(table)

    def run(self):
        """Main user profile setup flow"""
        console.print("[bold cyan]👤 AudiPy Phase 2: User Profile Setup[/]")
        console.print("[dim]Configure your preferences and settings[/]\n")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Find user from Phase 1
        if not self.find_user():
            return False
        
        # Load current preferences
        if not self.load_current_preferences():
            return False
        
        # Get updated preferences from user
        preferences = self.get_user_preferences()
        
        # Save preferences
        if not self.save_preferences(preferences):
            return False
        
        # Display summary
        self.display_summary(preferences)
        
        console.print("\n[bold green]🎉 Phase 2 Complete![/]")
        console.print("[green]✅ User preferences configured[/]")
        console.print("[green]✅ Profile setup complete[/]")
        console.print("\n[dim]You can now run Phase 3 to fetch your Audible library[/]")
        
        return True

def main():
    profile_setup = UserProfileSetup()
    success = profile_setup.run()
    
    if not success:
        console.print("\n[red]❌ Profile setup failed. Please check the errors above.[/]")
        exit(1)

if __name__ == "__main__":
    main() 