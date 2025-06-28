from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
from datetime import datetime

app = FastAPI(
    title="BOB Credit Card API",
    description="Simple API to query BOB Credit Card Types using PostgREST",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neon PostgREST endpoint
POSTGREST_URL = "https://app-tight-fog-08751337.dpl.myneon.app"

# Pydantic model for credit card
class CreditCard(BaseModel):
    card_name: str
    type: str
    key_features_and_benefits: str
    target_audience: str

# Helper function to make PostgREST requests
async def query_postgrest(endpoint: str, params: dict = None):
    """Query PostgREST endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POSTGREST_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BOB Credit Card API",
        "endpoints": [
            "/credit_cards - Get all credit cards",
            "/credit_cards/search?q={query} - Search credit cards",
            "/credit_cards/by_type?type={type} - Filter by card type"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/credit_cards", response_model=List[CreditCard])
async def get_credit_cards(
    limit: Optional[int] = Query(None, description="Limit results"),
    offset: Optional[int] = Query(None, description="Offset for pagination"),
    card_name: Optional[str] = Query(None, description="Filter by card name"),
    type: Optional[str] = Query(None, description="Filter by type"),
    target_audience: Optional[str] = Query(None, description="Filter by target audience")
):
    """Get credit cards with optional filtering"""
    try:
        params = {}
        
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset
        if card_name:
            params['card_name'] = f"ilike.*{card_name}*"
        if type:
            params['type'] = f"ilike.*{type}*"
        if target_audience:
            params['target_audience'] = f"ilike.*{target_audience}*"
            
        data = await query_postgrest("/bob_credit_card_types", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/credit_cards/search", response_model=List[CreditCard])
async def search_credit_cards(
    q: str = Query(..., description="Search query"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Search credit cards across all fields"""
    try:
        params = {
            'or': f"(card_name.ilike.*{q}*,type.ilike.*{q}*,key_features_and_benefits.ilike.*{q}*,target_audience.ilike.*{q}*)",
            'limit': limit
        }
        data = await query_postgrest("/bob_credit_card_types", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/credit_cards/by_type", response_model=List[CreditCard])
async def get_cards_by_type(
    card_type: str = Query(..., description="Card type to filter by"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Get credit cards by specific type"""
    try:
        params = {
            'type': f"eq.{card_type}",
            'limit': limit
        }
        data = await query_postgrest("/bob_credit_card_types", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test PostgREST connection
        await query_postgrest("/bob_credit_card_types", {"limit": 1})
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
