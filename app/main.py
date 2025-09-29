from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and models
from .database import engine, Base
from . import models

# Import API routers
from .api.endpoints import sensor_readings
from .api.endpoints import alerts as alerts_endpoints
from .api.endpoints import households as households_endpoints

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NYC Indoor Air Quality API",
    description="API for collecting and querying indoor air quality data across NYC",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    sensor_readings.router,
    prefix="/api/v1",
    tags=["sensor_readings"]
)
app.include_router(
    alerts_endpoints.router,
    prefix="/api/v1",
    tags=["alerts"]
)
app.include_router(
    households_endpoints.router,
    prefix="/api/v1",
    tags=["households"]
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the NYC Indoor Air Quality API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# For development
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
