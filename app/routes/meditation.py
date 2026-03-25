from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gemini import GeminiService
from app.services.crud import crud
from app.services.audio import AudioBlockService
from app.schemas.meditation import MeditationResponse
from app.database.models import MeditationStatus

from app.config.logger import logger
from app.database.db import get_db, AsyncSessionLocal
from app.config.settings import settings
import httpx
import os

router = APIRouter()


async def generate_meditation_background(med_id: int, session_id: int):
    async with AsyncSessionLocal() as db:
        try:
            await crud.update_meditation(db, med_id, status=MeditationStatus.GENERATING, progress=5)
            session = await crud.get_session(db, session_id)
            if not session:
                raise ValueError("Session not found")
            
            messages = await crud.get_session_messages(db, session_id)
            
            gemini = GeminiService()
            summary = await gemini.summarize_conversation(messages)       
            await crud.update_meditation(db, med_id, progress=15)
            
            scripts = await gemini.generate_meditation_script(summary)
            await crud.update_meditation(db, med_id, progress=30)
            
            music = await crud.get_matching_music(db, summary)
            music_path = None
            temp_music_path = None
            if music:
                temp_music_path = Path(settings.TEMP_DIR) / f"temp_{music.id}.mp3"
                temp_music_path.parent.mkdir(parents=True, exist_ok=True)
                async with httpx.AsyncClient() as client:
                    resp = await client.get(music.path)
                    with open(temp_music_path, "wb") as f:
                        f.write(resp.content)
                music_path = temp_music_path
                logger.info(f"Downloaded remote background music to: {temp_music_path}")
            
            await crud.update_meditation(db, med_id, progress=40)
            
            async def update_progress(p: int):
                await crud.update_meditation(db, med_id, progress=p)
            
            audio_service = AudioBlockService()
            audio_blocks = await audio_service.generate_audio_blocks(
                scripts, 
                meditation_id=med_id, 
                music_path=music_path, 
                progress_callback=update_progress
            )
            
            if temp_music_path and temp_music_path.exists():
                os.remove(temp_music_path)
            
            await crud.update_meditation(db, med_id, summary=summary, script=scripts, audio_blocks=audio_blocks, status=MeditationStatus.COMPLETED, progress=100)
        except Exception as e:
            logger.error(f"Meditation generation failed: {e}")
            await crud.update_meditation(db, med_id, status=MeditationStatus.FAILED)

@router.post("/sessions/{session_id}/start", response_model=MeditationResponse)
async def start_meditation(session_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    meditation = await crud.create_meditation(db, session_id)
    background_tasks.add_task(generate_meditation_background, meditation.id, session_id)
    
    return MeditationResponse(id=meditation.id, session_id=meditation.session_id, status=meditation.status.value, progress=meditation.progress)

@router.get("/{med_id}", response_model=MeditationResponse)
async def get_meditation(med_id: int, db: AsyncSession = Depends(get_db)):
    meditation = await crud.get_meditation(db, med_id)
    if not meditation:
        raise HTTPException(status_code=404, detail="Meditation not found")
    return MeditationResponse(
        id=meditation.id,
        session_id=meditation.session_id,
        summary=meditation.summary,
        script=meditation.script,
        audio_blocks=meditation.audio_blocks,
        status=meditation.status.value,
        progress=meditation.progress
    )
    
@router.get("/", response_model=List[MeditationResponse])
async def list_completed_meditations_full(
    session_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    
    meditations = await crud.list_completed_meditations(db, session_id, limit, offset)
    return [
        MeditationResponse(
            id=m.id,
            session_id=m.session_id,
            summary=m.summary,
            script=m.script,
            audio_blocks=m.audio_blocks,
            status=m.status.value,
            progress=m.progress
        )
        for m in meditations
    ]