from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
from datetime import datetime
import os
from dotenv import load_dotenv
from api.creditCardMetaData.creditCardMetaDataRoutes import creditCardMetaData
from api.utilities.healthCheckRoutes import healthCheckRouter
from api.offerRoutes.offerRoutes import offerRouter
from api.customerMetaData.customerMetaDataRoutes import customerMetaDataRouter
from api.transactionRoutes.transactionRoutes import transactionRouter

load_dotenv()

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
POSTGREST_URL = os.getenv("POSTGREST_URL")

# Validate required environment variables
if not POSTGREST_URL:
    raise ValueError("POSTGREST_URL environment variable is required")

@app.get("/")
async def root():
    return {
        "message": "BOB Credit Card API",
        "endpoints": [
            "/credit_cards - Get all credit cards",
            "/credit_cards/search?q={query} - Search credit cards",
            "/credit_cards/by_type?type={type} - Filter by card type",
            "/offers - Get all offers",
            "/offers/search?q={query} - Search offers",
            "/offers/by_category?category={category} - Filter by category",
            "/offers/by_brand?brand={brand} - Filter by brand",
            "/offers/active - Get active offers",
            "/customers/search?q={query} - Generic customer search",
            "/customers/search_by_name?name={name} - Search by name",
            "/customers/search_by_card_number?card_number={card_number} - Search by card number",
            "/customers/search_by_card_type?card_type={card_type} - Search by card type",
            "/customers/statistics - Get customer statistics",
            "/transactions/search_by_card_number?card_number={card_number} - Search transactions by card",
            "/transactions/search_by_mcc?mcc={mcc} - Search by merchant category code",
            "/transactions/search_by_month?month={month}&year={year} - Search by month/year",
            "/transactions/search_by_date_range?from_date={from_date}&to_date={to_date} - Search date range",
            "/transactions/search_by_specific_date?date={date} - Search specific date",
            "/transactions/search_by_card_and_mcc?card_number={card_number}&mcc={mcc} - Card + MCC filter",
            "/transactions/search_by_card_and_month?card_number={card_number}&month={month}&year={year} - Card + Month filter",
            "/transactions/search_by_card_and_merchant?card_number={card_number}&merchant={merchant} - Card + Merchant filter",
            "/transactions/search_by_card_and_date_range?card_number={card_number}&from_date={from_date}&to_date={to_date} - Card + Date range filter",
            "/transactions/search_by_card_advanced?card_number={card_number}&mcc={mcc}&merchant={merchant} - Advanced combined filters",
            "/transactions/get_transaction_summary - Get transaction statistics",
            "/transactions/aggregate_by_mcc?mcc={mcc}&card_number={card_number} - Aggregate transactions for specific MCC and card",
            "/transactions/aggregate_by_card - Aggregate transactions by card number", 
            "/transactions/aggregate_by_month - Aggregate transactions by month/year",
            "/transactions/aggregate_by_date_range - Aggregate transactions by date range with optional grouping",
            "/transactions/aggregate_comprehensive - Comprehensive aggregation with multiple groupings",
            "/transactions/aggregate_by_card_and_mcc_array?card_number={card_number}&mcc_codes={mcc_codes} - Aggregate by card and multiple MCC codes"
        ],
        "timestamp": datetime.now().isoformat()
    }

# Include credit card routes using APIRouter
app.include_router(
    creditCardMetaData,
    prefix="/credit_cards",
    tags=["credit_cards"],
    responses={404: {"description": "Not found"}}
)

# Include offer routes using APIRouter
app.include_router(
    offerRouter,
    prefix="/offers",
    tags=["offers"],
    responses={404: {"description": "Not found"}}
)

# Include customer metadata routes using APIRouter
app.include_router(
    customerMetaDataRouter,
    prefix="/customers",
    tags=["customers"],
    responses={404: {"description": "Not found"}}
)

# Include transaction routes using APIRouter
app.include_router(
    transactionRouter,
    prefix="/transactions",
    tags=["transactions"],
    responses={404: {"description": "Not found"}}
)

# Include health check routes using APIRouter
app.include_router(
    healthCheckRouter,
    tags=["health"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
