from fastapi import APIRouter
from datetime import datetime
import httpx
import os

# Create API Router for health checks
healthCheckRouter = APIRouter()

# Helper function to make PostgREST requests (for health check)
async def query_postgrest(endpoint: str, params: dict = None):
    """Query PostgREST endpoint"""
    POSTGREST_URL = os.getenv("POSTGREST_URL")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POSTGREST_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

@healthCheckRouter.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test PostgREST connection
        await query_postgrest("/bob_credit_card_types", {"limit": 1})
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()} 