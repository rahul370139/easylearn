"""
Career Matcher - Quiz-based career matching system with AI capabilities
Handles 10-question career quiz and generates comprehensive career roadmaps with AI
"""

import pandas as pd
import numpy as np
import json
import os
import httpx
from loguru import logger
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RIASEC interest dimensions
RIASEC = ["realistic", "investigative", "artistic", "social", "enterprising", "conventional"]

class CareerMatcher:
    def __init__(self):
        """Initialize career matcher with data and AI capabilities"""
        self.data_path = Path(__file__).parent / "data"
        
        # Load career data
        self.career_data = self._load_career_data()
        
        # Load quiz questions
        self.quiz_questions = self._load_quiz_questions()
        
        # Load career roadmaps
        self.career_roadmaps = self._load_career_roadmaps()
        
        # Initialize API helpers
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_key_2 = os.getenv("GROQ_API_KEY_2")
        
        logger.info("CareerMatcher initialized successfully with embedding capabilities")
    
    def _load_career_data(self) -> pd.DataFrame:
        """Load career data from CSV"""
        try:
            df = pd.read_csv(self.data_path / "onet_bls_trimmed.csv")
            logger.info(f"Loaded {len(df)} careers")
            return df
        except FileNotFoundError:
            logger.error("Career data not found. Please run backend/scripts/process_dataset.py first.")
            raise FileNotFoundError("Career data file not found")
    
    def _load_quiz_questions(self) -> List[Dict]:
        """Load quiz questions from JSON"""
        try:
            with open(self.data_path / "career_quiz_questions.json", "r") as f:
                data = json.load(f)
                return data["quiz_questions"]
        except FileNotFoundError:
            logger.error("Quiz questions not found")
            raise FileNotFoundError("Quiz questions file not found")
    
    def _load_career_roadmaps(self) -> Dict:
        """Load career roadmaps from JSON"""
        try:
            with open(self.data_path / "career_roadmaps.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Career roadmaps not found, using default")
            return self._create_default_roadmaps()
    
    def _create_default_roadmaps(self) -> Dict:
        """Create default career roadmaps"""
        return {
            "Software Developer": {
                "entry_level": {
                    "title": "Junior Developer",
                    "skills": ["Python", "JavaScript", "Git", "Basic Algorithms"],
                    "courses": ["Python Fundamentals", "Web Development Basics", "Version Control"],
                    "duration": "6-12 months",
                    "salary_range": "$60,000 - $80,000"
                },
                "mid_level": {
                    "title": "Software Developer",
                    "skills": ["Full-Stack Development", "Database Design", "API Development", "Testing"],
                    "courses": ["Advanced Web Development", "Database Systems", "API Design", "Testing Strategies"],
                    "duration": "2-3 years",
                    "salary_range": "$80,000 - $120,000"
                },
                "senior_level": {
                    "title": "Senior Developer",
                    "skills": ["System Architecture", "Team Leadership", "Performance Optimization", "DevOps"],
                    "courses": ["System Design", "Leadership Skills", "DevOps Practices", "Advanced Algorithms"],
                    "duration": "5+ years",
                    "salary_range": "$120,000 - $180,000"
                }
            },
            "Data Scientist": {
                "entry_level": {
                    "title": "Data Analyst",
                    "skills": ["SQL", "Python", "Excel", "Basic Statistics"],
                    "courses": ["Data Analysis Fundamentals", "SQL Mastery", "Python for Data Science"],
                    "duration": "6-12 months",
                    "salary_range": "$65,000 - $85,000"
                },
                "mid_level": {
                    "title": "Data Scientist",
                    "skills": ["Machine Learning", "Statistical Analysis", "Data Visualization", "Big Data Tools"],
                    "courses": ["Machine Learning Fundamentals", "Statistical Analysis", "Data Visualization", "Big Data Technologies"],
                    "duration": "2-4 years",
                    "salary_range": "$85,000 - $130,000"
                },
                "senior_level": {
                    "title": "Senior Data Scientist",
                    "skills": ["Advanced ML", "AI Strategy", "Team Leadership", "Business Intelligence"],
                    "courses": ["Advanced Machine Learning", "AI Strategy", "Leadership Skills", "Business Intelligence"],
                    "duration": "5+ years",
                    "salary_range": "$130,000 - $200,000"
                }
            }
        }
    
    def get_quiz_questions(self) -> List[Dict]:
        """Get all quiz questions"""
        return self.quiz_questions
    
    @staticmethod
    def answers_to_vec(answers: List[int]) -> np.ndarray:
        """Convert quiz answers to RIASEC vector"""
        if len(answers) != 10:
            raise ValueError("Must provide exactly 10 answers")
        
        vec = np.zeros(6)  # 6 RIASEC dimensions
        
        for i, answer in enumerate(answers):
            if 0 <= answer < len(RIASEC):
                question = CareerMatcher().quiz_questions[i]
                selected_option = question["options"][answer]
                scores = selected_option["score"]
                
                for dimension, score in scores.items():
                    vec[RIASEC.index(dimension)] += score
        
        # Normalize to unit length
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec
    
    async def get_career_matches(self, answers: List[int], user_skills: Optional[List[str]] = None, user_interests: Optional[List[str]] = None, top_k: int = 5) -> List[Dict]:
        """Get top career matches using advanced embedding-based matching"""
        if len(answers) != 10:
            raise ValueError("Must provide exactly 10 answers")
        
        try:
            # Create comprehensive user profile
            user_profile = await self._create_user_profile(answers, user_skills, user_interests)
            
            # Generate user profile embedding
            user_embedding = await self._generate_user_embedding(user_profile)
            
            # Get career embeddings and calculate similarities
            similarities = await self._calculate_career_similarities(user_embedding, user_profile)
            
            # Sort by similarity and return top matches
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # If all similarities are too low, use basic matching
            if similarities and similarities[0]["similarity"] < 0.3:
                logger.warning("Embedding similarities too low, using basic RIASEC matching")
                return self._get_basic_career_matches(answers, top_k)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Embedding-based career matching failed: {e}")
            # Fallback to basic RIASEC matching
            return self._get_basic_career_matches(answers, top_k)
    
    async def _create_user_profile(self, answers: List[int], user_skills: Optional[List[str]], user_interests: Optional[List[str]]) -> Dict:
        """Create comprehensive user profile for embedding generation"""
        # Convert answers to RIASEC scores
        riasec_scores = self.answers_to_vec(answers)
        
        # Extract skills and interests from quiz answers
        quiz_skills = self._extract_skills_from_answers(answers)
        quiz_interests = self._extract_interests_from_answers(answers)
        
        # Combine all user information
        profile = {
            "riasec_scores": {
                "realistic": float(riasec_scores[0]),
                "investigative": float(riasec_scores[1]),
                "artistic": float(riasec_scores[2]),
                "social": float(riasec_scores[3]),
                "enterprising": float(riasec_scores[4]),
                "conventional": float(riasec_scores[5])
            },
            "skills": list(set((user_skills or []) + quiz_skills)),
            "interests": list(set((user_interests or []) + quiz_interests)),
            "work_preferences": self._extract_work_preferences(answers),
            "learning_style": self._extract_learning_style(answers),
            "career_goals": self._extract_career_goals(answers)
        }
        
        return profile
    
    def _extract_skills_from_answers(self, answers: List[int]) -> List[str]:
        """Extract relevant skills based on quiz answers"""
        skills = []
        
        # Map answer patterns to skills
        if answers[0] >= 4:  # Technical/Hands-on preference
            skills.extend(["problem_solving", "technical_skills", "practical_application"])
        
        if answers[1] >= 4:  # Analytical thinking
            skills.extend(["data_analysis", "critical_thinking", "research"])
        
        if answers[2] >= 4:  # Creative thinking
            skills.extend(["creativity", "design_thinking", "innovation"])
        
        if answers[3] >= 4:  # Communication
            skills.extend(["communication", "teamwork", "leadership"])
        
        if answers[4] >= 4:  # Business/Management
            skills.extend(["project_management", "strategic_thinking", "business_acumen"])
        
        return list(set(skills))
    
    def _extract_interests_from_answers(self, answers: List[int]) -> List[str]:
        """Extract interests based on quiz answers"""
        interests = []
        
        # Map answer patterns to interests
        if answers[0] >= 4:
            interests.extend(["technology", "engineering", "hands_on_work"])
        
        if answers[1] >= 4:
            interests.extend(["science", "research", "analysis"])
        
        if answers[2] >= 4:
            interests.extend(["arts", "design", "creativity"])
        
        if answers[3] >= 4:
            interests.extend(["helping_others", "education", "social_impact"])
        
        if answers[4] >= 4:
            interests.extend(["business", "entrepreneurship", "leadership"])
        
        return list(set(interests))
    
    def _extract_work_preferences(self, answers: List[int]) -> Dict:
        """Extract work preferences from quiz answers"""
        return {
            "team_size": "small" if answers[5] <= 2 else "large" if answers[5] >= 4 else "medium",
            "work_environment": "remote" if answers[6] >= 4 else "office" if answers[6] <= 2 else "hybrid",
            "pace": "fast" if answers[7] >= 4 else "slow" if answers[7] <= 2 else "moderate",
            "structure": "flexible" if answers[8] >= 4 else "structured" if answers[8] <= 2 else "balanced"
        }
    
    def _extract_learning_style(self, answers: List[int]) -> str:
        """Extract learning style from quiz answers"""
        if answers[9] >= 4:
            return "hands_on_practical"
        elif answers[1] >= 4:
            return "analytical_theoretical"
        elif answers[2] >= 4:
            return "creative_experimental"
        else:
            return "balanced"
    
    def _extract_career_goals(self, answers: List[int]) -> List[str]:
        """Extract career goals from quiz answers"""
        goals = []
        
        if answers[4] >= 4:
            goals.append("leadership")
        if answers[1] >= 4:
            goals.append("expertise")
        if answers[3] >= 4:
            goals.append("impact")
        if answers[2] >= 4:
            goals.append("innovation")
        
        return goals if goals else ["growth"]
    
    async def _generate_user_embedding(self, user_profile: Dict) -> List[float]:
        """Generate embedding for user profile using Cohere"""
        try:
            # Create comprehensive user profile text
            profile_text = f"""
            User Profile:
            RIASEC Scores: {user_profile['riasec_scores']}
            Skills: {', '.join(user_profile['skills'])}
            Interests: {', '.join(user_profile['interests'])}
            Work Preferences: {user_profile['work_preferences']}
            Learning Style: {user_profile['learning_style']}
            Career Goals: {', '.join(user_profile['career_goals'])}
            """
            
            # Use Cohere API for embedding
            url = "https://api.cohere.ai/v1/embed"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "embed-english-light-v3.0",
                "texts": [profile_text],
                "input_type": "search_document"
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                embeddings = res.json()["embeddings"]
                return embeddings[0] if embeddings else self._generate_fallback_embedding(profile_text)
                
        except Exception as e:
            logger.error(f"Failed to generate user embedding: {e}")
            return self._generate_fallback_embedding(str(user_profile))
    
    async def _calculate_career_similarities(self, user_embedding: List[float], user_profile: Dict) -> List[Dict]:
        """Calculate similarities between user and all careers"""
        similarities = []
        
        for _, career in self.career_data.iterrows():
            try:
                # Create career profile text
                career_text = f"""
                Career: {career['title']}
                Skills: {career.get('top_skills', '')}
                Day in Life: {career.get('day_in_life', '')}
                Salary Range: ${career.get('salary_low', 0)} - ${career.get('salary_high', 0)}
                Growth: {career.get('growth_pct', 0)}%
                """
                
                # Generate career embedding
                career_embedding = await self._generate_career_embedding(career_text)
                
                # Calculate similarity
                similarity = self._calculate_embedding_similarity(user_embedding, career_embedding)
                
                # Add additional matching factors
                skill_match = self._calculate_skill_match(user_profile['skills'], career.get('top_skills', ''))
                interest_match = self._calculate_interest_match(user_profile['interests'], career_text)
                
                # Weighted similarity score
                weighted_similarity = (similarity * 0.5) + (skill_match * 0.3) + (interest_match * 0.2)
                
                similarities.append({
                    "title": career["title"],
                    "similarity": weighted_similarity,
                    "semantic_similarity": similarity,
                    "skill_match": skill_match,
                    "interest_match": interest_match,
                    "salary_low": career.get("salary_low", 0),
                    "salary_high": career.get("salary_high", 0),
                    "growth_pct": career.get("growth_pct", 0),
                    "top_skills": career.get("top_skills", ""),
                    "day_in_life": career.get("day_in_life", ""),
                    "matching_reasons": self._generate_matching_reasons(user_profile, career, weighted_similarity)
                })
                
            except Exception as e:
                logger.error(f"Failed to calculate similarity for {career['title']}: {e}")
                continue
        
        return similarities
    
    async def _generate_career_embedding(self, career_text: str) -> List[float]:
        """Generate embedding for career using Cohere with rate limiting"""
        try:
            # Add delay to prevent rate limiting
            import asyncio
            await asyncio.sleep(0.2)  # 200ms delay between requests
            
            url = "https://api.cohere.ai/v1/embed"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "embed-english-light-v3.0",
                "texts": [career_text],
                "input_type": "search_document"
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                embeddings = res.json()["embeddings"]
                return embeddings[0] if embeddings else self._generate_fallback_embedding(career_text)
            
        except Exception as e:
            logger.error(f"Failed to generate career embedding: {e}")
            # Return fallback embedding immediately to avoid cascading failures
            return self._generate_fallback_embedding(career_text)
    
    def _calculate_embedding_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        min_length = min(len(embedding1), len(embedding2))
        if min_length == 0:
            return 0.0
        
        dot_product = sum(embedding1[i] * embedding2[i] for i in range(min_length))
        magnitude1 = sum(val ** 2 for val in embedding1[:min_length]) ** 0.5
        magnitude2 = sum(val ** 2 for val in embedding2[:min_length]) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_skill_match(self, user_skills: List[str], career_skills: str) -> float:
        """Calculate skill match between user and career"""
        if not user_skills or not career_skills:
            return 0.0
        
        career_skill_list = [skill.strip().lower() for skill in career_skills.split(',')]
        user_skill_list = [skill.lower() for skill in user_skills]
        
        matches = sum(1 for skill in user_skill_list if any(skill in career_skill for career_skill in career_skill_list))
        return matches / len(user_skill_list) if user_skill_list else 0.0
    
    def _calculate_interest_match(self, user_interests: List[str], career_text: str) -> float:
        """Calculate interest match between user and career"""
        if not user_interests:
            return 0.0
        
        career_lower = career_text.lower()
        matches = sum(1 for interest in user_interests if interest.lower() in career_lower)
        return matches / len(user_interests) if user_interests else 0.0
    
    def _generate_matching_reasons(self, user_profile: Dict, career: pd.Series, similarity: float) -> List[str]:
        """Generate reasons why this career matches the user"""
        reasons = []
        
        # Skill-based reasons
        if user_profile['skills']:
            skill_match = self._calculate_skill_match(user_profile['skills'], career.get('top_skills', ''))
            if skill_match > 0.3:
                reasons.append(f"Your skills align well with this role ({skill_match:.1%} match)")
        
        # Interest-based reasons
        if user_profile['interests']:
            interest_match = self._calculate_interest_match(user_profile['interests'], str(career))
            if interest_match > 0.3:
                reasons.append(f"Your interests match this career path ({interest_match:.1%} match)")
        
        # Work preference reasons
        work_prefs = user_profile['work_preferences']
        if work_prefs.get('team_size') == 'small' and 'collaboration' in str(career).lower():
            reasons.append("You prefer small teams and this role offers close collaboration")
        
        # Learning style reasons
        if user_profile['learning_style'] == 'hands_on_practical' and 'hands-on' in str(career).lower():
            reasons.append("Your hands-on learning style fits this practical role")
        
        # Career goal reasons
        if 'leadership' in user_profile['career_goals'] and 'leadership' in str(career).lower():
            reasons.append("This role offers leadership opportunities aligned with your goals")
        
        return reasons if reasons else ["This role matches your overall profile and interests"]
    
    def _get_basic_career_matches(self, answers: List[int], top_k: int = 5) -> List[Dict]:
        """Fallback to basic RIASEC matching"""
        # Convert answers to RIASEC vector
        user_vec = self.answers_to_vec(answers)
        
        # Calculate similarity with career data
        similarities = []
        
        for _, career in self.career_data.iterrows():
            # Create career vector from RIASEC scores
            career_vec = np.array([
                career.get("realistic", 0),
                career.get("investigative", 0),
                career.get("artistic", 0),
                career.get("social", 0),
                career.get("enterprising", 0),
                career.get("conventional", 0)
            ])
            
            # Normalize career vector
            norm = np.linalg.norm(career_vec)
            if norm > 0:
                career_vec = career_vec / norm
            
            # Calculate cosine similarity
            similarity = np.dot(user_vec, career_vec)
            similarities.append({
                "title": career["title"],
                "similarity": similarity,
                "salary_low": career.get("salary_low", 0),
                "salary_high": career.get("salary_high", 0),
                "growth_pct": career.get("growth_pct", 0),
                "top_skills": career.get("top_skills", ""),
                "day_in_life": career.get("day_in_life", "")
            })
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Ensure diversity in results by filtering out very similar careers
        diverse_results = []
        seen_titles = set()
        
        for match in similarities:
            title = match["title"].lower()
            # Check if this career is too similar to already selected ones
            is_similar = any(
                any(word in title for word in existing_title.split()) or
                any(word in existing_title for word in title.split())
                for existing_title in seen_titles
            )
            
            if not is_similar and len(diverse_results) < top_k:
                diverse_results.append(match)
                seen_titles.add(title)
        
        # If we don't have enough diverse results, add more
        if len(diverse_results) < top_k:
            for match in similarities:
                if match not in diverse_results and len(diverse_results) < top_k:
                    diverse_results.append(match)
        
        return diverse_results
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding based on text characteristics"""
        embedding = [0.0] * 384  # Cohere embedding size
        
        # Basic text analysis
        words = text.lower().split()
        char_count = len(text)
        word_count = len(words)
        
        # Technical indicators
        technical_terms = ['api', 'database', 'algorithm', 'function', 'class', 'method', 'variable', 'loop', 'condition', 'error']
        framework_terms = ['react', 'python', 'javascript', 'docker', 'kubernetes', 'aws', 'azure', 'node', 'express', 'fastapi']
        learning_terms = ['learn', 'understand', 'practice', 'example', 'tutorial', 'guide', 'step', 'process', 'method']
        
        # Calculate technical density
        technical_score = sum(1 for word in words if word in technical_terms) / max(word_count, 1)
        framework_score = sum(1 for word in words if word in framework_terms) / max(word_count, 1)
        learning_score = sum(1 for word in words if word in learning_terms) / max(word_count, 1)
        
        # Set embedding values based on characteristics
        embedding[0] = min(technical_score, 1.0)
        embedding[1] = min(framework_score, 1.0)
        embedding[2] = min(learning_score, 1.0)
        embedding[3] = min(char_count / 1000, 1.0)
        embedding[4] = min(word_count / 100, 1.0)
        
        # Add some randomness for uniqueness
        import random
        random.seed(hash(text) % 10000)
        for i in range(5, 384):
            embedding[i] = random.uniform(-0.1, 0.1)
        
        return embedding

    def get_career_roadmap(self, career_title: str) -> Dict:
        """Get detailed career roadmap for a specific career"""
        # First check if we have a predefined roadmap
        if career_title in self.career_roadmaps:
            return self.career_roadmaps[career_title]
        
        # If not, find the closest match
        best_match = None
        best_similarity = 0
        
        for title in self.career_roadmaps.keys():
            similarity = self._calculate_title_similarity(career_title, title)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = title
        
        if best_match and best_similarity > 0.7:
            return self.career_roadmaps[best_match]
        
        # Return a generic roadmap if no good match found
        return self._create_generic_roadmap(career_title)

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two career titles"""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _create_generic_roadmap(self, career_title: str) -> Dict:
        """Create a generic roadmap for any career"""
        return {
            "entry_level": {
                "title": f"Junior {career_title}",
                "skills": ["Basic skills", "Industry knowledge", "Communication"],
                "courses": ["Fundamentals", "Industry Basics", "Communication Skills"],
                "duration": "6-12 months",
                "salary_range": "$50,000 - $70,000"
            },
            "mid_level": {
                "title": career_title,
                "skills": ["Advanced skills", "Specialization", "Leadership"],
                "courses": ["Advanced Training", "Specialization", "Leadership Skills"],
                "duration": "2-4 years",
                "salary_range": "$70,000 - $120,000"
            },
            "senior_level": {
                "title": f"Senior {career_title}",
                "skills": ["Expertise", "Strategic thinking", "Mentoring"],
                "courses": ["Expert Training", "Strategic Planning", "Mentoring Skills"],
                "duration": "5+ years",
                "salary_range": "$120,000 - $200,000"
            }
        }
    
    # AI-Powered Methods
    async def generate_ai_roadmap(self, career_title: str, user_skills: Optional[List[str]] = None) -> Dict:
        """Generate AI-powered detailed roadmap for any career"""
        try:
            prompt = f"""
            Create a detailed career roadmap for {career_title} with three levels:
            1. Entry Level (6-12 months)
            2. Mid Level (2-3 years) 
            3. Senior Level (5+ years)
            
            For each level include:
            - Title
            - Required skills
            - Recommended courses
            - Duration
            - Salary range
            
            User's current skills: {user_skills or []}
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating AI roadmap: {e}")
            return self._create_generic_roadmap(career_title)
    
    async def generate_interview_preparation(self, career_title: str) -> Dict:
        """Generate interview preparation content for a career"""
        try:
            prompt = f"""
            Create interview preparation guide for {career_title} position:
            
            Include:
            1. Common interview questions
            2. Technical assessment tips
            3. Behavioral questions
            4. Portfolio recommendations
            5. Salary negotiation tips
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating interview prep: {e}")
            return self._get_fallback_interview_prep(career_title)
    
    async def generate_market_insights(self, career_title: str) -> Dict:
        """Generate market insights for a career"""
        try:
            prompt = f"""
            Provide market insights for {career_title} career including:
            1. Current demand
            2. Salary trends
            3. Required skills
            4. Industry outlook
            5. Growth opportunities
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating market insights: {e}")
            return self._get_fallback_market_insights(career_title)
    
    async def generate_learning_plan(self, career_title: str, user_skills: Optional[List[str]] = None) -> Dict:
        """Generate personalized learning plan for a career"""
        try:
            prompt = f"""
            Create a personalized learning plan for {career_title} career:
            
            User's current skills: {user_skills or []}
            
            Include:
            1. Skill gaps analysis
            2. Learning priorities
            3. Recommended courses
            4. Timeline
            5. Milestones
            
            Return as JSON format.
            """
            
            response = await self._call_groq(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {e}")
            return self._get_fallback_learning_plan()
    
    async def generate_comprehensive_career_analysis(
        self, 
        answers: List[int], 
        user_skills: Optional[List[str]] = None
    ) -> Dict:
        """Generate comprehensive career analysis from quiz answers"""
        try:
            # Get career matches using embedding-based matching
            career_matches = await self.get_career_matches(answers, user_skills=user_skills, top_k=3)
            
            if not career_matches:
                return {"error": "No career matches found"}
            
            top_career = career_matches[0]["title"]
            
            # Generate AI-powered content for top career
            ai_roadmap = await self.generate_ai_roadmap(top_career, user_skills)
            interview_prep = await self.generate_interview_preparation(top_career)
            market_insights = await self.generate_market_insights(top_career)
            learning_plan = await self.generate_learning_plan(top_career, user_skills)
            
            return {
                "career_matches": career_matches,
                "top_career": top_career,
                "ai_roadmap": ai_roadmap,
                "interview_preparation": interview_prep,
                "market_insights": market_insights,
                "learning_plan": learning_plan,
                "analysis_timestamp": str(pd.Timestamp.now())
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API for AI generation with fallback to GROQ_API_KEY_2"""
        # Try primary API key first
        if self.groq_api_key:
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
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "stream": False
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                response_data = res.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    logger.info(f"GROQ API call successful using {key_type} key")
                    return response_data["choices"][0]["message"]["content"]
                logger.error(f"Unexpected Groq response format: {response_data}")
                return ""
        except Exception as e:
            logger.error(f"Groq API call failed ({key_type} key): {e}")
            return ""
    
    # Fallback methods
    def _get_fallback_interview_prep(self, career_title: str) -> Dict:
        """Fallback interview preparation"""
        return {
            "common_questions": [
                "Tell me about yourself",
                "Why do you want this position?",
                "What are your strengths and weaknesses?",
                "Where do you see yourself in 5 years?"
            ],
            "technical_tips": [
                "Practice coding problems",
                "Review fundamental concepts",
                "Prepare for system design questions"
            ],
            "behavioral_questions": [
                "Describe a challenging project",
                "How do you handle conflicts?",
                "Tell me about a time you failed"
            ],
            "portfolio_tips": [
                "Showcase relevant projects",
                "Include code samples",
                "Demonstrate problem-solving skills"
            ],
            "salary_negotiation": [
                "Research market rates",
                "Highlight your value",
                "Be prepared to negotiate"
            ]
        }
    
    def _get_fallback_market_insights(self, career_title: str) -> Dict:
        """Fallback market insights"""
        return {
            "current_demand": "High demand for tech roles",
            "salary_trends": "Salaries continue to rise",
            "required_skills": ["Technical skills", "Communication", "Problem solving"],
            "industry_outlook": "Positive growth expected",
            "growth_opportunities": "Many advancement opportunities available"
        }
    
    def _get_fallback_learning_plan(self) -> Dict:
        """Fallback learning plan"""
        return {
            "skill_gaps": ["Technical skills", "Industry knowledge"],
            "learning_priorities": [
                "Master core technologies",
                "Build practical projects",
                "Network with professionals"
            ],
            "recommended_courses": [
                "Fundamentals course",
                "Advanced specialization",
                "Industry certification"
            ],
            "timeline": "6-12 months",
            "milestones": [
                "Complete fundamentals",
                "Build portfolio",
                "Apply for positions"
            ]
        }

# Global instance for easy access
matcher = CareerMatcher()