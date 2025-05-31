#!/usr/bin/env python3
"""
View all book recommendations from the database
"""

import os
import mysql.connector
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Initialize rich console
console = Console()

def view_recommendations():
    """View all book recommendations"""
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
    
    try:
        # Connect to database
        db = mysql.connector.connect(**db_config)
        console.print("[green]✅ Connected to database[/]")
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                ur.suggestion_type,
                b.title,
                b.subtitle,
                ur.source_name,
                ur.confidence_score,
                ur.purchase_method,
                ur.generated_at
            FROM user_recommendations ur
            JOIN books b ON ur.book_id = b.id
            WHERE ur.user_id = 4
            ORDER BY ur.suggestion_type, ur.confidence_score DESC, b.title
        """)
        
        results = cursor.fetchall()
        
        if not results:
            console.print("[yellow]No recommendations found[/]")
            return
        
        # Create table
        table = Table(title=f"Book Recommendations ({len(results)} total)")
        table.add_column("Type", style="cyan")
        table.add_column("Title", style="green", max_width=40)
        table.add_column("Source", style="yellow", max_width=25)
        table.add_column("Confidence", style="magenta")
        table.add_column("Purchase", style="blue")
        
        for row in results:
            suggestion_type, title, subtitle, source_name, confidence, purchase_method, generated_at = row
            
            # Combine title and subtitle
            full_title = title
            if subtitle:
                full_title += f": {subtitle}"
            
            table.add_row(
                suggestion_type.title(),
                full_title,
                source_name or "",
                f"{confidence:.2f}",
                purchase_method
            )
        
        console.print(table)
        
        # Summary by type
        cursor.execute("""
            SELECT 
                ur.suggestion_type,
                COUNT(*) as count,
                AVG(ur.confidence_score) as avg_confidence
            FROM user_recommendations ur
            WHERE ur.user_id = 4
            GROUP BY ur.suggestion_type
            ORDER BY count DESC
        """)
        
        summary_results = cursor.fetchall()
        
        summary_table = Table(title="Summary by Type")
        summary_table.add_column("Type", style="cyan")
        summary_table.add_column("Count", style="green")
        summary_table.add_column("Avg Confidence", style="yellow")
        
        for row in summary_results:
            suggestion_type, count, avg_confidence = row
            summary_table.add_row(
                suggestion_type.title(),
                str(count),
                f"{avg_confidence:.2f}"
            )
        
        console.print("\n")
        console.print(summary_table)
        
        cursor.close()
        db.close()
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")

if __name__ == "__main__":
    console.print("[bold cyan]📚 AudiPy Book Recommendations[/]")
    view_recommendations() 