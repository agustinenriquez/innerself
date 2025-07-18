from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    DEVELOPER = "developer"
    PM = "pm" 
    QA = "qa"
    DESIGNER = "designer"
    ADMIN = "admin"

class EssenceMetrics(BaseModel):
    overall: float = 50.0
    pr_quality: float = 50.0
    communication_score: float = 50.0
    commit_activity: float = 50.0
    team_collaboration: float = 50.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class GitHubProfile(BaseModel):
    github_id: int
    username: str
    avatar_url: str
    profile_url: str
    access_token: Optional[str] = None

class User(BaseModel):
    id: Optional[str] = Field(alias="_id")
    email: str
    name: str
    role: UserRole
    github_profile: Optional[GitHubProfile] = None
    essence: EssenceMetrics = Field(default_factory=EssenceMetrics)
    is_active: bool = True
    is_online: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    email: str
    name: str
    role: UserRole

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None