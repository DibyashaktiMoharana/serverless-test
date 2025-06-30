from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Union
import httpx
import os
import re
from datetime import datetime

# Create API Router for transactions
transactionRouter = APIRouter()

# Pydantic model for transaction based on the actual table schema
class Transaction(BaseModel):
    card_no: str
    txn_date: str
    ref_no: str
    particulars: str
    reward_points: int
    source_currency: str
    source_amt: float
    amount: str
    mcc: int = Field(..., alias="MCC")

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

@transactionRouter.get("/search_by_card_number", response_model=List[Transaction])
async def search_transactions_by_card_number(
    card_number: str = Query(..., description="Card number (supports partial matching, e.g., last 4 digits or masked format)"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by card number"""
    try:
        params = {
            'card_no': f"ilike.*{card_number}*",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_mcc", response_model=List[Transaction])
async def search_transactions_by_mcc(
    mcc: int = Query(..., description="Merchant Category Code (MCC)"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by MCC (Merchant Category Code)"""
    try:
        params = {
            'MCC': f"eq.{mcc}",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_month", response_model=List[Transaction])
async def search_transactions_by_month(
    month: int = Query(..., description="Month (1-12)", ge=1, le=12),
    year: int = Query(..., description="Year (e.g., 2025)"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    limit: Optional[int] = Query(50, description="Limit results")
):
    """Search transactions by month and year (since txn_date is in DD/MM/YYYY format)"""
    try:
        # Format month to ensure two digits
        month_str = f"{month:02d}"
        # Create pattern for DD/MM/YYYY format - use ilike instead of regex for PostgREST
        date_pattern = f"*/{month_str}/{year}"
        
        params = {
            'txn_date': f"like.{date_pattern}",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        
        # Add card number filter if provided
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_date_range", response_model=List[Transaction])
async def search_transactions_by_date_range(
    from_date: str = Query(..., description="From date in DD/MM/YYYY format (e.g., 01/06/2025)"),
    to_date: str = Query(..., description="To date in DD/MM/YYYY format (e.g., 30/06/2025)"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    limit: Optional[int] = Query(50, description="Limit results")
):
    """Search transactions within a date range"""
    try:
        # Validate date format
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, from_date) or not re.match(date_pattern, to_date):
            raise HTTPException(status_code=400, detail="Date format must be DD/MM/YYYY")
        
        # Since PostgREST doesn't handle date comparison well with DD/MM/YYYY text format,
        # we'll get all transactions and filter in Python for now
        # For production, consider converting to proper date fields in the database
        
        params = {'limit': 1000}  # Get more records for filtering
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        data = await query_postgrest("/transactions", params)
        
        # Convert date strings to datetime objects for comparison
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        from_dt = parse_date(from_date)
        to_dt = parse_date(to_date)
        
        # Filter transactions within date range
        filtered_data = []
        for transaction in data:
            txn_dt = parse_date(transaction.get('txn_date', ''))
            if txn_dt and from_dt <= txn_dt <= to_dt:
                filtered_data.append(transaction)
        
        # Sort by date (newest first) and limit results
        filtered_data.sort(key=lambda x: parse_date(x.get('txn_date', '')), reverse=True)
        return filtered_data[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_specific_date", response_model=List[Transaction])
async def search_transactions_by_specific_date(
    date: str = Query(..., description="Specific date in DD/MM/YYYY format (e.g., 30/06/2025)"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions on a specific date"""
    try:
        # Validate date format
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, date):
            raise HTTPException(status_code=400, detail="Date format must be DD/MM/YYYY")
        
        params = {
            'txn_date': f"eq.{date}",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        
        # Add card number filter if provided
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_merchant", response_model=List[Transaction])
async def search_transactions_by_merchant(
    merchant: str = Query(..., description="Merchant name or particulars search"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by merchant name in particulars field"""
    try:
        params = {
            'particulars': f"ilike.*{merchant}*",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_high_value", response_model=List[Transaction])
async def search_high_value_transactions(
    min_amount: float = Query(1000.0, description="Minimum transaction amount"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search high-value transactions above a certain amount"""
    try:
        params = {
            'source_amt': f"gte.{min_amount}",
            'limit': limit,
            'order': 'source_amt.desc'
        }
        
        # Add card number filter if provided
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/get_mcc_categories", response_model=List[int])
async def get_unique_mcc_codes():
    """Get all unique MCC codes in the system"""
    try:
        params = {'select': 'MCC'}
        data = await query_postgrest("/transactions", params)
        mcc_codes = list(set([item['MCC'] for item in data if item.get('MCC')]))
        return sorted(mcc_codes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/get_transaction_summary")
async def get_transaction_summary(
    card_number: Optional[str] = Query(None, description="Optional card number filter")
):
    """Get transaction summary statistics"""
    try:
        params = {}
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {"message": "No transaction data found"}
        
        # Calculate statistics
        total_transactions = len(data)
        amounts = [item.get('source_amt', 0) for item in data if item.get('source_amt')]
        total_amount = sum(amounts)
        avg_amount = total_amount / len(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0
        min_amount = min(amounts) if amounts else 0
        
        # MCC distribution
        mcc_distribution = {}
        for transaction in data:
            mcc = transaction.get('MCC')
            if mcc:
                mcc_distribution[mcc] = mcc_distribution.get(mcc, 0) + 1
        
        # Currency distribution
        currency_distribution = {}
        for transaction in data:
            currency = transaction.get('source_currency', 'Unknown')
            currency_distribution[currency] = currency_distribution.get(currency, 0) + 1
        
        return {
            "total_transactions": total_transactions,
            "total_amount": round(total_amount, 2),
            "average_amount": round(avg_amount, 2),
            "maximum_amount": max_amount,
            "minimum_amount": min_amount,
            "top_5_mcc_codes": dict(sorted(mcc_distribution.items(), key=lambda x: x[1], reverse=True)[:5]),
            "currency_distribution": currency_distribution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_and_mcc", response_model=List[Transaction])
async def search_transactions_by_card_and_mcc(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    mcc: int = Query(..., description="Merchant Category Code (MCC)"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by card number AND MCC (optimized single query)"""
    try:
        params = {
            'card_no': f"ilike.*{card_number}*",
            'MCC': f"eq.{mcc}",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_and_month", response_model=List[Transaction])
async def search_transactions_by_card_and_month(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    month: int = Query(..., description="Month (1-12)", ge=1, le=12),
    year: int = Query(..., description="Year (e.g., 2025)"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by card number AND month/year (optimized single query)"""
    try:
        # Format month to ensure two digits
        month_str = f"{month:02d}"
        # Create pattern for DD/MM/YYYY format
        date_pattern = f"*/{month_str}/{year}"
        
        params = {
            'card_no': f"ilike.*{card_number}*",
            'txn_date': f"like.{date_pattern}",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_and_merchant", response_model=List[Transaction])
async def search_transactions_by_card_and_merchant(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    merchant: str = Query(..., description="Merchant name or particulars search"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by card number AND merchant (optimized single query)"""
    try:
        params = {
            'card_no': f"ilike.*{card_number}*",
            'particulars': f"ilike.*{merchant}*",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_and_date_range", response_model=List[Transaction])
async def search_transactions_by_card_and_date_range(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    from_date: str = Query(..., description="From date in DD/MM/YYYY format (e.g., 01/06/2025)"),
    to_date: str = Query(..., description="To date in DD/MM/YYYY format (e.g., 30/06/2025)"),
    limit: Optional[int] = Query(50, description="Limit results")
):
    """Search transactions by card number AND date range (optimized with PostgREST filtering)"""
    try:
        # Validate date format
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, from_date) or not re.match(date_pattern, to_date):
            raise HTTPException(status_code=400, detail="Date format must be DD/MM/YYYY")
        
        # First filter by card number, then handle date range in Python for accuracy
        # Since PostgREST doesn't handle date range comparison well with DD/MM/YYYY text format
        params = {
            'card_no': f"ilike.*{card_number}*",
            'limit': 1000  # Get more records for date filtering
        }
        
        data = await query_postgrest("/transactions", params)
        
        # Convert date strings to datetime objects for comparison
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        from_dt = parse_date(from_date)
        to_dt = parse_date(to_date)
        
        # Filter transactions within date range
        filtered_data = []
        for transaction in data:
            txn_dt = parse_date(transaction.get('txn_date', ''))
            if txn_dt and from_dt <= txn_dt <= to_dt:
                filtered_data.append(transaction)
        
        # Sort by date (newest first) and limit results
        filtered_data.sort(key=lambda x: parse_date(x.get('txn_date', '')), reverse=True)
        return filtered_data[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_and_amount_range", response_model=List[Transaction])
async def search_transactions_by_card_and_amount_range(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    min_amount: Optional[float] = Query(None, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, description="Maximum transaction amount"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Search transactions by card number AND amount range (optimized single query)"""
    try:
        params = {
            'card_no': f"ilike.*{card_number}*",
            'limit': limit,
            'order': 'source_amt.desc'
        }
        
        # Add amount filters if provided
        if min_amount is not None:
            params['source_amt'] = f"gte.{min_amount}"
        if max_amount is not None and min_amount is not None:
            params['source_amt'] = f"gte.{min_amount}"
            params['and'] = f"(source_amt.lte.{max_amount})"
        elif max_amount is not None:
            params['source_amt'] = f"lte.{max_amount}"
        
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search_by_card_advanced", response_model=List[Transaction])
async def search_transactions_by_card_advanced(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    mcc: Optional[int] = Query(None, description="Optional MCC filter"),
    merchant: Optional[str] = Query(None, description="Optional merchant filter"),
    min_amount: Optional[float] = Query(None, description="Optional minimum amount filter"),
    month: Optional[int] = Query(None, description="Optional month filter (1-12)", ge=1, le=12),
    year: Optional[int] = Query(None, description="Optional year filter (e.g., 2025)"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Advanced search by card number with multiple optional filters (optimized single query)"""
    try:
        params = {
            'card_no': f"ilike.*{card_number}*",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        
        # Add optional filters
        if mcc is not None:
            params['MCC'] = f"eq.{mcc}"
        
        if merchant:
            params['particulars'] = f"ilike.*{merchant}*"
        
        if min_amount is not None:
            params['source_amt'] = f"gte.{min_amount}"
        
        if month is not None and year is not None:
            month_str = f"{month:02d}"
            date_pattern = f"*/{month_str}/{year}"
            params['txn_date'] = f"like.{date_pattern}"
        
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/search", response_model=List[Transaction])
async def search_transactions(
    q: str = Query(..., description="Search query - searches across card number, particulars, and ref number"),
    limit: Optional[int] = Query(20, description="Limit results")
):
    """Generic search across transaction fields"""
    try:
        params = {
            'or': f"(card_no.ilike.*{q}*,particulars.ilike.*{q}*,ref_no.ilike.*{q}*)",
            'limit': limit,
            'order': 'txn_date.desc'
        }
        data = await query_postgrest("/transactions", params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 