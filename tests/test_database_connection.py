"""
Simple database connection test
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_database_connection():
    """Test database connection and check current state"""
    print("🔍 Testing database connection...")
    
    # Get database configuration from environment
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'contractor_enrichment')
    }
    
    print(f"📋 Database config: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    print(f"👤 User: {db_config['user']}")
    
    try:
        # First try to connect to postgres database
        print("\n🔌 Testing connection to postgres database...")
        conn = await asyncpg.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database='postgres'
        )
        
        print("✅ Successfully connected to postgres database")
        
        # Check if our target database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_config['database']
        )
        
        if db_exists:
            print(f"✅ Database '{db_config['database']}' exists")
            
            # Try to connect to our target database
            await conn.close()
            
            conn = await asyncpg.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            print(f"✅ Successfully connected to '{db_config['database']}' database")
            
            # Check what tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            if tables:
                print(f"\n📋 Existing tables:")
                for table in tables:
                    # Get row count for each table
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
                    print(f"   • {table['table_name']}: {count:,} rows")
            else:
                print("\n📋 No tables found - database is empty")
            
            # Check for indexes
            indexes = await conn.fetch("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            if indexes:
                print(f"\n🔍 Existing indexes:")
                for index in indexes:
                    print(f"   • {index['indexname']} on {index['tablename']}")
            else:
                print("\n🔍 No indexes found")
            
            await conn.close()
            
        else:
            print(f"❌ Database '{db_config['database']}' does not exist")
            print("💡 Run: python scripts/setup_database.py to create the database")
            await conn.close()
            
    except asyncpg.InvalidPasswordError:
        print("❌ Invalid password for database user")
        print("💡 Check your DB_PASSWORD in .env file")
    except asyncpg.InvalidAuthorizationSpecificationError:
        print("❌ Invalid username or authentication failed")
        print("💡 Check your DB_USER and DB_PASSWORD in .env file")
    except asyncpg.ConnectionDoesNotExistError:
        print("❌ Database server not found")
        print("💡 Check your DB_HOST and DB_PORT in .env file")
        print("💡 Make sure PostgreSQL is running")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Check your database configuration")


async def main():
    """Main function"""
    await test_database_connection()


if __name__ == "__main__":
    asyncio.run(main()) 