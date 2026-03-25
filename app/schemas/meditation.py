from pydantic import BaseModel
from typing import List, Optional

class AudioBlock(BaseModel):
    block: int
    duration: int
    url: str
    type: Optional[str] = None
    has_voice: Optional[bool] = False
    background_audio: Optional[str]

class MeditationResponse(BaseModel):
    id: int
    session_id: int
    summary: Optional[str] = None
    script: Optional[List[str]] = None
    audio_blocks: Optional[List[AudioBlock]] = None
    status: str
    progress: int = 0