# BOB Credit Card API

A comprehensive FastAPI application for Bank of Baroda Credit Card services, providing APIs for credit card metadata, customer information, offers, and advanced transaction analytics with powerful aggregation capabilities.

## Features

- **Credit Card Management**: Query and search credit card types and metadata
- **Customer Services**: Comprehensive customer search and account information
- **Offers Management**: Browse and filter available credit card offers
- **Transaction Analytics**: Advanced transaction search, analysis, and aggregation capabilities
- **Data Aggregation**: Comprehensive sum, average, and statistical analysis by MCC, card, month, and date ranges
- **Health Monitoring**: API health check endpoints

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with PostgREST
- **Language**: Python 3.x
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- PostgREST endpoint configured

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd serverless-test
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export POSTGREST_URL=your_postgrest_endpoint_url
```

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment
```bash
docker build -t bob-credit-api .
docker run -p 8000:8000 -e POSTGREST_URL=your_endpoint bob-credit-api
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## API Endpoints

### 🏥 Health Check

#### GET `/health`
Check the health status of the API and database connection.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

---

### 💳 Credit Cards

#### GET `/credit_cards`
Get all credit cards with optional filtering.

**Query Parameters:**
- `limit` (int, optional): Limit number of results
- `offset` (int, optional): Offset for pagination
- `card_name` (string, optional): Filter by card name
- `type` (string, optional): Filter by card type
- `target_audience` (string, optional): Filter by target audience

**Example:**
```bash
GET /credit_cards?limit=10&type=Premium
```

#### GET `/credit_cards/search`
Search credit cards across all fields.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /credit_cards/search?q=premium&limit=5
```

#### GET `/credit_cards/by_type`
Get credit cards by specific type.

**Query Parameters:**
- `card_type` (string, required): Card type to filter by
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /credit_cards/by_type?card_type=Gold
```

---

### 🎁 Offers

#### GET `/offers/search`
Search offers across multiple fields.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /offers/search?q=cashback&limit=10
```

#### GET `/offers/by_category`
Get offers by specific category.

**Query Parameters:**
- `category` (string, required): Category to filter by
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /offers/by_category?category=Travel&limit=5
```

#### GET `/offers/by_brand`
Get offers by specific brand.

**Query Parameters:**
- `brand` (string, required): Brand to filter by
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /offers/by_brand?brand=Amazon&limit=10
```

#### GET `/offers/active`
Get currently active offers based on validity date.

**Query Parameters:**
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /offers/active?limit=20
```

#### GET `/offers/categories`
Get all unique offer categories.

**Response:**
```json
["Travel", "Dining", "Shopping", "Fuel"]
```

#### GET `/offers/brands`
Get all unique offer brands.

**Response:**
```json
["Amazon", "Flipkart", "Swiggy", "Zomato"]
```

---

### 👥 Customers

#### GET `/customers/search`
Generic search across customer fields.

**Query Parameters:**
- `q` (string, required): Search query (searches name, card number, card type, state)
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /customers/search?q=John&limit=10
```

#### GET `/customers/search_by_name`
Search customers by cardholder name.

**Query Parameters:**
- `name` (string, required): Customer name to search
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /customers/search_by_name?name=John%20Doe&limit=5
```

#### GET `/customers/search_by_card_number`
Search customers by card number (supports partial matching).

**Query Parameters:**
- `card_number` (string, required): Card number (can be partial, e.g., last 4 digits)
- `limit` (int, optional, default=10): Limit results

**Example:**
```bash
GET /customers/search_by_card_number?card_number=1234&limit=5
```

#### GET `/customers/search_by_card_type`
Search customers by card type.

**Query Parameters:**
- `card_type` (string, required): Card type to filter by
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /customers/search_by_card_type?card_type=Platinum&limit=10
```

#### GET `/customers/search_by_state`
Search customers by state.

**Query Parameters:**
- `state` (string, required): State to filter by
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /customers/search_by_state?state=Maharashtra&limit=15
```

