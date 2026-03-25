from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, JSON, Enum, String, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.base import Base


# Enum for models -----------------------------------------

class MessageRole(enum.Enum):
    USER = "user"
    AGENT = "agent"
    
class MeditationStatus(enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    

# Database models ------------------------------------------

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", passive_deletes=True)
    meditations = relationship("Meditation", back_populates="session", cascade="all, delete-orphan", passive_deletes=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class Meditation(Base):
    __tablename__ = "meditations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    summary = Column(Text)
    script = Column(JSON)
    audio_blocks = Column(JSON)
    status = Column(Enum(MeditationStatus), default=MeditationStatus.PENDING)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="meditations")


class Music(Base):
    __tablename__ = "music"
    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    path = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    mood = Column(ARRAY(String), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))