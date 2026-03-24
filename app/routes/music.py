from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.crud import crud
from app.database.db import get_db
from app.schemas.music import MusicCreate, MusicUpdate, MusicResponse
from typing import List
from pathlib import Path
from app.config.settings import settings


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
    music_dir = Path(settings.STORAGE_PATH) / "music"
    music_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename
    file_path = music_dir / filename

    if file_path.exists():
        raise HTTPException(status_code=400, detail="File with this name already exists")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    public_path = f"/storage/music/{filename}"

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