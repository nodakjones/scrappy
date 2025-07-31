# 🚨 CRITICAL SETUP NOTES FOR DEVELOPERS

**READ THIS FIRST** before making any changes to the system configuration.

## ⚠️ NEVER OVERWRITE EXISTING CONFIGURATION FILES

### `.env` File - EXTREMELY IMPORTANT
- **NEVER copy .env.template over an existing .env file**
- **ALWAYS check if .env exists first**: `ls -la .env`
- **If .env exists, read it first** to understand current configuration
- **The .env file contains critical API keys and database passwords**
- **Overwriting .env will break the working system**

**Safe approach:**
```bash
# ALWAYS check first
if [ -f .env ]; then
    echo "⚠️  .env file exists - DO NOT OVERWRITE"
    echo "Current configuration:"
    cat .env
else
    echo "✅ Safe to create .env from template"
    cp .env.template .env
fi
```

## 🗄️ DATABASE CONSIDERATIONS

### Check Database State First
- **Database may already be populated** with processed data
- **NEVER assume database is empty**
- **Check for existing data before running setup scripts**

**Safe approach:**
```bash
# Check if database exists and has data
python3 -c "
import asyncio
from src.database.connection import DatabasePool

async def check_db():
    try:
        db = DatabasePool()
        await db.initialize()
        count = await db.pool.fetchval('SELECT COUNT(*) FROM contractors')
        print(f'Database has {count:,} contractors')
        await db.close()
    except Exception as e:
        print(f'Database check failed: {e}')

asyncio.run(check_db())
"
```

## 🔄 RECOVERY PROCEDURES

### If You Accidentally Overwrite .env:
1. **Don't panic** - the system can be recovered
2. **Check git history** for any clues about previous configuration
3. **The user likely has the API keys** - ask them for:
   - OpenAI API key
   - Google API key  
   - Google Search Engine ID
   - Database password (if any)
4. **PostgreSQL authentication** may need to be configured

### If Database is Empty But Should Have Data:
1. **Check if PostgreSQL is running**
2. **Verify database authentication**
3. **Look for backup files or dumps**
4. **May need to re-import from CSV and restart processing**

## 📋 PRE-FLIGHT CHECKLIST

Before making ANY system changes:

- [ ] Check if .env file exists
- [ ] Check database connection and record count
- [ ] Verify PostgreSQL is running
- [ ] Look for any processing logs or export files
- [ ] Ask user about current system state
- [ ] Read SETUP_COMPLETE.md and SYSTEM_READY.md if they exist

## 🎯 COMMON MISTAKES TO AVOID

1. **Assuming fresh setup** when system may already be configured
2. **Overwriting configuration files** without checking
3. **Running database setup** on populated database
4. **Not checking for running background processes**
5. **Making changes without understanding current state**

## 💡 BEST PRACTICES

1. **Always check existing state first**
2. **Ask user about current configuration**
3. **Read documentation files in the repo**
4. **Test database connectivity before making changes**
5. **Create backups before major changes**
6. **Document any configuration changes made**

---

**Remember: It's better to ask the user about the current state than to assume and break a working system.**