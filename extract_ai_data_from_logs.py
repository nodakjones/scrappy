#!/usr/bin/env python3
"""
Extract AI analysis data from processing logs and update database
"""

import asyncio
import sys
import os
import json
import re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import db_pool

def extract_ai_data_from_logs():
    """Extract AI analysis data from processing logs"""
    
    print("🔍 Extracting AI analysis data from processing logs...")
    
    # Read the processing log
    log_file = "logs/processing.log"
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # Find all AI responses
    ai_responses = []
    
    # Pattern to match AI tool calls with responses
    pattern = r'🤖 AI TOOL CALL: openai_gpt4_mini\n.*?"business_name": "([^"]+)"[^}]*"ai_response": "([^"]+)"'
    
    # Pattern for the actual format in logs (multi-line JSON)
    pattern2 = r'🤖 AI TOOL CALL: openai_gpt4_mini\n.*?"business_name": "([^"]+)"[^}]*"ai_response": "```json\s*(\{[\s\S]*?\})\s*```"'
    
    # Try both patterns
    matches = list(re.finditer(pattern, log_content, re.DOTALL))
    matches2 = list(re.finditer(pattern2, log_content, re.DOTALL))
    
    # Use the second pattern if it finds more matches
    if len(matches2) > len(matches):
        matches = matches2
        print(f"Using pattern2, found {len(matches)} matches")
    else:
        print(f"Using pattern1, found {len(matches)} matches")
    
    for match in matches:
        business_name = match.group(1)
        ai_response_raw = match.group(2)
        
        # Clean up the AI response (remove escape sequences)
        ai_response_clean = ai_response_raw.replace('\\n', '\n').replace('\\"', '"')
        
        try:
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', ai_response_clean, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(1))
                
                # Extract the fields we need
                residential_focus = ai_data.get('residential_focus')
                reasoning = ai_data.get('reasoning', '')
                
                ai_responses.append({
                    'business_name': business_name,
                    'residential_focus': residential_focus,
                    'business_description': reasoning
                })
                
                print(f"✅ Extracted data for {business_name}: residential_focus={residential_focus}, reasoning_length={len(reasoning)}")
                
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️  Failed to parse AI response for {business_name}: {e}")
            print(f"   Raw response: {ai_response_raw[:200]}...")
            continue
    
    print(f"📊 Found {len(ai_responses)} AI responses in logs")
    return ai_responses

async def update_database_with_ai_data(ai_responses):
    """Update database with extracted AI data"""
    
    await db_pool.initialize()
    
    try:
        updated_count = 0
        
        for response in ai_responses:
            business_name = response['business_name']
            residential_focus = response['residential_focus']
            business_description = response['business_description']
            
            # Update the contractor in the database
            query = """
            UPDATE contractors 
            SET 
                residential_focus = $1,
                business_description = $2,
                updated_at = NOW()
            WHERE business_name = $3 
            AND processing_status = 'completed'
            """
            
            result = await db_pool.execute(
                query,
                residential_focus,
                business_description,
                business_name
            )
            
            if result and 'UPDATE' in result:
                updated_count += 1
                print(f"✅ Updated {business_name}")
            else:
                print(f"⚠️  No match found for {business_name}")
        
        print(f"\n📈 Successfully updated {updated_count} contractors")
        
        # Check final counts
        async with db_pool.pool.acquire() as conn:
            result = await conn.fetch(
                "SELECT COUNT(*) as total, COUNT(residential_focus) as with_focus, COUNT(business_description) as with_desc FROM contractors WHERE processing_status = 'completed'"
            )
            row = result[0]
            print(f"\n📊 Final Database Status:")
            print(f"  Total completed: {row[0]}")
            print(f"  With residential_focus: {row[1]}")
            print(f"  With business_description: {row[2]}")
            
    finally:
        await db_pool.close()

async def main():
    """Main function"""
    
    print("🚀 Starting AI data extraction from logs...")
    
    # Extract AI data from logs
    ai_responses = extract_ai_data_from_logs()
    
    if not ai_responses:
        print("❌ No AI responses found in logs")
        return
    
    # Update database
    await update_database_with_ai_data(ai_responses)
    
    print("✅ AI data extraction and database update completed!")

if __name__ == "__main__":
    asyncio.run(main()) 