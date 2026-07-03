#!/usr/bin/env python3
"""
AudiPy Database Cleanup Script
Truncates all tables in the correct order to respect foreign key constraints
"""

import os
import mysql.connector
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

# Initialize rich console
console = Console()

class DatabaseCleanup:
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
        
        # Tables in order for truncation (child tables first, then parent tables)
        # This respects foreign key constraints
        self.table_order = [
            # Analytics and tracking (no dependencies)
            'user_analytics',
            'sync_jobs',
            
            # Extended data (depends on books)
            'book_extended_data',
            
            # Price and recommendation data
            'price_alerts',
            'user_recommendations',
            'book_prices',
            
            # User lists and collections
            'user_reading_list_books',
            'user_reading_lists',
            'user_wishlists',
            'user_libraries',
            
            # Relationship tables (depend on books, authors, narrators, series, categories)
            'book_categories',
            'book_series',
            'book_narrators',
            'book_authors',
            
            # Core entity tables
            'books',
            'categories',
            'series',
            'narrators',
            'authors',
            
            # User data
            'user_preferences',
            'user_audible_accounts',
            'user_oauth_tokens',
            'users'
        ]
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.db = mysql.connector.connect(**self.db_config)
            console.print("[green]✅ Connected to database[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Database connection failed: {e}[/]")
            return False
    
    def get_table_counts(self):
        """Get row counts for all tables"""
        cursor = self.db.cursor()
        table_counts = {}
        
        try:
            for table in self.table_order:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except mysql.connector.Error:
                    # Table might not exist
                    table_counts[table] = "N/A"
            
            return table_counts
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get table counts: {e}[/]")
            return {}
        finally:
            cursor.close()
    
    def display_table_status(self, table_counts, title="Current Table Status"):
        """Display table counts in a nice table"""
        table = Table(title=title)
        table.add_column("Table Name", style="cyan")
        table.add_column("Row Count", style="magenta", justify="right")
        
        total_rows = 0
        for table_name in self.table_order:
            count = table_counts.get(table_name, "N/A")
            if isinstance(count, int):
                total_rows += count
                count_str = f"{count:,}"
            else:
                count_str = str(count)
            
            table.add_row(table_name, count_str)
        
        table.add_row("", "")  # Separator
        table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_rows:,}[/bold]")
        
        console.print(table)
        return total_rows
    
    def truncate_tables(self, confirm_each=False):
        """Truncate all tables in the correct order"""
        cursor = self.db.cursor()
        truncated_tables = []
        skipped_tables = []
        
        try:
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            console.print("[yellow]🔓 Disabled foreign key checks[/]")
            
            for table in self.table_order:
                try:
                    if confirm_each:
                        if not Confirm.ask(f"Truncate table '{table}'?"):
                            skipped_tables.append(table)
                            continue
                    
                    cursor.execute(f"TRUNCATE TABLE {table}")
                    truncated_tables.append(table)
                    console.print(f"[green]✅ Truncated {table}[/]")
                    
                except mysql.connector.Error as e:
                    if "doesn't exist" in str(e).lower():
                        console.print(f"[yellow]⚠️  Table {table} doesn't exist, skipping[/]")
                        skipped_tables.append(table)
                    else:
                        console.print(f"[red]❌ Failed to truncate {table}: {e}[/]")
                        skipped_tables.append(table)
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            console.print("[green]🔒 Re-enabled foreign key checks[/]")
            
            return truncated_tables, skipped_tables
            
        except Exception as e:
            console.print(f"[red]❌ Truncation failed: {e}[/]")
            # Make sure to re-enable foreign key checks even if something fails
            try:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            except:
                pass
            return [], self.table_order
        finally:
            cursor.close()
    
    def reset_auto_increment(self):
        """Reset AUTO_INCREMENT counters for all tables"""
        cursor = self.db.cursor()
        reset_tables = []
        
        try:
            for table in reversed(self.table_order):  # Start with parent tables
                try:
                    cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                    reset_tables.append(table)
                except mysql.connector.Error as e:
                    if "doesn't exist" not in str(e).lower():
                        console.print(f"[yellow]⚠️  Could not reset AUTO_INCREMENT for {table}: {e}[/]")
            
            if reset_tables:
                console.print(f"[green]🔄 Reset AUTO_INCREMENT for {len(reset_tables)} tables[/]")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to reset AUTO_INCREMENT: {e}[/]")
        finally:
            cursor.close()
    
    def run_cleanup(self, mode="interactive"):
        """
        Run the cleanup process
        
        Args:
            mode: 'interactive', 'force', or 'confirm_each'
        """
        console.print("[bold red]🧹 AudiPy Database Cleanup[/]")
        console.print("[dim]This will truncate all tables and reset data[/]\n")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Show current status
        console.print("\n[bold blue]📊 Current Database Status[/]")
        table_counts = self.get_table_counts()
        total_rows = self.display_table_status(table_counts)
        
        if total_rows == 0:
            console.print("\n[green]✅ Database is already empty![/]")
            return True
        
        # Confirm cleanup
        if mode == "interactive":
            console.print(f"\n[bold yellow]⚠️  This will delete {total_rows:,} rows from {len(self.table_order)} tables![/]")
            if not Confirm.ask("Are you sure you want to proceed?"):
                console.print("[yellow]🚫 Cleanup cancelled[/]")
                return False
        elif mode == "force":
            console.print(f"\n[bold red]🚨 Force mode: Deleting {total_rows:,} rows...[/]")
        
        # Perform cleanup
        console.print("\n[bold blue]🧹 Starting cleanup...[/]")
        truncated, skipped = self.truncate_tables(confirm_each=(mode == "confirm_each"))
        
        # Reset AUTO_INCREMENT counters
        if truncated:
            self.reset_auto_increment()
        
        # Show results
        console.print(f"\n[bold green]✅ Cleanup Complete![/]")
        console.print(f"[green]📋 Truncated: {len(truncated)} tables[/]")
        if skipped:
            console.print(f"[yellow]⚠️  Skipped: {len(skipped)} tables[/]")
        
        # Show final status
        console.print("\n[bold blue]📊 Final Database Status[/]")
        final_counts = self.get_table_counts()
        self.display_table_status(final_counts, "After Cleanup")
        
        return True

def main():
    import sys
    
    # Parse command line arguments
    mode = "interactive"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--force", "-f"]:
            mode = "force"
        elif arg in ["--confirm-each", "-c"]:
            mode = "confirm_each"
        elif arg in ["--help", "-h"]:
            console.print("[bold cyan]AudiPy Database Cleanup[/]")
            console.print("\nUsage:")
            console.print("  python cleanup_database.py           # Interactive mode (default)")
            console.print("  python cleanup_database.py --force   # Force cleanup without confirmation")
            console.print("  python cleanup_database.py --confirm-each  # Confirm each table individually")
            console.print("  python cleanup_database.py --help    # Show this help")
            return
    
    cleanup = DatabaseCleanup()
    success = cleanup.run_cleanup(mode)
    
    if not success:
        console.print("\n[red]❌ Cleanup failed[/]")
        sys.exit(1)

if __name__ == "__main__":
    main() 