# Deployment Guide

This guide covers deploying Tavi to production.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

Railway handles Docker deployments automatically.

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Deploy Backend**:
   ```bash
   cd backend
   railway init
   railway up
   ```

4. **Deploy Frontend**:
   ```bash
   cd frontend
   railway init
   railway up
   ```

5. **Add PostgreSQL**:
   - In Railway dashboard: New → Database → PostgreSQL
   - Railway will auto-set `DATABASE_URL`

6. **Set Environment Variables**:
   - In Railway dashboard, add all API keys from `.env.example`

### Option 2: Fly.io

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**:
   ```bash
   fly auth login
   ```

3. **Deploy Backend**:
   ```bash
   cd backend
   fly launch
   fly secrets set OPENAI_API_KEY=your-key
   fly secrets set DATABASE_URL=your-postgres-url
   fly deploy
   ```

4. **Deploy Frontend**:
   ```bash
   cd frontend
   fly launch
   fly secrets set NEXT_PUBLIC_API_URL=https://your-backend.fly.dev
   fly deploy
   ```

### Option 3: Render

1. **Create New Web Service** (for backend):
   - Connect GitHub repo
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Create New Static Site** (for frontend):
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `.next`

3. **Add PostgreSQL**:
   - Create New → PostgreSQL
   - Copy connection string to backend environment

### Option 4: DigitalOcean App Platform

1. **Create New App**
2. **Add Components**:
   - Backend (Dockerfile: `backend/Dockerfile`)
   - Frontend (Dockerfile: `frontend/Dockerfile`)
   - PostgreSQL Database

3. **Configure Environment Variables**

4. **Deploy**

## 🗄️ Database Setup

### Option 1: Supabase (Free Tier)

1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings → Database
4. Update `DATABASE_URL` in your deployment platform

### Option 2: Railway PostgreSQL

1. Add PostgreSQL in Railway dashboard
2. Connection string is auto-set as `DATABASE_URL`

### Option 3: Render PostgreSQL

1. Create new PostgreSQL instance
2. Copy internal/external URL
3. Set as `DATABASE_URL`

## 🔑 Environment Variables for Production

Make sure to set these in your deployment platform:

### Backend
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
SENDGRID_API_KEY=SG...
GOOGLE_PLACES_API_KEY=AIza...
YELP_API_KEY=...
ENVIRONMENT=production
CORS_ORIGINS=["https://your-frontend.com"]
```

### Frontend
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## 📊 Database Migration

Run migrations after first deployment:

```bash
# If using Alembic (optional)
docker-compose exec backend alembic upgrade head

# Or tables will be created automatically on first run
```

## 🔒 Security Checklist

- [ ] All API keys in environment variables (not in code)
- [ ] CORS origins set to production domain only
- [ ] Database connection using SSL
- [ ] Environment set to `production`
- [ ] Secrets not logged or exposed in error messages
- [ ] Rate limiting enabled (if needed)

## 📈 Monitoring

### Logs
```bash
# Railway
railway logs

# Fly.io
fly logs

# Render
Check dashboard

# Docker
docker-compose logs -f
```

### Health Checks

- Backend: `https://your-backend.com/health`
- Check database connections
- Monitor API response times

## 🧪 Testing Production

1. Create a test work order
2. Verify vendor discovery works
3. Check communication logs
4. Test quote acceptance
5. Monitor for errors in logs

## 🆘 Rollback

### Railway
```bash
railway rollback
```

### Fly.io
```bash
fly releases
fly deploy --image <previous-version>
```

### Render
- Use dashboard to redeploy previous version

## 📝 Post-Deployment

1. **Test the live application**:
   - Create work order
   - Verify vendor contact
   - Check communication stream
   - Accept a quote

2. **Monitor costs**:
   - OpenAI API usage
   - Twilio SMS/calls
   - Database storage
   - Server compute time

3. **Set up alerts** (optional):
   - Error tracking (Sentry)
   - Uptime monitoring (UptimeRobot)
   - Cost alerts

## 💰 Cost Estimates

### Free Tier Deployment

- **Railway**: Free tier for hobby projects
- **Supabase**: 500MB database free
- **Render**: Free tier available (spins down on inactivity)
- **Vercel**: Free for personal projects

### API Costs (Per Work Order)

- **OpenAI** (GPT-4o-mini): ~$0.01-0.05 per work order
- **Twilio SMS**: $0.0079 per message
- **Twilio Voice**: $0.0140 per minute
- **SendGrid**: First 100 emails/day free
- **Google Places**: $17 per 1000 requests (first $200/month free)

**Estimated total**: $0.50-2.00 per work order with full multi-modal contact

## 🚀 Advanced: Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (if needed).

## 📞 Support

For deployment issues:
1. Check platform logs
2. Verify environment variables
3. Test database connectivity
4. Review API key permissions
