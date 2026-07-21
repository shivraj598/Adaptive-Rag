"""
Authentication middleware for FastAPI routes.
"""

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.db.supabase_client import SUPABASE_URL, SUPABASE_ANON_KEY

security = HTTPBearer(auto_error=False)

_AUTH_HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with Supabase and return user info."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                **_AUTH_HEADERS,
                "Authorization": f"Bearer {token}",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return resp.json()
