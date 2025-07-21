from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class GlassdoorCompany(BaseModel):
    """Glassdoor company data"""
    id: Optional[str] = Field(alias="_id")
    company_name: str
    glassdoor_url: str
    overall_rating: Optional[float] = None
    ceo_approval: Optional[float] = None
    recommend_to_friend: Optional[float] = None
    culture_rating: Optional[float] = None
    career_opportunities: Optional[float] = None
    compensation_benefits: Optional[float] = None
    work_life_balance: Optional[float] = None
    senior_management: Optional[float] = None
    review_count: Optional[int] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    raw_data: Dict[str, Any] = {}  # Store additional scraped data
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CompanyScrapeRequest(BaseModel):
    """Request model for scraping company data"""
    company_name: str
    glassdoor_url: Optional[str] = None  # Optional direct URL