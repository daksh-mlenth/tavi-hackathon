"""
Constants used across the backend application.
Centralized configuration for models, parameters, and thresholds.
"""

# AI Model Configuration
AI_MODEL = "gpt-4o-mini"
AI_TEMPERATURE_PARSING = 0.2  # Zero temperature for structured extraction - NO hallucinations
AI_TEMPERATURE_GENERATION = 0.7  # Higher temperature for creative message generation
AI_MAX_TOKENS_SHORT = 100  # For SMS and short responses
AI_MAX_TOKENS_MEDIUM = 500  # For emails and detailed responses
AI_MAX_TOKENS_LONG = 1000  # For comprehensive responses

# Vendor Discovery Configuration
VENDOR_SEARCH_RADIUS_METERS = 48280  # 30 miles in meters
VENDOR_SEARCH_LIMIT = 30  # Maximum vendors to discover per work order (show top 5, load more button shows remaining)
VENDOR_SCORE_REVIEW_WEIGHT = 50  # Weight for normalizing review counts

# Quote Scoring Weights
QUOTE_PRICE_WEIGHT = 0.4  # 40% weight on price
QUOTE_QUALITY_WEIGHT = 0.4  # 40% weight on vendor quality
QUOTE_AVAILABILITY_WEIGHT = 0.2  # 20% weight on availability

# Communication Configuration
SMS_MAX_LENGTH = 160  # Standard SMS length
EMAIL_FROM_ADDRESS = "noreply@tavi.com"
EMAIL_SUBJECT_PREFIX = "Service Opportunity"

# Vendor Contact Strategy
CONTACT_RETRY_DELAY_SECONDS = 5
CONTACT_TIMEOUT_SECONDS = 30

# Status Update Configuration
POLLING_INTERVAL_SECONDS = 5

# Trade Type Mappings
TRADE_TYPE_SEARCH_QUERIES = {
    "plumbing": "plumber",
    "electrical": "electrician",
    "hvac": "HVAC contractor",
    "landscaping": "landscaping service",
    "roofing": "roofing contractor",
    "painting": "painting contractor",
    "carpentry": "carpenter",
    "cleaning": "cleaning service",
    "pest_control": "pest control",
    "general_maintenance": "handyman service"
}

# API Response Formats
RESPONSE_FORMAT_JSON = {"type": "json_object"}

# Default Values
DEFAULT_URGENCY = "medium"
DEFAULT_TRADE_TYPE = "general_maintenance"
DEFAULT_VENDOR_SCORE = 50.0
DEFAULT_CURRENCY = "USD"
DEFAULT_COUNTRY = "United States"

# Country to Currency Mapping (ISO 4217 currency codes with symbols)
COUNTRY_CURRENCY_MAP = {
    # North America
    "united states": {"code": "USD", "symbol": "$", "name": "US Dollar"},
    "usa": {"code": "USD", "symbol": "$", "name": "US Dollar"},
    "canada": {"code": "CAD", "symbol": "C$", "name": "Canadian Dollar"},
    "mexico": {"code": "MXN", "symbol": "MX$", "name": "Mexican Peso"},
    
    # Europe
    "united kingdom": {"code": "GBP", "symbol": "£", "name": "British Pound"},
    "uk": {"code": "GBP", "symbol": "£", "name": "British Pound"},
    "germany": {"code": "EUR", "symbol": "€", "name": "Euro"},
    "france": {"code": "EUR", "symbol": "€", "name": "Euro"},
    "spain": {"code": "EUR", "symbol": "€", "name": "Euro"},
    "italy": {"code": "EUR", "symbol": "€", "name": "Euro"},
    "switzerland": {"code": "CHF", "symbol": "CHF", "name": "Swiss Franc"},
    
    # Asia
    "india": {"code": "INR", "symbol": "₹", "name": "Indian Rupee"},
    "china": {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan"},
    "japan": {"code": "JPY", "symbol": "¥", "name": "Japanese Yen"},
    "singapore": {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar"},
    "hong kong": {"code": "HKD", "symbol": "HK$", "name": "Hong Kong Dollar"},
    "south korea": {"code": "KRW", "symbol": "₩", "name": "South Korean Won"},
    "thailand": {"code": "THB", "symbol": "฿", "name": "Thai Baht"},
    "malaysia": {"code": "MYR", "symbol": "RM", "name": "Malaysian Ringgit"},
    "indonesia": {"code": "IDR", "symbol": "Rp", "name": "Indonesian Rupiah"},
    "philippines": {"code": "PHP", "symbol": "₱", "name": "Philippine Peso"},
    "vietnam": {"code": "VND", "symbol": "₫", "name": "Vietnamese Dong"},
    
    # Middle East
    "united arab emirates": {"code": "AED", "symbol": "د.إ", "name": "UAE Dirham"},
    "uae": {"code": "AED", "symbol": "د.إ", "name": "UAE Dirham"},
    "saudi arabia": {"code": "SAR", "symbol": "﷼", "name": "Saudi Riyal"},
    "qatar": {"code": "QAR", "symbol": "﷼", "name": "Qatari Riyal"},
    
    # Oceania
    "australia": {"code": "AUD", "symbol": "A$", "name": "Australian Dollar"},
    "new zealand": {"code": "NZD", "symbol": "NZ$", "name": "New Zealand Dollar"},
    
    # South America
    "brazil": {"code": "BRL", "symbol": "R$", "name": "Brazilian Real"},
    "argentina": {"code": "ARS", "symbol": "$", "name": "Argentine Peso"},
    
    # Africa
    "south africa": {"code": "ZAR", "symbol": "R", "name": "South African Rand"},
    "nigeria": {"code": "NGN", "symbol": "₦", "name": "Nigerian Naira"},
    "egypt": {"code": "EGP", "symbol": "E£", "name": "Egyptian Pound"},
}

def get_currency_info(country: str) -> dict:
    """
    Get currency information for a country (case-insensitive).
    Returns currency code, symbol, and name.
    """
    country_lower = country.lower().strip() if country else ""
    return COUNTRY_CURRENCY_MAP.get(country_lower, {
        "code": DEFAULT_CURRENCY,
        "symbol": "$",
        "name": "US Dollar"
    })
