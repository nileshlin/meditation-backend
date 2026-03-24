import asyncio
import csv
from pathlib import Path

# Adjust sys path so we can run directly as python scripts/seed_music.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.db import engine
from app.database.models import Base, Music
from app.services.supabase_storage import SupabaseStorage
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

def parse_csv_array(array_str):
    """
    Parses messy CSV array formats like:
    "{""peaceful,focused,grounding""}" or "{aware,open,gentle}"
    """
    if not array_str:
        return []
    cleaned = array_str.strip('"{ }').replace('""', '')
    if not cleaned:
        return []
    return [item.strip() for item in cleaned.split(',')]

async def seed_music():
    print("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    storage = SupabaseStorage()
    
    csv_file_path = Path("storage/background_music_dataset.csv")
    if not csv_file_path.exists():
        print(f"Dataset not found at {csv_file_path}")
        return

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print(f"Reading dataset: {csv_file_path}")
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        async with async_session() as session:
            for row in reader:
                local_rel_path = row["path"] # e.g. "music/mindfulness_01.mp3"
                local_path = Path("storage") / local_rel_path
                
                print(f"Processing {row['display_name']} ...")
                
                if not local_path.exists():
                    print(f" -> Local file missing at {local_path}. Skipping upload.")
                    public_url = f"/storage/{local_rel_path}" # Fallback
                else:
                    print(f" -> Uploading {local_path} to Supabase at {local_rel_path}...")
                    public_url = storage.upload_file_path(local_path, local_rel_path)
                    print(f" -> Upload complete! URL: {public_url}")

                moods = parse_csv_array(row["mood"])
                tags = parse_csv_array(row["tags"])

                # Check if exists
                stmt = select(Music).where(Music.display_name == row["display_name"])
                result = await session.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    print(f" -> Updating existing DB record for {row['display_name']}")
                    existing.path = public_url
                    existing.category = row["category"]
                    existing.mood = moods
                    existing.description = row["description"]
                    existing.tags = tags
                else:
                    print(f" -> Creating new DB record for {row['display_name']}")
                    new_music = Music(
                        display_name=row["display_name"],
                        path=public_url,
                        category=row["category"],
                        mood=moods,
                        description=row["description"],
                        tags=tags
                    )
                    session.add(new_music)
            
            await session.commit()
    print("\nDatabase Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_music())
