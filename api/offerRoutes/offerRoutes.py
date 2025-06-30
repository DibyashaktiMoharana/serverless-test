from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
import os

# Create API Router for offers
offerRouter = APIRouter()

# Pydantic model for offers based on the table schema
class Offer(BaseModel):
    title: str
    description: str
    valid_till: str
    code: str
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    category: str
    duration: str
    brand: str
    type: str
    payment: str
    offer_details: str
    terms_and_conditions: str
    how_to_redeem: str
    avail_offer_link: Optional[str] = None



# Helper function to make PostgREST requests
async def query_postgrest(endpoint: str, params: dict = None, method: str = "GET", data: dict = None):
    """Query PostgREST endpoint"""
    POSTGREST_URL = os.getenv("POSTGREST_URL")
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{POSTGREST_URL}{endpoint}", params=params)
        elif method == "POST":
            response = await client.post(f"{POSTGREST_URL}{endpoint}", json=data, params=params)
        elif method == "PATCH":
            response = await client.patch(f"{POSTGREST_URL}{endpoint}", json=data, params=params)
        elif method == "DELETE":
            response = await client.delete(f"{POSTGREST_URL}{endpoint}", params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None


@offerRouter.get("/search", response_model=List[Offer])
async def search_offers(
    q: str = Query(..., description="Search query"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Search offers across multiple fields"""
    try:
        params = {
            'or': f"(title.ilike.*{q}*,description.ilike.*{q}*,category.ilike.*{q}*,brand.ilike.*{q}*,offer_details.ilike.*{q}*)",
            'limit': limit
        }
        data = await query_postgrest("/offers", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offerRouter.get("/by_category", response_model=List[Offer])
async def get_offers_by_category(
    category: str = Query(..., description="Category to filter by"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Get offers by specific category"""
    try:
        params = {
            'category': f"eq.{category}",
            'limit': limit
        }
        data = await query_postgrest("/offers", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offerRouter.get("/by_brand", response_model=List[Offer])
async def get_offers_by_brand(
    brand: str = Query(..., description="Brand to filter by"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Get offers by specific brand"""
    try:
        params = {
            'brand': f"eq.{brand}",
            'limit': limit
        }
        data = await query_postgrest("/offers", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offerRouter.get("/active", response_model=List[Offer])
async def get_active_offers(
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Get currently active offers (based on valid_till date)"""
    try:
        from datetime import datetime
        today = datetime.now().strftime("%d-%m-%Y")
        params = {
            'valid_till': f"gte.{today}",
            'limit': limit,
            'order': 'valid_till.asc'
        }
        data = await query_postgrest("/offers", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 #future use
# @offerRouter.delete("/{offer_id}")
# async def delete_offer(offer_id: int):
#     """Delete an offer"""
#     try:
#         params = {'id': f"eq.{offer_id}"}
#         await query_postgrest("/offers", method="DELETE", params=params)
#         return {"message": f"Offer {offer_id} deleted successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@offerRouter.get("/categories", response_model=List[str])
async def get_offer_categories():
    """Get all unique offer categories"""
    try:
        params = {'select': 'category'}
        data = await query_postgrest("/offers", params)
        categories = list(set([item['category'] for item in data if item['category']]))
        return sorted(categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offerRouter.get("/brands", response_model=List[str])
async def get_offer_brands():
    """Get all unique offer brands"""
    try:
        params = {'select': 'brand'}
        data = await query_postgrest("/offers", params)
        brands = list(set([item['brand'] for item in data if item['brand']]))
        return sorted(brands)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 