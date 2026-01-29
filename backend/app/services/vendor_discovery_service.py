import googlemaps
import requests
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.config import settings
from app.constants import (
    VENDOR_SEARCH_RADIUS_METERS,
    VENDOR_SEARCH_LIMIT,
    VENDOR_SCORE_REVIEW_WEIGHT,
    TRADE_TYPE_SEARCH_QUERIES,
    DEFAULT_VENDOR_SCORE,
    AI_MODEL,
    AI_TEMPERATURE_GENERATION,
)
from app.models.work_order import WorkOrder
from app.models.vendor import Vendor
from app.services.vendor_service import VendorService
from openai import AsyncOpenAI


class VendorDiscoveryService:
    """Service for discovering and scoring vendors using AI-powered search"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vendor_service = VendorService(db)
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_PLACES_API_KEY) if settings.GOOGLE_PLACES_API_KEY else None
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        # 30 minutes drive ≈ 20km at average city speed
        self.search_radius_meters = 20000  # 20km radius for 30-min drive
    
    async def discover_vendors_for_work_order(self, work_order: WorkOrder) -> List[Vendor]:
        """
        Discover vendors for a work order using AI-powered search:
        1. Generate optimized search query using AI
        2. Find vendors within 30-min drive radius
        3. Score them based on Google + Yelp reviews (0-10 scale)
        4. Store top vendors in database
        """
        vendors = []
        
        # Generate AI-powered search query
        search_queries = await self._generate_ai_search_queries(work_order)
        location = f"{work_order.location_address}, {work_order.location_city or ''}, {work_order.location_state or ''}"
        
        print(f"🤖 AI-generated search queries: {search_queries}")
        print(f"🔍 Searching within 30-min drive (~20km) of '{location}'")
        
        # Search Google Places with AI-generated queries
        if self.gmaps:
            try:
                all_places = []
                for query in search_queries[:2]:  # Use top 2 search queries
                    places_results = await self._search_google_places(
                        query=query,
                        location=location,
                        radius=self.search_radius_meters
                    )
                    all_places.extend(places_results)
                
                # Remove duplicates by place_id
                seen_place_ids = set()
                unique_places = []
                for place in all_places:
                    place_id = place.get('place_id')
                    if place_id and place_id not in seen_place_ids:
                        seen_place_ids.add(place_id)
                        unique_places.append(place)
                
                # Process and score vendors
                for place in unique_places[:VENDOR_SEARCH_LIMIT]:
                    vendor_data = await self._process_and_score_vendor(place, work_order)
                    if vendor_data:
                        vendor = self.vendor_service.create_or_update_vendor(vendor_data)
                        vendors.append(vendor)
                        print(f"  ✓ {vendor.business_name}: Score {vendor.composite_score:.1f}/10 (G:{vendor.google_rating or 0}, Y:{vendor.yelp_rating or 0})")
            
            except Exception as e:
                print(f"❌ Vendor discovery error: {e}")
                vendors = self._create_mock_vendors(work_order)
        else:
            print("⚠️  No API keys configured, using mock vendors")
            vendors = self._create_mock_vendors(work_order)
        
        # Sort by composite score (highest first)
        vendors.sort(key=lambda v: v.composite_score or 0, reverse=True)
        
        # Create initial quotes for all discovered vendors so they show up on frontend
        from app.models.quote import Quote, QuoteStatus
        for vendor in vendors:
            # Check if quote already exists
            existing_quote = (
                self.db.query(Quote)
                .filter(Quote.work_order_id == work_order.id, Quote.vendor_id == vendor.id)
                .first()
            )
            if not existing_quote:
                quote = Quote(
                    work_order_id=work_order.id,
                    vendor_id=vendor.id,
                    status=QuoteStatus.PENDING,  # Waiting for human to review/request quote
                    composite_score=vendor.composite_score
                )
                self.db.add(quote)
        
        self.db.commit()
        
        return vendors
    
    async def _generate_ai_search_queries(self, work_order: WorkOrder) -> List[str]:
        """
        Use AI to generate optimized search queries based on work order details.
        Returns multiple search query variations for better vendor discovery.
        """
        if not self.openai_client:
            # Fallback to basic search queries
            return [TRADE_TYPE_SEARCH_QUERIES.get(work_order.trade_type.value, "contractor")]
        
        try:
            prompt = f"""Generate 3 optimized Google search queries to find the best service providers for this work order:

Work Order Details:
- Trade Type: {work_order.trade_type.value}
- Title: {work_order.title}
- Description: {work_order.description}
- Urgency: {work_order.urgency}
- Work Type: {work_order.work_type.value if work_order.work_type else 'reactive'}

