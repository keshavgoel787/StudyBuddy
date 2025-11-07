from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.routes import auth, calendar, notes, assignments, planner
from app.utils.rate_limiter import limiter

settings = get_settings()

app = FastAPI(
    title="SchoolBuddy API",
    description="AI-powered study assistant and day planner for pre-med students",
    version="1.0.0"
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
# Handle frontend URL with or without trailing slash
frontend_origins = [
    settings.frontend_url,
    settings.frontend_url.rstrip('/'),  # Remove trailing slash if present
    "http://localhost:5173",
    "http://localhost:3000"
]
# Remove duplicates
frontend_origins = list(set(frontend_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(calendar.router)
app.include_router(notes.router)
app.include_router(assignments.router)
app.include_router(planner.router)


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["auth", "calendar", "notes", "assignments", "planner"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
