"""
Prompts for parsing vendor responses and extracting structured data.
"""

VENDOR_RESPONSE_PARSING_SYSTEM_PROMPT = """Extract quote information from a vendor's response.

Return a JSON object with:
- price: float or null (extract the dollar amount if mentioned)
- availability_date: ISO format string or null (extract the date if mentioned)
- notes: string (any additional relevant information)

Be lenient in parsing - extract what you can and use null for missing information.

Example input: "We can do the job for $450. Available next Tuesday."
Example output:
{
  "price": 450.0,
  "availability_date": "2024-02-01T09:00:00",
  "notes": "Available next Tuesday"
}

Example input: "Sorry, we're fully booked this week."
Example output:
{
  "price": null,
  "availability_date": null,
  "notes": "Fully booked this week, declined quote"
}"""


def VENDOR_RESPONSE_PARSING_USER_PROMPT(response_text: str) -> str:
    """Generate user prompt for response parsing."""
    return f"""Parse this vendor response and extract quote information:

"{response_text}"

Return JSON with price, availability_date, and notes."""
