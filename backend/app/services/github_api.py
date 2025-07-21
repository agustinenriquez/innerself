import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.config import settings

class GitHubAPIService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Add token if available
        if hasattr(settings, 'github_token') and settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user data from GitHub API
        
        Args:
            username: GitHub username
            
        Returns:
            User data dict or None if not found
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users/{username}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
                    
            except httpx.RequestError as e:
                raise Exception(f"GitHub API request failed: {str(e)}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"GitHub API returned error {e.response.status_code}: {e.response.text}")
    
    async def get_user_repos(self, username: str, per_page: int = 30, page: int = 1) -> Optional[list]:
        """
        Fetch user repositories from GitHub API
        
        Args:
            username: GitHub username
            per_page: Number of repos per page (max 100)
            page: Page number
            
        Returns:
            List of repositories or None if user not found
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users/{username}/repos",
                    headers=self.headers,
                    params={
                        "per_page": min(per_page, 100),
                        "page": page,
                        "sort": "updated",
                        "direction": "desc"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
                    
            except httpx.RequestError as e:
                raise Exception(f"GitHub API request failed: {str(e)}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"GitHub API returned error {e.response.status_code}: {e.response.text}")

github_api = GitHubAPIService()