#!/usr/bin/env python3
"""
Import categories from data/categories.csv into the database
"""
import asyncio
import sys
import os
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.config import config

async def import_categories():
    """Import categories from CSV file into database"""
    try:
        # Initialize database connection
        await db_pool.initialize()
        
        # Read categories CSV file
        categories_file = Path("data/categories.csv")
        if not categories_file.exists():
            print(f"❌ Categories file not found: {categories_file}")
            return False
        
        print(f"📖 Reading categories from: {categories_file}")
        df = pd.read_csv(categories_file)
        
        print(f"📊 Found {len(df)} categories")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Display sample data
        print("\n📄 Sample categories:")
        print(df.head(5).to_string())
        
        # Check for required columns
        required_columns = ['Record Id', 'Mailer Category Name', 'Priority']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Clean and prepare data
        categories_data = []
        for _, row in df.iterrows():
            # Parse modified time
            modified_time = None
            if pd.notna(row.get('Modified Time')):
                try:
                    modified_time = pd.to_datetime(row['Modified Time'])
                except:
                    modified_time = None
            
            category = {
                'record_id': str(row['Record Id']),
                'name': str(row['Mailer Category Name']),
                'priority': row['Priority'] == 'true' if isinstance(row['Priority'], str) else bool(row['Priority']),
                'afb_name': str(row.get('AFB Name', '')) if pd.notna(row.get('AFB Name')) else '',
                'category': str(row.get('Category', '')) if pd.notna(row.get('Category')) else '',
                'modified_time': modified_time
            }
            categories_data.append(category)
        
        print(f"\n🔄 Importing {len(categories_data)} categories...")
        
        # Import into database
        async with db_pool.pool.acquire() as conn:
            # Clear existing categories
            await conn.execute("DELETE FROM categories")
            print("🗑️  Cleared existing categories")
            
            # Insert new categories
            for category in categories_data:
                await conn.execute("""
                    INSERT INTO categories (
                        record_id, name, priority, afb_name, category, modified_time
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                category['record_id'],
                category['name'],
                category['priority'],
                category['afb_name'],
                category['category'],
                category['modified_time']
                )
            
            # Verify import
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM categories")
            imported_count = result['count']
            
            # Get priority categories count
            priority_result = await conn.fetchrow("SELECT COUNT(*) as count FROM categories WHERE priority = true")
            priority_count = priority_result['count']
            
            print(f"✅ Successfully imported {imported_count} categories")
            print(f"⭐ Priority categories: {priority_count}")
            
            # Display some sample categories
            sample_categories = await conn.fetch("""
                SELECT name, priority FROM categories 
                ORDER BY priority DESC, name 
                LIMIT 10
            """)
            
            print(f"\n📋 Sample categories:")
            for cat in sample_categories:
                priority_mark = "⭐" if cat['priority'] else "  "
                print(f"  {priority_mark} {cat['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing categories: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_pool.close()

async def export_categories_to_config():
    """Export categories to config for OpenAI usage"""
    try:
        await db_pool.initialize()
        
        async with db_pool.pool.acquire() as conn:
            # Get all categories
            categories = await conn.fetch("SELECT name, priority FROM categories ORDER BY priority DESC, name")
            
            # Create category lists
            all_categories = [cat['name'] for cat in categories]
            priority_categories = [cat['name'] for cat in categories if cat['priority']]
            
            print(f"📊 Categories for config:")
            print(f"  Total categories: {len(all_categories)}")
            print(f"  Priority categories: {len(priority_categories)}")
            
            # Create config file content
            config_content = f'''# Categories Configuration
# Auto-generated from database on {pd.Timestamp.now()}

# All contractor categories for OpenAI analysis
ALL_CATEGORIES = {repr(all_categories)}

# Priority categories (high-value residential services)
PRIORITY_CATEGORIES = {repr(priority_categories)}

# Category count
TOTAL_CATEGORIES = {len(all_categories)}
PRIORITY_CATEGORIES_COUNT = {len(priority_categories)}
'''
            
            # Write to config file
            config_file = Path("src/categories_config.py")
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            print(f"✅ Categories exported to: {config_file}")
            
            # Display sample categories
            print(f"\n⭐ Priority categories (first 10):")
            for cat in priority_categories[:10]:
                print(f"  - {cat}")
            
            print(f"\n📋 All categories (first 10):")
            for cat in all_categories[:10]:
                print(f"  - {cat}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exporting categories to config: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_pool.close()

async def main():
    """Main function to import categories and export to config"""
    print("🚀 Starting category import process...")
    
    # Import categories to database
    success = await import_categories()
    if not success:
        print("❌ Failed to import categories")
        return
    
    # Export categories to config
    success = await export_categories_to_config()
    if not success:
        print("❌ Failed to export categories to config")
        return
    
    print("\n✅ Category import process completed successfully!")
    print("\n📝 Next steps:")
    print("  1. Restart the application to load new categories")
    print("  2. Categories are now available in src/categories_config.py")
    print("  3. OpenAI calls will include the full category list")

if __name__ == "__main__":
    asyncio.run(main()) 