from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import lessons, licks, settings, tags, transcribe

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load AI models here if needed in future
    print("🎸 Refret Backend Starting...")
    yield
    print("👋 Refret Backend Shutting down...")

app = FastAPI(
    title="Refret API",
    description="Backend for Refret Guitar Lesson Review Tool",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
# Allow all origins to support various deployment environments
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lessons.router, prefix="/api/lessons", tags=["lessons"])
app.include_router(licks.router, prefix="/api/licks", tags=["licks"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Refret Backend is running 🎸"}
