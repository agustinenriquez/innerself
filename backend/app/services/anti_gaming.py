from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from collections import defaultdict

from app.db.mongodb import get_database

class AntiGamingDetector:
    """Detects and prevents gaming of the essence system"""
    
    # Thresholds for gaming detection
    SUSPICIOUS_PATTERNS = {
        "rapid_commits": {
            "threshold": 20,  # More than 20 commits in 1 hour
            "timeframe": 3600,  # 1 hour in seconds
            "penalty": -5.0
        },
        "tiny_commits": {
            "threshold": 0.7,  # 70% of commits are < 5 lines
            "min_commits": 10,  # Need at least 10 commits to analyze
            "penalty": -3.0
        },
        "pr_spam": {
            "threshold": 10,  # More than 10 PRs in 1 day
            "timeframe": 86400,  # 1 day in seconds
            "penalty": -10.0
        },
        "review_spam": {
            "threshold": 50,  # More than 50 reviews in 1 day
            "timeframe": 86400,
            "penalty": -8.0
        },
        "artificial_collaboration": {
            "threshold": 0.8,  # 80% of reviews are on same person's PRs
            "min_reviews": 15,
            "penalty": -5.0
        },
        "essence_manipulation": {
            "threshold": 50,  # Gain more than 50 essence in 1 day
            "timeframe": 86400,
            "penalty": -20.0
        }
    }
    
    @classmethod
    async def detect_gaming_patterns(cls, user_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Detect potential gaming patterns for a user"""
        db = await get_database()
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        detected_patterns = []
        
        # Check rapid commits
        rapid_commits = await cls._check_rapid_commits(db, user_id, start_date, end_date)
        if rapid_commits:
            detected_patterns.append(rapid_commits)
        
        # Check tiny commits
        tiny_commits = await cls._check_tiny_commits(db, user_id, start_date, end_date)
        if tiny_commits:
            detected_patterns.append(tiny_commits)
        
        # Check PR spam
        pr_spam = await cls._check_pr_spam(db, user_id, start_date, end_date)
        if pr_spam:
            detected_patterns.append(pr_spam)
        
        # Check review spam
        review_spam = await cls._check_review_spam(db, user_id, start_date, end_date)
        if review_spam:
            detected_patterns.append(review_spam)
        
        # Check artificial collaboration
        artificial_collab = await cls._check_artificial_collaboration(db, user_id, start_date, end_date)
        if artificial_collab:
            detected_patterns.append(artificial_collab)
        
        # Check essence manipulation
        essence_manip = await cls._check_essence_manipulation(db, user_id, start_date, end_date)
        if essence_manip:
            detected_patterns.append(essence_manip)
        
        return detected_patterns
    
    @classmethod
    async def _check_rapid_commits(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for suspiciously rapid commits"""
        commits = []
        async for commit in db.commit_activity.find({
            "user_id": user_id,
            "commit_time": {"$gte": start_date, "$lte": end_date}
        }).sort("commit_time", 1):
            commits.append(commit["commit_time"])
        
        if len(commits) < 10:
            return None
        
        # Check for clusters of commits
        for i in range(len(commits) - cls.SUSPICIOUS_PATTERNS["rapid_commits"]["threshold"]):
            window_commits = commits[i:i + cls.SUSPICIOUS_PATTERNS["rapid_commits"]["threshold"]]
            time_diff = (window_commits[-1] - window_commits[0]).total_seconds()
            
            if time_diff <= cls.SUSPICIOUS_PATTERNS["rapid_commits"]["timeframe"]:
                return {
                    "type": "rapid_commits",
                    "severity": "high",
                    "description": f"Made {len(window_commits)} commits in {time_diff/60:.1f} minutes",
                    "penalty": cls.SUSPICIOUS_PATTERNS["rapid_commits"]["penalty"],
                    "detected_at": datetime.utcnow()
                }
        
        return None
    
    @classmethod
    async def _check_tiny_commits(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for pattern of very small commits (potential gaming)"""
        commits = []
        async for commit in db.commit_activity.find({
            "user_id": user_id,
            "commit_time": {"$gte": start_date, "$lte": end_date}
        }):
            total_changes = len(commit.get("additions", [])) + len(commit.get("deletions", []))
            commits.append(total_changes)
        
        if len(commits) < cls.SUSPICIOUS_PATTERNS["tiny_commits"]["min_commits"]:
            return None
        
        tiny_commits = sum(1 for changes in commits if changes < 5)
        tiny_ratio = tiny_commits / len(commits)
        
        if tiny_ratio > cls.SUSPICIOUS_PATTERNS["tiny_commits"]["threshold"]:
            return {
                "type": "tiny_commits",
                "severity": "medium",
                "description": f"{tiny_ratio*100:.1f}% of commits are very small (< 5 lines)",
                "penalty": cls.SUSPICIOUS_PATTERNS["tiny_commits"]["penalty"],
                "detected_at": datetime.utcnow()
            }
        
        return None
    
    @classmethod
    async def _check_pr_spam(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for PR spam"""
        pr_count = await db.pull_requests.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        days = (end_date - start_date).days
        daily_average = pr_count / max(days, 1)
        
        if daily_average > cls.SUSPICIOUS_PATTERNS["pr_spam"]["threshold"]:
            return {
                "type": "pr_spam",
                "severity": "high",
                "description": f"Created {pr_count} PRs in {days} days (avg {daily_average:.1f}/day)",
                "penalty": cls.SUSPICIOUS_PATTERNS["pr_spam"]["penalty"],
                "detected_at": datetime.utcnow()
            }
        
        return None
    
    @classmethod
    async def _check_review_spam(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for review spam"""
        review_count = await db.code_reviews.count_documents({
            "reviewer_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        days = (end_date - start_date).days
        daily_average = review_count / max(days, 1)
        
        if daily_average > cls.SUSPICIOUS_PATTERNS["review_spam"]["threshold"]:
            return {
                "type": "review_spam",
                "severity": "medium",
                "description": f"Submitted {review_count} reviews in {days} days (avg {daily_average:.1f}/day)",
                "penalty": cls.SUSPICIOUS_PATTERNS["review_spam"]["penalty"],
                "detected_at": datetime.utcnow()
            }
        
        return None
    
    @classmethod
    async def _check_artificial_collaboration(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for artificial collaboration (reviewing only specific people)"""
        reviews = []
        async for review in db.code_reviews.find({
            "reviewer_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }):
            # Get PR author from the PR record
            pr = await db.pull_requests.find_one({"_id": review["pr_id"]})
            if pr:
                reviews.append(pr["user_id"])
        
        if len(reviews) < cls.SUSPICIOUS_PATTERNS["artificial_collaboration"]["min_reviews"]:
            return None
        
        # Count reviews per author
        author_counts = defaultdict(int)
        for author in reviews:
            author_counts[author] += 1
        
        # Check if too concentrated on one author
        max_count = max(author_counts.values())
        concentration_ratio = max_count / len(reviews)
        
        if concentration_ratio > cls.SUSPICIOUS_PATTERNS["artificial_collaboration"]["threshold"]:
            return {
                "type": "artificial_collaboration",
                "severity": "medium",
                "description": f"{concentration_ratio*100:.1f}% of reviews are for the same author",
                "penalty": cls.SUSPICIOUS_PATTERNS["artificial_collaboration"]["penalty"],
                "detected_at": datetime.utcnow()
            }
        
        return None
    
    @classmethod
    async def _check_essence_manipulation(cls, db, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Check for suspicious essence gains"""
        essence_logs = []
        async for log in db.essence_logs.find({
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
            "essence_delta": {"$gt": 0}  # Only positive gains
        }):
            essence_logs.append(log["essence_delta"])
        
        if not essence_logs:
            return None
        
        daily_gain = sum(essence_logs)
        days = (end_date - start_date).days or 1
        daily_average = daily_gain / days
        
        if daily_average > cls.SUSPICIOUS_PATTERNS["essence_manipulation"]["threshold"]:
            return {
                "type": "essence_manipulation",
                "severity": "high",
                "description": f"Gained {daily_gain:.1f} essence in {days} days (avg {daily_average:.1f}/day)",
                "penalty": cls.SUSPICIOUS_PATTERNS["essence_manipulation"]["penalty"],
                "detected_at": datetime.utcnow()
            }
        
        return None
    
    @classmethod
    async def apply_anti_gaming_penalties(cls, user_id: str) -> List[Dict[str, Any]]:
        \"\"\"Apply penalties for detected gaming patterns\"\"\"
        db = await get_database()
        
        # Detect gaming patterns
        patterns = await cls.detect_gaming_patterns(user_id, days_back=7)
        
        applied_penalties = []
        
        for pattern in patterns:
            # Check if this pattern was already penalized recently
            existing_penalty = await db.essence_logs.find_one({
                "user_id": user_id,
                "event_type": "anti_gaming_penalty",
                "reason": {"$regex": pattern["type"]},
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}
            })
            
            if existing_penalty:
                continue  # Don't double-penalize
            
            # Apply penalty
            penalty = pattern["penalty"]
            
            # Get current user essence
            user = await db.users.find_one({"_id": user_id})
            if not user:
                continue
            
            current_essence = user.get("essence", {}).get("overall", 50.0)
            new_essence = max(0, current_essence + penalty)  # Don't go below 0
            
            # Update user essence
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {"essence.overall": new_essence}}
            )
            
            # Log the penalty
            penalty_log = {
                "user_id": user_id,
                "event_type": "anti_gaming_penalty",
                "essence_delta": penalty,
                "previous_essence": current_essence,
                "new_essence": new_essence,
                "reason": f"Gaming detection: {pattern['description']}",
                "metadata": pattern,
                "created_at": datetime.utcnow()
            }
            
            await db.essence_logs.insert_one(penalty_log)
            applied_penalties.append(penalty_log)
        
        return applied_penalties
    
    @classmethod
    async def get_gaming_report(cls, user_id: str) -> Dict[str, Any]:
        \"\"\"Get a comprehensive gaming detection report for a user\"\"\"
        patterns = await cls.detect_gaming_patterns(user_id, days_back=30)
        
        # Calculate risk score
        risk_score = 0
        for pattern in patterns:
            if pattern["severity"] == "high":
                risk_score += 3
            elif pattern["severity"] == "medium":
                risk_score += 2
            else:
                risk_score += 1
        
        # Determine risk level
        if risk_score >= 8:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"
        elif risk_score >= 1:
            risk_level = "low"
        else:
            risk_level = "none"
        
        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "detected_patterns": patterns,
            "total_patterns": len(patterns),
            "generated_at": datetime.utcnow()
        }