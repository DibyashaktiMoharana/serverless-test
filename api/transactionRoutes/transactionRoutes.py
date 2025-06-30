from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Union
import httpx
import os
import re
from datetime import datetime, timedelta

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

@transactionRouter.get("/aggregate_by_mcc")
async def aggregate_transactions_by_mcc(
    mcc: int = Query(..., description="Merchant Category Code (MCC) to aggregate"),
    card_number: str = Query(..., description="Card number (supports partial matching)")
):
    """Get transaction aggregations (sum, average, count) for a specific MCC and card number"""
    try:
        # Filter by both MCC and card number
        params = {
            'MCC': f"eq.{mcc}",
            'card_no': f"ilike.*{card_number}*"
        }
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {
                "message": "No transaction data found",
                "mcc_code": mcc,
                "card_number_filter": card_number,
                "details": "No transactions found for this MCC and card number combination"
            }
        
        # Calculate aggregations for the specific MCC and card combination
        amounts = [transaction.get('source_amt', 0) for transaction in data if transaction.get('source_amt')]
        reward_points = [transaction.get('reward_points', 0) for transaction in data]
        
        # Get unique transaction dates for date range info
        transaction_dates = []
        for transaction in data:
            txn_date = transaction.get('txn_date')
            if txn_date:
                try:
                    parsed_date = datetime.strptime(txn_date, "%d/%m/%Y")
                    transaction_dates.append(parsed_date)
                except:
                    continue
        
        # Calculate date range
        date_range = None
        if transaction_dates:
            earliest_date = min(transaction_dates).strftime("%d/%m/%Y")
            latest_date = max(transaction_dates).strftime("%d/%m/%Y")
            date_range = f"{earliest_date} to {latest_date}"
        
        # Get unique merchants/particulars
        merchants = list(set([transaction.get('particulars', '') for transaction in data if transaction.get('particulars')]))
        
        # Mask card number for privacy
        masked_card = f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else card_number
        
        aggregation_result = {
            "mcc_code": mcc,
            "card_number_masked": masked_card,
            "card_number_filter": card_number,
            "transaction_count": len(data),
            "total_amount": round(sum(amounts), 2) if amounts else 0,
            "average_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
            "min_amount": round(min(amounts), 2) if amounts else 0,
            "max_amount": round(max(amounts), 2) if amounts else 0,
            "total_reward_points": sum(reward_points) if reward_points else 0,
            "average_reward_points": round(sum(reward_points) / len(reward_points), 2) if reward_points else 0,
            "date_range": date_range,
            "unique_merchants": len(merchants),
            "top_merchants": merchants[:5] if merchants else []
        }
        
        return {
            "aggregation_type": "by_specific_mcc_and_card",
            "filter_applied": {
                "mcc": mcc,
                "card_number": card_number
            },
            "aggregation": aggregation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/aggregate_by_card")
async def aggregate_transactions_by_card(
    mcc: Optional[int] = Query(None, description="Optional MCC filter"),
    min_transactions: Optional[int] = Query(1, description="Minimum number of transactions for inclusion")
):
    """Get transaction aggregations (sum, average, count) grouped by card number"""
    try:
        params = {}
        if mcc:
            params['MCC'] = f"eq.{mcc}"
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {"message": "No transaction data found"}
        
        # Group by card number
        card_aggregates = {}
        for transaction in data:
            card_no = transaction.get('card_no')
            amount = transaction.get('source_amt', 0)
            reward_points = transaction.get('reward_points', 0)
            
            if card_no and amount:
                if card_no not in card_aggregates:
                    card_aggregates[card_no] = {
                        'transactions': [],
                        'total_amount': 0,
                        'total_reward_points': 0,
                        'count': 0,
                        'mcc_codes': set()
                    }
                
                card_aggregates[card_no]['transactions'].append(amount)
                card_aggregates[card_no]['total_amount'] += amount
                card_aggregates[card_no]['total_reward_points'] += reward_points
                card_aggregates[card_no]['count'] += 1
                if transaction.get('MCC'):
                    card_aggregates[card_no]['mcc_codes'].add(transaction.get('MCC'))
        
        # Calculate final aggregations
        result = {}
        for card_no, data in card_aggregates.items():
            if data['count'] >= min_transactions:
                # Mask card number for privacy (show only last 4 digits)
                masked_card = f"****-****-****-{card_no[-4:]}" if len(card_no) >= 4 else card_no
                
                result[card_no] = {
                    'card_number_masked': masked_card,
                    'transaction_count': data['count'],
                    'total_amount': round(data['total_amount'], 2),
                    'average_amount': round(data['total_amount'] / data['count'], 2),
                    'min_amount': round(min(data['transactions']), 2),
                    'max_amount': round(max(data['transactions']), 2),
                    'total_reward_points': data['total_reward_points'],
                    'average_reward_points': round(data['total_reward_points'] / data['count'], 2),
                    'unique_mcc_codes': len(data['mcc_codes']),
                    'mcc_codes_used': sorted(list(data['mcc_codes']))
                }
        
        # Sort by total amount descending
        sorted_result = dict(sorted(result.items(), key=lambda x: x[1]['total_amount'], reverse=True))
        
        return {
            "aggregation_type": "by_card",
            "total_cards": len(sorted_result),
            "filter_applied": f"mcc: {mcc}" if mcc else "none",
            "aggregations": sorted_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/aggregate_by_month")
async def aggregate_transactions_by_month(
    year: Optional[int] = Query(None, description="Filter by specific year (e.g., 2025)"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    min_transactions: Optional[int] = Query(1, description="Minimum number of transactions for inclusion")
):
    """Get transaction aggregations (sum, average, count) grouped by month/year"""
    try:
        params = {}
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {"message": "No transaction data found"}
        
        # Helper function to parse dates
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        # Group by month/year
        month_aggregates = {}
        for transaction in data:
            txn_date = transaction.get('txn_date')
            amount = transaction.get('source_amt', 0)
            reward_points = transaction.get('reward_points', 0)
            
            if txn_date and amount:
                parsed_date = parse_date(txn_date)
                if parsed_date:
                    # Filter by year if specified
                    if year and parsed_date.year != year:
                        continue
                    
                    month_key = f"{parsed_date.year}-{parsed_date.month:02d}"
                    month_name = parsed_date.strftime("%B %Y")
                    
                    if month_key not in month_aggregates:
                        month_aggregates[month_key] = {
                            'month_name': month_name,
                            'year': parsed_date.year,
                            'month': parsed_date.month,
                            'transactions': [],
                            'total_amount': 0,
                            'total_reward_points': 0,
                            'count': 0,
                            'unique_cards': set(),
                            'unique_mcc_codes': set()
                        }
                    
                    month_aggregates[month_key]['transactions'].append(amount)
                    month_aggregates[month_key]['total_amount'] += amount
                    month_aggregates[month_key]['total_reward_points'] += reward_points
                    month_aggregates[month_key]['count'] += 1
                    month_aggregates[month_key]['unique_cards'].add(transaction.get('card_no'))
                    if transaction.get('MCC'):
                        month_aggregates[month_key]['unique_mcc_codes'].add(transaction.get('MCC'))
        
        # Calculate final aggregations
        result = {}
        for month_key, data in month_aggregates.items():
            if data['count'] >= min_transactions:
                result[month_key] = {
                    'month_name': data['month_name'],
                    'year': data['year'],
                    'month': data['month'],
                    'transaction_count': data['count'],
                    'total_amount': round(data['total_amount'], 2),
                    'average_amount': round(data['total_amount'] / data['count'], 2),
                    'min_amount': round(min(data['transactions']), 2),
                    'max_amount': round(max(data['transactions']), 2),
                    'total_reward_points': data['total_reward_points'],
                    'average_reward_points': round(data['total_reward_points'] / data['count'], 2),
                    'unique_cards': len(data['unique_cards']),
                    'unique_mcc_codes': len(data['unique_mcc_codes'])
                }
        
        # Sort by year and month
        sorted_result = dict(sorted(result.items()))
        
        return {
            "aggregation_type": "by_month",
            "total_months": len(sorted_result),
            "filter_applied": {
                "year": year,
                "card_number": card_number
            },
            "aggregations": sorted_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/aggregate_by_date_range")
async def aggregate_transactions_by_date_range(
    from_date: str = Query(..., description="From date in DD/MM/YYYY format"),
    to_date: str = Query(..., description="To date in DD/MM/YYYY format"),
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    mcc: Optional[int] = Query(None, description="Optional MCC filter"),
    group_by_days: Optional[int] = Query(None, description="Group results by number of days (e.g., 7 for weekly)")
):
    """Get transaction aggregations for a specific date range with optional grouping"""
    try:
        # Validate date format
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, from_date) or not re.match(date_pattern, to_date):
            raise HTTPException(status_code=400, detail="Date format must be DD/MM/YYYY")
        
        params = {}
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        if mcc:
            params['MCC'] = f"eq.{mcc}"
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {"message": "No transaction data found"}
        
        # Helper function to parse dates
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        from_dt = parse_date(from_date)
        to_dt = parse_date(to_date)
        
        # Filter transactions within date range
        filtered_transactions = []
        for transaction in data:
            txn_dt = parse_date(transaction.get('txn_date', ''))
            if txn_dt and from_dt <= txn_dt <= to_dt:
                filtered_transactions.append(transaction)
        
        if not filtered_transactions:
            return {"message": "No transactions found in the specified date range"}
        
        # Aggregate the data
        if group_by_days:
            # Group by specified day intervals
            groups = {}
            for transaction in filtered_transactions:
                txn_dt = parse_date(transaction.get('txn_date', ''))
                if txn_dt:
                    days_from_start = (txn_dt - from_dt).days
                    group_number = days_from_start // group_by_days
                    group_start = from_dt + timedelta(days=group_number * group_by_days)
                    group_end = min(group_start + timedelta(days=group_by_days - 1), to_dt)
                    
                    group_key = f"Group_{group_number + 1}"
                    group_range = f"{group_start.strftime('%d/%m/%Y')} to {group_end.strftime('%d/%m/%Y')}"
                    
                    if group_key not in groups:
                        groups[group_key] = {
                            'date_range': group_range,
                            'transactions': [],
                            'total_amount': 0,
                            'total_reward_points': 0,
                            'count': 0,
                            'unique_cards': set(),
                            'unique_mcc_codes': set()
                        }
                    
                    amount = transaction.get('source_amt', 0)
                    reward_points = transaction.get('reward_points', 0)
                    
                    groups[group_key]['transactions'].append(amount)
                    groups[group_key]['total_amount'] += amount
                    groups[group_key]['total_reward_points'] += reward_points
                    groups[group_key]['count'] += 1
                    groups[group_key]['unique_cards'].add(transaction.get('card_no'))
                    if transaction.get('MCC'):
                        groups[group_key]['unique_mcc_codes'].add(transaction.get('MCC'))
            
            # Calculate aggregations for groups
            result = {}
            for group_key, data in groups.items():
                result[group_key] = {
                    'date_range': data['date_range'],
                    'transaction_count': data['count'],
                    'total_amount': round(data['total_amount'], 2),
                    'average_amount': round(data['total_amount'] / data['count'], 2),
                    'min_amount': round(min(data['transactions']), 2),
                    'max_amount': round(max(data['transactions']), 2),
                    'total_reward_points': data['total_reward_points'],
                    'average_reward_points': round(data['total_reward_points'] / data['count'], 2),
                    'unique_cards': len(data['unique_cards']),
                    'unique_mcc_codes': len(data['unique_mcc_codes'])
                }
        else:
            # Single aggregation for entire date range
            amounts = [t.get('source_amt', 0) for t in filtered_transactions if t.get('source_amt')]
            reward_points = [t.get('reward_points', 0) for t in filtered_transactions]
            unique_cards = set([t.get('card_no') for t in filtered_transactions if t.get('card_no')])
            unique_mccs = set([t.get('MCC') for t in filtered_transactions if t.get('MCC')])
            
            result = {
                'overall': {
                    'date_range': f"{from_date} to {to_date}",
                    'transaction_count': len(filtered_transactions),
                    'total_amount': round(sum(amounts), 2),
                    'average_amount': round(sum(amounts) / len(amounts), 2) if amounts else 0,
                    'min_amount': round(min(amounts), 2) if amounts else 0,
                    'max_amount': round(max(amounts), 2) if amounts else 0,
                    'total_reward_points': sum(reward_points),
                    'average_reward_points': round(sum(reward_points) / len(reward_points), 2) if reward_points else 0,
                    'unique_cards': len(unique_cards),
                    'unique_mcc_codes': len(unique_mccs)
                }
            }
        
        return {
            "aggregation_type": "by_date_range",
            "date_range": f"{from_date} to {to_date}",
            "group_by_days": group_by_days,
            "filter_applied": {
                "card_number": card_number,
                "mcc": mcc
            },
            "aggregations": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/aggregate_comprehensive")
async def aggregate_transactions_comprehensive(
    card_number: Optional[str] = Query(None, description="Optional card number filter"),
    mcc: Optional[int] = Query(None, description="Optional MCC filter"),
    month: Optional[int] = Query(None, description="Optional month filter (1-12)", ge=1, le=12),
    year: Optional[int] = Query(None, description="Optional year filter"),
    min_amount: Optional[float] = Query(None, description="Optional minimum amount filter"),
    top_n: Optional[int] = Query(10, description="Number of top results to show for each category")
):
    """Get comprehensive transaction aggregations with multiple groupings and insights"""
    try:
        params = {}
        if card_number:
            params['card_no'] = f"ilike.*{card_number}*"
        if mcc:
            params['MCC'] = f"eq.{mcc}"
        
        # Get all transactions for analysis
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {"message": "No transaction data found"}
        
        # Helper function to parse dates
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        # Filter by additional criteria
        filtered_transactions = []
        for transaction in data:
            include = True
            
            # Date filters
            if month or year:
                txn_dt = parse_date(transaction.get('txn_date', ''))
                if txn_dt:
                    if month and txn_dt.month != month:
                        include = False
                    if year and txn_dt.year != year:
                        include = False
                else:
                    include = False
            
            # Amount filter
            if min_amount and transaction.get('source_amt', 0) < min_amount:
                include = False
            
            if include:
                filtered_transactions.append(transaction)
        
        if not filtered_transactions:
            return {"message": "No transactions found matching the criteria"}
        
        # Overall statistics
        amounts = [t.get('source_amt', 0) for t in filtered_transactions if t.get('source_amt')]
        reward_points = [t.get('reward_points', 0) for t in filtered_transactions]
        
        overall_stats = {
            'total_transactions': len(filtered_transactions),
            'total_amount': round(sum(amounts), 2),
            'average_amount': round(sum(amounts) / len(amounts), 2) if amounts else 0,
            'min_amount': round(min(amounts), 2) if amounts else 0,
            'max_amount': round(max(amounts), 2) if amounts else 0,
            'total_reward_points': sum(reward_points),
            'average_reward_points': round(sum(reward_points) / len(reward_points), 2) if reward_points else 0
        }
        
        # Group by MCC
        mcc_groups = {}
        card_groups = {}
        month_groups = {}
        
        for transaction in filtered_transactions:
            # MCC grouping
            mcc_code = transaction.get('MCC')
            if mcc_code:
                if mcc_code not in mcc_groups:
                    mcc_groups[mcc_code] = {'amount': 0, 'count': 0, 'reward_points': 0}
                mcc_groups[mcc_code]['amount'] += transaction.get('source_amt', 0)
                mcc_groups[mcc_code]['count'] += 1
                mcc_groups[mcc_code]['reward_points'] += transaction.get('reward_points', 0)
            
            # Card grouping
            card_no = transaction.get('card_no')
            if card_no:
                if card_no not in card_groups:
                    card_groups[card_no] = {'amount': 0, 'count': 0, 'reward_points': 0}
                card_groups[card_no]['amount'] += transaction.get('source_amt', 0)
                card_groups[card_no]['count'] += 1
                card_groups[card_no]['reward_points'] += transaction.get('reward_points', 0)
            
            # Month grouping
            txn_dt = parse_date(transaction.get('txn_date', ''))
            if txn_dt:
                month_key = f"{txn_dt.year}-{txn_dt.month:02d}"
                if month_key not in month_groups:
                    month_groups[month_key] = {'amount': 0, 'count': 0, 'reward_points': 0, 'month_name': txn_dt.strftime('%B %Y')}
                month_groups[month_key]['amount'] += transaction.get('source_amt', 0)
                month_groups[month_key]['count'] += 1
                month_groups[month_key]['reward_points'] += transaction.get('reward_points', 0)
        
        # Top MCCs by amount
        top_mccs = dict(sorted(mcc_groups.items(), key=lambda x: x[1]['amount'], reverse=True)[:top_n])
        for mcc, data in top_mccs.items():
            data['average_amount'] = round(data['amount'] / data['count'], 2)
            data['total_amount'] = round(data['amount'], 2)
        
        # Top cards by amount
        top_cards = dict(sorted(card_groups.items(), key=lambda x: x[1]['amount'], reverse=True)[:top_n])
        for card, data in top_cards.items():
            data['average_amount'] = round(data['amount'] / data['count'], 2)
            data['total_amount'] = round(data['amount'], 2)
            data['card_masked'] = f"****-****-****-{card[-4:]}" if len(card) >= 4 else card
        
        # Top months by amount
        top_months = dict(sorted(month_groups.items(), key=lambda x: x[1]['amount'], reverse=True)[:top_n])
        for month_key, data in top_months.items():
            data['average_amount'] = round(data['amount'] / data['count'], 2)
            data['total_amount'] = round(data['amount'], 2)
        
        return {
            "aggregation_type": "comprehensive",
            "filters_applied": {
                "card_number": card_number,
                "mcc": mcc,
                "month": month,
                "year": year,
                "min_amount": min_amount
            },
            "overall_statistics": overall_stats,
            "top_mcc_codes": top_mccs,
            "top_cards": top_cards,
            "top_months": top_months,
            "summary": {
                "unique_mcc_codes": len(mcc_groups),
                "unique_cards": len(card_groups),
                "unique_months": len(month_groups)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactionRouter.get("/aggregate_by_card_and_mcc_array")
async def aggregate_transactions_by_card_and_mcc_array(
    card_number: str = Query(..., description="Card number (supports partial matching)"),
    mcc_codes: List[int] = Query(..., description="Array of MCC codes to aggregate (e.g., [5411,5812,4111])")
):
    """Get transaction aggregations for a specific card across multiple MCC codes"""
    try:
        # Validate input
        if not mcc_codes:
            raise HTTPException(status_code=400, detail="At least one MCC code must be provided")
        
        # Get all transactions for the card number first
        params = {
            'card_no': f"ilike.*{card_number}*"
        }
        
        data = await query_postgrest("/transactions", params)
        
        if not data:
            return {
                "message": "No transaction data found",
                "card_number_filter": card_number,
                "mcc_codes_filter": mcc_codes,
                "details": "No transactions found for this card number"
            }
        
        # Filter transactions by the specified MCC codes
        filtered_transactions = []
        for transaction in data:
            transaction_mcc = transaction.get('MCC')
            if transaction_mcc and transaction_mcc in mcc_codes:
                filtered_transactions.append(transaction)
        
        if not filtered_transactions:
            return {
                "message": "No transactions found for the specified MCC codes",
                "card_number_filter": card_number,
                "mcc_codes_filter": mcc_codes,
                "total_transactions_for_card": len(data),
                "details": "Card has transactions but none match the specified MCC codes"
            }
        
        # Helper function to parse dates
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return None
        
        # Group transactions by MCC code
        mcc_aggregates = {}
        overall_amounts = []
        overall_reward_points = []
        transaction_dates = []
        unique_merchants = set()
        
        for transaction in filtered_transactions:
            mcc = transaction.get('MCC')
            amount = transaction.get('source_amt', 0)
            reward_points = transaction.get('reward_points', 0)
            txn_date = transaction.get('txn_date')
            particulars = transaction.get('particulars', '')
            
            # Collect overall data
            if amount:
                overall_amounts.append(amount)
            overall_reward_points.append(reward_points)
            
            if particulars:
                unique_merchants.add(particulars)
            
            # Parse and collect transaction dates
            if txn_date:
                parsed_date = parse_date(txn_date)
                if parsed_date:
                    transaction_dates.append(parsed_date)
            
            # Group by MCC
            if mcc and amount:
                if mcc not in mcc_aggregates:
                    mcc_aggregates[mcc] = {
                        'transactions': [],
                        'total_amount': 0,
                        'total_reward_points': 0,
                        'count': 0,
                        'merchants': set(),
                        'dates': []
                    }
                
                mcc_aggregates[mcc]['transactions'].append(amount)
                mcc_aggregates[mcc]['total_amount'] += amount
                mcc_aggregates[mcc]['total_reward_points'] += reward_points
                mcc_aggregates[mcc]['count'] += 1
                if particulars:
                    mcc_aggregates[mcc]['merchants'].add(particulars)
                if parsed_date:
                    mcc_aggregates[mcc]['dates'].append(parsed_date)
        
        # Calculate date range
        date_range = None
        if transaction_dates:
            earliest_date = min(transaction_dates).strftime("%d/%m/%Y")
            latest_date = max(transaction_dates).strftime("%d/%m/%Y")
            date_range = f"{earliest_date} to {latest_date}"
        
        # Calculate individual MCC aggregations
        mcc_results = {}
        for mcc, data in mcc_aggregates.items():
            mcc_date_range = None
            if data['dates']:
                earliest = min(data['dates']).strftime("%d/%m/%Y")
                latest = max(data['dates']).strftime("%d/%m/%Y")
                mcc_date_range = f"{earliest} to {latest}"
            
            mcc_results[str(mcc)] = {
                'mcc_code': mcc,
                'transaction_count': data['count'],
                'total_amount': round(data['total_amount'], 2),
                'average_amount': round(data['total_amount'] / data['count'], 2),
                'min_amount': round(min(data['transactions']), 2),
                'max_amount': round(max(data['transactions']), 2),
                'total_reward_points': data['total_reward_points'],
                'average_reward_points': round(data['total_reward_points'] / data['count'], 2),
                'unique_merchants': len(data['merchants']),
                'top_merchants': list(data['merchants'])[:5],
                'date_range': mcc_date_range,
                'percentage_of_total': round((data['total_amount'] / sum(overall_amounts)) * 100, 2) if overall_amounts else 0
            }
        
        # Sort MCC results by total amount descending
        sorted_mcc_results = dict(sorted(mcc_results.items(), key=lambda x: x[1]['total_amount'], reverse=True))
        
        # Overall aggregations
        masked_card = f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else card_number
        
        overall_aggregation = {
            'card_number_masked': masked_card,
            'card_number_filter': card_number,
            'mcc_codes_analyzed': sorted(mcc_codes),
            'mcc_codes_found': sorted(list(mcc_aggregates.keys())),
            'missing_mcc_codes': sorted([mcc for mcc in mcc_codes if mcc not in mcc_aggregates]),
            'total_transactions': len(filtered_transactions),
            'total_amount': round(sum(overall_amounts), 2) if overall_amounts else 0,
            'average_amount': round(sum(overall_amounts) / len(overall_amounts), 2) if overall_amounts else 0,
            'min_amount': round(min(overall_amounts), 2) if overall_amounts else 0,
            'max_amount': round(max(overall_amounts), 2) if overall_amounts else 0,
            'total_reward_points': sum(overall_reward_points),
            'average_reward_points': round(sum(overall_reward_points) / len(overall_reward_points), 2) if overall_reward_points else 0,
            'date_range': date_range,
            'unique_merchants_across_all_mccs': len(unique_merchants),
            'top_merchants_across_all_mccs': list(unique_merchants)[:10]
        }
        
        # Calculate distribution percentages
        mcc_distribution = {}
        total_amount = sum(overall_amounts) if overall_amounts else 1
        for mcc, data in mcc_aggregates.items():
            mcc_distribution[str(mcc)] = {
                'mcc_code': mcc,
                'amount': round(data['total_amount'], 2),
                'percentage': round((data['total_amount'] / total_amount) * 100, 2),
                'transaction_count': data['count']
            }
        
        return {
            "aggregation_type": "by_card_and_mcc_array",
            "filter_applied": {
                "card_number": card_number,
                "mcc_codes": mcc_codes
            },
            "overall_aggregation": overall_aggregation,
            "mcc_breakdown": sorted_mcc_results,
            "spending_distribution": dict(sorted(mcc_distribution.items(), key=lambda x: x[1]['amount'], reverse=True)),
            "summary": {
                "total_mcc_codes_requested": len(mcc_codes),
                "mcc_codes_with_transactions": len(mcc_aggregates),
                "coverage_percentage": round((len(mcc_aggregates) / len(mcc_codes)) * 100, 2),
                "top_spending_mcc": max(mcc_aggregates.keys(), key=lambda x: mcc_aggregates[x]['total_amount']) if mcc_aggregates else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 