Generate queries that will find:
1. Highly rated professionals specializing in this exact service
2. Emergency/urgent providers if needed
3. Licensed and insured businesses

Return a JSON array of 3 search query strings.
Example: ["emergency plumber licensed insured", "24/7 plumbing repair service", "licensed plumber burst pipe repair"]
"""
            
            response = await self.openai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at generating search queries to find the best service providers. Return ONLY a JSON array of strings."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=AI_TEMPERATURE_GENERATION,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            queries = result.get('queries', result.get('search_queries', []))
            
            if queries and isinstance(queries, list):
                print(f"✨ AI generated {len(queries)} search queries")
                return queries
            
        except Exception as e:
            print(f"⚠️  AI query generation failed: {e}")
        
        # Fallback to basic queries
        base_query = TRADE_TYPE_SEARCH_QUERIES.get(work_order.trade_type.value, "contractor")
        return [
            base_query,
            f"{base_query} near me",
            f"licensed {base_query}"
        ]
    
    def _get_search_query(self, trade_type: str) -> str:
        """Convert trade type to search query (fallback)"""
        return TRADE_TYPE_SEARCH_QUERIES.get(trade_type, "contractor")
    
    async def _search_google_places(
        self,
        query: str,
        location: str,
        radius: int
    ) -> List[Dict[str, Any]]:
        """Search Google Places API"""
        try:
            # First, geocode the location
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                print(f"⚠️  Could not geocode location: {location}")
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Search for places
            places_result = self.gmaps.places_nearby(
                location=lat_lng,
                keyword=query,
                radius=radius,
                rank_by=None
            )
            
            return places_result.get('results', [])
        
        except Exception as e:
            print(f"Google Places API error: {e}")
            return []
    
    async def _process_and_score_vendor(
        self,
        place: Dict[str, Any],
        work_order: WorkOrder
    ) -> Optional[Dict[str, Any]]:
        """
        Process Google Places result and score vendor out of 10.
        Combines Google reviews + Yelp reviews for comprehensive quality score.
        """
        place_id = place.get('place_id')
        
        # Get detailed information from Google
        if self.gmaps:
            try:
                details = self.gmaps.place(place_id)['result']
            except:
                details = place
        else:
            details = place
        
        business_name = details.get('name', 'Unknown Business')
        
        # Extract contact info
        phone = details.get('formatted_phone_number') or details.get('international_phone_number')
        website = details.get('website')
        address = details.get('formatted_address')
        
        # Get Google ratings and pricing
        google_rating = details.get('rating', 0)
        google_review_count = details.get('user_ratings_total', 0)
        price_level = details.get('price_level')  # 0-4 scale from Google Places
        
        # Try to get Yelp data for additional verification
        yelp_data = await self._search_yelp_business(business_name, address)
        yelp_rating = yelp_data.get('rating', 0) if yelp_data else 0
        yelp_review_count = yelp_data.get('review_count', 0) if yelp_data else 0
        yelp_price = yelp_data.get('price') if yelp_data else None  # $ to $$$$
        
        # Calculate quality score (0-10 scale)
        quality_score = self._calculate_quality_score(
            google_rating=google_rating,
            google_reviews=google_review_count,
            yelp_rating=yelp_rating,
            yelp_reviews=yelp_review_count
        )
        
        # Convert price level to display format ($ to $$$$)
        price_display = None
        if price_level is not None and price_level > 0:
            price_display = '$' * price_level
        elif yelp_price:
            price_display = yelp_price
        
        # Store price info in source_data for frontend access
        enriched_details = details.copy()
        enriched_details['price_display'] = price_display
        enriched_details['yelp_data'] = yelp_data
        
        vendor_data = {
            "business_name": business_name,
            "phone": phone,
            "email": None,
            "website": website,
            "address": address,
            "latitude": details.get('geometry', {}).get('location', {}).get('lat'),
            "longitude": details.get('geometry', {}).get('location', {}).get('lng'),
            "trade_specialties": [work_order.trade_type.value],
            "google_rating": google_rating,
            "google_review_count": google_review_count,
            "yelp_rating": yelp_rating,
            "yelp_review_count": yelp_review_count,
            "composite_score": quality_score,
            "google_place_id": place_id,
            "yelp_business_id": yelp_data.get('id') if yelp_data else None,
            "source_data": enriched_details
        }
        
        return vendor_data
    
    def _calculate_quality_score(
        self,
        google_rating: float,
        google_reviews: int,
        yelp_rating: float,
        yelp_reviews: int
    ) -> float:
        """
        Calculate vendor quality score (0-10 scale) using Bayesian averaging.
        
        This ensures vendors with MORE reviews are trusted more.
        Example: 300 reviews @ 4.0★ > 2 reviews @ 5.0★
        
        Formula (Bayesian averaging like IMDB):
        weighted_rating = (v/(v+m)) * R + (m/(v+m)) * C
        
        Where:
        - v = number of reviews
        - m = minimum reviews threshold (confidence level = 25)
        - R = actual rating
        - C = baseline rating (3.5 for conservative estimate)
        """
        CONFIDENCE_THRESHOLD = 25  # Need 25+ reviews for full trust
        BASELINE_RATING = 3.5  # Conservative baseline (out of 5)
        
        # Process Google data
        google_weighted = 0
        if google_rating > 0:
            v = google_reviews
            m = CONFIDENCE_THRESHOLD
            R = google_rating  # Already 0-5 scale
            C = BASELINE_RATING
            
            # Bayesian weighted rating (0-5 scale)
            google_weighted = (v / (v + m)) * R + (m / (v + m)) * C
        
        # Process Yelp data
        yelp_weighted = 0
        if yelp_rating > 0:
            v = yelp_reviews
            m = CONFIDENCE_THRESHOLD
            R = yelp_rating  # Already 0-5 scale
            C = BASELINE_RATING
            
            # Bayesian weighted rating (0-5 scale)
            yelp_weighted = (v / (v + m)) * R + (m / (v + m)) * C
        
        # Combine scores (Google 60%, Yelp 40%)
        final_score = 0
        if google_weighted > 0 and yelp_weighted > 0:
            # Both sources available
            final_score = (google_weighted * 0.6 + yelp_weighted * 0.4)
        elif google_weighted > 0:
            # Only Google
            final_score = google_weighted
        elif yelp_weighted > 0:
            # Only Yelp
            final_score = yelp_weighted
        else:
            # No data - return baseline
            final_score = BASELINE_RATING
        
        # Convert 0-5 scale to 0-10 scale
        score_out_of_10 = (final_score / 5.0) * 10
        
        return round(score_out_of_10, 1)
    
    async def _search_yelp_business(
        self,
        business_name: str,
        address: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Search Yelp for additional business data"""
        if not settings.YELP_API_KEY:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {settings.YELP_API_KEY}"}
            params = {
                "term": business_name,
                "location": address or "",
                "limit": 1
            }
            
            response = requests.get(
                "https://api.yelp.com/v3/businesses/search",
                headers=headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get('businesses', [])
                if businesses:
                    return businesses[0]
        
        except Exception as e:
            print(f"⚠️  Yelp search failed for {business_name}: {e}")
        
        return None
    
    def _create_mock_vendors(self, work_order: WorkOrder) -> List[Vendor]:
        """Create mock vendors for testing when API is unavailable (scored 0-10)"""
        trade = work_order.trade_type.value
        mock_vendors_data = [
            {
                "business_name": f"Elite {trade.title()} Professionals",
                "phone": "+1-555-0101",
                "email": f"info@elite{trade}.com",
                "address": f"123 Main St, {work_order.location_city or 'Dallas'}, TX",
                "trade_specialties": [trade],
                "google_rating": 4.7,
                "google_review_count": 127,
                "yelp_rating": 4.5,
                "yelp_review_count": 89,
                "composite_score": 9.2  # Excellent rating
            },
            {
                "business_name": f"Reliable {trade.title()} Services",
                "phone": "+1-555-0102",
                "email": f"contact@reliable{trade}.com",
                "address": f"456 Oak Ave, {work_order.location_city or 'Dallas'}, TX",
                "trade_specialties": [trade],
                "google_rating": 4.3,
                "google_review_count": 64,
                "yelp_rating": 4.0,
                "yelp_review_count": 42,
                "composite_score": 8.3  # Good rating
            },
            {
                "business_name": f"Budget {trade.title()} Co",
                "phone": "+1-555-0103",
                "email": f"hello@budget{trade}.com",
                "address": f"789 Elm St, {work_order.location_city or 'Dallas'}, TX",
                "trade_specialties": [trade],
                "google_rating": 3.9,
                "google_review_count": 28,
                "yelp_rating": 3.5,
                "yelp_review_count": 15,
                "composite_score": 7.1  # Average rating
            }
        ]
        
        vendors = []
        for vendor_data in mock_vendors_data:
            vendor = self.vendor_service.create_or_update_vendor(vendor_data)
            vendors.append(vendor)
        
        return vendors
