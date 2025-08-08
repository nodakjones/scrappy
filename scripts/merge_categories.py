#!/usr/bin/env python3
"""
Merge categories from categories table into mailer_categories table
while preserving existing metadata
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.config import config

async def merge_categories():
    """Merge categories from categories table into mailer_categories table"""
    try:
        # Initialize database connection
        await db_pool.initialize()
        
        async with db_pool.pool.acquire() as conn:
            # Get existing mailer_categories with metadata
            existing_categories = await conn.fetch('''
                SELECT category_name, priority, keywords, typical_services, active, sort_order
                FROM mailer_categories
            ''')
            
            # Create a lookup dictionary for existing categories
            existing_lookup = {cat['category_name']: cat for cat in existing_categories}
            
            print(f"📋 Found {len(existing_categories)} existing categories with metadata")
            
            # Get all categories from categories table
            all_categories = await conn.fetch('''
                SELECT name, priority, afb_name, category
                FROM categories
                ORDER BY name
            ''')
            
            print(f"📊 Found {len(all_categories)} categories to merge")
            
            # Track statistics
            inserted = 0
            updated = 0
            skipped = 0
            
            # Process each category
            for cat in all_categories:
                category_name = cat['name']
                
                if category_name in existing_lookup:
                    # Category exists - update priority and other fields but preserve metadata
                    existing = existing_lookup[category_name]
                    
                    await conn.execute('''
                        UPDATE mailer_categories 
                        SET 
                            priority = $1,
                            afb_name = $2,
                            category = $3,
                            active = true
                        WHERE category_name = $4
                    ''', cat['priority'], cat['afb_name'], cat['category'], category_name)
                    
                    updated += 1
                    print(f"  🔄 Updated: {category_name}")
                else:
                    # New category - insert with default metadata
                    await conn.execute('''
                        INSERT INTO mailer_categories (
                            category_name, priority, afb_name, category, 
                            keywords, typical_services, active, sort_order
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ''', 
                    category_name,
                    cat['priority'],
                    cat['afb_name'],
                    cat['category'],
                    [],  # Empty keywords array
                    [],  # Empty typical_services array
                    True,  # Active
                    None   # No sort order
                    )
                    
                    inserted += 1
                    print(f"  ➕ Inserted: {category_name}")
            
            # Verify final count
            final_count = await conn.fetchval('SELECT COUNT(*) FROM mailer_categories')
            priority_count = await conn.fetchval('SELECT COUNT(*) FROM mailer_categories WHERE priority = true')
            
            print(f"\n📊 Merge Results:")
            print(f"  ✅ Inserted: {inserted} new categories")
            print(f"  🔄 Updated: {updated} existing categories")
            print(f"  📋 Total categories: {final_count}")
            print(f"  ⭐ Priority categories: {priority_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error merging categories: {e}")
        return False
    finally:
        await db_pool.close()

async def main():
    """Main function"""
    print("🔄 Starting category merge process...")
    
    success = await merge_categories()
    
    if success:
        print("✅ Category merge completed successfully!")
    else:
        print("❌ Category merge failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 