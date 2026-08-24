from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.router import api_router
from app.core.logging import setup_logging
from app.core.exception_handlers import custom_exception_handler
from app.core.exceptions import LegalAIException
from app.core.middleware import CustomMiddleware

logger = setup_logging()

app = FastAPI(
    title="Legal AI System API",
    version="1.0.0",
    description="API for the Legal AI Consultation & Case Management System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://legal.mangoitsol.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CustomMiddleware)
app.add_exception_handler(LegalAIException, custom_exception_handler)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the FastAPI application")

@app.get("/")
def root():
    return {"message": "Welcome to Legal AI System API"}
