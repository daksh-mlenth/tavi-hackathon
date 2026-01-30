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

### Reset database
```bash
docker-compose down -v
docker-compose up --build
```
