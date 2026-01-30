from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routes import (
    work_orders,
    vendors,
    quotes,
    communications,
    voice,
    webhooks,
    demo,
    confirmations,
    automation,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Initializing Tavi Backend...")
    init_db()
    print("✅ Database initialized")
    yield
    print("👋 Shutting down Tavi Backend...")


app = FastAPI(
    title="Tavi API",
    description="AI-native managed marketplace for trade services",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(work_orders.router, prefix="/api/work-orders", tags=["Work Orders"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["Quotes"])
app.include_router(
    communications.router, prefix="/api/communications", tags=["Communications"]
)
app.include_router(voice.router, prefix="/api/communications", tags=["Voice"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])
app.include_router(
    confirmations.router, prefix="/api/confirmations", tags=["Confirmations"]
)
app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])


@app.get("/")
async def root():
    return {"message": "Welcome to Tavi API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
