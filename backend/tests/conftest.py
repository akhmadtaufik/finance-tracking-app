import asyncio
import os
import sys
import secrets
import pytest
import pytest_asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set test database URL
TEST_DATABASE_URL = "postgresql://postgres:Rnpl1105@localhost:5432/finance_test_db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
TEST_USER_PASSWORD = os.getenv("TEST_PASSWORD") or secrets.token_urlsafe(24)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create and setup test database, teardown after all tests."""
    # Connect to default postgres to create test db
    sys_conn = await asyncpg.connect(
        "postgresql://postgres:Rnpl1105@localhost:5432/postgres"
    )
    
    # Drop if exists and create fresh test database
    await sys_conn.execute("DROP DATABASE IF EXISTS finance_test_db")
    await sys_conn.execute("CREATE DATABASE finance_test_db")
    await sys_conn.close()
    
    # Connect to test database and create schema
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    
    # Read and execute schema
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "db", "schema.sql"
    )
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    await conn.execute(schema_sql)
    
    # Create refresh_tokens table (from security migration)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_revoked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_agent VARCHAR(255),
            ip_address VARCHAR(45)
        )
    """)
    
    await conn.close()
    
    # Create connection pool for tests
    pool = await asyncpg.create_pool(TEST_DATABASE_URL, min_size=2, max_size=5)
    
    yield pool
    
    # Teardown: close pool and drop database
    await pool.close()
    
    sys_conn = await asyncpg.connect(
        "postgresql://postgres:Rnpl1105@localhost:5432/postgres"
    )
    await sys_conn.execute("DROP DATABASE IF EXISTS finance_test_db")
    await sys_conn.close()


@pytest_asyncio.fixture
async def db_conn(test_db):
    """Get a connection from the test pool for each test."""
    async with test_db.acquire() as conn:
        yield conn


@pytest_asyncio.fixture
async def client(test_db):
    """Create async test client with dependency override."""
    from backend.main import app
    from backend.app.core.database import get_db_conn
    
    # Override database dependency
    async def override_get_db_conn():
        async with test_db.acquire() as conn:
            yield conn
    
    app.dependency_overrides[get_db_conn] = override_get_db_conn
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(client):
    """Create a test user via API and return user data with password."""
    password = TEST_USER_PASSWORD
    
    # Register user via API
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": password
    })
    
    if response.status_code == 201:
        data = response.json()
        return {**data, "password": password}
    elif response.status_code == 400:
        # User already exists, return existing data
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "password": password
        }
    else:
        raise Exception(f"Failed to create test user: {response.text}")


@pytest_asyncio.fixture
async def auth_token(client, test_user):
    """Login and return access token."""
    response = await client.post(
        "/auth/token",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Return authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
