# backend/main.py
import sys
import os

# Add project root to path so we can import llm_engine and utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.routes.query import router as query_router
from backend.routes.upload import router as upload_router
from utils.database import csv_to_sqlite

# Initialize the default database on startup
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "India Life Insurance Claims.csv")

app = FastAPI(title="InsightAI API", version="1.0.0")

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


@app.on_event("startup")
async def startup():
    """Initialize default SQLite database from CSV on startup."""
    if os.path.exists(CSV_PATH):
        csv_to_sqlite(CSV_PATH)
        print("✅ Default database initialized.")
    else:
        print(f"⚠️ CSV not found at {CSV_PATH}")


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": "meta-llama/llama-3.3-70b-instruct"}
