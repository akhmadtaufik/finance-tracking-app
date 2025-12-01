from datetime import datetime
from typing import Optional
import asyncpg


class RefreshTokenRepository:
    """Repository for managing refresh tokens in the database."""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
    
    async def create(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> dict:
        """Store a new refresh token hash."""
        row = await self.conn.fetchrow("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, token_hash, expires_at, is_revoked, created_at
        """, user_id, token_hash, expires_at, user_agent, ip_address)
        return dict(row) if row else None
    
    async def get_by_hash(self, token_hash: str) -> Optional[dict]:
        """Get a valid (non-revoked, non-expired) token by its hash."""
        row = await self.conn.fetchrow("""
            SELECT id, user_id, token_hash, expires_at, is_revoked, created_at
            FROM refresh_tokens 
            WHERE token_hash = $1 
              AND is_revoked = FALSE 
              AND expires_at > NOW()
        """, token_hash)
        return dict(row) if row else None
    
    async def revoke(self, token_hash: str) -> bool:
        """Revoke a specific token by its hash."""
        result = await self.conn.execute("""
            UPDATE refresh_tokens 
            SET is_revoked = TRUE 
            WHERE token_hash = $1
        """, token_hash)
        return result == "UPDATE 1"
    
    async def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke all tokens for a user (logout from all devices)."""
        result = await self.conn.execute("""
            UPDATE refresh_tokens 
            SET is_revoked = TRUE 
            WHERE user_id = $1 AND is_revoked = FALSE
        """, user_id)
        # Extract count from "UPDATE N"
        return int(result.split()[1]) if result.startswith("UPDATE") else 0
    
    async def cleanup_expired(self) -> int:
        """Remove expired tokens from the database."""
        result = await self.conn.execute("""
            DELETE FROM refresh_tokens 
            WHERE expires_at < NOW() OR is_revoked = TRUE
        """)
        return int(result.split()[1]) if result.startswith("DELETE") else 0
    
    async def get_active_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user."""
        rows = await self.conn.fetch("""
            SELECT id, created_at, expires_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE user_id = $1 AND is_revoked = FALSE AND expires_at > NOW()
            ORDER BY created_at DESC
        """, user_id)
        return [dict(row) for row in rows]
