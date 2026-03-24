from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.crud import crud
from app.database.db import get_db
from app.schemas.music import MusicCreate, MusicUpdate, MusicResponse
from typing import List
from pathlib import Path
from app.config.settings import settings
from app.services.supabase_storage import SupabaseStorage


router = APIRouter()


@router.post("/", response_model=MusicResponse)
async def create_music(
    display_name: str,
    category: str,
    mood: List[str],
    description: str = None,
    tags: List[str] = None,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Upload directly to Supabase
    filename = file.filename
    bucket_path = f"music/{filename}"
    file_bytes = await file.read()
    
    storage = SupabaseStorage()
    public_path = storage.upload_file_bytes(file_bytes, bucket_path, "audio/mpeg")

    music_create = MusicCreate(
        display_name=display_name,
        path=public_path,
        category=category,
        mood=mood,
        description=description,
        tags=tags
    )

    music = await crud.create_music(db, music_create)
    return music

@router.put("/{music_id}", response_model=MusicResponse)
async def update_music(
    music_id: int,
    update: MusicUpdate,
    db: AsyncSession = Depends(get_db)
):
    music = await crud.update_music(db, music_id, update)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    return music

@router.get("/list", response_model=List[MusicResponse])
async def list_music(db: AsyncSession = Depends(get_db)):
    return await crud.list_music(db)

@router.get("/{music_id}", response_model=MusicResponse)
async def get_music(music_id: int, db: AsyncSession = Depends(get_db)):
    music = await crud.get_music(db, music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    return music