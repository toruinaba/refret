from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.routers import lessons

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
# Allow local frontend development (Vite usually runs on 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lessons.router, prefix="/api/lessons", tags=["lessons"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Refret Backend is running 🎸"}

