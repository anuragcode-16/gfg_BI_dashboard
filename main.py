# main.py
"""
InsightAI - FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.database import csv_to_sqlite
from routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure the default insurance DB exists."""
    csv_path = os.path.join(BASE_DIR, "data", "India Life Insurance Claims.csv")
    if os.path.exists(csv_path):
        csv_to_sqlite(csv_path)
        logger.info("Default insurance database ready")
    else:
        logger.warning("Default CSV not found at %s", csv_path)
    yield


app = FastAPI(
    title="InsightAI API",
    description="Natural language BI analytics API - converts questions to SQL, executes queries, and returns data with visualization configs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
