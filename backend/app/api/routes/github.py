from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.models.github_user import GitHubUser, GitHubUserCreate
from app.models.user import User
from app.db.mongodb import get_database
from app.api.routes.auth import get_current_user
from app.services.github_api import github_api

router = APIRouter()

@router.post("/fetch-user", response_model=GitHubUser)
async def fetch_github_user(
    request: GitHubUserCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Fetch GitHub user data and save to database
    
    Args:
        request: Contains the GitHub username to fetch
        current_user: Current authenticated user
        
    Returns:
        GitHubUser: The fetched and saved GitHub user data
    """
    db = await get_database()
    username = request.username.strip()
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    try:
        # Fetch data from GitHub API
        github_data = await github_api.get_user(username)
        
        if not github_data:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        
        # Check if user already exists in our database
        existing_user = await db.github_users.find_one({"github_id": github_data["id"]})
        
        # Parse dates from GitHub API response
        created_at = datetime.fromisoformat(github_data["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(github_data["updated_at"].replace("Z", "+00:00"))
        
        # Create GitHubUser object
        github_user_data = {
            "github_id": github_data["id"],
            "login": github_data["login"],
            "name": github_data.get("name"),
            "email": github_data.get("email"),
            "avatar_url": github_data["avatar_url"],
            "html_url": github_data["html_url"],
            "bio": github_data.get("bio"),
            "company": github_data.get("company"),
            "location": github_data.get("location"),
            "blog": github_data.get("blog"),
            "twitter_username": github_data.get("twitter_username"),
            "public_repos": github_data.get("public_repos", 0),
            "public_gists": github_data.get("public_gists", 0),
            "followers": github_data.get("followers", 0),
            "following": github_data.get("following", 0),
            "created_at": created_at,
            "updated_at": updated_at,
            "raw_data": github_data,
            "fetched_at": datetime.utcnow()
        }
        
        if existing_user:
            # Update existing user
            await db.github_users.update_one(
                {"github_id": github_data["id"]},
                {"$set": github_user_data}
            )
            github_user_data["_id"] = str(existing_user["_id"])
        else:
            # Create new user
            result = await db.github_users.insert_one(github_user_data)
            github_user_data["_id"] = str(result.inserted_id)
        
        return GitHubUser(**github_user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub user: {str(e)}")

@router.get("/user/{username}", response_model=Optional[GitHubUser])
async def get_github_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get GitHub user data from database
    
    Args:
        username: GitHub username
        current_user: Current authenticated user
        
    Returns:
        GitHubUser or None if not found
    """
    db = await get_database()
    
    github_user = await db.github_users.find_one({"login": username.lower()})
    
    if not github_user:
        raise HTTPException(status_code=404, detail="GitHub user not found in database")
    
    github_user["_id"] = str(github_user["_id"])
    return GitHubUser(**github_user)

@router.get("/users")
async def list_github_users(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    List all GitHub users in database
    
    Args:
        limit: Maximum number of users to return
        current_user: Current authenticated user
        
    Returns:
        List of GitHubUser objects
    """
    db = await get_database()
    
    users = []
    async for user_doc in db.github_users.find().sort("fetched_at", -1).limit(limit):
        user_doc["_id"] = str(user_doc["_id"])
        users.append(GitHubUser(**user_doc))
    
    return users

@router.delete("/user/{username}")
async def delete_github_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete GitHub user from database
    
    Args:
        username: GitHub username
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = await get_database()
    
    result = await db.github_users.delete_one({"login": username.lower()})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="GitHub user not found")
    
    return {"message": f"GitHub user {username} deleted successfully"}