#### GET `/customers/card_types`
Get all unique card types.

**Response:**
```json
["Gold", "Platinum", "Premium", "Classic"]
```

#### GET `/customers/states`
Get all unique states.

**Response:**
```json
["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]
```

#### GET `/customers/high_credit_limit`
Get customers with high credit limits.

**Query Parameters:**
- `min_limit` (int, optional, default=100000): Minimum credit limit
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /customers/high_credit_limit?min_limit=500000&limit=10
```

#### GET `/customers/payment_due_soon`
Get customers with payments due soon.

**Query Parameters:**
- `days_ahead` (int, optional, default=7): Number of days ahead to check
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /customers/payment_due_soon?days_ahead=3&limit=15
```

#### GET `/customers/statistics`
Get comprehensive customer statistics.

**Response:**
```json
{
  "total_customers": 1500,
  "card_type_distribution": {"Gold": 500, "Platinum": 300},
  "credit_limit_stats": {
    "average": 125000.50,
    "maximum": 1000000,
    "minimum": 25000
  },
  "top_5_states": {"Maharashtra": 300, "Delhi": 250}
}
```

---

### 🏪 Transactions

#### Transaction Search Endpoints

#### GET `/transactions/search`
Generic search across transaction fields.

**Query Parameters:**
- `q` (string, required): Search query (searches card number, particulars, ref number)
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search?q=Amazon&limit=10
```

#### GET `/transactions/search_by_card_number`
Search transactions by card number.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search_by_card_number?card_number=1234&limit=15
```

#### GET `/transactions/search_by_mcc`
Search transactions by Merchant Category Code.

**Query Parameters:**
- `mcc` (int, required): Merchant Category Code
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search_by_mcc?mcc=5411&limit=10
```

#### GET `/transactions/search_by_month`
Search transactions by month and year.

**Query Parameters:**
- `month` (int, required, 1-12): Month
- `year` (int, required): Year
- `card_number` (string, optional): Optional card number filter
- `limit` (int, optional, default=50): Limit results

**Example:**
```bash
GET /transactions/search_by_month?month=6&year=2025&limit=20
```

#### GET `/transactions/search_by_date_range`
Search transactions within a date range.

**Query Parameters:**
- `from_date` (string, required): From date in DD/MM/YYYY format
- `to_date` (string, required): To date in DD/MM/YYYY format
- `card_number` (string, optional): Optional card number filter
- `limit` (int, optional, default=50): Limit results

**Example:**
```bash
GET /transactions/search_by_date_range?from_date=01/06/2025&to_date=30/06/2025&limit=25
```

#### GET `/transactions/search_by_specific_date`
Search transactions on a specific date.

**Query Parameters:**
- `date` (string, required): Specific date in DD/MM/YYYY format
- `card_number` (string, optional): Optional card number filter
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search_by_specific_date?date=15/06/2025&limit=10
```

#### GET `/transactions/search_by_merchant`
Search transactions by merchant name.

