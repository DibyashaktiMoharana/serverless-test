from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os

# Create API Router
creditCardMetaData = APIRouter()

# Pydantic model for credit card
class CreditCard(BaseModel):
    card_name: str
    type: str
    key_features_and_benefits: str
    target_audience: str

# Helper function to make PostgREST requests
async def query_postgrest(endpoint: str, params: dict = None):
    """Query PostgREST endpoint"""
    POSTGREST_URL = os.getenv("POSTGREST_URL")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POSTGREST_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

@creditCardMetaData.get("", response_model=List[CreditCard])
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

@creditCardMetaData.get("/search", response_model=List[CreditCard])
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

@creditCardMetaData.get("/by_type", response_model=List[CreditCard])
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
