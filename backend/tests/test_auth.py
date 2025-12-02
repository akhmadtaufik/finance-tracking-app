import pytest
from httpx import AsyncClient


class TestAuthentication:
    """Test authentication endpoints."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass!23"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "password" not in data
    
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post("/auth/register", json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak"  # Too short, no uppercase, no digit
        })
        
        assert response.status_code == 422
        assert "VALIDATION_ERROR" in response.text
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post("/auth/register", json={
            "email": test_user["email"],  # Already exists
            "username": "another",
            "password": "AnotherPass!23"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login returns tokens."""
        response = await client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Check refresh token cookie
        assert "refresh_token" in response.cookies
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": "WrongPassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/auth/token",
            data={
                "username": "nobody@example.com",
                "password": "SomePass123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
    
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers):
        """Test getting current user profile."""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test accessing protected route without token fails."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
