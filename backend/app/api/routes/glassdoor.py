from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.glassdoor_company import GlassdoorCompany, CompanyScrapeRequest
from app.models.user import User
from app.db.mongodb import get_database
from app.api.routes.auth import get_current_user
from app.services.glassdoor_scraper import glassdoor_scraper

router = APIRouter()

@router.post("/scrape-company", response_model=GlassdoorCompany)
async def scrape_company_data(
    request: CompanyScrapeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Scrape company data from Glassdoor and save to database
    
    Args:
        request: Contains company name and optional Glassdoor URL
        current_user: Current authenticated user
        
    Returns:
        GlassdoorCompany: The scraped and saved company data
    """
    db = await get_database()
    company_name = request.company_name.strip()
    
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is required")
    
    try:
        # Check if we have recent data (less than 24 hours old)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        existing_company = await db.glassdoor_companies.find_one({
            "company_name": {"$regex": f"^{company_name}$", "$options": "i"},
            "scraped_at": {"$gte": recent_cutoff}
        })
        
        if existing_company:
            existing_company["_id"] = str(existing_company["_id"])
            return GlassdoorCompany(**existing_company)
        
        # Scrape fresh data
        scraped_data = await glassdoor_scraper.get_company_rating(
            company_name, 
            request.glassdoor_url
        )
        
        if not scraped_data.get("overall_rating"):
            raise HTTPException(status_code=404, detail="Could not find rating for this company")
        
        # Prepare data for database
        company_data = {
            "company_name": company_name,
            "glassdoor_url": scraped_data.get("glassdoor_url", ""),
            "overall_rating": scraped_data.get("overall_rating"),
            "ceo_approval": scraped_data.get("ceo_approval"),
            "recommend_to_friend": scraped_data.get("recommend_to_friend"),
            "culture_rating": scraped_data.get("culture_rating"),
            "career_opportunities": scraped_data.get("career_opportunities"),
            "compensation_benefits": scraped_data.get("compensation_benefits"),
            "work_life_balance": scraped_data.get("work_life_balance"),
            "senior_management": scraped_data.get("senior_management"),
            "review_count": scraped_data.get("review_count"),
            "company_size": scraped_data.get("company_size"),
            "industry": scraped_data.get("industry"),
            "headquarters": scraped_data.get("headquarters"),
            "founded": scraped_data.get("founded"),
            "raw_data": scraped_data,
            "scraped_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        
        # Update existing or insert new
        existing = await db.glassdoor_companies.find_one({
            "company_name": {"$regex": f"^{company_name}$", "$options": "i"}
        })
        
        if existing:
            await db.glassdoor_companies.update_one(
                {"_id": existing["_id"]},
                {"$set": company_data}
            )
            company_data["_id"] = str(existing["_id"])
        else:
            result = await db.glassdoor_companies.insert_one(company_data)
            company_data["_id"] = str(result.inserted_id)
        
        return GlassdoorCompany(**company_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape company data: {str(e)}")

@router.get("/company/{company_name}", response_model=Optional[GlassdoorCompany])
async def get_company_data(
    company_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get company data from database
    
    Args:
        company_name: Name of the company
        current_user: Current authenticated user
        
    Returns:
        GlassdoorCompany or None if not found
    """
    db = await get_database()
    
    company = await db.glassdoor_companies.find_one({
        "company_name": {"$regex": f"^{company_name}$", "$options": "i"}
    })
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found in database")
    
    company["_id"] = str(company["_id"])
    return GlassdoorCompany(**company)

@router.get("/company/{company_name}/rating")
async def get_company_rating(company_name: str):
    """
    Get just the company rating (public endpoint)
    
    Args:
        company_name: Name of the company
        
    Returns:
        Simple rating object
    """
    db = await get_database()
    
    company = await db.glassdoor_companies.find_one({
        "company_name": {"$regex": f"^{company_name}$", "$options": "i"}
    })
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "company_name": company["company_name"],
        "overall_rating": company.get("overall_rating"),
        "review_count": company.get("review_count"),
        "glassdoor_url": company.get("glassdoor_url"),
        "last_updated": company.get("scraped_at")
    }

@router.get("/companies")
async def list_companies(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    List all companies in database
    
    Args:
        limit: Maximum number of companies to return
        current_user: Current authenticated user
        
    Returns:
        List of GlassdoorCompany objects
    """
    db = await get_database()
    
    companies = []
    async for company_doc in db.glassdoor_companies.find().sort("scraped_at", -1).limit(limit):
        company_doc["_id"] = str(company_doc["_id"])
        companies.append(GlassdoorCompany(**company_doc))
    
    return companies

@router.delete("/company/{company_name}")
async def delete_company(
    company_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete company from database
    
    Args:
        company_name: Name of the company
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = await get_database()
    
    result = await db.glassdoor_companies.delete_one({
        "company_name": {"$regex": f"^{company_name}$", "$options": "i"}
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"message": f"Company {company_name} deleted successfully"}

@router.post("/refresh-company/{company_name}", response_model=GlassdoorCompany)
async def refresh_company_data(
    company_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Force refresh company data (ignoring cache)
    
    Args:
        company_name: Name of the company
        current_user: Current authenticated user
        
    Returns:
        Updated GlassdoorCompany data
    """
    db = await get_database()
    
    # Get existing company to preserve URL if available
    existing = await db.glassdoor_companies.find_one({
        "company_name": {"$regex": f"^{company_name}$", "$options": "i"}
    })
    
    glassdoor_url = existing.get("glassdoor_url") if existing else None
    
    request = CompanyScrapeRequest(
        company_name=company_name,
        glassdoor_url=glassdoor_url
    )
    
    # Force fresh scrape by temporarily removing from cache
    if existing:
        await db.glassdoor_companies.update_one(
            {"_id": existing["_id"]},
            {"$set": {"scraped_at": datetime.utcnow() - timedelta(days=1)}}
        )
    
    return await scrape_company_data(request, current_user)