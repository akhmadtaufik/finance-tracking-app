"""
Security Migration: Create refresh_tokens table for JWT refresh token rotation.
Run: python -m backend.app.db.migrate_security
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

MIGRATION_SQL = """
-- Create refresh_tokens table for token rotation
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent VARCHAR(255),
    ip_address VARCHAR(45)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
"""


async def run_migration():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not set")
        return
    
    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        print("Running security migration...")
        await conn.execute(MIGRATION_SQL)
        print("Migration completed successfully!")
        
        # Verify table created
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'refresh_tokens'
        """)
        
        if result > 0:
            print("✓ refresh_tokens table created")
        else:
            print("✗ Failed to create refresh_tokens table")
            
    except Exception as e:
        print(f"Migration error: {e}")
        raise
    finally:
        await conn.close()
        print("Database connection closed")


if __name__ == "__main__":
    asyncio.run(run_migration())
