from sqlalchemy import func, or_, select, update, delete
from sqlalchemy.sql import any_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import MeditationStatus, Session, Message, Meditation, MessageRole, Music
from app.schemas.session import SessionCreate
from app.schemas.music import MusicCreate, MusicUpdate
from typing import List, Optional
from app.config.logger import logger


class CRUD:
    async def create_session(self, db: AsyncSession, session: SessionCreate) -> Session:
        db_session = Session()
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        return db_session

    async def get_session(self, db: AsyncSession, session_id: int) -> Session:
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def session_cleanup(self, db: AsyncSession) -> None:
        stmt = delete(Session)
        await db.execute(stmt)
        await db.commit()

    async def create_message(self, db: AsyncSession, session_id: int, role: MessageRole, content: str) -> Message:
        db_message = Message(session_id=session_id, role=role, content=content)
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        return db_message

    async def get_session_messages(self, db: AsyncSession, session_id: int) -> List[Message]:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
        result = await db.execute(stmt)
        return result.scalars().all()

    # Meditation services --------------------------------------

    async def create_meditation(self, db: AsyncSession, session_id: int) -> Meditation:
        db_med = Meditation(session_id=session_id)
        db.add(db_med)
        await db.commit()
        await db.refresh(db_med)
        return db_med

    async def update_meditation(self, db: AsyncSession, med_id: int, **kwargs) -> Meditation:
        stmt = update(Meditation).where(Meditation.id == med_id).values(**kwargs)
        await db.execute(stmt)
        await db.commit()
        stmt = select(Meditation).where(Meditation.id == med_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_meditation(self, db: AsyncSession, med_id: int) -> Meditation:
        stmt = select(Meditation).where(Meditation.id == med_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    async def list_completed_meditations(
        self,
        db: AsyncSession,
        session_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Meditation]:
        stmt = (
            select(Meditation)
            .where(Meditation.status == MeditationStatus.COMPLETED)
            .order_by(Meditation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if session_id is not None:
            stmt = stmt.where(Meditation.session_id == session_id)

        result = await db.execute(stmt)
        return result.scalars().all()
    

    # Music services ------------------------------------

    async def create_music(self, db: AsyncSession, music: MusicCreate) -> Music:
        db_music = Music(**music.dict())
        db.add(db_music)
        await db.commit()
        await db.refresh(db_music)
        return db_music

    async def update_music(self, db: AsyncSession, music_id: int, data: MusicUpdate) -> Optional[Music]:
        stmt = update(Music).where(Music.id == music_id).values(**data.dict(exclude_unset=True))
        await db.execute(stmt)
        await db.commit()
        stmt = select(Music).where(Music.id == music_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_music(self, db: AsyncSession, music_id: int) -> Optional[Music]:
        stmt = select(Music).where(Music.id == music_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_music(self, db: AsyncSession) -> List[Music]:
        stmt = select(Music)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_matching_music(self, db: AsyncSession, summary: str) -> Optional[Music]:
        summary_lower = summary.lower()
        keywords = []
        
        if any(k in summary_lower for k in ["nature", "forest", "rain", "ocean", "birds", "natural", "outdoor"]):
            keywords.append("nature")
        if any(k in summary_lower for k in ["relax", "calm", "peace", "rest", "sleep", "sooth", "chill"]):
            keywords.append("relax")
        if any(k in summary_lower for k in ["mindful", "focus", "aware", "present", "still", "meditat"]):
            keywords.append("mindfulness")

        if not keywords:
            logger.info("No matching keywords found in summary for music selection")
            return None

        # Build conditions safely
        conditions = []

        if keywords:
            conditions.append(
                or_(*(Music.category.ilike(f"%{kw}%") for kw in keywords))
            )

        if keywords:
            conditions.append(
                or_(*(any_(Music.mood) == kw for kw in keywords))
            )

        if keywords:
            conditions.append(
                or_(*(any_(Music.tags) == kw for kw in keywords))
            )

        if not conditions:
            return None

        stmt = (
            select(Music)
            .where(or_(*conditions))
            .limit(1)
        )

        result = await db.execute(stmt)
        music = result.scalar_one_or_none()

        return music

crud = CRUD()