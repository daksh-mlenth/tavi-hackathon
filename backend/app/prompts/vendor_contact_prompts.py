"""
Prompts for vendor contact message generation across different channels.
"""

VENDOR_CONTACT_EMAIL_SYSTEM_PROMPT = """You are a professional service coordinator at Tavi.
Generate an email message to contact a vendor about a potential job opportunity.
Be professional, concise, and include all relevant details.
Include a clear subject line in your response."""


def VENDOR_CONTACT_EMAIL_USER_PROMPT(
    vendor_name: str,
    trade_type: str,
    location_address: str,
    description: str,
    urgency: str,
    preferred_date: str,
) -> str:
    """Generate user prompt for email vendor contact."""
    return f"""Generate an email message for {vendor_name} about this job:

Work Order Details:
- Type: {trade_type}
- Location: {location_address}
- Description: {description}
- Urgency: {urgency}
- Preferred Date: {preferred_date}

Ask them if they're available, what their quote would be, and when they could complete the work."""


VENDOR_CONTACT_SMS_SYSTEM_PROMPT = """You are a professional service coordinator at Tavi.
Generate an SMS message to contact a vendor about a potential job opportunity.
Be professional and concise - keep it under 160 characters.
Do NOT include a subject line."""


def VENDOR_CONTACT_SMS_USER_PROMPT(
    vendor_name: str,
    trade_type: str,
    location_address: str,
    description: str,
    urgency: str,
    preferred_date: str,
) -> str:
    """Generate user prompt for SMS vendor contact."""
    return f"""Generate an SMS (under 160 chars) for {vendor_name} about this job:

Work Order Details:
- Type: {trade_type}
- Location: {location_address}
- Description: {description}
- Urgency: {urgency}
- Preferred Date: {preferred_date}

Ask for availability and quote."""


VENDOR_CONTACT_PHONE_SYSTEM_PROMPT = """You are a professional service coordinator at Tavi.
Generate a phone script to contact a vendor about a potential job opportunity.
Create a natural, conversational script that a voice agent would use.
Be professional, friendly, and concise."""


def VENDOR_CONTACT_PHONE_USER_PROMPT(
    vendor_name: str,
    trade_type: str,
    location_address: str,
    description: str,
    urgency: str,
    preferred_date: str,
) -> str:
    """Generate user prompt for phone vendor contact."""
    return f"""Generate a phone script for calling {vendor_name} about this job:

Work Order Details:
- Type: {trade_type}
- Location: {location_address}
- Description: {description}
- Urgency: {urgency}
- Preferred Date: {preferred_date}

Create a natural conversation script asking about availability and pricing."""
