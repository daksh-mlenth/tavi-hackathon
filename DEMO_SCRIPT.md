# Demo Script for Tavi Hackathon

This script will help you deliver an impressive 60-minute demo/technical rundown.

## 🎯 Demo Objectives

1. Show end-to-end workflow in action
2. Highlight technical sophistication
3. Demonstrate "taste" in UX decisions
4. Prove you can "hustle" (built this in tight timeline)

## ⏱️ Timeline (60 minutes)

### Part 1: Introduction (5 min)
### Part 2: Live Demo (15 min)
### Part 3: Technical Deep Dive (30 min)
### Part 4: Q&A (10 min)

---

## Part 1: Introduction (5 min)

### Opening Statement
> "I built Tavi - an AI-native marketplace that automates the entire vendor discovery and 
> contact process for facility managers. Let me show you how it works end-to-end."

### Architecture Overview (Show ARCHITECTURE.md diagram)
- **Frontend**: Next.js with natural language interface
- **Backend**: FastAPI with AI agents
- **Database**: PostgreSQL with proper relational design
- **AI Integration**: OpenAI for parsing and generation
- **Communication**: Multi-modal (email, SMS, phone)

### Key Differentiators
1. **Natural Language Input**: No forms to fill
2. **AI Agents Do the Work**: Fully automated vendor contact
3. **Human-in-the-Loop**: Clear intervention points
4. **Unified Context**: All communications in one stream

---

## Part 2: Live Demo (15 min)

### Setup Before Demo
```bash
# Start the application
docker-compose up -d

# Verify it's running
open http://localhost:3000
open http://localhost:8000/docs
```

### Demo Scenario: Emergency Plumbing

#### Step 1: Create Work Order (2 min)

Navigate to http://localhost:3000

**Say**: "Let me create a work order using natural language..."

**Type/Speak**:
```
I need an emergency plumber for a major leak at our Dallas office 
located at 456 Oak Avenue, Dallas, TX 75201. The bathroom pipe burst 
and we need it fixed today. Budget is around $500.
```

**Click**: Submit

**Point Out**:
- Voice input option (click microphone icon to show)
- No complex form to fill
- AI will extract all structured data

#### Step 2: Dashboard View (2 min)

**Click**: "View Dashboard"

**Show**:
- Real-time status updates
- Multiple work orders with different statuses
- Clean, modern UI

**Point Out**:
- Status pipeline (submitted → discovering → contacting → evaluating)
- Statistics cards showing metrics
- Professional command center feel

#### Step 3: Work Order Detail (5 min)

**Click**: On the newly created work order

**Show**:
- Parsed structured data (title, description, location, urgency)
- Trade type correctly identified as "plumbing"
- Status changing in real-time

**Wait 10-15 seconds** (refresh if needed)

**Point Out**:
- Status changed to "discovering_vendors"
- Then "contacting_vendors"

**Scroll to Quotes Section**:
- Show vendors appearing with scores
- Price, availability, quality rating
- Composite score calculation

**Scroll to Communication Stream**:
- Email sent to Vendor A
- SMS sent to Vendor B  
- Phone script for Vendor C
- All in unified timeline

**Point Out**:
- Multi-modal approach (tries email first, then SMS, then phone)
- Human can see everything AI is doing
- Context preserved across channels

#### Step 4: Quote Acceptance (3 min)

**Show**:
- Vendors ranked by composite score
- Price + Quality + Availability factors
- Clear comparison

**Click**: "Accept This Quote" on best vendor

**Show**:
- Status changed to "dispatched"
- Other quotes automatically rejected
- Confirmation logged

#### Step 5: API Documentation (3 min)

**Navigate to**: http://localhost:8000/docs

**Show**:
- Complete API documentation
- RESTful design
- Clear endpoint structure

---

## Part 3: Technical Deep Dive (30 min)

### 3.1 Natural Language Processing (5 min)

**Open**: `backend/app/services/ai_agent_service.py`

**Explain**:
```python
async def parse_work_order_input(self, raw_input: str):
    # Using GPT-4o-mini with structured output
    # Extracts: title, description, trade_type, location, urgency
    # Falls back gracefully if API unavailable
```

