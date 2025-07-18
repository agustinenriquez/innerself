from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import JWTError, jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.user import User, GitHubProfile
from app.db.mongodb import get_database

router = APIRouter()
security = HTTPBearer()

async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = await get_database()
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

@router.get("/github")
async def github_oauth():
    """Redirect to GitHub OAuth"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=read:user,user:email,repo"
        f"&redirect_uri=http://localhost:8000/auth/github/callback"
    )
    return {"auth_url": github_auth_url}

@router.get("/github/callback")
async def github_callback(code: str):
    """Handle GitHub OAuth callback"""
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        github_user = user_response.json()
        
        # Get user email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"}
        )
        
        emails = email_response.json() if email_response.status_code == 200 else []
        primary_email = next((email["email"] for email in emails if email["primary"]), github_user.get("email"))
        
        if not primary_email:
            raise HTTPException(status_code=400, detail="No email found")
        
        # Create or update user
        db = await get_database()
        
        github_profile = GitHubProfile(
            github_id=github_user["id"],
            username=github_user["login"],
            avatar_url=github_user["avatar_url"],
            profile_url=github_user["html_url"],
            access_token=access_token
        )
        
        # Check if user exists
        existing_user = await db.users.find_one({"github_profile.github_id": github_user["id"]})
        
        if existing_user:
            # Update existing user
            await db.users.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "github_profile": github_profile.dict(),
                        "updated_at": datetime.utcnow(),
                        "is_online": True
                    }
                }
            )
            user_id = existing_user["_id"]
        else:
            # Create new user
            new_user = User(
                email=primary_email,
                name=github_user.get("name") or github_user["login"],
                role="developer",  # Default role
                github_profile=github_profile,
                is_online=True
            )
            
            result = await db.users.insert_one(new_user.dict(by_alias=True, exclude={"id"}))
            user_id = str(result.inserted_id)
        
        # Create JWT token
        access_token_jwt = await create_access_token({"sub": user_id})
        
        return {
            "access_token": access_token_jwt,
            "token_type": "bearer",
            "user_id": user_id
        }

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    db = await get_database()
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"is_online": False}}
    )
    return {"message": "Logged out successfully"}