from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EssenceEventType(str, Enum):
    MESSAGE_SENT = "message_sent"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    PR_REVIEWED = "pr_reviewed"
    COMMIT_MADE = "commit_made"
    HELPFUL_COMMENT = "helpful_comment"
    MICROMANAGEMENT_DETECTED = "micromanagement_detected"
    POSITIVE_FEEDBACK = "positive_feedback"
    MANUAL_ADJUSTMENT = "manual_adjustment"

class EssenceLog(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    event_type: EssenceEventType
    essence_delta: float
    previous_essence: float
    new_essence: float
    reason: str
    metadata: Optional[Dict[str, Any]] = None
    related_object_id: Optional[str] = None  # Message ID, PR ID, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EssenceSnapshot(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    overall_essence: float
    pr_quality_essence: float
    communication_essence: float
    commit_activity_essence: float
    team_collaboration_essence: float
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }