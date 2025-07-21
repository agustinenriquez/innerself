from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class GitHubUser(BaseModel):
    """GitHub user profile data"""
    id: Optional[str] = Field(alias="_id")
    github_id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: str
    html_url: str
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    created_at: datetime
    updated_at: datetime
    raw_data: Dict[str, Any] = {}  # Store the full GitHub API response
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GitHubUserCreate(BaseModel):
    """Request model for creating GitHub user"""
    username: str