**Query Parameters:**
- `merchant` (string, required): Merchant name or particulars search
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search_by_merchant?merchant=Starbucks&limit=10
```

#### GET `/transactions/search_high_value`
Search high-value transactions above a certain amount.

**Query Parameters:**
- `min_amount` (float, optional, default=1000.0): Minimum transaction amount
- `card_number` (string, optional): Optional card number filter
- `limit` (int, optional, default=20): Limit results

**Example:**
```bash
GET /transactions/search_high_value?min_amount=5000&limit=15
```

#### GET `/transactions/get_mcc_categories`
Get all unique MCC codes in the system.

**Response:**
```json
[5411, 5812, 4111, 5541]
```

#### GET `/transactions/get_transaction_summary`
Get comprehensive transaction statistics.

**Query Parameters:**
- `card_number` (string, optional): Optional card number filter

**Response:**
```json
{
  "total_transactions": 1250,
  "total_amount": 125000.50,
  "average_amount": 100.25,
  "maximum_amount": 5000.00,
  "minimum_amount": 10.00,
  "top_5_mcc_codes": {"5411": 150, "5812": 120},
  "currency_distribution": {"INR": 1200, "USD": 50}
}
```

### 📊 Transaction Aggregation Endpoints

#### GET `/transactions/aggregate_by_mcc`
Get transaction aggregations (sum, average, count) for a specific MCC and card number combination.

**Query Parameters:**
- `mcc` (int, required): Merchant Category Code (MCC) to aggregate
- `card_number` (string, required): Card number (supports partial matching)

**Response:**
```json
{
  "aggregation_type": "by_specific_mcc_and_card",
  "filter_applied": {
    "mcc": 5411,
    "card_number": "1234"
  },
  "aggregation": {
    "mcc_code": 5411,
    "card_number_masked": "****-****-****-1234",
    "card_number_filter": "1234",
    "transaction_count": 45,
    "total_amount": 15750.25,
    "average_amount": 350.01,
    "min_amount": 50.00,
    "max_amount": 2500.00,
    "total_reward_points": 315,
    "average_reward_points": 7.0,
    "date_range": "01/01/2025 to 30/06/2025",
    "unique_merchants": 8,
    "top_merchants": ["WALMART", "KROGER", "SAFEWAY", "TARGET", "COSTCO"]
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_by_mcc?mcc=5411&card_number=1234
```

#### GET `/transactions/aggregate_by_card`
Get transaction aggregations (sum, average, count) grouped by card number.

**Query Parameters:**
- `mcc` (int, optional): Optional MCC filter
- `min_transactions` (int, optional, default=1): Minimum number of transactions for inclusion

**Response:**
```json
{
  "aggregation_type": "by_card",
  "total_cards": 25,
  "filter_applied": "mcc: 5411",
  "aggregations": {
    "1234567890123456": {
      "card_number_masked": "****-****-****-3456",
      "transaction_count": 78,
      "total_amount": 45600.75,
      "average_amount": 584.63,
      "min_amount": 25.00,
      "max_amount": 5000.00,
      "total_reward_points": 912,
      "average_reward_points": 11.69,
      "unique_mcc_codes": 12,
      "mcc_codes_used": [5411, 5812, 4111]
    }
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_by_card?mcc=5411&min_transactions=10
```

#### GET `/transactions/aggregate_by_month`
Get transaction aggregations (sum, average, count) grouped by month/year.

**Query Parameters:**
- `year` (int, optional): Filter by specific year
- `card_number` (string, optional): Optional card number filter
- `min_transactions` (int, optional, default=1): Minimum number of transactions for inclusion

**Response:**
```json
{
  "aggregation_type": "by_month",
  "total_months": 12,
  "filter_applied": {
    "year": 2025,
    "card_number": null
  },
  "aggregations": {
    "2025-06": {
      "month_name": "June 2025",
      "year": 2025,
      "month": 6,
      "transaction_count": 156,
      "total_amount": 78450.25,
      "average_amount": 503.14,
      "min_amount": 10.00,
      "max_amount": 8500.00,
      "total_reward_points": 1568,
      "average_reward_points": 10.05,
      "unique_cards": 45,
      "unique_mcc_codes": 28
    }
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_by_month?year=2025&card_number=1234
```

#### GET `/transactions/aggregate_by_date_range`
Get transaction aggregations for a specific date range with optional grouping.

**Query Parameters:**
- `from_date` (string, required): From date in DD/MM/YYYY format
- `to_date` (string, required): To date in DD/MM/YYYY format
- `card_number` (string, optional): Optional card number filter
- `mcc` (int, optional): Optional MCC filter
- `group_by_days` (int, optional): Group results by number of days (e.g., 7 for weekly)

**Response (with grouping):**
```json
{
  "aggregation_type": "by_date_range",
  "date_range": "01/06/2025 to 30/06/2025",
  "group_by_days": 7,
  "filter_applied": {
    "card_number": "1234",
    "mcc": null
  },
  "aggregations": {
    "Group_1": {
      "date_range": "01/06/2025 to 07/06/2025",
      "transaction_count": 34,
      "total_amount": 12450.75,
      "average_amount": 366.19,
      "min_amount": 25.00,
      "max_amount": 2500.00,
      "total_reward_points": 248,
      "average_reward_points": 7.29,
      "unique_cards": 12,
      "unique_mcc_codes": 15
    }
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_by_date_range?from_date=01/06/2025&to_date=30/06/2025&group_by_days=7
```

#### GET `/transactions/aggregate_comprehensive`
Get comprehensive transaction aggregations with multiple groupings and insights.

**Query Parameters:**
- `card_number` (string, optional): Optional card number filter
- `mcc` (int, optional): Optional MCC filter
- `month` (int, optional, 1-12): Optional month filter
- `year` (int, optional): Optional year filter
- `min_amount` (float, optional): Optional minimum amount filter
- `top_n` (int, optional, default=10): Number of top results to show for each category

**Response:**
```json
{
  "aggregation_type": "comprehensive",
  "filters_applied": {
    "card_number": null,
    "mcc": null,
    "month": 6,
    "year": 2025,
    "min_amount": 1000
  },
  "overall_statistics": {
    "total_transactions": 245,
    "total_amount": 156750.50,
    "average_amount": 639.80,
    "min_amount": 1000.00,
    "max_amount": 15000.00,
    "total_reward_points": 3135,
    "average_reward_points": 12.80
  },
  "top_mcc_codes": {
    "5411": {
      "count": 45,
      "total_amount": 28450.75,
      "average_amount": 632.24
    }
  },
  "top_cards": {
    "1234567890123456": {
      "card_masked": "****-****-****-3456",
      "count": 23,
      "total_amount": 18750.25,
      "average_amount": 815.23
    }
  },
  "top_months": {
    "2025-06": {
      "month_name": "June 2025",
      "count": 245,
      "total_amount": 156750.50,
      "average_amount": 639.80
    }
  },
  "summary": {
    "unique_mcc_codes": 28,
    "unique_cards": 67,
    "unique_months": 1
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_comprehensive?year=2025&min_amount=1000&top_n=5
```

#### GET `/transactions/aggregate_by_card_and_mcc_array`
Get transaction aggregations for a specific card across multiple MCC codes.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `mcc_codes` (array of int, required): Array of MCC codes to aggregate

**Response:**
```json
{
  "aggregation_type": "by_card_and_mcc_array",
  "filter_applied": {
    "card_number": "1234",
    "mcc_codes": [5411, 5812, 4111]
  },
  "overall_aggregation": {
    "card_number_masked": "****-****-****-1234",
    "mcc_codes_analyzed": [4111, 5411, 5812],
    "mcc_codes_found": [5411, 5812],
    "missing_mcc_codes": [4111],
    "total_transactions": 67,
    "total_amount": 25430.75,
    "average_amount": 379.56,
    "min_amount": 15.50,
    "max_amount": 3500.00,
    "total_reward_points": 508,
    "date_range": "05/01/2025 to 28/06/2025",
    "unique_merchants_across_all_mccs": 18
  },
  "mcc_breakdown": {
    "5411": {
      "mcc_code": 5411,
      "transaction_count": 45,
      "total_amount": 18250.25,
      "average_amount": 405.56,
      "percentage_of_total": 71.76,
      "unique_merchants": 8,
      "top_merchants": ["WALMART", "KROGER", "SAFEWAY", "TARGET", "COSTCO"]
    },
    "5812": {
      "mcc_code": 5812,
      "transaction_count": 22,
      "total_amount": 7180.50,
      "average_amount": 326.39,
      "percentage_of_total": 28.24,
      "unique_merchants": 6,
      "top_merchants": ["MCDONALD'S", "STARBUCKS", "SUBWAY", "KFC", "TACO BELL"]
    }
  },
  "spending_distribution": {
    "5411": {
      "mcc_code": 5411,
      "amount": 18250.25,
      "percentage": 71.76,
      "transaction_count": 45
    },
    "5812": {
      "mcc_code": 5812,
      "amount": 7180.50,
      "percentage": 28.24,
      "transaction_count": 22
    }
  },
  "summary": {
    "total_mcc_codes_requested": 3,
    "mcc_codes_with_transactions": 2,
    "coverage_percentage": 66.67,
    "top_spending_mcc": 5411
  }
}
```

**Example:**
```bash
GET /transactions/aggregate_by_card_and_mcc_array?card_number=1234&mcc_codes=5411&mcc_codes=5812&mcc_codes=4111
```

### Advanced Transaction Searches

#### GET `/transactions/search_by_card_and_mcc`
Search transactions by card number AND MCC.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `mcc` (int, required): Merchant Category Code
- `limit` (int, optional, default=20): Limit results

#### GET `/transactions/search_by_card_and_month`
Search transactions by card number AND month/year.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `month` (int, required, 1-12): Month
- `year` (int, required): Year
- `limit` (int, optional, default=20): Limit results

#### GET `/transactions/search_by_card_and_merchant`
Search transactions by card number AND merchant.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `merchant` (string, required): Merchant name or particulars search
- `limit` (int, optional, default=20): Limit results

#### GET `/transactions/search_by_card_and_date_range`
Search transactions by card number AND date range.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `from_date` (string, required): From date in DD/MM/YYYY format
- `to_date` (string, required): To date in DD/MM/YYYY format
- `limit` (int, optional, default=50): Limit results

#### GET `/transactions/search_by_card_and_amount_range`
Search transactions by card number AND amount range.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `min_amount` (float, optional): Minimum transaction amount
- `max_amount` (float, optional): Maximum transaction amount
- `limit` (int, optional, default=20): Limit results

#### GET `/transactions/search_by_card_advanced`
Advanced search with multiple optional filters.

**Query Parameters:**
- `card_number` (string, required): Card number (supports partial matching)
- `mcc` (int, optional): Optional MCC filter
- `merchant` (string, optional): Optional merchant filter
- `min_amount` (float, optional): Optional minimum amount filter
- `month` (int, optional, 1-12): Optional month filter
- `year` (int, optional): Optional year filter
- `limit` (int, optional, default=20): Limit results

---

## Data Models

### Credit Card
```json
{
  "card_name": "BOB Premier",
  "type": "Premium",
  "key_features_and_benefits": "...",
  "target_audience": "High Income Individuals"
}
```

### Customer Credit Card Holder
```json
{
  "cardholder_name": "John Doe",
  "address": "123 Main St",
  "card_type": "Gold",
  "state": "Maharashtra",
  "card_no": "****-****-****-1234",
  "credit_limit": 100000,
  "available_credit_limit": 75000,
  "payment_due_date": "15/02/2025",
  "minimum_amount_due": 2500.00
}
```

### Offer
```json
{
  "title": "Amazon Cashback Offer",
  "description": "Get 5% cashback on Amazon purchases",
  "valid_till": "31/12/2025",
  "category": "E-commerce",
  "brand": "Amazon",
  "type": "Cashback"
}
```

### Transaction
```json
{
  "card_no": "****-****-****-1234",
  "txn_date": "15/06/2025",
  "particulars": "AMAZON.IN",
  "source_amt": 1500.00,
  "source_currency": "INR",
  "mcc": 5964,
  "reward_points": 15
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. For production use, consider implementing rate limiting based on your requirements.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## Support

For support and questions, please refer to the API documentation at `/docs` or contact the development team.
