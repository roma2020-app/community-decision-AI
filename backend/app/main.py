import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from app.routers import datasets, chat, insights, recommendations

# Initialize database schema on startup for easy hackathon environment setup
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
except Exception as e:
    print(f"Error initializing database tables: {str(e)}")

app = FastAPI(
    title="Community Decision Intelligence API",
    description="Backend API serving community data, insights, risk predictions, and recommendations.",
    version="1.0.0"
)

# Configure CORS for Streamlit frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")




@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Community Decision Intelligence API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
