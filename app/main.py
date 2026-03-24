import sys
import asyncio
from pathlib import Path
from fastapi.staticfiles import StaticFiles

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import session, meditation, music
from app.database.base import Base
from app.database.db import engine


app = FastAPI(
    title="Meditation Guide Services",
    version="1.0.0",
    description="Personalized meditation audio generation backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(session.router, prefix="/session", tags=["Session"])
app.include_router(meditation.router, prefix="/meditation", tags=["Meditation"])
app.include_router(music.router, prefix="/music", tags=["Pregenerated Blocks"])

# Mounting the audio blocks
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}