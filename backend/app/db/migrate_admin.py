import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def migrate():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Adding is_superuser column...")
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE
        """)
        
        print("Adding is_active column...")
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
        """)
        
        print("Migration completed successfully!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
