#!/usr/bin/env python3
"""
Add Puget Sound column to contractors table
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def add_puget_sound_column():
    """Add puget_sound column to contractors table"""
    
    print("🏔️ ADDING PUGET SOUND COLUMN")
    print("=" * 40)
    
    await db_pool.initialize()
    
    try:
        # Add the column
        await db_pool.execute('''
            ALTER TABLE contractors 
            ADD COLUMN IF NOT EXISTS puget_sound BOOLEAN DEFAULT FALSE
        ''')
        
        # Create index
        await db_pool.execute('''
            CREATE INDEX IF NOT EXISTS idx_contractors_puget_sound 
            ON contractors(puget_sound)
        ''')
        
        print("✅ Puget Sound column added successfully!")
        print("✅ Index created for efficient filtering!")
        
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(add_puget_sound_column()) 