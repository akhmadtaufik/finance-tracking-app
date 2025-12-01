import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

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
        
        print("Database initialization complete!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