**Key Points**:
- Structured JSON output from GPT
- Cost-effective model choice (gpt-4o-mini vs gpt-4)
- Fallback mechanism for reliability
- Logs everything for future training

### 3.2 Vendor Discovery (5 min)

**Open**: `backend/app/services/vendor_discovery_service.py`

**Explain**:
```python
async def discover_vendors_for_work_order(self, work_order):
    # 1. Google Places search within 30-mile radius
    # 2. Fetch detailed vendor info
    # 3. Calculate composite score from reviews
    # 4. Store in database for reuse
```

**Show Database Design** (`backend/app/models/vendor.py`):
- Proper normalization
- Review data from multiple sources (Google, Yelp, BBB)
- Composite scoring algorithm

**Key Points**:
- Real API integration (Google Places)
- Smart fallback to mock vendors for demo
- Scoring algorithm considers multiple factors
- Caching vendors for future work orders

### 3.3 Multi-Modal Communication (7 min) ⭐ MOST IMPORTANT

**Open**: `backend/app/services/vendor_contact_service.py`

**Explain the Strategy**:
```python
async def _contact_single_vendor(self, work_order, vendor):
    # Priority: Email > SMS > Phone
    # 1. Try email (professional, detailed)
    # 2. If fails, try SMS (quick, concise)
    # 3. If fails, try phone (voice call)
    # Log everything in unified stream
```

**Show Each Channel**:

1. **Email** (`_send_email`):
   - AI-generated professional message
   - SendGrid integration
   - Subject + detailed body

2. **SMS** (`_send_sms`):
   - Concise <160 char message
   - Twilio integration
   - Immediate delivery

3. **Phone** (`_make_phone_call`):
   - AI-generated script
   - Twilio Voice (simulated in demo)
   - Could use OpenAI Realtime API

**Key Points**:
- Truly multi-modal (not just one channel)
- Context-aware message generation
- Graceful degradation (tries multiple methods)
- All logged in single stream (human oversight)

### 3.4 Response Processing (3 min)

**Show**:
```python
async def parse_vendor_response(self, response_text):
    # AI extracts: price, availability_date, notes
    # Updates quote with structured data
    # Calculates composite score
```

**Key Points**:
- Handles unstructured vendor responses
- Extracts key information automatically
- Human can still see original message

### 3.5 Database Design (5 min)

**Show**: Database schema in `backend/app/models/`

**Explain Tables**:
1. `work_orders` - Core entity with status tracking
2. `vendors` - Reusable vendor database
3. `quotes` - Links work orders to vendors with pricing
4. `communication_logs` - Complete audit trail

**Show**: Relationships and foreign keys

**Key Points**:
- Proper relational design (not just NoSQL)
- Normalized for production use
- Indexes on frequently queried fields
- JSON fields for flexible metadata

### 3.6 Frontend Architecture (5 min)

**Show**: Frontend structure

**Navigate Through**:
1. `src/app/page.tsx` - Landing page with form
2. `src/app/dashboard/page.tsx` - Command center
3. `src/app/work-orders/[id]/page.tsx` - Detail view

**Key Points**:
- Next.js 14 App Router (modern)
- TypeScript for type safety
- TailwindCSS for clean UI
- Real-time polling (every 5 seconds)
- Voice input using Web Speech API

**Show UI/UX Decisions**:
- Natural language textarea (not rigid form)
- Microphone button for voice
- Real-time status updates
- Unified communication timeline
- Clear call-to-action buttons

---

## Part 4: Q&A (10 min)

### Anticipated Questions & Answers

**Q: How do you handle vendor responses?**

A: "Currently simulated for demo, but the architecture supports:
- Webhooks from Twilio for SMS/calls
- Email forwarding to API endpoint  
- Manual entry by operators
- Response parsing with AI
The system logs everything and updates quotes in real-time."

**Q: What about payment processing?**

A: "Not implemented yet, but the architecture supports it:
- Quote acceptance creates a payment intent
- Stripe integration in the dispatch workflow
- Escrow until work completion
- Vendor payouts after verification"

**Q: How do you ensure vendor quality?**

