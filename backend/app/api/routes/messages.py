from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.models.message import Message, MessageCreate, MessageUpdate
from app.models.user import User
from app.db.mongodb import get_database
from app.api.routes.auth import get_current_user
from app.services.essence_analyzer import analyze_message_essence

router = APIRouter()

@router.get("/", response_model=List[Message])
async def get_messages(
    channel: str = "general",
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get messages from a channel"""
    db = await get_database()
    
    messages = []
    async for message_doc in db.messages.find(
        {"channel": channel}
    ).sort("timestamp", -1).limit(limit):
        message_doc["_id"] = str(message_doc["_id"])
        messages.append(Message(**message_doc))
    
    return list(reversed(messages))  # Return chronological order

@router.post("/", response_model=Message)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new message"""
    db = await get_database()
    
    # Analyze message for essence impact
    essence_impact = await analyze_message_essence(
        message_data.content, 
        current_user.id, 
        message_data.channel
    )
    
    message = Message(
        author_id=current_user.id,
        content=message_data.content,
        channel=message_data.channel,
        reply_to=message_data.reply_to,
        essence_impact=essence_impact
    )
    
    result = await db.messages.insert_one(message.dict(by_alias=True, exclude={"id"}))
    
    # Update user essence if there's an impact
    if essence_impact and essence_impact.score_delta != 0:
        await update_user_essence(current_user.id, essence_impact.score_delta, essence_impact.reason)
    
    # Get the created message
    created_message = await db.messages.find_one({"_id": result.inserted_id})
    created_message["_id"] = str(created_message["_id"])
    
    return Message(**created_message)

@router.put("/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a message"""
    db = await get_database()
    
    try:
        # Check if message exists and user owns it
        existing_message = await db.messages.find_one({"_id": ObjectId(message_id)})
        if not existing_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if existing_message["author_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this message")
        
        # Update message
        update_data = {
            "content": message_update.content,
            "is_edited": True,
            "edit_history": existing_message.get("edit_history", []) + [{
                "previous_content": existing_message["content"],
                "edited_at": datetime.utcnow()
            }]
        }
        
        await db.messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": update_data}
        )
        
        # Get updated message
        updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
        updated_message["_id"] = str(updated_message["_id"])
        
        return Message(**updated_message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a message"""
    db = await get_database()
    
    try:
        # Check if message exists and user owns it
        existing_message = await db.messages.find_one({"_id": ObjectId(message_id)})
        if not existing_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if existing_message["author_id"] != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
        
        await db.messages.delete_one({"_id": ObjectId(message_id)})
        
        return {"message": "Message deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_user_essence(user_id: str, delta: float, reason: str):
    """Update user essence and log the change"""
    db = await get_database()
    
    # Get current user
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return
    
    # Update essence
    current_essence = user_doc.get("essence", {}).get("communication_score", 50.0)
    new_essence = max(0, current_essence + delta)  # Don't go below 0
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"essence.communication_score": new_essence}}
    )
    
    # Log the change
    from app.models.essence_log import EssenceLog, EssenceEventType
    
    essence_log = EssenceLog(
        user_id=user_id,
        event_type=EssenceEventType.MESSAGE_SENT,
        essence_delta=delta,
        previous_essence=current_essence,
        new_essence=new_essence,
        reason=reason
    )
    
    await db.essence_logs.insert_one(essence_log.dict(by_alias=True, exclude={"id"}))