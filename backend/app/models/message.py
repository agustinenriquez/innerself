from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EssenceImpactType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"

class EssenceImpact(BaseModel):
    type: EssenceImpactType
    score_delta: float
    reason: str
    analysis_metadata: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    id: Optional[str] = Field(alias="_id")
    author_id: str
    content: str
    channel: str = "general"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    essence_impact: Optional[EssenceImpact] = None
    is_edited: bool = False
    edit_history: Optional[list] = None
    reply_to: Optional[str] = None  # Message ID if reply
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MessageCreate(BaseModel):
    content: str
    channel: str = "general"
    reply_to: Optional[str] = None

class MessageUpdate(BaseModel):
    content: str