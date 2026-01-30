import json
from typing import Dict, Any
from openai import AsyncOpenAI

from app.config import settings
from app.constants import (
    AI_MODEL,
    AI_TEMPERATURE_PARSING,
    AI_TEMPERATURE_GENERATION,
    AI_MAX_TOKENS_SHORT,
    AI_MAX_TOKENS_MEDIUM,
    RESPONSE_FORMAT_JSON,
)
from app.prompts import (
    WORK_ORDER_PARSING_SYSTEM_PROMPT,
    WORK_ORDER_PARSING_USER_PROMPT,
    VENDOR_CONTACT_EMAIL_SYSTEM_PROMPT,
    VENDOR_CONTACT_EMAIL_USER_PROMPT,
    VENDOR_CONTACT_SMS_SYSTEM_PROMPT,
    VENDOR_CONTACT_SMS_USER_PROMPT,
    VENDOR_CONTACT_PHONE_SYSTEM_PROMPT,
    VENDOR_CONTACT_PHONE_USER_PROMPT,
    VENDOR_RESPONSE_PARSING_SYSTEM_PROMPT,
    VENDOR_RESPONSE_PARSING_USER_PROMPT,
)
from app.prompts.vendor_communication_prompts import (
    VENDOR_EMAIL_REPLY_PROMPT,
    VENDOR_PHONE_RESPONSE_PARSE_PROMPT,
    VENDOR_SMS_REPLY_PROMPT,
    NEGOTIATION_PROMPT,
)


