from datetime import datetime
from typing import Dict, Any
import asyncio

from app.db.mongodb import get_database
from app.services.essence_calculator import EssenceCalculator

class GitHubEventHandler:
    """Handles GitHub webhook events and calculates essence impact"""
    
    def __init__(self):
        self.essence_calc = EssenceCalculator()
    
    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Route GitHub events to appropriate handlers"""
        handlers = {
            "pull_request": self._handle_pull_request,
            "push": self._handle_push,
            "pull_request_review": self._handle_pull_request_review,
            "issue_comment": self._handle_issue_comment,
            "commit_comment": self._handle_commit_comment,
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                await handler(data)
            except Exception as e:
                print(f"Error handling {event_type}: {e}")
    
    async def _handle_pull_request(self, data: Dict[str, Any]):
        """Handle pull request events"""
        action = data.get("action")
        pr_data = data.get("pull_request", {})
        
        if action not in ["opened", "closed", "merged"]:
            return
        
        # Find user by GitHub ID
        user = await self._get_user_by_github_id(pr_data.get("user", {}).get("id"))
        if not user:
            return
        
        db = await get_database()
        
        # Store PR data
        pr_record = {
            "user_id": user["_id"],
            "github_pr_id": pr_data.get("id"),
            "repository": data.get("repository", {}).get("full_name"),
            "title": pr_data.get("title"),
            "body": pr_data.get("body"),
            "status": "merged" if pr_data.get("merged") else pr_data.get("state"),
            "lines_added": pr_data.get("additions", 0),
            "lines_deleted": pr_data.get("deletions", 0),
            "files_changed": pr_data.get("changed_files", 0),
            "created_at": datetime.fromisoformat(pr_data.get("created_at").replace("Z", "+00:00")),
            "updated_at": datetime.fromisoformat(pr_data.get("updated_at").replace("Z", "+00:00")),
            "merged_at": datetime.fromisoformat(pr_data.get("merged_at").replace("Z", "+00:00")) if pr_data.get("merged_at") else None,
        }
        
        # Calculate essence impact
        essence_impact = await self.essence_calc.calculate_pr_essence(pr_record, action)
        pr_record["essence_score"] = essence_impact
        
        # Upsert PR record
        await db.pull_requests.update_one(
            {"github_pr_id": pr_record["github_pr_id"]},
            {"$set": pr_record},
            upsert=True
        )
        
        # Update user essence
        if essence_impact != 0:
            await self._update_user_essence(
                user["_id"], 
                "pr_quality", 
                essence_impact,
                f"PR {action}: {pr_data.get('title', '')}"
            )
    
    async def _handle_push(self, data: Dict[str, Any]):
        """Handle push events (commits)"""
        commits = data.get("commits", [])
        repository = data.get("repository", {}).get("full_name")
        
        for commit in commits:
            user = await self._get_user_by_github_id(commit.get("author", {}).get("id"))
            if not user:
                continue
            
            db = await get_database()
            
            # Store commit data
            commit_record = {
                "user_id": user["_id"],
                "repository": repository,
                "commit_sha": commit.get("id"),
                "message": commit.get("message"),
                "additions": commit.get("added", []),
                "deletions": commit.get("removed", []),
                "is_merge_commit": len(commit.get("parents", [])) > 1,
                "commit_time": datetime.fromisoformat(commit.get("timestamp").replace("Z", "+00:00")),
            }
            
            # Calculate essence impact
            essence_impact = await self.essence_calc.calculate_commit_essence(commit_record)
            commit_record["essence_impact"] = essence_impact
            
            # Store commit
            await db.commit_activity.insert_one(commit_record)
            
            # Update user essence
            if essence_impact != 0:
                await self._update_user_essence(
                    user["_id"], 
                    "commit_activity", 
                    essence_impact,
                    f"Commit: {commit.get('message', '')[:50]}..."
                )
    
    async def _handle_pull_request_review(self, data: Dict[str, Any]):
        """Handle PR review events"""
        review_data = data.get("review", {})
        pr_data = data.get("pull_request", {})
        
        user = await self._get_user_by_github_id(review_data.get("user", {}).get("id"))
        if not user:
            return
        
        db = await get_database()
        
        # Store review data
        review_record = {
            "reviewer_id": user["_id"],
            "github_review_id": review_data.get("id"),
            "review_state": review_data.get("state"),
            "comment_count": len(review_data.get("body", "")),
            "created_at": datetime.fromisoformat(review_data.get("submitted_at").replace("Z", "+00:00")),
        }
        
        # Calculate essence impact
        essence_impact = await self.essence_calc.calculate_review_essence(review_record)
        review_record["essence_impact"] = essence_impact
        
        # Store review
        await db.code_reviews.insert_one(review_record)
        
        # Update user essence
        if essence_impact != 0:
            await self._update_user_essence(
                user["_id"], 
                "team_collaboration", 
                essence_impact,
                f"Code review: {review_data.get('state')}"
            )
    
    async def _handle_issue_comment(self, data: Dict[str, Any]):
        """Handle issue/PR comment events"""
        if data.get("action") != "created":
            return
        
        comment_data = data.get("comment", {})
        user = await self._get_user_by_github_id(comment_data.get("user", {}).get("id"))
        
        if not user:
            return
        
        # Calculate essence impact for helpful comments
        essence_impact = await self.essence_calc.calculate_comment_essence(comment_data)
        
        if essence_impact != 0:
            await self._update_user_essence(
                user["_id"], 
                "communication_score", 
                essence_impact,
                "GitHub comment contribution"
            )
    
    async def _handle_commit_comment(self, data: Dict[str, Any]):
        """Handle commit comment events"""
        await self._handle_issue_comment(data)  # Similar logic
    
    async def _get_user_by_github_id(self, github_id: int):
        """Find user by GitHub ID"""
        if not github_id:
            return None
        
        db = await get_database()
        return await db.users.find_one({"github_profile.github_id": github_id})
    
    async def _update_user_essence(self, user_id: str, metric: str, delta: float, reason: str):
        """Update user essence and log the change"""
        db = await get_database()
        
        # Get current user
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return
        
        # Update specific essence metric
        current_value = user.get("essence", {}).get(metric, 50.0)
        new_value = max(0, current_value + delta)
        
        # Recalculate overall essence
        essence_metrics = user.get("essence", {})
        essence_metrics[metric] = new_value
        
        overall = (
            essence_metrics.get("pr_quality", 50) * 0.3 +
            essence_metrics.get("communication_score", 50) * 0.25 +
            essence_metrics.get("commit_activity", 50) * 0.25 +
            essence_metrics.get("team_collaboration", 50) * 0.2
        )
        essence_metrics["overall"] = overall
        
        # Update user
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"essence": essence_metrics, "updated_at": datetime.utcnow()}}
        )
        
        # Log the change
        essence_log = {
            "user_id": user_id,
            "event_type": "github_activity",
            "essence_delta": delta,
            "previous_essence": current_value,
            "new_essence": new_value,
            "reason": reason,
            "created_at": datetime.utcnow()
        }
        
        await db.essence_logs.insert_one(essence_log)