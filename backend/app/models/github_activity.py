from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class GitHubEventType(str, Enum):
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    ISSUE = "issue"
    PULL_REQUEST_REVIEW = "pull_request_review"
    COMMIT_COMMENT = "commit_comment"
    ISSUE_COMMENT = "issue_comment"

class PRStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"

class GitHubActivity(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    github_user_id: int
    event_type: GitHubEventType
    repository: str
    event_data: Dict[str, Any]
    essence_impact: float = 0.0
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PullRequest(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    github_pr_id: int
    repository: str
    title: str
    body: Optional[str] = None
    status: PRStatus
    lines_added: int = 0
    lines_deleted: int = 0
    files_changed: int = 0
    review_comments: int = 0
    reviews_received: int = 0
    merge_time_hours: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    essence_score: float = 0.0
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CodeReview(BaseModel):
    id: Optional[str] = Field(alias="_id")
    reviewer_id: str
    pr_id: str
    github_review_id: int
    review_state: str  # "approved", "changes_requested", "commented"
    comment_count: int = 0
    helpful_score: float = 0.0  # Based on PR author feedback
    response_time_hours: float = 0.0
    created_at: datetime
    essence_impact: float = 0.0
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CommitActivity(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    repository: str
    commit_sha: str
    message: str
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0
    is_merge_commit: bool = False
    commit_time: datetime
    essence_impact: float = 0.0
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }