import pytest
from httpx import AsyncClient


class TestTransactions:
    """Test transaction endpoints."""
    
    @pytest.fixture
    async def setup_wallets(self, client, auth_headers):
        """Create two wallets via API."""
        response_a = await client.post(
            "/wallets",
            json={"name": "Wallet A", "balance": 1000000},
            headers=auth_headers
        )
        wallet_a = response_a.json()
        
        response_b = await client.post(
            "/wallets",
            json={"name": "Wallet B", "balance": 500000},
            headers=auth_headers
        )
        wallet_b = response_b.json()
        
        return {
            "wallet_a": wallet_a,
            "wallet_b": wallet_b
        }
    
    @pytest.fixture
    async def setup_category(self, client, auth_headers):
        """Get global expense category (seeded during test_db setup)."""
        response = await client.get("/categories", headers=auth_headers)
        categories = response.json()
        
        # Find an EXPENSE category
        expense_cat = next(
            (c for c in categories if c["type"] == "EXPENSE"),
            None
        )
        
        # If no category exists, create one
        if not expense_cat:
            response = await client.post(
                "/categories",
                json={"name": "Food", "type": "EXPENSE", "icon": "utensils"},
                headers=auth_headers
            )
            expense_cat = response.json()
        
        return expense_cat
    
    async def test_create_transaction_success(
        self, client: AsyncClient, auth_headers, setup_wallets, setup_category
    ):
        """Test creating a transaction."""
        response = await client.post(
            "/transactions",
            json={
                "wallet_id": setup_wallets["wallet_a"]["id"],
                "category_id": setup_category["id"],
                "amount": 50000,
                "type": "EXPENSE",
                "description": "Lunch"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "50000.00"
        assert data["type"] == "EXPENSE"
    
    async def test_create_transaction_negative_amount(
        self, client: AsyncClient, auth_headers, setup_wallets, setup_category
    ):
        """Test creating transaction with negative amount fails."""
        response = await client.post(
            "/transactions",
            json={
                "wallet_id": setup_wallets["wallet_a"]["id"],
                "category_id": setup_category["id"],
                "amount": -50000,  # Negative
                "type": "EXPENSE"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        assert "greater than 0" in response.text
    
    async def test_create_transaction_xss_description(
        self, client: AsyncClient, auth_headers, setup_wallets, setup_category
    ):
        """Test XSS in description is rejected."""
        response = await client.post(
            "/transactions",
            json={
                "wallet_id": setup_wallets["wallet_a"]["id"],
                "category_id": setup_category["id"],
                "amount": 50000,
                "type": "EXPENSE",
                "description": "<script>alert('xss')</script>"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        assert "HTML/Script" in response.text


class TestTransferFunds:
    """Integration tests for wallet-to-wallet transfers."""
    
    @pytest.fixture
    async def setup_transfer_wallets(self, client, auth_headers, test_user):
        """Create two wallets via API."""
        response_a = await client.post(
            "/wallets",
            json={"name": "Source Wallet", "balance": 1000000},
            headers=auth_headers
        )
        wallet_a = response_a.json()
        
        response_b = await client.post(
            "/wallets",
            json={"name": "Destination Wallet", "balance": 200000},
            headers=auth_headers
        )
        wallet_b = response_b.json()
        
        return {
            "source": wallet_a,
            "dest": wallet_b,
            "user_id": test_user["id"]
        }
    
    async def test_transfer_success(
        self, client: AsyncClient, auth_headers, setup_transfer_wallets
    ):
        """Test successful fund transfer between wallets."""
        source = setup_transfer_wallets["source"]
        dest = setup_transfer_wallets["dest"]
        transfer_amount = 300000
        
        # Perform transfer
        response = await client.post(
            "/transactions/transfer",
            json={
                "source_wallet_id": source["id"],
                "dest_wallet_id": dest["id"],
                "amount": transfer_amount,
                "description": "Test transfer"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Transfer successful"
        assert float(data["amount"]) == transfer_amount
        
        # Verify balances via API
        response = await client.get("/wallets", headers=auth_headers)
        wallets = response.json()
        
        # Find our wallets by ID
        new_source = next(w for w in wallets if w["id"] == source["id"])
        new_dest = next(w for w in wallets if w["id"] == dest["id"])
        
        # Verify source wallet balance decreased
        expected_source_balance = float(source["balance"]) - transfer_amount
        assert float(new_source["balance"]) == expected_source_balance
        
        # Verify destination wallet balance increased
        expected_dest_balance = float(dest["balance"]) + transfer_amount
        assert float(new_dest["balance"]) == expected_dest_balance
    
    async def test_transfer_insufficient_balance(
        self, client: AsyncClient, auth_headers, setup_transfer_wallets
    ):
        """Test transfer fails when source has insufficient balance."""
        source = setup_transfer_wallets["source"]
        dest = setup_transfer_wallets["dest"]
        
        response = await client.post(
            "/transactions/transfer",
            json={
                "source_wallet_id": source["id"],
                "dest_wallet_id": dest["id"],
                "amount": 5000000,  # More than source balance
                "description": "Too much"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]
    
    async def test_transfer_same_wallet(
        self, client: AsyncClient, auth_headers, setup_transfer_wallets
    ):
        """Test transfer to same wallet fails."""
        source = setup_transfer_wallets["source"]
        
        response = await client.post(
            "/transactions/transfer",
            json={
                "source_wallet_id": source["id"],
                "dest_wallet_id": source["id"],  # Same wallet
                "amount": 100000
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "must be different" in response.json()["detail"]
    
    async def test_transfer_zero_amount(
        self, client: AsyncClient, auth_headers, setup_transfer_wallets
    ):
        """Test transfer with zero amount fails."""
        source = setup_transfer_wallets["source"]
        dest = setup_transfer_wallets["dest"]
        
        response = await client.post(
            "/transactions/transfer",
            json={
                "source_wallet_id": source["id"],
                "dest_wallet_id": dest["id"],
                "amount": 0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"]
