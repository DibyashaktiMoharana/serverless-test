from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Union
import httpx
import os

# Create API Router for customer metadata
customerMetaDataRouter = APIRouter()

# Pydantic model for customer credit card holder based on the actual table schema
class CustomerCreditCardHolder(BaseModel):
    cardholder_name: str = Field(..., alias="Cardholder Name")
    address: str = Field(..., alias="Address")
    card_type: str = Field(..., alias="Card Type")
    state: str = Field(..., alias="State")
    card_no: str = Field(..., alias="Card No.")
    statement_date: str = Field(..., alias="Statement Date")
    statement_period: str = Field(..., alias="Statement Period")
    sanctioned_credit_limit: int = Field(..., alias="Sanctioned Credit Limit")
    credit_limit: int = Field(..., alias="Credit Limit")
    available_credit_limit: int = Field(..., alias="Available Credit Limit")
    cash_limit: int = Field(..., alias="Cash Limit")
    available_cash_limit: int = Field(..., alias="Available Cash Limit")
    payment_due_date: str = Field(..., alias="Payment Due Date")
    minimum_amount_due: float = Field(..., alias="Minimum Amount Due")
    total_amount_due: str = Field(..., alias="Total Amount Due")
    opening_balance: float = Field(..., alias="Opening Balance")
    payment_credits: float = Field(..., alias="Payment/Credits")
    new_purchases_debits: float = Field(..., alias="New Purchases/Debits")
    closing_balance: float = Field(..., alias="Closing Balance")
    online_pay_id: str = Field(..., alias="Online Pay I.D.")
    bonus_reward_points_opening: int = Field(..., alias="Bonus/Reward Points Opening")
    bonus_reward_points_earned: int = Field(..., alias="Bonus/Reward Points Earned")
    bonus_reward_points_redeemed_expired: int = Field(..., alias="Bonus/Reward Points Redeemed/Expired")
    bonus_reward_points_closing: int = Field(..., alias="Bonus/Reward Points Closing")

    class Config:
        populate_by_name = True

# Helper function to make PostgREST requests
async def query_postgrest(endpoint: str, params: dict = None, method: str = "GET"):
    """Query PostgREST endpoint"""
    POSTGREST_URL = os.getenv("POSTGREST_URL")
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{POSTGREST_URL}{endpoint}", params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else []

@customerMetaDataRouter.get("/search", response_model=List[CustomerCreditCardHolder])
async def search_customers(
    q: str = Query(..., description="Search query - searches across name, card number, and card type"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Generic search across customer name, card number, and card type"""
    try:
        params = {
            'or': f"(Cardholder Name.ilike.*{q}*,Card No..ilike.*{q}*,Card Type.ilike.*{q}*,State.ilike.*{q}*)",
            'limit': limit
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/search_by_name", response_model=List[CustomerCreditCardHolder])
async def search_customers_by_name(
    name: str = Query(..., description="Customer name to search for")
):
    """Search customers by cardholder name"""
    try:
        params = {
            'Cardholder Name': f"ilike.*{name}*",
            'order': 'Cardholder Name.asc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/search_by_card_number", response_model=List[CustomerCreditCardHolder])
async def search_customers_by_card_number(
    card_number: str = Query(..., description="Card number (can be partial, e.g., last 4 digits)"),
    limit: Optional[int] = Query(10, description="Limit results")
):
    """Search customers by card number (supports partial matching)"""
    try:
        params = {
            'Card No.': f"ilike.*{card_number}*",
            'limit': limit,
            'order': 'Cardholder Name.asc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/search_by_card_type", response_model=List[CustomerCreditCardHolder])
async def search_customers_by_card_type(
    card_type: str = Query(..., description="Card type to filter by"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search customers by card type"""
    try:
        params = {
            'Card Type': f"eq.{card_type}",
            'limit': limit,
            'order': 'Cardholder Name.asc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/search_by_state", response_model=List[CustomerCreditCardHolder])
async def search_customers_by_state(
    state: str = Query(..., description="State to filter by"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search customers by state"""
    try:
        params = {
            'State': f"ilike.*{state}*",
            'limit': limit,
            'order': 'Cardholder Name.asc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/card_types", response_model=List[str])
async def get_card_types():
    """Get all unique card types"""
    try:
        params = {'select': 'Card Type'}
        data = await query_postgrest("/bob_credit_card_holders", params)
        card_types = list(set([item['Card Type'] for item in data if item['Card Type']]))
        return sorted(card_types)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/states", response_model=List[str])
async def get_states():
    """Get all unique states"""
    try:
        params = {'select': 'State'}
        data = await query_postgrest("/bob_credit_card_holders", params)
        states = list(set([item['State'] for item in data if item['State']]))
        return sorted(states)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/high_credit_limit", response_model=List[CustomerCreditCardHolder])
async def get_high_credit_limit_customers(
    min_limit: int = Query(100000, description="Minimum credit limit"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Get customers with high credit limits"""
    try:
        params = {
            'Credit Limit': f"gte.{min_limit}",
            'limit': limit,
            'order': 'Credit Limit.desc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/payment_due_soon", response_model=List[CustomerCreditCardHolder])
async def get_customers_payment_due_soon(
    days_ahead: int = Query(7, description="Number of days ahead to check for due payments"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Get customers with payments due soon"""
    try:
        from datetime import datetime, timedelta
        
        # Calculate the target date
        target_date = datetime.now() + timedelta(days=days_ahead)
        target_date_str = target_date.strftime("%d/%m/%Y")
        
        params = {
            'Payment Due Date': f"lte.{target_date_str}",
            'limit': limit,
            'order': 'Payment Due Date.asc'
        }
        data = await query_postgrest("/bob_credit_card_holders", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@customerMetaDataRouter.get("/statistics")
async def get_customer_statistics():
    """Get basic statistics about customers"""
    try:
        # Get all customers for statistics
        all_customers = await query_postgrest("/bob_credit_card_holders", {})
        
        if not all_customers:
            return {"message": "No customer data found"}
        
        # Calculate statistics
        total_customers = len(all_customers)
        
        # Card type distribution
        card_types = {}
        credit_limits = []
        states = {}
        
        for customer in all_customers:
            # Card type stats
            card_type = customer.get('Card Type', 'Unknown')
            card_types[card_type] = card_types.get(card_type, 0) + 1
            
            # Credit limit stats
            if customer.get('Credit Limit'):
                credit_limits.append(customer['Credit Limit'])
            
            # State stats
            state = customer.get('State', 'Unknown')
            states[state] = states.get(state, 0) + 1
        
        # Calculate credit limit statistics
        avg_credit_limit = sum(credit_limits) / len(credit_limits) if credit_limits else 0
        max_credit_limit = max(credit_limits) if credit_limits else 0
        min_credit_limit = min(credit_limits) if credit_limits else 0
        
        return {
            "total_customers": total_customers,
            "card_type_distribution": card_types,
            "credit_limit_stats": {
                "average": round(avg_credit_limit, 2),
                "maximum": max_credit_limit,
                "minimum": min_credit_limit
            },
            "top_5_states": dict(sorted(states.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
