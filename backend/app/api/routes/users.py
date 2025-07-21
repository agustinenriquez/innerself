from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId

from app.models.user import User, UserUpdate
from app.db.mongodb import get_database
from app.api.routes.auth import get_current_user

router = APIRouter()

@router.get("/public", response_model=List[User])
async def get_users_public():
    """Get all users (public endpoint for stats)"""
    db = await get_database()
    users_cursor = db.users.find({"is_active": True})
    users = []
    
    async for user_doc in users_cursor:
        user_doc["_id"] = str(user_doc["_id"])
        users.append(User(**user_doc))
    
    return users

@router.get("/", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all users"""
    db = await get_database()
    users_cursor = db.users.find({"is_active": True})
    users = []
    
    async for user_doc in users_cursor:
        user_doc["_id"] = str(user_doc["_id"])
        users.append(User(**user_doc))
    
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Get user by ID"""
    db = await get_database()
    
    try:
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_doc["_id"] = str(user_doc["_id"])
    return User(**user_doc)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update user"""
    # Only allow users to update their own profile or admins
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    db = await get_database()
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    
    return User(**updated_user)

@router.get("/{user_id}/essence/history")
async def get_user_essence_history(
    user_id: str, 
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get user essence history"""
    db = await get_database()
    
    from datetime import datetime, timedelta
    start_date = datetime.utcnow() - timedelta(days=days)
    
    try:
        essence_logs = []
        async for log in db.essence_logs.find(
            {"user_id": user_id, "created_at": {"$gte": start_date}}
        ).sort("created_at", 1):
            log["_id"] = str(log["_id"])
            essence_logs.append(log)
        
        return {"user_id": user_id, "days": days, "logs": essence_logs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))