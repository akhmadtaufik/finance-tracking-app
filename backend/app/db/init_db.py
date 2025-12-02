import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@finance.com")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

DEFAULT_CATEGORIES = [
    # INCOME categories
    ("Gaji", "INCOME", "wallet"),
    ("Bonus", "INCOME", "gift"),
    ("Hadiah", "INCOME", "present"),
    ("Investasi", "INCOME", "trending-up"),
    ("Penjualan", "INCOME", "shopping-bag"),
    ("Lainnya", "INCOME", "more-horizontal"),
    # EXPENSE categories
    ("Makanan", "EXPENSE", "utensils"),
    ("Transportasi", "EXPENSE", "car"),
    ("Tagihan", "EXPENSE", "file-text"),
    ("Belanja", "EXPENSE", "shopping-cart"),
    ("Hiburan", "EXPENSE", "film"),
    ("Kesehatan", "EXPENSE", "heart"),
    ("Pendidikan", "EXPENSE", "book"),
    ("Cicilan", "EXPENSE", "credit-card"),
    ("Donasi", "EXPENSE", "hand-heart"),
]


async def init_database():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Read and execute schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        print("Creating tables...")
        await conn.execute(schema_sql)
        print("Tables created successfully!")
        
        # Check if categories table is empty
        count = await conn.fetchval("SELECT COUNT(*) FROM categories WHERE user_id IS NULL")
        
        if count == 0:
            print("Seeding default categories...")
            for name, cat_type, icon in DEFAULT_CATEGORIES:
                await conn.execute(
                    """
                    INSERT INTO categories (user_id, name, type, icon)
                    VALUES (NULL, $1, $2, $3)
                    ON CONFLICT (user_id, name, type) DO NOTHING
                    """,
                    name, cat_type, icon
                )
            print(f"Seeded {len(DEFAULT_CATEGORIES)} default categories!")
        else:
            print(f"Categories already exist ({count} global categories found). Skipping seed.")
        
        # Check if superuser exists
        superuser = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            ADMIN_EMAIL
        )
        
        if not superuser:
            if not ADMIN_PASSWORD:
                print("WARNING: ADMIN_PASSWORD not set. Skipping superuser creation.")
            else:
                print("Creating superuser account...")
                hashed_password = pwd_context.hash(ADMIN_PASSWORD)
                await conn.execute(
                    """
                    INSERT INTO users (email, username, password_hash, is_superuser, is_active)
                    VALUES ($1, $2, $3, TRUE, TRUE)
                    ON CONFLICT (email) DO UPDATE SET is_superuser = TRUE
                    """,
                    ADMIN_EMAIL, ADMIN_USERNAME, hashed_password
                )
                print(f"Superuser created: {ADMIN_EMAIL}")
        else:
            print("Superuser already exists. Skipping.")
        
        print("Database initialization complete!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
