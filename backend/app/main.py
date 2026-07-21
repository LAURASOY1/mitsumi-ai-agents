"""
Mitsumi AI Agent Platform - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import auth router only
from app.routers import auth_router

# Create FastAPI app
app = FastAPI(
    title="Mitsumi AI Agent Platform",
    description="AI Agent Platform with MongoDB",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Mitsumi AI Agent Platform"}

@app.get("/")
async def root():
    return {"message": "Mitsumi AI Agent Platform API"}
