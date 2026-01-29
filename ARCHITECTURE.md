# System Architecture

## 🏗️ High-Level Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│   Next.js    │────────▶│   FastAPI   │
│  (User UI)  │◀────────│   Frontend   │◀────────│   Backend   │
└─────────────┘         └──────────────┘         └─────────────┘
                                                         │
                        ┌────────────────────────────────┼────────────┐
                        │                                │            │
                        ▼                                ▼            ▼
                  ┌──────────┐                    ┌──────────┐  ┌─────────┐
                  │   AI     │                    │  Twilio  │  │ Google  │
                  │ (OpenAI) │                    │(SMS/Call)│  │ Places  │
                  └──────────┘                    └──────────┘  └─────────┘
                        │                                │
                        └────────────────────────────────┤
                                                         │
                                                         ▼
                                                   ┌──────────┐
                                                   │PostgreSQL│
                                                   │ Database │
                                                   └──────────┘
```

## 📊 Data Flow

### 1. Work Order Creation

```
User Input (NL) 
  → Frontend Form
    → POST /api/work-orders
      → AI Agent (Parse)
        → Database (Insert)
          → Background Task (Vendor Discovery)
```

### 2. Vendor Discovery

```
Work Order Created
  → Vendor Discovery Service
    → Google Places API (Search)
      → For each vendor:
        - Fetch reviews
        - Calculate score
        - Store in DB
    → Status: "discovering_vendors"
```

### 3. Vendor Contact (Multi-Modal)

```
Vendors Discovered
  → Vendor Contact Service
    → For each vendor (parallel):
      - Create Quote (pending)
      - Try Email (SendGrid)
        - If fail/unavailable → Try SMS (Twilio)
          - If fail/unavailable → Try Phone (Twilio Voice)
      - Log communication
    → Status: "contacting_vendors"
```

### 4. Quote Evaluation

```
Vendor Responses
  → AI Parser (Extract price/availability)
    → Update Quote record
      → Calculate composite score
        - Price score (40%)
        - Quality score (40%)
        - Availability score (20%)
    → Sort by score
    → Status: "evaluating_quotes"
```

### 5. Quote Acceptance

```
User Accepts Quote
  → POST /api/quotes/{id}/accept
    → Update Quote status → "accepted"
    → Update Work Order → "dispatched"
    → Reject other quotes
    → Send confirmation to vendor
```

## 🗄️ Database Schema

### Tables

#### `work_orders`
```sql
- id (UUID, PK)
- title (VARCHAR)
- description (TEXT)
- trade_type (ENUM)
- location_* (address, city, state, zip, lat, lng)
- status (ENUM)
- urgency (VARCHAR)
- preferred_date (TIMESTAMP)
- customer_* (name, email, phone)
- raw_input (TEXT)
- ai_processing_log (JSON)
- created_at, updated_at
```

#### `vendors`
```sql
- id (UUID, PK)
- business_name (VARCHAR)
- contact_name (VARCHAR)
- phone, email, website
- address, city, state, zip, lat, lng
- trade_specialties (ARRAY)
- *_rating, *_review_count (google, yelp, bbb)
- composite_score (FLOAT)
- source_data (JSON)
- created_at, updated_at
```

#### `quotes`
```sql
- id (UUID, PK)
- work_order_id (FK)
- vendor_id (FK)
- price, currency
- availability_date
- estimated_duration_hours
- status (ENUM: pending, received, accepted, rejected)
- quote_text (TEXT)
- *_score (price, quality, availability, composite)
- requested_at, received_at, expires_at
```

#### `communication_logs`
```sql
- id (UUID, PK)
- work_order_id (FK)
- vendor_id (FK, nullable)
- channel (ENUM: email, sms, phone, system)
- direction (VARCHAR: outbound, inbound)
- subject, message, response
- sent_successfully (BOOL)
- call_duration_seconds, call_recording_url, call_transcript
- ai_model_used, ai_prompt, ai_response, ai_metadata
- external_id (Twilio SID, SendGrid ID, etc.)
- timestamp, created_at
```

### Relationships

```
work_orders
  ├── 1:N → quotes
  └── 1:N → communication_logs

