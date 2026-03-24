from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.services.gemini import GeminiService
from app.services.crud import crud
from app.schemas.session import SessionCreate, SessionResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.database.models import MessageRole

router = APIRouter()

@router.post("/", response_model=SessionResponse)
async def create_session(session: SessionCreate = SessionCreate(), db: AsyncSession = Depends(get_db)):
    db_session = await crud.create_session(db, session)
    return SessionResponse(id=db_session.id)

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: int, message: MessageCreate, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    await crud.create_message(db, session_id, MessageRole.USER, message.content)
    
    # Get all messages
    messages = await crud.get_session_messages(db, session_id)
    
    # Generate agent response
    gemini = GeminiService()
    agent_content = await gemini.generate_agent_response(messages)
    
    # Add agent message
    agent_message = await crud.create_message(db, session_id, MessageRole.AGENT, agent_content)
    
    return MessageResponse(
        id=agent_message.id,
        role=agent_message.role.value,
        content=agent_message.content,
        created_at=agent_message.created_at.isoformat()
    )


@router.delete("/delete-all")
async def delete_all_sessions(db: AsyncSession = Depends(get_db)):
    await crud.session_cleanup(db)
    return {
        "message": "All sessions deleted successfully" 
    }