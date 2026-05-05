"""
Unified Career System - Comprehensive career roadmap generation
Handles main career page functionality with target roles, interests, and skills
"""

import asyncio
import json
import os
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from schemas import (
    UnifiedRoadmapRequest, UnifiedRoadmapResponse, InterviewPrepRequest, InterviewPrepResponse
)

class UnifiedCareerSystem:
    """
    Unified career system for comprehensive roadmap generation:
    1. Generate roadmaps with or without target role
    2. Provide detailed learning paths and skill development
    3. Include interview preparation and market insights
    """
    
    def __init__(self):
        # Initialize API helpers
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_key_2 = os.getenv("GROQ_API_KEY_2")
        self.data_path = Path(__file__).parent / "data"
        
        # Load career data and roadmaps
        self.career_data = self._load_career_data()
        self.career_roadmaps = self._load_career_roadmaps()
        self.micro_lessons = self._load_micro_lessons()
        
        # Create career mapping for better matching
        self.career_mapping = self._create_career_mapping()
        
        logger.info("UnifiedCareerSystem initialized successfully with embedding capabilities")
    
    async def cohere_embed(self, batch: List[str]) -> List[List[float]]:
        """Generate embeddings using Cohere API"""
        url = "https://api.cohere.ai/v1/embed"
        headers = {
            "Authorization": f"Bearer {self.cohere_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "embed-english-light-v3.0",
            "texts": batch,
            "input_type": "search_document"
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            return res.json()["embeddings"]

    async def call_groq(self, messages: List[Dict]) -> str:
        """Call Groq API with optimized model and fallback to GROQ_API_KEY_2"""
        # Try primary API key first
        if self.groq_api_key:
            result = await self._call_groq_with_key(messages, self.groq_api_key, "primary")
            if result:
                return result
        
        # Try fallback key if primary failed
        if self.groq_api_key_2:
            logger.info("Primary GROQ API key failed, trying fallback key")
            result = await self._call_groq_with_key(messages, self.groq_api_key_2, "fallback")
            if result:
                return result
        
        logger.error("All GROQ API keys failed")
        return ""

    async def _call_groq_with_key(self, messages: List[Dict], api_key: str, key_type: str) -> str:
        """Call Groq API with specific key"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",  # High-quality model for best performance
            "messages": messages,
            "temperature": 0.7,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
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
    
    def _load_career_data(self) -> pd.DataFrame:
        """Load career data from CSV"""
        try:
            df = pd.read_csv(self.data_path / "onet_bls_trimmed.csv")
            logger.info(f"Loaded {len(df)} careers")
            return df
        except FileNotFoundError:
            logger.warning("Career data not found, using sample data")
            return self._create_sample_career_data()
    
    def _load_career_roadmaps(self) -> Dict:
        """Load career roadmaps from JSON"""
        try:
            with open(self.data_path / "career_roadmaps.json", "r") as f:
                roadmaps = json.load(f)
                logger.info(f"Loaded {len(roadmaps)} career roadmaps")
                return roadmaps
        except FileNotFoundError:
            logger.warning("Career roadmaps not found, using default")
            return self._create_default_roadmaps()
    
    def _load_micro_lessons(self) -> Dict:
        """Load micro-lessons data"""
        try:
            with open(self.data_path / "micro_lessons.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_micro_lessons()
    
    def _create_career_mapping(self) -> Dict:
        """Create mapping between career data and roadmaps for better matching"""
        mapping = {}
        
        # Map career data titles to roadmap titles
        for _, career in self.career_data.iterrows():
            career_title = career['title']
            
            # Find best matching roadmap
            best_match = None
            best_similarity = 0
            
            for roadmap_title in self.career_roadmaps.keys():
                similarity = self._calculate_title_similarity(career_title, roadmap_title)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = roadmap_title
            
            if best_match and best_similarity > 0.3:  # Threshold for matching
                mapping[career_title] = {
                    'roadmap_title': best_match,
                    'similarity': best_similarity,
                    'has_roadmap': True
                }
            else:
                mapping[career_title] = {
                    'roadmap_title': None,
                    'similarity': 0,
                    'has_roadmap': False
                }
        
        logger.info(f"Created career mapping for {len(mapping)} careers")
        return mapping
    
    def _create_sample_career_data(self) -> pd.DataFrame:
        """Create sample career data for testing"""
        return pd.DataFrame({
            'title': ['Software Developer', 'Data Scientist', 'DevOps Engineer', 'Frontend Developer', 'Backend Developer'],
            'salary_low': [60000, 70000, 65000, 55000, 65000],
            'salary_high': [120000, 140000, 130000, 110000, 130000],
            'growth_pct': [15.0, 25.0, 20.0, 12.0, 18.0],
            'top_skills': ['python,api,testing', 'python,ml,statistics', 'docker,aws,ci_cd', 'javascript,react,css', 'python,java,api'],
            'day_in_life': ['Develop software applications', 'Analyze data and build ML models', 'Manage infrastructure', 'Build user interfaces', 'Develop server-side applications']
        })
    
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
            }
        }
    
    def _create_default_micro_lessons(self) -> Dict:
        """Create default micro-lessons"""
        return {
            "programming": [
                {"title": "Python Basics", "description": "Learn Python fundamentals", "duration": 30, "skills": ["python"]},
                {"title": "JavaScript Fundamentals", "description": "Learn JavaScript basics", "duration": 30, "skills": ["javascript"]}
            ],
            "data_science": [
                {"title": "Data Analysis", "description": "Learn data analysis basics", "duration": 45, "skills": ["python", "pandas"]},
                {"title": "Machine Learning", "description": "Introduction to ML", "duration": 60, "skills": ["python", "scikit-learn"]}
            ]
        }
    
    async def generate_unified_roadmap(
        self,
        user_profile: Optional[Dict] = None,
        target_role: Optional[str] = None,
        user_skills: Optional[List[str]] = None,
        user_interests: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate comprehensive unified roadmap using embedding-based matching.
        Works with both quiz results and direct user input.
        """
        try:
            # If no target role provided, use embedding-based recommendation
            if not target_role:
                target_role = await self._recommend_target_role_embedding(
                    user_profile, user_skills, user_interests
                )
            
            # Get comprehensive career analysis using embeddings
            career_analysis = await self._get_embedding_based_career_analysis(
                target_role, user_skills, user_interests, user_profile
            )
            
            # Ensure the response has the required fields for frontend
            if "total_duration" not in career_analysis:
                career_analysis["total_duration"] = "6-12 months"
            if "difficulty_level" not in career_analysis:
                career_analysis["difficulty_level"] = "Intermediate"
            if "steps" not in career_analysis:
                career_analysis["steps"] = []
            
            return career_analysis
            
        except Exception as e:
            logger.error(f"Unified roadmap generation failed: {e}")
            return self._get_fallback_roadmap(target_role, user_skills, user_interests)
    
    async def _recommend_target_role_embedding(
        self, 
        user_profile: Optional[Dict] = None,
        user_skills: Optional[List[str]] = None,
        user_interests: Optional[List[str]] = None
    ) -> str:
        """Recommend target role using embedding-based matching"""
        try:
            # Create user profile for embedding
            user_profile_text = self._create_user_profile_text(user_profile, user_skills, user_interests)
            
            # Generate user embedding
            user_embedding = await self._generate_user_embedding(user_profile_text)
            
            # Find best matching career
            best_career = await self._find_best_career_match(user_embedding, user_skills, user_interests)
            
            return best_career
            
        except Exception as e:
            logger.error(f"Embedding-based role recommendation failed: {e}")
            return "Software Engineer"  # Fallback
    
    def _create_user_profile_text(
        self, 
        user_profile: Optional[Dict], 
        user_skills: Optional[List[str]], 
        user_interests: Optional[List[str]]
    ) -> str:
        """Create comprehensive user profile text for embedding"""
        profile_parts = []
        
        if user_profile:
            profile_parts.append(f"User Profile: {user_profile}")
        
        if user_skills:
            profile_parts.append(f"Skills: {', '.join(user_skills)}")
        
        if user_interests:
            profile_parts.append(f"Interests: {', '.join(user_interests)}")
        
        if not profile_parts:
            profile_parts.append("General user seeking career guidance")
        
        return " | ".join(profile_parts)
    
    async def _generate_user_embedding(self, user_profile_text: str) -> List[float]:
        """Generate embedding for user profile using Cohere"""
        try:
            embeddings = await self.cohere_embed([user_profile_text])
            return embeddings[0] if embeddings else self._generate_fallback_embedding(user_profile_text)
        except Exception as e:
            logger.error(f"Failed to generate user embedding: {e}")
            return self._generate_fallback_embedding(user_profile_text)
    
    async def _find_best_career_match(
        self, 
        user_embedding: List[float], 
        user_skills: Optional[List[str]], 
        user_interests: Optional[List[str]]
    ) -> str:
        """Find best career match using embeddings"""
        best_career = None
        best_similarity = 0
        
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
                
                # Add skill and interest matching
                skill_match = self._calculate_skill_match(user_skills or [], career.get('top_skills', ''))
                interest_match = self._calculate_interest_match(user_interests or [], career_text)
                
                # Weighted similarity score
                weighted_similarity = (similarity * 0.5) + (skill_match * 0.3) + (interest_match * 0.2)
                
                if weighted_similarity > best_similarity:
                    best_similarity = weighted_similarity
                    best_career = career['title']
                    
            except Exception as e:
                logger.error(f"Failed to calculate similarity for {career['title']}: {e}")
                continue
        
        return best_career or "Software Engineer"
    
    async def _generate_career_embedding(self, career_text: str) -> List[float]:
        """Generate embedding for career using Cohere"""
        try:
            embeddings = await self.cohere_embed([career_text])
            return embeddings[0] if embeddings else self._generate_fallback_embedding(career_text)
        except Exception as e:
            logger.error(f"Failed to generate career embedding: {e}")
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
    
    async def _get_embedding_based_career_analysis(
        self,
        target_role: str,
        user_skills: Optional[List[str]] = None,
        user_interests: Optional[List[str]] = None,
        user_profile: Optional[Dict] = None
    ) -> Dict:
        """Get comprehensive career analysis using embedding-based matching"""
        try:
            # Get detailed roadmap
            roadmap = await self._generate_detailed_roadmap(target_role, user_skills, user_profile)
            
            # Generate AI-powered content
            ai_roadmap = await self._generate_ai_roadmap(target_role, user_skills)
            interview_prep = await self._generate_interview_preparation(target_role, user_profile)
            market_insights = await self._generate_market_insights(target_role)
            learning_plan = await self._generate_learning_plan(target_role, user_skills, user_profile, roadmap)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(user_skills, target_role)
            
            # Generate matching reasons
            matching_reasons = self._generate_matching_reasons(target_role, user_skills, user_interests)
            
            # Get role-specific duration and difficulty
            duration, difficulty = self._get_role_difficulty_and_duration(target_role)
            
            return {
                "target_role": target_role,
                "career_title": target_role,
                "total_duration": duration["entry"],
                "difficulty_level": difficulty,
                "roadmap": roadmap,
                "interview_preparation": interview_prep,
                "market_insights": market_insights,
                "learning_plan": learning_plan,
                "coaching_advice": {
                    "advice": "Focus on developing the skills outlined in the roadmap",
                    "tips": matching_reasons,
                    "next_steps": ["Start with foundational skills", "Build a portfolio", "Network in the field"]
                },
                "confidence_score": confidence_score,
                "timeline": self._create_timeline(roadmap, user_profile),
                "estimated_time_to_target": self._estimate_time_to_target(roadmap, user_profile),
                "steps": self._create_roadmap_steps(target_role, duration)
            }
            
        except Exception as e:
            logger.error(f"Embedding-based career analysis failed: {e}")
            return self._get_fallback_roadmap(target_role, user_skills, user_interests)
    
    def _generate_matching_reasons(
        self, 
        target_role: str, 
        user_skills: Optional[List[str]], 
        user_interests: Optional[List[str]]
    ) -> List[str]:
        """Generate reasons why this role matches the user"""
        reasons = []
        
        # Find career data for this role
        career_data = None
        for _, career in self.career_data.iterrows():
            if career['title'].lower() == target_role.lower():
                career_data = career
                break
        
        if career_data is not None:
            # Skill-based reasons
            if user_skills:
                skill_match = self._calculate_skill_match(user_skills, career_data.get('top_skills', ''))
                if skill_match > 0.3:
                    reasons.append(f"Your skills align well with this role ({skill_match:.1%} match)")
            
            # Interest-based reasons
            if user_interests:
                interest_match = self._calculate_interest_match(user_interests, str(career_data))
                if interest_match > 0.3:
                    reasons.append(f"Your interests match this career path ({interest_match:.1%} match)")
            
            # Growth and salary reasons
            growth_pct = career_data.get('growth_pct', 0)
            if growth_pct > 10:
                reasons.append(f"This role offers strong growth potential ({growth_pct}% projected growth)")
            
            salary_high = career_data.get('salary_high', 0)
            if salary_high > 80000:
                reasons.append(f"Competitive salary range with high earning potential")
        
        # Default reasons if no specific data
        if not reasons:
            reasons.extend([
                "This role matches your overall profile and interests",
                "Good alignment with current market demands",
                "Strong potential for career advancement"
            ])
        
        return reasons
    
    def _get_best_roadmap(self, target_role: str) -> Dict:
        """Get the best matching roadmap for a target role"""
        # First check if we have an exact match
        if target_role in self.career_roadmaps:
            return {
                'roadmap': self.career_roadmaps[target_role],
                'source': 'exact_match',
                'similarity': 1.0
            }
        
        # Check career mapping for best match
        if target_role in self.career_mapping:
            mapping = self.career_mapping[target_role]
            if mapping['has_roadmap']:
                roadmap_title = mapping['roadmap_title']
                return {
                    'roadmap': self.career_roadmaps[roadmap_title],
                    'source': 'mapped_match',
                    'similarity': mapping['similarity'],
                    'original_title': target_role,
                    'roadmap_title': roadmap_title
                }
        
        # Find closest match in all roadmaps
        best_match = None
        best_similarity = 0
        
        for roadmap_title in self.career_roadmaps.keys():
            similarity = self._calculate_title_similarity(target_role, roadmap_title)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = roadmap_title
        
        if best_match and best_similarity > 0.5:
            return {
                'roadmap': self.career_roadmaps[best_match],
                'source': 'similarity_match',
                'similarity': best_similarity,
                'original_title': target_role,
                'roadmap_title': best_match
            }
        
        # No good match found
        return {
            'roadmap': None,
            'source': 'generated',
            'similarity': 0
        }
    
    # Removed old _recommend_target_role method - using _recommend_target_role_embedding instead
    
    async def _generate_detailed_roadmap(
        self, 
        target_role: str, 
        user_skills: Optional[List[str]] = None,
        user_profile: Optional[Dict] = None,
        roadmap_data: Optional[Dict] = None
    ) -> Dict:
        """Generate detailed roadmap for target role"""
        try:
            # Use roadmap data if available
            if roadmap_data and roadmap_data.get('roadmap'):
                roadmap = roadmap_data['roadmap']
                logger.info(f"Using {roadmap_data['source']} roadmap for {target_role}")
            else:
                # Generate AI roadmap
                roadmap = await self._generate_ai_roadmap(target_role, user_skills)
                logger.info(f"Generated AI roadmap for {target_role}")
            
            # Add skill gap analysis
            skill_gaps = self._analyze_skill_gaps(user_skills or [], roadmap)
            roadmap["skill_gaps"] = skill_gaps
            
            # Add roadmap metadata
            roadmap["metadata"] = {
                "target_role": target_role,
                "source": roadmap_data.get('source', 'generated') if roadmap_data else 'generated',
                "similarity": roadmap_data.get('similarity', 0) if roadmap_data else 0,
                "has_predefined_roadmap": roadmap_data.get('source') != 'generated' if roadmap_data else False
            }
        
            return roadmap
    
        except Exception as e:
            logger.error(f"Error generating detailed roadmap: {e}")
            return self._create_fallback_roadmap(target_role)
    
    async def _generate_ai_roadmap(self, target_role: str, user_skills: Optional[List[str]]) -> Dict:
        """Generate AI-powered roadmap"""
        try:
            # Build comprehensive prompt for better AI generation
            skills_context = f"User's current skills: {', '.join(user_skills or [])}" if user_skills else "User is starting fresh"
            
            prompt = f"""
            Create a comprehensive career roadmap for {target_role} with detailed progression levels.
            
            {skills_context}
            
            Generate a detailed roadmap with these exact levels:
            1. Entry Level (0-2 years experience)
            2. Mid Level (2-5 years experience) 
            3. Senior Level (5+ years experience)
            
            For each level, provide:
            - title: Specific job title
            - skills: List of required technical and soft skills
            - courses: List of recommended courses/certifications
            - duration: Time to reach this level
            - salary_range: Expected salary range
            - responsibilities: Key responsibilities and duties
            - projects: Types of projects they would work on
            - learning_path: Specific steps to reach this level
            
            Return ONLY valid JSON with this exact structure:
            {{
                "entry_level": {{
                    "title": "Junior {target_role}",
                    "skills": ["skill1", "skill2", "skill3"],
                    "courses": ["course1", "course2"],
                    "duration": "6-12 months",
                    "salary_range": "$50,000 - $70,000",
                    "responsibilities": ["responsibility1", "responsibility2"],
                    "projects": ["project1", "project2"],
                    "learning_path": ["step1", "step2", "step3"]
                }},
                "mid_level": {{
                    "title": "{target_role}",
                    "skills": ["skill1", "skill2", "skill3"],
                    "courses": ["course1", "course2"],
                    "duration": "2-3 years",
                    "salary_range": "$70,000 - $120,000",
                    "responsibilities": ["responsibility1", "responsibility2"],
                    "projects": ["project1", "project2"],
                    "learning_path": ["step1", "step2", "step3"]
                }},
                "senior_level": {{
                    "title": "Senior {target_role}",
                    "skills": ["skill1", "skill2", "skill3"],
                    "courses": ["course1", "course2"],
                    "duration": "5+ years",
                    "salary_range": "$120,000 - $200,000",
                    "responsibilities": ["responsibility1", "responsibility2"],
                    "projects": ["project1", "project2"],
                    "learning_path": ["step1", "step2", "step3"]
                }}
            }}
            
            Make the roadmap specific to {target_role} and realistic for the industry.
            """
            
            response = await self._call_groq(prompt)
            
            # If Groq call failed, return fallback
            if not response:
                logger.warning(f"Groq API failed for {target_role}, using fallback")
                return self._create_fallback_roadmap(target_role)
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    roadmap_data = json.loads(json_str)
                    
                    # Validate the structure
                    if all(level in roadmap_data for level in ['entry_level', 'mid_level', 'senior_level']):
                        logger.info(f"Successfully generated AI roadmap for {target_role}")
                        return roadmap_data
                    else:
                        logger.warning(f"Invalid roadmap structure for {target_role}, using fallback")
                        return self._create_fallback_roadmap(target_role)
                else:
                    logger.warning(f"No JSON found in response for {target_role}, using fallback")
                    return self._create_fallback_roadmap(target_role)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for {target_role}: {e}, using fallback")
                return self._create_fallback_roadmap(target_role)
            
        except Exception as e:
            logger.error(f"Error generating AI roadmap for {target_role}: {e}")
            return self._create_fallback_roadmap(target_role)
    
    async def _generate_interview_preparation(self, target_role: str, user_profile: Optional[Dict] = None) -> Dict:
        """Generate interview preparation content"""
        try:
            prompt = f"""
            Create interview preparation guide for {target_role} position.
            
            Return a JSON object with these fields:
            - common_questions: array of common interview questions
            - technical_skills: array of technical skills to focus on
            - behavioral_questions: array of behavioral questions
            - portfolio_suggestions: array of portfolio recommendations
            - interview_tips: array of interview tips
            - salary_negotiation: array of salary negotiation tips
            """
            
            response = await self._call_groq(prompt)
            
            # If Groq call failed, return fallback
            if not response:
                return self._get_fallback_interview_prep(target_role)
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    # If no JSON found, create structured response
                    return {
                        "common_questions": [
                            f"Tell me about your experience in {target_role}",
                            "What are your strengths and weaknesses?",
                            "Where do you see yourself in 5 years?"
                        ],
                        "technical_skills": ["Core skills", "Industry knowledge"],
                        "behavioral_questions": [
                            "Describe a challenging project you worked on",
                            "How do you handle conflicts in a team?"
                        ],
                        "portfolio_suggestions": ["Create a portfolio", "Showcase your work"],
                        "interview_tips": ["Research the company", "Practice common questions"],
                        "salary_negotiation": ["Know your worth", "Research market rates"]
                    }
            except json.JSONDecodeError:
                # Fallback to structured response
                return {
                    "common_questions": [
                        f"Tell me about your experience in {target_role}",
                        "What are your strengths and weaknesses?",
                        "Where do you see yourself in 5 years?"
                    ],
                    "technical_skills": ["Core skills", "Industry knowledge"],
                    "behavioral_questions": [
                        "Describe a challenging project you worked on",
                        "How do you handle conflicts in a team?"
                    ],
                    "portfolio_suggestions": ["Create a portfolio", "Showcase your work"],
                    "interview_tips": ["Research the company", "Practice common questions"],
                    "salary_negotiation": ["Know your worth", "Research market rates"]
                }
            
        except Exception as e:
            logger.error(f"Error generating interview prep: {e}")
            return self._get_fallback_interview_prep(target_role)
    
    async def _generate_market_insights(self, target_role: str) -> Dict:
        """Generate market insights for target role"""
        try:
            # Get career data
            career_info = self.career_data[self.career_data['title'] == target_role]
            if career_info.empty:
                career_info = self.career_data.iloc[0]  # Fallback
            
            return {
                "salary_range": f"${career_info.get('salary_low', 60000):,} - ${career_info.get('salary_high', 120000):,}",
                "growth_rate": f"{career_info.get('growth_pct', 15):.1f}%",
                "demand_level": "High" if career_info.get('growth_pct', 15) > 10 else "Medium",
                "top_skills": career_info.get('top_skills', '').split(',')[:5],
                "day_in_life": career_info.get('day_in_life', '')
            }
            
        except Exception as e:
            logger.error(f"Error generating market insights: {e}")
            return self._get_fallback_market_insights(career_info)
    
    async def _generate_learning_plan(
        self, 
        target_role: str, 
        user_skills: Optional[List[str]] = None,
        user_profile: Optional[Dict] = None,
        roadmap_data: Optional[Dict] = None
    ) -> Dict:
        """Generate personalized learning plan"""
        try:
            # Use roadmap data to create better learning plan
            roadmap = None
            logger.info(f"Learning plan - roadmap_data type: {type(roadmap_data)}")
            logger.info(f"Learning plan - roadmap_data: {roadmap_data}")
            
            if isinstance(roadmap_data, dict):
                # If roadmap_data is the roadmap itself
                if 'entry_level' in roadmap_data or 'mid_level' in roadmap_data or 'senior_level' in roadmap_data:
                    roadmap = roadmap_data
                    logger.info("Learning plan - Using roadmap_data directly as roadmap")
                else:
                    # If roadmap_data is a wrapper with 'roadmap' key
                    roadmap = roadmap_data.get('roadmap')
                    logger.info(f"Learning plan - Extracted roadmap from wrapper: {roadmap is not None}")
            elif isinstance(roadmap_data, str):
                # If roadmap_data is a string, try to parse it
                try:
                    roadmap = json.loads(roadmap_data)
                    logger.info("Learning plan - Parsed roadmap from string")
                except:
                    roadmap = None
                    logger.warning("Learning plan - Failed to parse roadmap from string")
            else:
                logger.warning(f"Learning plan - Unknown roadmap_data type: {type(roadmap_data)}")
            
            if roadmap and isinstance(roadmap, dict):
                # Extract courses from roadmap
                all_courses = []
                for level, details in roadmap.items():
                    if level in ['entry_level', 'mid_level', 'senior_level'] and isinstance(details, dict):
                        all_courses.extend(details.get('courses', []))
                
                # Find relevant micro-lessons
                relevant_lessons = []
                for category, category_lessons in self.micro_lessons.items():
                    for lesson_id, lesson in category_lessons.items():
                        if isinstance(lesson, dict) and any(skill in lesson.get('skills', []) for skill in (user_skills or [])):
                            relevant_lessons.append(lesson)
                
                return {
                    "recommended_lessons": relevant_lessons[:10],
                    "learning_path": all_courses,
                    "estimated_duration": "6-12 months",
                    "difficulty_level": self._assess_difficulty_level(user_skills, target_role),
                    "roadmap_based": True
                }
            else:
                # Fallback to generic learning plan
                relevant_lessons = []
                for category, category_lessons in self.micro_lessons.items():
                    for lesson_id, lesson in category_lessons.items():
                        if isinstance(lesson, dict) and any(skill in lesson.get('skills', []) for skill in (user_skills or [])):
                            relevant_lessons.append(lesson)
                
                return {
                    "recommended_lessons": relevant_lessons[:10],
                    "learning_path": self._create_learning_path(target_role, user_skills),
                    "estimated_duration": "6-12 months",
                    "difficulty_level": self._assess_difficulty_level(user_skills, target_role),
                    "roadmap_based": False
                }
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {e}")
            return self._get_fallback_learning_plan()
    

    
    def _calculate_confidence_score(self, user_skills: Optional[List[str]], target_role: str) -> float:
        """Calculate confidence score for target role"""
        if not user_skills:
            return 0.3
        
        # Get required skills for target role
        required_skills = self._get_required_skills(target_role)
        
        # Calculate overlap
        overlap = len(set(user_skills) & set(required_skills))
        total_required = len(required_skills)
        
        if total_required == 0:
            return 0.7  # Higher base confidence if no specific skills required
        
        # Calculate confidence based on skill overlap
        skill_confidence = min(overlap / total_required, 1.0)
        
        # Boost confidence for common skills and experience
        if user_skills:
            common_skills = ["Python", "JavaScript", "Git", "HTML", "CSS", "SQL"]
            common_overlap = len(set(user_skills) & set(common_skills))
            if common_overlap > 0:
                skill_confidence = min(skill_confidence + 0.2, 1.0)  # Boost by 0.2 for common skills
        
        return max(skill_confidence, 0.4)  # Minimum confidence of 0.4
    
    def _create_timeline(self, roadmap: Dict, user_profile: Optional[Dict] = None) -> Dict:
        """Create timeline for career progression"""
        timeline = []
        current_date = datetime.now()
        
        for level, details in roadmap.items():
            if level in ['entry_level', 'mid_level', 'senior_level']:
                timeline.append({
                    "level": level,
                    "title": details.get('title', ''),
                    "duration": details.get('duration', ''),
                    "skills": details.get('skills', []),
                    "courses": details.get('courses', [])
                })
        
        return {"timeline": timeline}
    
    def _estimate_time_to_target(self, roadmap: Dict, user_profile: Optional[Dict] = None) -> Dict:
        """Estimate time to reach target role"""
        total_months = 0
        for level, details in roadmap.items():
            if level in ['entry_level', 'mid_level', 'senior_level']:
                duration = details.get('duration', '')
                if 'months' in duration:
                    # Handle ranges like "6-12 months"
                    try:
                        if '-' in duration:
                            # Take the average of the range
                            parts = duration.split()[0].split('-')
                            months = (int(parts[0]) + int(parts[1])) // 2
                        else:
                            months = int(duration.split()[0])
                        total_months += months
                    except (ValueError, IndexError):
                        # Fallback to default
                        total_months += 12
                elif 'years' in duration:
                    try:
                        if '-' in duration:
                            # Take the average of the range
                            parts = duration.split()[0].split('-')
                            years = (int(parts[0]) + int(parts[1])) // 2
                        else:
                            years = int(duration.split()[0])
                        total_months += years * 12
                    except (ValueError, IndexError):
                        # Fallback to default
                        total_months += 24
        
        return {
            "total_months": total_months,
            "estimated_years": round(total_months / 12, 1),
            "fast_track_possible": total_months > 24
        }
    
    def _find_closest_role(self, recommended_role: str) -> str:
        """Find closest role in our data"""
        available_roles = self.career_data['title'].unique()
        
        best_match = available_roles[0]
        best_similarity = 0
        
        for role in available_roles:
            similarity = self._calculate_title_similarity(recommended_role, role)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = role
        
        return best_match
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _analyze_skill_gaps(self, user_skills: List[str], roadmap: Dict) -> List[str]:
        """Analyze skill gaps between user skills and roadmap requirements"""
        required_skills = []
        for level, details in roadmap.items():
            if level in ['entry_level', 'mid_level', 'senior_level']:
                required_skills.extend(details.get('skills', []))
        
        user_skill_set = set(user_skills)
        required_skill_set = set(required_skills)
        
        gaps = required_skill_set - user_skill_set
        return list(gaps)
    
    def _get_required_skills(self, target_role: str) -> List[str]:
        """Get required skills for target role"""
        # Check if we have a roadmap for this role
        roadmap_data = self._get_best_roadmap(target_role)
        if roadmap_data and roadmap_data.get('roadmap'):
            roadmap = roadmap_data['roadmap']
            skills = []
            for level, details in roadmap.items():
                if level in ['entry_level', 'mid_level', 'senior_level']:
                    skills.extend(details.get('skills', []))
            return skills
        
        # Fallback to career data
        career_info = self.career_data[self.career_data['title'] == target_role]
        if not career_info.empty:
            skills_str = career_info.iloc[0].get('top_skills', '')
            return [skill.strip() for skill in skills_str.split(',') if skill.strip()]
        
        return []
    
    def _create_learning_path(self, target_role: str, user_skills: Optional[List[str]]) -> List[str]:
        """Create learning path for target role"""
        roadmap_data = self._get_best_roadmap(target_role)
        if roadmap_data and roadmap_data.get('roadmap'):
            roadmap = roadmap_data['roadmap']
            path = []
            for level, details in roadmap.items():
                if level in ['entry_level', 'mid_level', 'senior_level']:
                    path.extend(details.get('courses', []))
            return path
        return ["Fundamentals", "Advanced Training", "Specialization"]
    
    def _assess_difficulty_level(self, user_skills: Optional[List[str]], target_role: str) -> str:
        """Assess difficulty level based on user skills and target role"""
        if not user_skills:
            return "Beginner"
        
        required_skills = self._get_required_skills(target_role)
        overlap = len(set(user_skills) & set(required_skills))
        
        if overlap >= len(required_skills) * 0.7:
            return "Advanced"
        elif overlap >= len(required_skills) * 0.4:
            return "Intermediate"
        else:
            return "Beginner"
    
    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API for AI generation"""
        try:
            messages = [{"role": "user", "content": prompt}]
            return await self.call_groq(messages)
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return ""
    
    def _create_fallback_roadmap(self, target_role: str) -> Dict:
        """Create detailed fallback roadmap with role-specific content"""
        # Get role-specific information from career data
        career_info = self._get_career_info_for_role(target_role)
        
        # Determine appropriate duration and difficulty based on role
        duration, difficulty = self._get_role_difficulty_and_duration(target_role)
        
        return {
            "entry_level": {
                "title": f"Junior {target_role}",
                "skills": self._get_role_specific_skills(target_role, "entry"),
                "courses": self._get_role_specific_courses(target_role, "entry"),
                "duration": duration["entry"],
                "salary_range": career_info.get("entry_salary", "$50,000 - $70,000"),
                "responsibilities": self._get_role_specific_responsibilities(target_role, "entry"),
                "projects": self._get_role_specific_projects(target_role, "entry"),
                "learning_path": self._get_role_specific_learning_path(target_role, "entry")
            },
            "mid_level": {
                "title": target_role,
                "skills": self._get_role_specific_skills(target_role, "mid"),
                "courses": self._get_role_specific_courses(target_role, "mid"),
                "duration": duration["mid"],
                "salary_range": career_info.get("mid_salary", "$70,000 - $120,000"),
                "responsibilities": self._get_role_specific_responsibilities(target_role, "mid"),
                "projects": self._get_role_specific_projects(target_role, "mid"),
                "learning_path": self._get_role_specific_learning_path(target_role, "mid")
            },
            "senior_level": {
                "title": f"Senior {target_role}",
                "skills": self._get_role_specific_skills(target_role, "senior"),
                "courses": self._get_role_specific_courses(target_role, "senior"),
                "duration": duration["senior"],
                "salary_range": career_info.get("senior_salary", "$120,000 - $200,000"),
                "responsibilities": self._get_role_specific_responsibilities(target_role, "senior"),
                "projects": self._get_role_specific_projects(target_role, "senior"),
                "learning_path": self._get_role_specific_learning_path(target_role, "senior")
            }
        }
    
    def _get_fallback_interview_prep(self, target_role: str) -> Dict:
        """Get fallback interview preparation"""
        return {
            "common_questions": [
                f"Tell me about your experience in {target_role}",
                "What are your strengths and weaknesses?",
                "Where do you see yourself in 5 years?"
            ],
            "technical_tips": [
                "Review core concepts",
                "Practice coding problems",
                "Prepare portfolio"
            ],
            "behavioral_tips": [
                "Use STAR method",
                "Provide specific examples",
                "Show enthusiasm"
            ]
        }
    
    def _get_fallback_market_insights(self, career_info) -> Dict:
        """Get fallback market insights"""
        return {
            "salary_range": "$60,000 - $120,000",
            "growth_rate": "15.0%",
            "demand_level": "High",
            "top_skills": ["python", "javascript", "communication"],
            "day_in_life": "Collaborate with team, solve problems, learn new technologies"
        }
    
    def _get_fallback_learning_plan(self) -> Dict:
        """Get fallback learning plan"""
        return {
            "recommended_lessons": [],
            "learning_path": ["Fundamentals", "Advanced Training", "Specialization"],
            "estimated_duration": "6-12 months",
            "difficulty_level": "Beginner"
        }
    

    
    def _get_fallback_roadmap(self, target_role: Optional[str], user_skills: Optional[List[str]], user_interests: Optional[List[str]]) -> Dict:
        """Get fallback roadmap with role-specific information"""
        role = target_role or "Software Developer"
        career_info = self._get_career_info_for_role(role)
        duration, difficulty = self._get_role_difficulty_and_duration(role)
        
        return {
            "target_role": role,
            "career_title": role,
            "total_duration": duration["entry"],
            "difficulty_level": difficulty,
            "roadmap": self._create_fallback_roadmap(role),
            "interview_preparation": self._get_fallback_interview_prep(role),
            "market_insights": {
                "salary_range": f"${career_info['salary_low']:,} - ${career_info['salary_high']:,}",
                "growth_rate": f"{career_info['growth_pct']:.1f}%",
                "demand_level": "High" if career_info['growth_pct'] > 10 else "Medium",
                "top_skills": career_info['top_skills'].split(',')[:5] if career_info['top_skills'] else ["Technical skills", "Problem solving", "Communication"],
                "day_in_life": career_info['day_in_life']
            },
            "learning_plan": self._get_fallback_learning_plan(),
            "coaching_advice": {
                "advice": f"Focus on developing the skills outlined in the roadmap for {role}",
                "tips": [
                    f"Start with {role} fundamentals",
                    "Build a portfolio showcasing your skills",
                    "Network with professionals in the field",
                    "Stay updated with industry trends"
                ],
                "next_steps": [
                    f"Complete {role} foundational training",
                    "Build practical projects",
                    "Connect with industry professionals",
                    "Apply for entry-level positions"
                ]
            },
            "confidence_score": 0.7,
            "timeline": {"timeline": []},
            "estimated_time_to_target": {
                "total_months": 12 if "month" in duration["entry"] else 24,
                "estimated_years": 1.0 if "month" in duration["entry"] else 2.0,
                "fast_track_possible": True
            },
            "steps": self._create_roadmap_steps(role, duration)
        }

    def _get_career_info_for_role(self, target_role: str) -> Dict:
        """Get career information for a specific role from O*NET data"""
        try:
            # Find matching career in O*NET data
            for _, career in self.career_data.iterrows():
                if target_role.lower() in career['title'].lower() or career['title'].lower() in target_role.lower():
                    return {
                        "title": career['title'],
                        "salary_low": career.get('salary_low', 50000),
                        "salary_high": career.get('salary_high', 100000),
                        "growth_pct": career.get('growth_pct', 15),
                        "top_skills": career.get('top_skills', ''),
                        "day_in_life": career.get('day_in_life', ''),
                        "entry_salary": f"${career.get('salary_low', 50000):,} - ${int(career.get('salary_low', 50000) * 1.3):,}",
                        "mid_salary": f"${int(career.get('salary_low', 50000) * 1.3):,} - ${int(career.get('salary_high', 100000) * 0.8):,}",
                        "senior_salary": f"${int(career.get('salary_high', 100000) * 0.8):,} - ${career.get('salary_high', 100000):,}"
                    }
        except Exception as e:
            logger.error(f"Error getting career info for {target_role}: {e}")
        
        # Fallback if no match found
        return {
            "title": target_role,
            "salary_low": 50000,
            "salary_high": 100000,
            "growth_pct": 15,
            "top_skills": "technical skills, problem solving, communication",
            "day_in_life": "Collaborate with team, solve problems, learn new technologies",
            "entry_salary": "$50,000 - $65,000",
            "mid_salary": "$65,000 - $90,000",
            "senior_salary": "$90,000 - $120,000"
        }
    
    def _get_role_difficulty_and_duration(self, target_role: str) -> tuple:
        """Get appropriate duration and difficulty for a role"""
        role_lower = target_role.lower()
        
        # Technical roles typically take longer
        if any(tech in role_lower for tech in ['engineer', 'developer', 'scientist', 'architect']):
            return {
                "entry": "8-12 months",
                "mid": "2-4 years", 
                "senior": "5+ years"
            }, "Intermediate"
        # Management roles
        elif any(mgmt in role_lower for mgmt in ['manager', 'director', 'lead', 'head']):
            return {
                "entry": "6-10 months",
                "mid": "2-3 years",
                "senior": "4+ years"
            }, "Advanced"
        # Creative roles
        elif any(creative in role_lower for creative in ['designer', 'writer', 'artist', 'creative']):
            return {
                "entry": "4-8 months",
                "mid": "1-3 years",
                "senior": "3+ years"
            }, "Beginner"
        # Default
        else:
            return {
                "entry": "6-12 months",
                "mid": "2-3 years",
                "senior": "4+ years"
            }, "Intermediate"
    
    def _get_role_specific_skills(self, target_role: str, level: str) -> List[str]:
        """Get role-specific skills based on O*NET data"""
        career_info = self._get_career_info_for_role(target_role)
        base_skills = career_info.get('top_skills', '').split(',')[:3] if career_info.get('top_skills') else []
        
        # Add level-specific skills
        if level == "entry":
            return base_skills + ["Basic problem solving", "Communication", "Learning agility"]
        elif level == "mid":
            return base_skills + ["Advanced problem solving", "Leadership", "Project management"]
        else:  # senior
            return base_skills + ["Strategic thinking", "Team leadership", "Industry expertise"]
    
    def _get_role_specific_courses(self, target_role: str, level: str) -> List[str]:
        """Get role-specific courses"""
        if level == "entry":
            return [f"{target_role} Fundamentals", "Industry Basics", "Professional Skills"]
        elif level == "mid":
            return [f"Advanced {target_role}", "Leadership Development", "Specialization"]
        else:  # senior
            return [f"Senior {target_role} Mastery", "Executive Leadership", "Strategic Planning"]
    
    def _get_role_specific_responsibilities(self, target_role: str, level: str) -> List[str]:
        """Get role-specific responsibilities"""
        if level == "entry":
            return ["Learn core concepts", "Work under supervision", "Complete assigned tasks", "Build foundational skills"]
        elif level == "mid":
            return ["Lead small projects", "Mentor junior team members", "Make technical decisions", "Contribute to strategy"]
        else:  # senior
            return ["Set technical direction", "Lead large initiatives", "Make strategic decisions", "Drive innovation"]
    
    def _get_role_specific_projects(self, target_role: str, level: str) -> List[str]:
        """Get role-specific project types"""
        if level == "entry":
            return ["Small feature development", "Bug fixes", "Documentation", "Testing"]
        elif level == "mid":
            return ["Feature development", "System design", "Team coordination", "Process improvement"]
        else:  # senior
            return ["Architecture design", "Strategic initiatives", "Cross-team collaboration", "Innovation projects"]
    
    def _get_role_specific_learning_path(self, target_role: str, level: str) -> List[str]:
        """Get role-specific learning path"""
        if level == "entry":
            return ["Complete foundational training", "Build portfolio projects", "Network with professionals", "Apply for positions"]
        elif level == "mid":
            return ["Take on leadership roles", "Develop expertise", "Build professional network", "Contribute to knowledge"]
        else:  # senior
            return ["Develop executive presence", "Build industry reputation", "Mentor others", "Drive strategic initiatives"]
    
    def _create_roadmap_steps(self, target_role: str, duration: Dict) -> List[Dict]:
        """Create roadmap steps for the frontend"""
        return [
            {
                "step": 1,
                "title": f"Foundation Skills for {target_role}",
                "description": f"Learn the fundamental skills required for {target_role}",
                "duration": duration["entry"],
                "skills": self._get_role_specific_skills(target_role, "entry")[:3],
                "resources": [f"{target_role} Fundamentals", "Industry Basics", "Professional Skills"]
            },
            {
                "step": 2,
                "title": f"Intermediate {target_role} Development",
                "description": "Build practical projects and gain hands-on experience",
                "duration": duration["mid"],
                "skills": self._get_role_specific_skills(target_role, "mid")[:3],
                "resources": [f"Advanced {target_role}", "Project Management", "Leadership Skills"]
            },
            {
                "step": 3,
                "title": f"Advanced {target_role} Specialization",
                "description": "Specialize in advanced topics and prepare for senior roles",
                "duration": duration["senior"],
                "skills": self._get_role_specific_skills(target_role, "senior")[:3],
                "resources": [f"Senior {target_role} Mastery", "Strategic Planning", "Industry Leadership"]
            }
        ]

# Global instance for easy access
unified_career_system = UnifiedCareerSystem() 