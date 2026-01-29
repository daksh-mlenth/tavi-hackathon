# Quick Start Guide - Get Running in 5 Minutes

## Prerequisites
- Docker Desktop installed and running
- That's it! (API keys optional)

## 🚀 Fastest Path to Running App

### Step 1: Setup (30 seconds)
```bash
cd tavi-hackathon
cp .env.example .env
```

### Step 2: Start (2-3 minutes first time)
```bash
docker-compose up --build
```

### Step 3: Access (immediate)
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (if needed)

## 🎯 Test It Out (2 minutes)

1. Go to http://localhost:3000
2. Type in the text box:
   ```
   Need emergency plumber at 123 Main St, Dallas TX for burst pipe. Very urgent!
   ```
3. Click "Submit Work Order"
4. Click "View Dashboard"
5. Click on your work order
6. Watch vendors appear in real-time!

## ✨ It Works Without API Keys!

The app uses mock vendors and simulates communications.
Add API keys later for real integrations.

## 🔧 Troubleshooting

### Port Already in Use
```bash
docker-compose down
# Edit docker-compose.yml to change ports
docker-compose up
```

### Need to Reset Everything
```bash
docker-compose down -v
docker-compose up --build
```

### Check Logs
```bash
docker-compose logs -f
```

## 📝 Adding API Keys (Optional)

Edit `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
SENDGRID_API_KEY=SG.your-key
GOOGLE_PLACES_API_KEY=your-key
```

Restart:
```bash
docker-compose restart
```

## 🎬 Ready for Demo?

Read `DEMO_SCRIPT.md` for full presentation guide.

## ❓ Need Help?

1. Check `README.md` for detailed instructions
2. Check `ARCHITECTURE.md` for how it works
3. Check logs: `docker-compose logs -f`

That's it! You're running a full AI-powered marketplace! 🎉
