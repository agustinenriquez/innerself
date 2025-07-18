from typing import Optional
from datetime import datetime, timedelta
import re

from app.models.message import EssenceImpact, EssenceImpactType
from app.db.mongodb import get_database

class EssenceAnalyzer:
    """Analyzes messages and activities for essence impact"""
    
    @staticmethod
    async def analyze_message_content(content: str) -> dict:
        """Analyze message content for sentiment and patterns"""
        content_lower = content.lower()
        
        # Positive patterns
        positive_patterns = [
            r'\b(thanks?|thank you|great|awesome|excellent|good job|well done)\b',
            r'\b(helps?|helpful|support|assist)\b',
            r'\b(solved?|fixed?|resolved?)\b',
            r'\b(nice|cool|amazing|fantastic)\b'
        ]
        
        # Negative patterns
        negative_patterns = [
            r'\b(urgent|asap|immediately|now)\b',
            r'\b(why haven\'t|where is|what about)\b',
            r'\b(should have|could have|need to)\b',
            r'[?]{2,}',  # Multiple question marks
            r'[!]{2,}'   # Multiple exclamation marks
        ]
        
        # Question patterns (neutral but frequent questions from same user = micromanagement)
        question_patterns = [
            r'can you\b',
            r'could you\b',
            r'what\'s the status',
            r'any update',
            r'how\'s it going'
        ]
        
        positive_score = sum(1 for pattern in positive_patterns if re.search(pattern, content_lower))
        negative_score = sum(1 for pattern in negative_patterns if re.search(pattern, content_lower))
        question_score = sum(1 for pattern in question_patterns if re.search(pattern, content_lower))
        
        return {
            "positive_score": positive_score,
            "negative_score": negative_score,
            "question_score": question_score,
            "word_count": len(content.split()),
            "has_code": bool(re.search(r'```|`[^`]+`', content)),
            "has_link": bool(re.search(r'https?://', content))
        }
    
    @staticmethod
    async def check_micromanagement(user_id: str, channel: str, timeframe_minutes: int = 60) -> bool:
        """Check if user is exhibiting micromanagement behavior"""
        db = await get_database()
        
        # Look for multiple messages in short timeframe
        start_time = datetime.utcnow() - timedelta(minutes=timeframe_minutes)
        
        message_count = await db.messages.count_documents({
            "author_id": user_id,
            "channel": channel,
            "timestamp": {"$gte": start_time}
        })
        
        # Get recent messages to analyze pattern
        recent_messages = []
        async for msg in db.messages.find({
            "author_id": user_id,
            "channel": channel,
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", -1).limit(10):
            recent_messages.append(msg["content"])
        
        # Micromanagement indicators:
        # 1. More than 5 messages in 1 hour
        # 2. High percentage of questions
        # 3. Repetitive content
        
        if message_count >= 5:
            question_count = sum(1 for msg in recent_messages if '?' in msg)
            question_ratio = question_count / len(recent_messages) if recent_messages else 0
            
            # If >60% of messages are questions, likely micromanagement
            if question_ratio > 0.6:
                return True
        
        return False

async def analyze_message_essence(content: str, user_id: str, channel: str) -> Optional[EssenceImpact]:
    """Main function to analyze a message and determine essence impact"""
    analyzer = EssenceAnalyzer()
    
    # Analyze content
    analysis = await analyzer.analyze_message_content(content)
    
    # Check for micromanagement
    is_micromanagement = await analyzer.check_micromanagement(user_id, channel)
    
    # Determine essence impact
    if is_micromanagement:
        return EssenceImpact(
            type=EssenceImpactType.NEGATIVE,
            score_delta=-2.0,
            reason="Multiple requests in rapid succession (micromanagement detected)",
            analysis_metadata=analysis
        )
    
    # Positive impact for helpful messages
    if analysis["positive_score"] > 0 or analysis["has_code"] or analysis["has_link"]:
        delta = 1.0 + (analysis["positive_score"] * 0.5)
        if analysis["has_code"]:
            delta += 0.5  # Bonus for sharing code
        
        return EssenceImpact(
            type=EssenceImpactType.POSITIVE,
            score_delta=delta,
            reason="Helpful or constructive message",
            analysis_metadata=analysis
        )
    
    # Negative impact for demanding/urgent messages
    if analysis["negative_score"] > 1:
        return EssenceImpact(
            type=EssenceImpactType.NEGATIVE,
            score_delta=-1.0,
            reason="Demanding or urgent tone detected",
            analysis_metadata=analysis
        )
    
    # Neutral for normal messages
    return EssenceImpact(
        type=EssenceImpactType.NEUTRAL,
        score_delta=0.0,
        reason="Standard message",
        analysis_metadata=analysis
    )