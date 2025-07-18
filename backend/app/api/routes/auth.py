from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from bson import ObjectId

from app.core.config import settings
from app.models.user import User, GitHubProfile, UserRegister, UserLogin, UserRole
from app.db.mongodb import get_database

router = APIRouter()
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def convert_user_doc(user_doc: dict) -> dict:
    """Convert MongoDB document to format compatible with User model"""
    if user_doc:
        # Convert ObjectId to string
        user_doc["_id"] = str(user_doc["_id"])
        
        # Handle datetime fields in essence if they exist
        if "essence" in user_doc and "last_updated" in user_doc["essence"]:
            if not isinstance(user_doc["essence"]["last_updated"], str):
                user_doc["essence"]["last_updated"] = user_doc["essence"]["last_updated"].isoformat()
                
        # Handle root-level datetime fields
        for field in ["created_at", "updated_at"]:
            if field in user_doc and not isinstance(user_doc[field], str):
                user_doc[field] = user_doc[field].isoformat()
                
    return user_doc

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
    try:
        # Convert string ID to ObjectId for MongoDB query
        object_id = ObjectId(user_id)
        user_doc = await db.users.find_one({"_id": object_id})
    except Exception:
        # If user_id is not a valid ObjectId, try as string
        user_doc = await db.users.find_one({"_id": user_id})
    
    if user_doc is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_doc = convert_user_doc(user_doc)
    return User(**user_doc)

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

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new InnerSelf account"""
    db = await get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create new user
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "password_hash": password_hash,
        "is_online": True,
        "essence": {
            "overall": 50.0,
            "pr_quality": 50.0,
            "communication_score": 50.0,
            "commit_activity": 50.0,
            "team_collaboration": 50.0,
            "last_updated": datetime.utcnow()
        },
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Create JWT token
    access_token = await create_access_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id
    }

@router.post("/login")
async def login(user_credentials: UserLogin):
    """Login with email and password"""
    db = await get_database()
    
    # Find user by email
    user_doc = await db.users.find_one({"email": user_credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_doc = convert_user_doc(user_doc)
    user = User(**user_doc)
    
    # Check password
    if not user.password_hash or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update user online status
    try:
        object_id = ObjectId(user.id)
        await db.users.update_one(
            {"_id": object_id},
            {"$set": {"is_online": True, "updated_at": datetime.utcnow()}}
        )
    except Exception:
        await db.users.update_one(
            {"_id": user.id},
            {"$set": {"is_online": True, "updated_at": datetime.utcnow()}}
        )
    
    # Create JWT token
    access_token = await create_access_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }