# Tavi - AI-Native Service Marketplace

An AI-powered marketplace for ordering, managing, and paying for trade services. Built for the Tavi Hackathon.

## 🚀 Features

- **Natural Language Work Order Intake**: Submit work orders via chat or voice
- **AI-Powered Vendor Discovery**: Automatically finds and scores vendors near your location
- **Multi-Modal Vendor Contact**: AI agents contact vendors via email, SMS, and phone
- **Unified Communication Stream**: All interactions in one place for human oversight
- **Intelligent Quote Comparison**: Vendors ranked by price, quality, and availability
- **Command Center Dashboard**: Real-time view of all work orders and their status

## 📁 Project Structure

```
tavi-hackathon/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Pages (App Router)
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml    # Orchestration
```

## 🛠 Tech Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- OpenAI GPT-4o-mini
- Twilio (SMS & Voice)
- SendGrid (Email)
- Google Places API

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Axios for API calls
- Web Speech API for voice input

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL 15

## 📋 Prerequisites

- Docker and Docker Compose installed
- API keys (optional for full functionality):
  - OpenAI API key
  - Twilio credentials (Account SID, Auth Token, Phone Number)
  - SendGrid API key
  - Google Places API key
  - Yelp API key (optional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd tavi-hackathon
```

### 2. Set Up Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required for AI features
OPENAI_API_KEY=sk-your-openai-key

# Optional (for real vendor contact)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
SENDGRID_API_KEY=your-sendgrid-key

# Optional (for real vendor discovery)
GOOGLE_PLACES_API_KEY=your-google-key
YELP_API_KEY=your-yelp-key
```

**Note**: The app works without API keys! It will use mock vendors and simulate communications.

### 3. Start the Application

```bash
docker-compose up --build
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

### 4. Access the Application

Open your browser and go to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage Guide

### Creating a Work Order

1. Go to http://localhost:3000
2. Describe your service need in natural language:
   ```
   "I need a plumber to fix a leaking pipe at 123 Main St, Dallas, TX. 
   It's urgent and I'd like it done by Thursday."
   ```
3. Click the microphone icon to use voice input (optional)
4. Submit the form

### What Happens Next

1. **AI Parsing** (instant): AI extracts structured data from your description
2. **Vendor Discovery** (10-30s): System finds vendors near your location
3. **Vendor Contact** (30-60s): AI agents reach out via email, SMS, and phone
4. **Quote Collection** (real-time): Responses are parsed and displayed
5. **Comparison** (instant): Vendors ranked by composite score
6. **Human Approval**: You choose the best vendor and dispatch

### Viewing Work Orders

1. Click "View Dashboard" in the header
2. See all work orders with their statuses
3. Click any work order to see:
   - Full details
   - Vendor quotes with scores
   - Complete communication timeline

## 🐳 Docker Commands

### Start all services
```bash
docker-compose up
```

### Start in background
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop all services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up --build
```

### Reset database
```bash
docker-compose down -v
docker-compose up --build
```

## 🧪 Testing the Full Workflow

### Test Scenario: Plumbing Job

1. **Create Work Order**:
   ```
   "Need emergency plumbing at 456 Oak Avenue, Austin, TX 78701. 
   Kitchen sink is completely clogged. Need it fixed today."
   ```

2. **Monitor Progress**:
   - Dashboard shows status changing in real-time
   - Check work order detail page for vendor communications

3. **Review Quotes**:
   - See vendors ranked by composite score
   - Price, quality rating, and availability displayed

4. **Accept Quote**:
   - Click "Accept This Quote" on your preferred vendor
   - Status changes to "dispatched"

## 🏗 Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations (if needed)
alembic upgrade head

# View logs
docker-compose logs -f backend
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend sh

# Install new package
npm install <package-name>

# View logs
docker-compose logs -f frontend
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U tavi -d tavi_db

# View tables
\dt

# Query work orders
SELECT * FROM work_orders;
```

## 📊 API Endpoints

### Work Orders
- `POST /api/work-orders` - Create work order
- `GET /api/work-orders` - List all work orders
- `GET /api/work-orders/{id}` - Get specific work order
- `POST /api/work-orders/{id}/discover-vendors` - Trigger vendor discovery
- `POST /api/work-orders/{id}/contact-vendors` - Contact vendors

### Vendors
- `GET /api/vendors` - List vendors
- `GET /api/vendors/{id}` - Get vendor details
- `GET /api/vendors/{id}/score` - Get vendor score breakdown

### Quotes
- `GET /api/quotes/work-order/{id}` - Get quotes for work order
- `POST /api/quotes/{id}/accept` - Accept a quote

### Communications
- `GET /api/communications/work-order/{id}` - Get communication stream

Full API documentation: http://localhost:8000/docs

## 🎨 Key Features Demonstrated

### 1. AI-Powered Natural Language Processing
- Extracts structured data from unstructured input
- Handles various phrasings and incomplete information
- Works with both text and voice input

### 2. Intelligent Vendor Discovery
- Uses Google Places API to find nearby vendors
- Calculates composite quality scores from multiple sources
- Falls back to mock vendors when APIs unavailable

### 3. Multi-Modal Communication
- **Email**: Professional outreach with job details
- **SMS**: Quick text messages for rapid response
- **Phone**: Voice calls with AI script (simulated)
- Unified view of all channels in single thread

### 4. Human-in-the-Loop Design
- AI handles grunt work (discovery, contact)
- Humans make final decisions (quote acceptance)
- Clear intervention points throughout workflow

### 5. Real-Time Updates
- Dashboard polls for changes every 5 seconds
- Status updates as workflow progresses
- Live quote collection and display

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Recommended | For AI parsing and message generation |
| `TWILIO_ACCOUNT_SID` | Optional | For SMS and phone calls |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio authentication |
| `TWILIO_PHONE_NUMBER` | Optional | Your Twilio phone number |
| `SENDGRID_API_KEY` | Optional | For email sending |
| `GOOGLE_PLACES_API_KEY` | Optional | For vendor discovery |
| `YELP_API_KEY` | Optional | For additional vendor data |

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose up --build backend
```

### Frontend won't start
```bash
# Check logs
docker-compose logs frontend

# Clear node_modules and rebuild
docker-compose down
docker-compose up --build frontend
```

### Database connection error
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### Port already in use
```bash
# Change ports in docker-compose.yml
# Backend: ports: - "8001:8000"
# Frontend: ports: - "3001:3000"
```

## 📝 Architecture Decisions

1. **PostgreSQL**: Production-grade relational database for complex queries
2. **FastAPI**: High-performance async Python framework
3. **Next.js 14**: Modern React with App Router for better DX
4. **Docker Compose**: Easy local development and deployment
5. **Background Tasks**: Vendor discovery/contact runs async
6. **Polling**: Frontend polls for updates (WebSocket alternative)

## 🎯 Production Deployment

### Deploy to Railway/Render/Fly.io

1. **Backend**:
   ```bash
   # Railway
   railway up
   
   # Or use Dockerfile directly
   docker build -t tavi-backend ./backend
   ```

2. **Frontend**:
   ```bash
   # Vercel (recommended for Next.js)
   vercel deploy
   
   # Or Railway
   railway up
   ```

3. **Database**:
   - Use managed PostgreSQL (Railway, Supabase, or Render)
   - Update `DATABASE_URL` in environment

4. **Environment Variables**:
   - Set all API keys in production environment
   - Update `NEXT_PUBLIC_API_URL` to backend URL

## 📞 Support

For questions or issues:
- Check the API docs: http://localhost:8000/docs
- Review logs: `docker-compose logs`
- Inspect database: `docker-compose exec db psql -U tavi -d tavi_db`

## 🏆 Hackathon Highlights

This project demonstrates:
- ✅ **Technical Aptitude**: Full-stack with AI agents, async processing, multi-modal communication
- ✅ **Hustle**: Complete end-to-end application in tight timeline
- ✅ **Taste**: Clean UI, intuitive workflows, production-ready architecture