class AIAgentService:
    def __init__(self):
        self.client = (
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            if settings.OPENAI_API_KEY
            else None
        )

    async def parse_work_order_input(self, raw_input: str) -> Dict[str, Any]:
        if not self.client:
            return self._fallback_parse(raw_input)

        try:
            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": WORK_ORDER_PARSING_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": WORK_ORDER_PARSING_USER_PROMPT(raw_input),
                    },
                ],
                response_format=RESPONSE_FORMAT_JSON,
                temperature=AI_TEMPERATURE_PARSING,
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"AI parsing error: {e}")
            return self._fallback_parse(raw_input)

    def _fallback_parse(self, raw_input: str) -> Dict[str, Any]:
        return {
            "title": "Work Order from Natural Language",
            "description": raw_input,
            "trade_type": "general_maintenance",
            "location_address": "Address to be specified",
            "location_city": None,
            "location_state": None,
            "location_zip": None,
            "urgency": "medium",
            "preferred_date": None,
        }

    async def generate_vendor_contact_message(
        self, work_order_data: Dict[str, Any], vendor_name: str, channel: str
    ) -> str:
        if not self.client:
            return self._fallback_contact_message(work_order_data, vendor_name, channel)

        if channel == "email":
            system_prompt = VENDOR_CONTACT_EMAIL_SYSTEM_PROMPT
            user_prompt = VENDOR_CONTACT_EMAIL_USER_PROMPT(
                vendor_name=vendor_name,
                trade_type=work_order_data.get("trade_type", "general service"),
                location_address=work_order_data.get("location_address", "TBD"),
                description=work_order_data.get("description", "Service needed"),
                urgency=work_order_data.get("urgency", "medium"),
                preferred_date=work_order_data.get("preferred_date", "flexible"),
            )
            max_tokens = AI_MAX_TOKENS_MEDIUM
        elif channel == "sms":
            system_prompt = VENDOR_CONTACT_SMS_SYSTEM_PROMPT
            user_prompt = VENDOR_CONTACT_SMS_USER_PROMPT(
                vendor_name=vendor_name,
                trade_type=work_order_data.get("trade_type", "general service"),
                location_address=work_order_data.get("location_address", "TBD"),
                description=work_order_data.get("description", "Service needed"),
                urgency=work_order_data.get("urgency", "medium"),
                preferred_date=work_order_data.get("preferred_date", "flexible"),
            )
            max_tokens = AI_MAX_TOKENS_SHORT
        else:
            system_prompt = VENDOR_CONTACT_PHONE_SYSTEM_PROMPT
            user_prompt = VENDOR_CONTACT_PHONE_USER_PROMPT(
                vendor_name=vendor_name,
                trade_type=work_order_data.get("trade_type", "general service"),
                location_address=work_order_data.get("location_address", "TBD"),
                description=work_order_data.get("description", "Service needed"),
                urgency=work_order_data.get("urgency", "medium"),
                preferred_date=work_order_data.get("preferred_date", "flexible"),
            )
            max_tokens = AI_MAX_TOKENS_MEDIUM

        try:
            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=AI_TEMPERATURE_GENERATION,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI message generation error: {e}")
            return self._fallback_contact_message(work_order_data, vendor_name, channel)

    def _fallback_contact_message(
        self, work_order_data: Dict[str, Any], vendor_name: str, channel: str
    ) -> str:
        trade = work_order_data.get("trade_type", "service")
        location = work_order_data.get("location_address", "local area")

        if channel == "sms":
            return f"Hi {vendor_name}! Tavi here. Need {trade} work at {location}. Available for quote? Reply with rate & availability."
        elif channel == "email":
            return f"""Subject: Service Opportunity - {trade.title()} Work

Dear {vendor_name},

We have a {trade} job at {location} that needs attention. 

Details:
{work_order_data.get("description", "Service required")}

Could you provide a quote and your availability? Please reply with your rate and when you could complete this work.

Best regards,
Tavi Team"""
        else:
            return f"Hello, this is Tavi calling about a {trade} job opportunity at {location}. Are you available to provide a quote?"

    async def parse_vendor_response(self, response_text: str) -> Dict[str, Any]:
        if not self.client:
            return {"price": None, "availability_date": None, "notes": response_text}

        try:
            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": VENDOR_RESPONSE_PARSING_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": VENDOR_RESPONSE_PARSING_USER_PROMPT(response_text),
                    },
                ],
                response_format=RESPONSE_FORMAT_JSON,
                temperature=AI_TEMPERATURE_PARSING,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"AI response parsing error: {e}")
            return {"price": None, "availability_date": None, "notes": response_text}

    async def parse_vendor_email_response(
        self, message: str, conversation_history: str, work_order_data: dict
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "needs_human": True,
                "reason": "No AI client",
                "draft_response": "Thank you for your response.",
            }

        turn_count = work_order_data.get("turn_count", 0)

        try:
            prompt = VENDOR_EMAIL_REPLY_PROMPT.format(
                turn_count=turn_count,
                conversation_history=conversation_history,
                vendor_message=message,
                description=work_order_data.get("description", ""),
                budget=work_order_data.get("budget", "flexible"),
            )

            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional service coordinator.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=RESPONSE_FORMAT_JSON,
                temperature=AI_TEMPERATURE_GENERATION,
            )

            result = json.loads(response.choices[0].message.content)

            if not result.get("needs_human"):
                quote_info = await self.parse_vendor_response(message)
                result["extracted_info"] = quote_info

            return result

        except Exception as e:
            print(f"AI email response error: {e}")
            return {
                "needs_human": True,
                "reason": f"AI error: {str(e)}",
                "draft_response": "Thank you for your response. We will review and get back to you shortly.",
            }

    async def parse_vendor_phone_response(
        self, transcript: str, work_order_data: dict
    ) -> Dict[str, Any]:
        if not self.client:
            return {"extracted_info": None}

        try:
            prompt = VENDOR_PHONE_RESPONSE_PARSE_PROMPT.format(
                transcript=transcript,
                description=work_order_data.get("description", ""),
                trade_type=work_order_data.get("trade_type", ""),
            )

            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You parse call transcripts and extract quote info as JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=AI_TEMPERATURE_PARSING,
            )

            content = response.choices[0].message.content.strip()

            parsed = json.loads(content)
            return parsed

        except Exception as e:
            print(f"Error parsing phone response: {e}")
            return {"extracted_info": None}

    async def parse_vendor_sms_response(
        self, message: str, conversation_history: str, work_order_data: dict
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "needs_human": True,
                "reason": "No AI client",
                "response": "Thanks! Reviewing.",
            }

        turn_count = work_order_data.get("turn_count", 0)

        try:
            prompt = VENDOR_SMS_REPLY_PROMPT.format(
                turn_count=turn_count,
                conversation_history=conversation_history,
                vendor_message=message,
                description=work_order_data.get("description", ""),
                budget=work_order_data.get("budget", "flexible"),
            )

            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a service coordinator texting a vendor.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=RESPONSE_FORMAT_JSON,
                temperature=AI_TEMPERATURE_GENERATION,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"AI SMS response error: {e}")
            return {
                "needs_human": True,
                "reason": f"AI error: {str(e)}",
                "response": "Thanks! We'll review and get back to you.",
            }

    # IDEA: This is not used anywhere BUT I plan to have good negotiation model pipline that can help to sign best rated vendor on our desired pricing.
    async def generate_negotiation_message(
        self,
        vendor_price: float,
        vendor_availability: str,
        customer_budget: float,
        channel: str,
        work_order_data: dict,
    ) -> str:
        currency_symbol = work_order_data.get("currency", "$")

        if not self.client:
            return f"Thank you for your quote of {currency_symbol}{vendor_price}. Can you match our budget of {currency_symbol}{customer_budget}?"

        try:
            prompt = NEGOTIATION_PROMPT.format(
                vendor_price=vendor_price,
                vendor_availability=vendor_availability,
                customer_budget=customer_budget,
                urgency=work_order_data.get("urgency", ""),
                other_quotes="Multiple competitive quotes received",
                channel=channel,
            )

            response = await self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a skilled negotiator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=AI_TEMPERATURE_GENERATION,
                max_tokens=AI_MAX_TOKENS_MEDIUM,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI negotiation error: {e}")
            return "Thank you for your quote. Can we discuss pricing?"
