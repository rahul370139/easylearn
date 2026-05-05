import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from groq import Groq
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent

class DashboardSystem:
    """
    Dashboard System for TrainPI
    Handles: Recommendations, Career Coaching, Analytics, Progress Tracking, Achievements
    """
    
    def __init__(self):
        """Initialize dashboard system with AI capabilities"""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_key_2 = os.getenv("GROQ_API_KEY_2")
        # Initialize with primary key, will fallback if needed
        self.client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.career_data = self._load_career_data()
        self.micro_lessons = self._load_micro_lessons()
        
    def _load_career_data(self) -> pd.DataFrame:
        """Load career data from CSV"""
        try:
            return pd.read_csv(_BACKEND_ROOT / "data" / "onet_bls_trimmed.csv")
        except Exception as e:
            logger.warning(f"Could not load career data: {e}")
            return self._create_sample_career_data()
    
    def _load_micro_lessons(self) -> Dict:
        """Load micro lessons from JSON"""
        try:
            with open(_BACKEND_ROOT / "data" / "micro_lessons.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load micro lessons: {e}")
            return self._create_default_micro_lessons()
    
    def _create_sample_career_data(self) -> pd.DataFrame:
        """Create sample career data"""
        return pd.DataFrame({
            'title': ['Software Developer', 'Data Scientist', 'Product Manager'],
            'riasec_realistic': [3, 2, 2],
            'riasec_investigative': [4, 5, 3],
            'riasec_artistic': [2, 1, 3],
            'riasec_social': [2, 2, 4],
            'riasec_enterprising': [3, 2, 5],
            'riasec_conventional': [2, 3, 2]
        })
    
    def _create_default_micro_lessons(self) -> Dict:
        """Create default micro lessons"""
        return {
            "python": [
                {"title": "Python Basics", "duration": "2 hours", "difficulty": "beginner"},
                {"title": "Advanced Python", "duration": "4 hours", "difficulty": "intermediate"}
            ],
            "javascript": [
                {"title": "JavaScript Fundamentals", "duration": "3 hours", "difficulty": "beginner"},
                {"title": "React Development", "duration": "5 hours", "difficulty": "intermediate"}
            ]
        }
    
    async def generate_personalized_recommendations(
        self, 
        user_id: str,
        user_profile: Optional[Dict] = None,
        user_skills: Optional[List[str]] = None,
        user_interests: Optional[List[str]] = None,
        target_role: Optional[str] = None
    ) -> Dict:
        """Generate comprehensive personalized recommendations"""
        try:
            # Generate AI-powered recommendations
            recommendations = await self._generate_ai_recommendations(
                user_profile, user_skills, user_interests, target_role
            )
            
            # Add skill-based recommendations
            skill_recommendations = self._get_skill_based_recommendations(user_skills or [])
            
            # Add market trends
            market_trends = await self._get_market_trends()
            
            return {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "career_recommendations": recommendations,
                "skill_recommendations": skill_recommendations,
                "market_trends": market_trends,
                "learning_paths": self._get_learning_paths(user_skills or []),
                "next_steps": await self._generate_next_steps(user_profile, user_skills)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_fallback_recommendations(user_id)
    
    async def _generate_ai_recommendations(
        self,
        user_profile: Optional[Dict],
        user_skills: Optional[List[str]],
        user_interests: Optional[List[str]],
        target_role: Optional[str]
    ) -> Dict:
        """Generate AI-powered career recommendations"""
        try:
            prompt = f"""
            Generate personalized career recommendations based on:
            
            User Profile: {user_profile or {}}
            Current Skills: {user_skills or []}
            Interests: {user_interests or []}
            Target Role: {target_role or 'Not specified'}
            
            Provide recommendations for:
            1. Career paths to explore
            2. Skills to develop
            3. Learning priorities
            4. Market opportunities
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            return self._get_fallback_career_recommendations()
    
    def _get_skill_based_recommendations(self, user_skills: List[str]) -> List[Dict]:
        """Get recommendations based on user skills"""
        recommendations = []
        
        for skill in user_skills:
            if skill.lower() in self.micro_lessons:
                lessons = self.micro_lessons[skill.lower()]
                recommendations.extend(lessons)
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    async def _get_market_trends(self) -> Dict:
        """Get current market trends"""
        try:
            prompt = """
            Provide current market trends for tech careers including:
            1. High-demand skills
            2. Emerging roles
            3. Salary trends
            4. Industry shifts
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error getting market trends: {e}")
            return self._get_fallback_market_trends()
    
    def _get_learning_paths(self, user_skills: List[str]) -> List[Dict]:
        """Get personalized learning paths"""
        paths = []
        
        # Create learning paths based on skill gaps
        target_skills = ["python", "javascript", "react", "node.js", "sql"]
        missing_skills = [skill for skill in target_skills if skill not in [s.lower() for s in user_skills]]
        
        for skill in missing_skills[:3]:  # Top 3 missing skills
            paths.append({
                "skill": skill,
                "estimated_duration": "2-4 weeks",
                "difficulty": "intermediate",
                "resources": self._get_skill_resources(skill)
            })
        
        return paths
    
    def _get_skill_resources(self, skill: str) -> List[str]:
        """Get learning resources for a skill"""
        resources = {
            "python": ["Python.org tutorials", "Codecademy Python", "Real Python"],
            "javascript": ["MDN Web Docs", "JavaScript.info", "Eloquent JavaScript"],
            "react": ["React docs", "React Tutorial", "Full Stack Open"],
            "node.js": ["Node.js docs", "Express.js guide", "Node.js Tutorial"],
            "sql": ["SQL Tutorial", "W3Schools SQL", "SQLite Tutorial"]
        }
        return resources.get(skill, ["Online tutorials", "Documentation", "Practice projects"])
    
    async def _generate_next_steps(self, user_profile: Optional[Dict], user_skills: Optional[List[str]]) -> List[str]:
        """Generate actionable next steps"""
        try:
            prompt = f"""
            Based on user profile: {user_profile or {}}
            And current skills: {user_skills or []}
            
            Provide 5 actionable next steps for career development.
            Return as a simple list of steps.
            """
            
            response = await self._call_groq(prompt)
            return [step.strip() for step in response.split('\n') if step.strip()][:5]
            
        except Exception as e:
            logger.error(f"Error generating next steps: {e}")
            return self._get_fallback_next_steps()
    
    async def generate_career_coaching_advice(
        self,
        user_id: str,
        user_profile: Optional[Dict] = None,
        target_role: Optional[str] = None,
        current_challenges: Optional[List[str]] = None
    ) -> Dict:
        """Generate personalized career coaching advice"""
        try:
            # Generate AI coaching advice
            coaching_advice = await self._generate_ai_coaching_advice(
                user_profile, target_role, current_challenges
            )
            
            # Add progress tracking
            progress_stats = self._get_user_progress_stats(user_id)
            
            # Add achievement tracking
            achievements = self._get_user_achievements(user_id)
            
            return {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "coaching_advice": coaching_advice,
                "progress_stats": progress_stats,
                "achievements": achievements,
                "action_plan": await self._generate_action_plan(user_profile, target_role)
            }
            
        except Exception as e:
            logger.error(f"Error generating coaching advice: {e}")
            return self._get_fallback_coaching_advice(user_id)
    
    async def _generate_ai_coaching_advice(
        self,
        user_profile: Optional[Dict],
        target_role: Optional[str],
        current_challenges: Optional[List[str]]
    ) -> Dict:
        """Generate AI-powered career coaching advice"""
        try:
            prompt = f"""
            Provide comprehensive career coaching advice for:
            
            User Profile: {user_profile or {}}
            Target Role: {target_role or 'Not specified'}
            Current Challenges: {current_challenges or []}
            
            Include advice on:
            1. Skill development strategies
            2. Networking approaches
            3. Interview preparation
            4. Career transition tips
            5. Work-life balance
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating AI coaching advice: {e}")
            return self._get_fallback_coaching_content()
    
    def _get_user_progress_stats(self, user_id: str) -> Dict:
        """Get user progress statistics"""
        # Mock progress data - in production, this would come from database
        return {
            "total_lessons_completed": 15,
            "current_streak": 7,
            "total_study_time": "45 hours",
            "skill_progress": {
                "python": {"completed": 8, "total": 12, "percentage": 67},
                "javascript": {"completed": 5, "total": 10, "percentage": 50},
                "react": {"completed": 3, "total": 8, "percentage": 38}
            },
            "certificates_earned": 3,
            "projects_completed": 5
        }
    
    def _get_user_achievements(self, user_id: str) -> List[Dict]:
        """Get user achievements"""
        return [
            {
                "id": "first_lesson",
                "title": "First Lesson Completed",
                "description": "Completed your first lesson",
                "earned_date": "2024-01-15",
                "icon": "🎯"
            },
            {
                "id": "week_streak",
                "title": "Week Warrior",
                "description": "Completed lessons for 7 days straight",
                "earned_date": "2024-01-22",
                "icon": "🔥"
            },
            {
                "id": "skill_master",
                "title": "Python Master",
                "description": "Completed all Python lessons",
                "earned_date": "2024-01-25",
                "icon": "🐍"
            }
        ]
    
    async def _generate_action_plan(self, user_profile: Optional[Dict], target_role: Optional[str]) -> Dict:
        """Generate personalized action plan"""
        try:
            prompt = f"""
            Create a 30-day action plan for:
            
            User Profile: {user_profile or {}}
            Target Role: {target_role or 'Career development'}
            
            Include:
            1. Daily/weekly goals
            2. Skill-building activities
            3. Networking opportunities
            4. Project work
            5. Learning milestones
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating action plan: {e}")
            return self._get_fallback_action_plan()
    
    async def get_user_analytics(self, user_id: str, time_period: str = "30d") -> Dict:
        """Get comprehensive user analytics"""
        try:
            # Get progress data
            progress_stats = self._get_user_progress_stats(user_id)
            
            # Get learning analytics
            learning_analytics = await self._generate_learning_analytics(user_id)
            
            # Get career analytics
            career_analytics = await self._generate_career_analytics(user_id)
            
            return {
                "user_id": user_id,
                "time_period": time_period,
                "timestamp": datetime.now().isoformat(),
                "progress_stats": progress_stats,
                "learning_analytics": learning_analytics,
                "career_analytics": career_analytics,
                "insights": await self._generate_analytics_insights(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return self._get_fallback_analytics(user_id)
    
    async def _generate_learning_analytics(self, user_id: str) -> Dict:
        """Generate learning analytics"""
        try:
            prompt = f"""
            Analyze learning patterns for user {user_id} and provide insights on:
            1. Learning efficiency
            2. Skill development trends
            3. Study habits
            4. Knowledge retention
            5. Learning recommendations
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating learning analytics: {e}")
            return self._get_fallback_learning_analytics()
    
    async def _generate_career_analytics(self, user_id: str) -> Dict:
        """Generate career analytics"""
        try:
            prompt = f"""
            Analyze career progression for user {user_id} and provide insights on:
            1. Career trajectory
            2. Skill market alignment
            3. Salary progression potential
            4. Industry trends alignment
            5. Career opportunities
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating career analytics: {e}")
            return self._get_fallback_career_analytics()
    
    async def _generate_analytics_insights(self, user_id: str) -> List[str]:
        """Generate actionable insights from analytics"""
        try:
            prompt = f"""
            Based on user {user_id}'s learning and career data, provide 5 actionable insights.
            Focus on practical recommendations for improvement.
            Return as a simple list of insights.
            """
            
            response = await self._call_groq(prompt)
            return [insight.strip() for insight in response.split('\n') if insight.strip()][:5]
            
        except Exception as e:
            logger.error(f"Error generating analytics insights: {e}")
            return self._get_fallback_insights()
    
    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API with fallback to GROQ_API_KEY_2"""
        # Try primary API key first
        if self.groq_api_key and self.client:
            result = await self._call_groq_with_key(prompt, self.groq_api_key, "primary")
            if result:
                return result
        
        # Try fallback key if primary failed
        if self.groq_api_key_2:
            logger.info("Primary GROQ API key failed, trying fallback key")
            result = await self._call_groq_with_key(prompt, self.groq_api_key_2, "fallback")
            if result:
                return result
        
        logger.error("All GROQ API keys failed")
        return "AI service temporarily unavailable"

    async def _call_groq_with_key(self, prompt: str, api_key: str, key_type: str) -> str:
        """Call Groq API with specific key"""
        try:
            # Create a new client with the specific key
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            logger.info(f"GROQ API call successful using {key_type} key")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed ({key_type} key): {e}")
            return ""
    
    # Fallback methods
    def _get_fallback_recommendations(self, user_id: str) -> Dict:
        """Fallback recommendations"""
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "career_recommendations": {"message": "Recommendations temporarily unavailable"},
            "skill_recommendations": [],
            "market_trends": self._get_fallback_market_trends(),
            "learning_paths": [],
            "next_steps": self._get_fallback_next_steps()
        }
    
    def _get_fallback_career_recommendations(self) -> Dict:
        """Fallback career recommendations"""
        return {
            "recommended_careers": ["Software Developer", "Data Scientist", "Product Manager"],
            "skill_priorities": ["Python", "JavaScript", "SQL"],
            "learning_focus": "Full-stack development",
            "market_opportunities": "High demand for tech roles"
        }
    
    def _get_fallback_market_trends(self) -> Dict:
        """Fallback market trends"""
        return {
            "high_demand_skills": ["Python", "JavaScript", "React", "Node.js"],
            "emerging_roles": ["AI Engineer", "DevOps Engineer", "Data Engineer"],
            "salary_trends": "Tech salaries continue to rise",
            "industry_shifts": "Remote work becoming standard"
        }
    
    def _get_fallback_next_steps(self) -> List[str]:
        """Fallback next steps"""
        return [
            "Complete current learning path",
            "Build a portfolio project",
            "Network with professionals",
            "Apply for entry-level positions",
            "Continue skill development"
        ]
    
    def _get_fallback_coaching_advice(self, user_id: str) -> Dict:
        """Fallback coaching advice"""
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "coaching_advice": {"message": "Coaching advice temporarily unavailable"},
            "progress_stats": self._get_user_progress_stats(user_id),
            "achievements": self._get_user_achievements(user_id),
            "action_plan": self._get_fallback_action_plan()
        }
    
    def _get_fallback_coaching_content(self) -> Dict:
        """Fallback coaching content"""
        return {
            "skill_development": "Focus on practical projects",
            "networking": "Attend industry events and meetups",
            "interview_prep": "Practice common technical questions",
            "career_transition": "Start with entry-level positions",
            "work_life_balance": "Set clear boundaries and priorities"
        }
    
    def _get_fallback_action_plan(self) -> Dict:
        """Fallback action plan"""
        return {
            "week_1": ["Complete 3 lessons", "Start a project"],
            "week_2": ["Build portfolio", "Network online"],
            "week_3": ["Apply to jobs", "Practice interviews"],
            "week_4": ["Follow up applications", "Continue learning"]
        }
    
    def _get_fallback_analytics(self, user_id: str) -> Dict:
        """Fallback analytics"""
        return {
            "user_id": user_id,
            "time_period": "30d",
            "timestamp": datetime.now().isoformat(),
            "progress_stats": self._get_user_progress_stats(user_id),
            "learning_analytics": self._get_fallback_learning_analytics(),
            "career_analytics": self._get_fallback_career_analytics(),
            "insights": self._get_fallback_insights()
        }
    
    def _get_fallback_learning_analytics(self) -> Dict:
        """Fallback learning analytics"""
        return {
            "learning_efficiency": "Good",
            "skill_development_trends": "Steady improvement",
            "study_habits": "Consistent",
            "knowledge_retention": "Strong",
            "learning_recommendations": "Continue current pace"
        }
    
    def _get_fallback_career_analytics(self) -> Dict:
        """Fallback career analytics"""
        return {
            "career_trajectory": "Positive",
            "skill_market_alignment": "Good",
            "salary_progression_potential": "High",
            "industry_trends_alignment": "Strong",
            "career_opportunities": "Many available"
        }
    
    def _get_fallback_insights(self) -> List[str]:
        """Fallback insights"""
        return [
            "Continue building practical projects",
            "Focus on in-demand skills",
            "Network with industry professionals",
            "Stay updated with market trends",
            "Maintain consistent learning schedule"
        ]

# Global dashboard instance
dashboard_system = DashboardSystem() 