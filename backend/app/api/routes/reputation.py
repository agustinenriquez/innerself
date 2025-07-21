from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta

from app.models.user import User
from app.models.essence_log import EssenceLog
from app.db.mongodb import get_database
from app.api.routes.auth import get_current_user

router = APIRouter()

@router.get("/leaderboard/public")
async def get_essence_leaderboard_public(
    limit: int = 10,
    timeframe: str = "all",  # "day", "week", "month", "all"
):
    """Get essence leaderboard (public endpoint for stats)"""
    db = await get_database()
    
    # Calculate date filter
    date_filter = {}
    if timeframe != "all":
        now = datetime.utcnow()
        if timeframe == "day":
            start_date = now - timedelta(days=1)
        elif timeframe == "week":
            start_date = now - timedelta(weeks=1)
        elif timeframe == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)  # Default to week
        
        date_filter = {"updated_at": {"$gte": start_date}}
    
    # Get users sorted by overall essence
    users = []
    async for user_doc in db.users.find(
        {**date_filter, "is_active": True}
    ).sort("essence.overall", -1).limit(limit):
        user_doc["_id"] = str(user_doc["_id"])
        users.append({
            "user_id": user_doc["_id"],
            "name": user_doc["name"],
            "essence": user_doc.get("essence", {}).get("overall", 50),
            "rank": len(users) + 1
        })
    
    return users

@router.get("/leaderboard")
async def get_essence_leaderboard(
    limit: int = 10,
    timeframe: str = "all",  # "day", "week", "month", "all"
    current_user: User = Depends(get_current_user)
):
    """Get essence leaderboard"""
    db = await get_database()
    
    # Calculate date filter
    date_filter = {}
    if timeframe != "all":
        now = datetime.utcnow()
        if timeframe == "day":
            start_date = now - timedelta(days=1)
        elif timeframe == "week":
            start_date = now - timedelta(weeks=1)
        elif timeframe == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)  # Default to week
        
        date_filter = {"updated_at": {"$gte": start_date}}
    
    # Get users sorted by overall essence
    users = []
    async for user_doc in db.users.find(
        {**date_filter, "is_active": True}
    ).sort("essence.overall", -1).limit(limit):
        user_doc["_id"] = str(user_doc["_id"])
        users.append({
            "user_id": user_doc["_id"],
            "name": user_doc["name"],
            "role": user_doc["role"],
            "avatar_url": user_doc.get("github_profile", {}).get("avatar_url"),
            "overall_essence": user_doc.get("essence", {}).get("overall", 50),
            "essence_breakdown": user_doc.get("essence", {})
        })
    
    return {
        "timeframe": timeframe,
        "leaderboard": users
    }

@router.get("/analytics")
async def get_essence_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get essence analytics for the team"""
    db = await get_database()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get essence trends
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "event_type": "$event_type"
            },
            "total_delta": {"$sum": "$essence_delta"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    
    trends = []
    async for doc in db.essence_logs.aggregate(pipeline):
        trends.append({
            "date": doc["_id"]["date"],
            "event_type": doc["_id"]["event_type"],
            "total_delta": doc["total_delta"],
            "count": doc["count"]
        })
    
    # Get top performers
    top_performers = []
    async for user_doc in db.users.find(
        {"is_active": True}
    ).sort("essence.overall", -1).limit(5):
        user_doc["_id"] = str(user_doc["_id"])
        top_performers.append({
            "user_id": user_doc["_id"],
            "name": user_doc["name"],
            "overall_essence": user_doc.get("essence", {}).get("overall", 50)
        })
    
    # Get micromanagement incidents
    micromanagement_count = await db.essence_logs.count_documents({
        "event_type": "micromanagement_detected",
        "created_at": {"$gte": start_date}
    })
    
    return {
        "period_days": days,
        "trends": trends,
        "top_performers": top_performers,
        "micromanagement_incidents": micromanagement_count,
        "generated_at": datetime.utcnow()
    }

@router.get("/user/{user_id}/details")
async def get_user_essence_details(
    user_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get detailed essence breakdown for a user"""
    db = await get_database()
    
    try:
        # Get user
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent essence changes
        recent_changes = []
        async for log in db.essence_logs.find(
            {"user_id": user_id, "created_at": {"$gte": start_date}}
        ).sort("created_at", -1).limit(20):
            log["_id"] = str(log["_id"])
            recent_changes.append(log)
        
        # Get GitHub activity summary
        github_stats = {}
        if "github_profile" in user_doc:
            # Count PRs, commits, reviews in the period
            pr_count = await db.pull_requests.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            })
            
            commit_count = await db.commit_activity.count_documents({
                "user_id": user_id,
                "commit_time": {"$gte": start_date}
            })
            
            review_count = await db.code_reviews.count_documents({
                "reviewer_id": user_id,
                "created_at": {"$gte": start_date}
            })
            
            github_stats = {
                "pull_requests": pr_count,
                "commits": commit_count,
                "code_reviews": review_count
            }
        
        # Calculate essence velocity (change rate)
        total_delta = sum(log.get("essence_delta", 0) for log in recent_changes)
        essence_velocity = total_delta / days if days > 0 else 0
        
        return {
            "user_id": user_id,
            "name": user_doc["name"],
            "role": user_doc["role"],
            "current_essence": user_doc.get("essence", {}),
            "period_days": days,
            "essence_velocity": essence_velocity,
            "recent_changes": recent_changes,
            "github_activity": github_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recalculate/{user_id}")
async def recalculate_user_essence(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Recalculate essence for a user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # This would trigger a full recalculation of the user's essence
    # based on their GitHub activity and message history
    # Implementation would go here
    
    return {"message": f"Essence recalculation triggered for user {user_id}"}