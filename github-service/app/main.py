from fastapi import FastAPI, Request, HTTPException, Header
from contextlib import asynccontextmanager
import hashlib
import hmac
import json
from typing import Optional

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.github_handler import GitHubEventHandler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="InnerSelf GitHub Integration",
    description="GitHub webhook handler for essence tracking",
    version="1.0.0",
    lifespan=lifespan
)

event_handler = GitHubEventHandler()

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature:
        return False
    
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False
    
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """Handle GitHub webhook events"""
    payload = await request.body()
    
    # Verify signature
    if not verify_github_signature(payload, x_hub_signature_256 or "", settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Process the event
    await event_handler.handle_event(x_github_event, data)
    
    return {"status": "processed"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "github-integration"}

@app.get("/")
async def root():
    return {"message": "InnerSelf GitHub Integration Service"}