A: "Multi-source scoring:
- Google reviews (rating + count)
- Yelp data
- BBB rating
- Weighted composite score
- Historical performance (future)
Plus human approval required for final selection."

**Q: What's the cost per work order?**

A: "Current estimates:
- OpenAI API: ~$0.01-0.05 (GPT-4o-mini)
- Twilio SMS: $0.0079 per message
- SendGrid: First 100/day free
- Google Places: First $200/month free
Total: ~$0.50-2.00 per work order with full multi-modal contact"

**Q: How does this scale?**

A: "Current architecture supports:
- Stateless backend (horizontal scaling)
- PostgreSQL connection pooling
- Background tasks for heavy operations
- Docker for consistent deployment
Future: Add Redis queue, separate worker processes, rate limiting"

**Q: Why not use [other AI service]?**

A: "OpenAI GPT-4o-mini because:
- Cost-effective ($0.15 per 1M input tokens)
- Structured output support (JSON mode)
- Fast response times
- Reliable API
Could easily swap for Claude/Gemini if needed."

---

## 🎨 Talking Points on "Taste"

### UX Decisions
1. **Natural Language First**: No tedious forms
2. **Voice Input**: Modern, accessible
3. **Real-time Updates**: Users see progress
4. **Unified Timeline**: All communications in context
5. **Clear Status Pipeline**: Transparency in process
6. **Visual Hierarchy**: Important info stands out
7. **Mobile-Responsive**: Works on all devices

### Technical Taste
1. **Proper Architecture**: Not a hack job
2. **Type Safety**: TypeScript + Pydantic
3. **Error Handling**: Graceful fallbacks
4. **Logging**: Complete audit trail for compliance
5. **Dockerized**: Production-ready deployment
6. **Documentation**: README, API docs, architecture

---

## 🚀 Hustle Demonstration

### What You Built in Limited Time

**Backend** (FastAPI):
- 4 database models with relationships
- 8+ Pydantic schemas
- 15+ API endpoints
- 6 service layers
- AI agent integration
- Multi-modal communication
- Background task processing

**Frontend** (Next.js):
- 3 complete pages
- 5+ React components
- API client library
- Real-time polling
- Voice input integration
- Responsive design

**Infrastructure**:
- Docker Compose orchestration
- PostgreSQL setup
- Environment configuration
- Comprehensive documentation

**Documentation**:
- README with full instructions
- Architecture diagrams
- Deployment guide
- Demo script

### Development Approach
- Used modern tools (Cursor/Claude)
- Source-code first (not no-code)
- Production-ready patterns
- Clean, maintainable code

---

## 📋 Pre-Demo Checklist

- [ ] Docker running
- [ ] Application started (`docker-compose up -d`)
- [ ] Frontend loads (http://localhost:3000)
- [ ] Backend healthy (http://localhost:8000/health)
- [ ] API docs accessible (http://localhost:8000/docs)
- [ ] Demo scenario planned
- [ ] Code files ready to show
- [ ] Terminal ready for commands
- [ ] Browser tabs open

---

## 🎬 Closing Statement

> "I built this in [X days/hours] to demonstrate:
> 
> 1. **Technical Aptitude**: Full-stack with AI agents, async processing, multi-modal communication, production-ready architecture
> 
> 2. **Hustle**: Complete end-to-end application with frontend, backend, database, AI integration, and comprehensive documentation
> 
> 3. **Taste**: Intuitive natural language interface, real-time updates, human-in-the-loop design, clean modern UI
> 
> This is ready to run in production with real API keys. Happy to answer any questions!"

---

## 💡 Pro Tips

1. **Run through demo at least once before presenting**
2. **Have backup demo if live demo fails** (screen recording)
3. **Know your code** - be ready to navigate quickly
4. **Emphasize the "meat"** - vendor contact is the key innovation
5. **Be honest about limitations** - show maturity
6. **Have next steps ready** - show you're thinking ahead

## 🎥 Optional: Record Your Demo

```bash
# Use QuickTime or OBS to record:
# 1. Browser window with application
# 2. Code editor for technical walkthrough
# 3. Terminal for Docker commands

# Export as MP4 for easy sharing
```

Good luck! 🚀
