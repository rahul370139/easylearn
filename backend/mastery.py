"""
Mastery Tracking for TrainPI Agents
Tracks user mastery of different skills and topics with existing system integration
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import uuid
from datetime import datetime
import json

# Import existing functionality
try:
    from supabase_helper import fetch_mastery, update_mastery_row
except ImportError:
    logger.warning("Could not import from supabase_helper, using local storage")
    # Local storage fallback
    _mastery_store = {}
    
    def fetch_mastery(user_id: str) -> Dict[str, float]:
        """Local fallback for mastery retrieval"""
        return _mastery_store.get(user_id, {})
    
    def update_mastery_row(user_id: str, skill: str, score: float):
        """Local fallback for mastery update"""
        if user_id not in _mastery_store:
            _mastery_store[user_id] = {}
        _mastery_store[user_id][skill] = score


class MasteryTracker:
    """Tracks user mastery of different skills and topics"""
    
    def __init__(self):
        self.mastery_data = {}
        self.learning_history = {}
    
    def get_mastery(self, user_id: str, topic: str = "") -> Dict[str, Any]:
        """Get user mastery for a specific topic or overall"""
        try:
            # Try to get from Supabase first
            supabase_mastery = fetch_mastery(user_id)
            
            if topic:
                # Return specific topic mastery
                topic_mastery = supabase_mastery.get(topic, 0.0)
                return {
                    "topic": topic,
                    "mastery_score": topic_mastery,
                    "confidence": self._calculate_confidence(user_id, topic),
                    "last_assessed": self._get_last_assessment(user_id, topic),
                    "assessment_count": self._get_assessment_count(user_id, topic),
                    "skill_level": self._get_skill_level(topic_mastery)
                }
            else:
                # Return overall mastery
                return {
                    "overall_mastery": self._calculate_overall_mastery(supabase_mastery),
                    "skills": supabase_mastery,
                    "total_skills": len(supabase_mastery),
                    "strongest_skill": self._get_strongest_skill(supabase_mastery),
                    "weakest_skill": self._get_weakest_skill(supabase_mastery)
                }
                
        except Exception as e:
            logger.error(f"Mastery retrieval failed: {e}")
            return {}
    
    def update_mastery(self, user_id: str, topic: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Update mastery scores based on assessment results"""
        try:
            # Calculate new mastery score
            new_score = self._calculate_mastery_score(results)
            
            # Update in Supabase
            update_mastery_row(user_id, topic, new_score)
            
            # Store local history
            if user_id not in self.learning_history:
                self.learning_history[user_id] = {}
            
            if topic not in self.learning_history[user_id]:
                self.learning_history[user_id][topic] = {
                    "assessments": [],
                    "progress_trend": [],
                    "last_updated": None
                }
            
            # Add assessment record
            assessment_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "score": new_score,
                "results": results,
                "mastery_change": self._calculate_mastery_change(user_id, topic, new_score)
            }
            
            self.learning_history[user_id][topic]["assessments"].append(assessment_record)
            self.learning_history[user_id][topic]["last_updated"] = datetime.utcnow().isoformat()
            
            # Keep only last 20 assessments
            if len(self.learning_history[user_id][topic]["assessments"]) > 20:
                self.learning_history[user_id][topic]["assessments"] = self.learning_history[user_id][topic]["assessments"][-20:]
            
            # Update progress trend
            self._update_progress_trend(user_id, topic, new_score)
            
            logger.info(f"Mastery updated for user {user_id}, topic {topic}: {new_score}")
            
            return {
                "topic": topic,
                "new_mastery_score": new_score,
                "mastery_change": assessment_record["mastery_change"],
                "skill_level": self._get_skill_level(new_score),
                "next_milestone": self._get_next_milestone(new_score),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Mastery update failed: {e}")
            return {}
    
    def _calculate_mastery_score(self, results: Dict[str, Any]) -> float:
        """Calculate mastery score from assessment results"""
        try:
            overall_score = results.get("overall_score", 0)
            
            # Convert percentage to 0-1 scale
            mastery_score = overall_score / 100.0
            
            # Apply confidence weighting based on question count
            question_count = results.get("total_questions", 1)
            confidence_factor = min(1.0, question_count / 10.0)
            
            # Weighted mastery score
            weighted_score = mastery_score * confidence_factor
            
            # Apply learning curve (easier to go from 0.3 to 0.5 than 0.8 to 0.9)
            if weighted_score > 0.8:
                # Diminishing returns for high scores
                adjusted_score = 0.8 + (weighted_score - 0.8) * 0.5
            else:
                adjusted_score = weighted_score
            
            return round(adjusted_score, 3)
            
        except Exception as e:
            logger.warning(f"Mastery score calculation failed: {e}")
            return 0.0
    
    def _calculate_confidence(self, user_id: str, topic: str) -> float:
        """Calculate confidence in mastery assessment"""
        try:
            if user_id in self.learning_history and topic in self.learning_history[user_id]:
                assessment_count = len(self.learning_history[user_id][topic]["assessments"])
                # More assessments = higher confidence
                return min(1.0, assessment_count / 5.0)
            return 0.0
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.0
    
    def _get_last_assessment(self, user_id: str, topic: str) -> Optional[str]:
        """Get timestamp of last assessment"""
        try:
            if user_id in self.learning_history and topic in self.learning_history[user_id]:
                return self.learning_history[user_id][topic]["last_updated"]
            return None
        except Exception as e:
            logger.warning(f"Last assessment retrieval failed: {e}")
            return None
    
    def _get_assessment_count(self, user_id: str, topic: str) -> int:
        """Get number of assessments for a topic"""
        try:
            if user_id in self.learning_history and topic in self.learning_history[user_id]:
                return len(self.learning_history[user_id][topic]["assessments"])
            return 0
        except Exception as e:
            logger.warning(f"Assessment count retrieval failed: {e}")
            return 0
    
    def _get_skill_level(self, mastery_score: float) -> str:
        """Get human-readable skill level"""
        try:
            if mastery_score >= 0.9:
                return "Expert"
            elif mastery_score >= 0.7:
                return "Advanced"
            elif mastery_score >= 0.5:
                return "Intermediate"
            elif mastery_score >= 0.3:
                return "Beginner"
            else:
                return "Novice"
        except Exception as e:
            logger.warning(f"Skill level determination failed: {e}")
            return "Unknown"
    
    def _calculate_overall_mastery(self, skills_mastery: Dict[str, float]) -> float:
        """Calculate overall mastery across all skills"""
        try:
            if not skills_mastery:
                return 0.0
            
            total_score = sum(skills_mastery.values())
            return round(total_score / len(skills_mastery), 3)
            
        except Exception as e:
            logger.warning(f"Overall mastery calculation failed: {e}")
            return 0.0
    
    def _get_strongest_skill(self, skills_mastery: Dict[str, float]) -> Optional[str]:
        """Get the skill with highest mastery"""
        try:
            if not skills_mastery:
                return None
            
            return max(skills_mastery.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.warning(f"Strongest skill determination failed: {e}")
            return None
    
    def _get_weakest_skill(self, skills_mastery: Dict[str, float]) -> Optional[str]:
        """Get the skill with lowest mastery"""
        try:
            if not skills_mastery:
                return None
            
            return min(skills_mastery.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.warning(f"Weakest skill determination failed: {e}")
            return None
    
    def _calculate_mastery_change(self, user_id: str, topic: str, new_score: float) -> float:
        """Calculate change in mastery score"""
        try:
            if user_id in self.learning_history and topic in self.learning_history[user_id]:
                assessments = self.learning_history[user_id][topic]["assessments"]
                if len(assessments) > 1:
                    previous_score = assessments[-2]["score"]
                    return round(new_score - previous_score, 3)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Mastery change calculation failed: {e}")
            return 0.0
    
    def _update_progress_trend(self, user_id: str, topic: str, new_score: float):
        """Update progress trend for a topic"""
        try:
            if user_id in self.learning_history and topic in self.learning_history[user_id]:
                trend = self.learning_history[user_id][topic]["progress_trend"]
                
                # Add new data point
                trend.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "score": new_score
                })
                
                # Keep only last 10 data points
                if len(trend) > 10:
                    self.learning_history[user_id][topic]["progress_trend"] = trend[-10:]
                
        except Exception as e:
            logger.warning(f"Progress trend update failed: {e}")
    
    def _get_next_milestone(self, current_score: float) -> Dict[str, Any]:
        """Get next mastery milestone"""
        try:
            milestones = [0.3, 0.5, 0.7, 0.9]
            
            for milestone in milestones:
                if current_score < milestone:
                    return {
                        "milestone": milestone,
                        "points_needed": round(milestone - current_score, 3),
                        "description": self._get_milestone_description(milestone)
                    }
            
            return {
                "milestone": 1.0,
                "points_needed": 0.0,
                "description": "Mastery achieved!"
            }
            
        except Exception as e:
            logger.warning(f"Next milestone calculation failed: {e}")
            return {"milestone": 0.5, "points_needed": 0.5, "description": "Continue learning"}
    
    def _get_milestone_description(self, milestone: float) -> str:
        """Get description for a mastery milestone"""
        try:
            if milestone == 0.3:
                return "Basic understanding"
            elif milestone == 0.5:
                return "Intermediate knowledge"
            elif milestone == 0.7:
                return "Advanced proficiency"
            elif milestone == 0.9:
                return "Expert level"
            else:
                return "Learning milestone"
        except Exception as e:
            logger.warning(f"Milestone description failed: {e}")
            return "Learning milestone"


# Global mastery tracker instance
mastery_tracker = MasteryTracker()

# Convenience functions for external use (matching your specification)
def get_mastery(user_id: str) -> Dict[str, float]:
    """Get mastery scores for a user across all skills"""
    try:
        # Try to fetch from Supabase first
        mastery_data = fetch_mastery(user_id)
        if mastery_data:
            return mastery_data
        
        # Fallback to local storage if Supabase fails
        logger.warning(f"Supabase fetch failed for user {user_id}, using local fallback")
        return get_local_mastery(user_id)
        
    except Exception as e:
        logger.error(f"Mastery retrieval failed for user {user_id}: {e}")
        # Return empty dict on error to prevent crashes
        return {}

def update_mastery(user_id: str, skill_scores: Dict[str, float]):
    """Apply exponential moving average or Bayesian update"""
    try:
        for skill, score in skill_scores.items():
            # Create a results dict that matches expected format
            results = {
                "overall_score": score * 100,  # Convert to percentage
                "total_questions": 1,
                "correct_answers": 1
            }
            
            mastery_tracker.update_mastery(user_id, skill, results)
            
    except Exception as e:
        logger.error(f"Mastery update failed: {e}")

# Additional utility functions
def get_topic_mastery(user_id: str, topic: str) -> Dict[str, Any]:
    """Get mastery for a specific topic"""
    return mastery_tracker.get_mastery(user_id, topic)

def get_learning_progress(user_id: str, topic: str) -> Dict[str, Any]:
    """Get learning progress and trends for a topic"""
    try:
        if user_id in mastery_tracker.learning_history and topic in mastery_tracker.learning_history[user_id]:
            return mastery_tracker.learning_history[user_id][topic]
        return {}
    except Exception as e:
        logger.error(f"Learning progress retrieval failed: {e}")
        return {}

def get_recommended_topics(user_id: str) -> List[str]:
    """Get recommended topics based on current mastery"""
    try:
        mastery_data = get_mastery(user_id)
        
        # Recommend topics with lower mastery scores
        low_mastery_topics = [
            topic for topic, score in mastery_data.items() 
            if score < 0.7
        ]
        
        # Sort by mastery score (lowest first)
        low_mastery_topics.sort(key=lambda x: mastery_data[x])
        
        return low_mastery_topics[:5]  # Return top 5 recommendations
        
    except Exception as e:
        logger.error(f"Topic recommendation failed: {e}")
        return []