vendors
  └── 1:N → quotes

quotes
  ├── N:1 → work_orders
  └── N:1 → vendors
```

## 🔄 Status Flow

```
submitted
  ↓
discovering_vendors
  ↓
contacting_vendors
  ↓
evaluating_quotes
  ↓
awaiting_approval
  ↓
dispatched
  ↓
in_progress
  ↓
completed
```

## 🤖 AI Agent Architecture

### Input Parser Agent
```python
Input: Natural language text/voice
Process: GPT-4o-mini with structured output
Output: JSON {title, description, trade_type, location, urgency, date}
```

### Vendor Contact Agent
```python
Input: Work order details, vendor info, channel
Process: Generate contextual message (email/SMS/phone script)
Output: Professional, concise message
Channels: Email (long form), SMS (<160 chars), Phone (script)
```

### Response Parser Agent
```python
Input: Vendor's text response
Process: Extract quote information
Output: JSON {price, availability_date, notes}
```

## 🔌 External Integrations

### OpenAI
- **Purpose**: NL parsing, message generation, response parsing
- **Model**: GPT-4o-mini (cost-effective)
- **Fallback**: Template-based responses

### Twilio
- **SMS**: Send quote requests, receive responses
- **Voice**: Make outbound calls (simulated in demo)
- **Webhooks**: Handle inbound responses (future)

### SendGrid
- **Email**: Professional vendor outreach
- **Templates**: Dynamic email generation
- **Tracking**: Delivery status

### Google Places
- **Search**: Find vendors by trade + location
- **Details**: Get contact info, reviews, ratings
- **Geocoding**: Convert addresses to lat/lng

### Yelp Fusion (Optional)
- **Reviews**: Additional quality data
- **Ratings**: Cross-reference with Google

## 🔐 Security

### Authentication (Future)
- JWT tokens for API access
- OAuth for user login
- API key rotation

### Data Protection
- Environment variables for secrets
- Database connection pooling
- SQL injection prevention (ORM)
- CORS restrictions
- Input validation (Pydantic)

## ⚡ Performance

### Caching Strategy
- Vendor data (24h TTL)
- API responses (5min TTL)
- Static assets (CDN)

### Async Operations
- Background tasks for vendor discovery
- Parallel vendor contact
- Non-blocking API calls

### Database Optimization
- Indexes on foreign keys
- Composite indexes on queries
- Connection pooling

## 📈 Scalability

### Horizontal Scaling
- Stateless backend (multiple instances)
- Load balancer (nginx/traefik)
- Shared PostgreSQL

### Queue System (Future)
- Redis/Celery for background jobs
- Separate workers for vendor contact
- Message queue for high volume

## 🧪 Testing Strategy

### Unit Tests
- Service layer methods
- AI parsing accuracy
- Score calculation

### Integration Tests
- API endpoints
- Database operations
- External API mocks

### End-to-End Tests
- Full workflow simulation
- UI interaction tests

## 📊 Monitoring

### Metrics to Track
- Work order creation rate
- Vendor discovery success rate
- Quote response rate
- Average time to quote
- API costs per work order

### Logging
- Structured JSON logs
- Request/response logging
- Error tracking with context
- AI interaction logging (for training)

## 🔄 Future Enhancements

1. **Real-time Updates**: WebSockets instead of polling
2. **Payment Processing**: Stripe integration
3. **Vendor Portal**: Self-service vendor management
4. **Mobile Apps**: React Native
5. **Advanced Scoring**: ML model for vendor ranking
6. **Automated Dispatch**: Skip human approval for trusted vendors
7. **Quality Verification**: Photo uploads, completion confirmation
8. **Analytics Dashboard**: Business intelligence
