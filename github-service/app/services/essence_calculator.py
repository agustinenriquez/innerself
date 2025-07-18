from typing import Dict, Any
import re

class EssenceCalculator:
    """Calculates essence impact from GitHub activities"""
    
    async def calculate_pr_essence(self, pr_data: Dict[str, Any], action: str) -> float:
        """Calculate essence impact for PR actions"""
        if action == "opened":
            # Base points for opening a PR
            base_points = 5.0
            
            # Bonus for good PR practices
            title = pr_data.get("title", "")
            body = pr_data.get("body", "")
            
            # Good title (descriptive, follows patterns)
            if len(title) > 10 and not title.lower().startswith(("fix", "update", "change")):
                base_points += 2.0
            
            # Good description
            if body and len(body) > 50:
                base_points += 3.0
                
                # Check for good PR practices
                if "## " in body or "### " in body:  # Structured description
                    base_points += 2.0
                if re.search(r'(fixes?|closes?|resolves?) #\d+', body.lower()):  # Links to issues
                    base_points += 2.0
            
            # Size bonus/penalty
            files_changed = pr_data.get("files_changed", 0)
            lines_added = pr_data.get("lines_added", 0)
            lines_deleted = pr_data.get("lines_deleted", 0)
            
            # Reasonable size (not too big, not too small)
            total_changes = lines_added + lines_deleted
            if 10 <= total_changes <= 500:
                base_points += 3.0
            elif total_changes > 1000:
                base_points -= 2.0  # Very large PRs are harder to review
            
            return base_points
            
        elif action == "merged":
            # Bonus for successful merge
            merge_bonus = 10.0
            
            # Time to merge bonus (faster = better for team velocity)
            created_at = pr_data.get("created_at")
            merged_at = pr_data.get("merged_at")
            
            if created_at and merged_at:
                hours_to_merge = (merged_at - created_at).total_seconds() / 3600
                
                if hours_to_merge <= 4:  # Same day merge
                    merge_bonus += 5.0
                elif hours_to_merge <= 24:  # Next day merge
                    merge_bonus += 3.0
                elif hours_to_merge > 168:  # More than a week
                    merge_bonus -= 2.0
            
            return merge_bonus
            
        elif action == "closed":
            # Small penalty for closed without merge (unless it's a good reason)
            return -2.0
        
        return 0.0
    
    async def calculate_commit_essence(self, commit_data: Dict[str, Any]) -> float:
        """Calculate essence impact for commits"""
        message = commit_data.get("message", "")
        
        # Base points for any commit
        base_points = 1.0
        
        # Good commit message practices
        if len(message) > 10:
            base_points += 1.0
        
        # Conventional commit format
        if re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+', message):
            base_points += 2.0
        
        # Avoid merge commits (they don't add much value)
        if commit_data.get("is_merge_commit"):
            return 0.5
        
        # Small commits are generally better
        additions = len(commit_data.get("additions", []))
        deletions = len(commit_data.get("deletions", []))
        total_changes = additions + deletions
        
        if total_changes <= 50:
            base_points += 1.0
        elif total_changes > 200:
            base_points -= 0.5
        
        return base_points
    
    async def calculate_review_essence(self, review_data: Dict[str, Any]) -> float:
        """Calculate essence impact for code reviews"""
        state = review_data.get("review_state", "")
        comment_count = review_data.get("comment_count", 0)
        
        base_points = 3.0  # Base points for doing a review
        
        if state == "approved":
            base_points += 2.0
        elif state == "changes_requested":
            base_points += 5.0  # More valuable as it helps improve code
            
            # Bonus for detailed feedback
            if comment_count > 100:  # Substantial review
                base_points += 3.0
            elif comment_count > 50:
                base_points += 2.0
        elif state == "commented":
            base_points += 1.0
            
            # Bonus for helpful comments
            if comment_count > 50:
                base_points += 2.0
        
        return base_points
    
    async def calculate_comment_essence(self, comment_data: Dict[str, Any]) -> float:
        """Calculate essence impact for comments"""
        body = comment_data.get("body", "")
        
        if len(body) < 10:
            return 0.0  # Too short to be helpful
        
        base_points = 1.0
        
        # Look for helpful patterns
        helpful_patterns = [
            r'here\'s how to',
            r'you can try',
            r'have you considered',
            r'this might help',
            r'documentation says',
            r'similar issue',
            r'```',  # Code examples
        ]
        
        for pattern in helpful_patterns:
            if re.search(pattern, body.lower()):
                base_points += 1.0
        
        # Bonus for longer, detailed comments
        if len(body) > 200:
            base_points += 2.0
        elif len(body) > 100:
            base_points += 1.0
        
        # Look for negative patterns
        negative_patterns = [
            r'why did you',
            r'this is wrong',
            r'you should have',
            r'obviously',
        ]
        
        for pattern in negative_patterns:
            if re.search(pattern, body.lower()):
                base_points -= 1.0
        
        return max(0, base_points)  # Don't go negative