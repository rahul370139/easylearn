from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ExplanationLevel(str, Enum):
    FIVE_YEAR_OLD = "5_year_old"
    INTERN = "intern"
    SENIOR = "senior"

class Framework(str, Enum):
    FASTAPI = "fastapi"
    DOCKER = "docker"
    PYTHON = "python"
    MACHINE_LEARNING = "machine_learning"
    AI = "ai"
    LANGCHAIN = "langchain"
    REACT = "react"
    NEXTJS = "nextjs"
    TYPESCRIPT = "typescript"
    NODEJS = "nodejs"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    GENERIC = "generic"

class DistillRequest(BaseModel):
    owner_id: str = Field(..., description="Supabase user UUID")
    explanation_level: ExplanationLevel = Field(default=ExplanationLevel.INTERN, description="Explanation complexity level")
    framework: Framework = Field(default=Framework.GENERIC, description="Primary framework/tool category")

class DistillResponse(BaseModel):
    lesson_id: int
    bullets: list[str]
    flashcards: list[dict]
    quiz: list[dict]
    concept_map: Optional[Dict] = Field(default=None, description="AI-generated concept relationships")
    framework: Framework
    explanation_level: ExplanationLevel

class LessonCompletion(BaseModel):
    lesson_id: int
    user_id: str
    completed_at: str
    progress_percentage: float = Field(..., ge=0, le=100)

class UserRole(BaseModel):
    user_id: str
    role: str = Field(..., description="User's professional role")
    experience_level: str = Field(..., description="Junior, Mid, Senior")
    interests: List[str] = Field(default=[], description="Areas of interest")

class RecommendationRequest(BaseModel):
    user_id: str
    role: Optional[str] = None
    experience_level: Optional[str] = None
    interests: Optional[List[str]] = None

# Chatbot schemas
class ChatMessage(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    explanation_level: ExplanationLevel = Field(default=ExplanationLevel.INTERN, description="Explanation complexity level")

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: str
    file_processed: Optional[bool] = Field(default=None, description="Whether a file was processed")
    lesson_id: Optional[int] = Field(default=None, description="Lesson ID if file was processed")
    pdf_name: Optional[str] = Field(default=None, description="Name of uploaded PDF")
    summary: Optional[str] = Field(default=None, description="Summary of processed content")
    framework_detection: Optional[Dict] = Field(default=None, description="Detected frameworks")
    action_buttons: Optional[List[Dict]] = Field(default=None, description="Available action buttons")
    interactive_options: Optional[bool] = Field(default=None, description="Whether interactive options are available")
    actions: Optional[List[str]] = Field(default=None, description="Available actions for dashboard")
    lesson_ingested: Optional[bool] = Field(default=None, description="Whether a lesson was ingested")
    title: Optional[str] = Field(default=None, description="Lesson title")
    framework: Optional[str] = Field(default=None, description="Lesson framework")
    # NEW: Structured payloads for interactive rendering in chat
    type: Optional[str] = Field(default=None, description="Type of generated content: chat|lesson|quiz|flashcards|workflow|summary|help|explanation")
    quiz_data: Optional[Dict[str, Any]] = Field(default=None, description="Quiz payload with { questions: [...] }")
    flashcard_data: Optional[Dict[str, Any]] = Field(default=None, description="Flashcard payload with { cards: [...] }")
    lesson_data: Optional[Dict[str, Any]] = Field(default=None, description="Lesson/microlearning payload")
    summary_data: Optional[Dict[str, Any]] = Field(default=None, description="Summary payload")
    workflow_data: Optional[Dict[str, Any]] = Field(default=None, description="Workflow payload")
    # Compatibility fields for frontends expecting flat arrays
    quiz: Optional[List[Dict[str, Any]]] = Field(default=None, description="Quiz questions array for direct rendering")
    flashcards: Optional[List[Dict[str, Any]]] = Field(default=None, description="Flashcards array for direct rendering")

class ChatWithFileRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    explanation_level: ExplanationLevel = Field(default=ExplanationLevel.INTERN, description="Explanation complexity level")

class ConversationHistory(BaseModel):
    conversation_id: str
    user_id: str
    messages: List[Dict]
    created_at: str
    updated_at: str

class ChatFileUpload(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    explanation_level: ExplanationLevel = Field(default=ExplanationLevel.INTERN, description="Explanation complexity level")

class IngestLessonRequest(BaseModel):
    lesson_id: int = Field(..., description="Lesson ID to ingest")
    user_id: str = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")

# Career matching schemas
class QuizAnswer(BaseModel):
    qid: int
    value: int = Field(ge=1, le=5, description="Answer value from 1 (Strongly dislike) to 5 (Love it)")

class CareerMatchRequest(BaseModel):
    owner_id: str
    answers: List[int] = Field(..., min_length=10, max_length=10, description="10 quiz answers (1-5)")
    user_profile: Optional[Dict] = Field(default=None, description="Optional user profile with skills, experience_level, salary_preference, growth_preference")

class CareerCard(BaseModel):
    title: str
    salary_low: int
    salary_high: int
    growth_pct: float
    common_skills: List[str]
    day_in_life: str
    similarity: float
    roadmap: Optional[Dict] = Field(default=None, description="Career progression roadmap with learning paths")

class CareerMatchResponse(BaseModel):
    results: List[CareerCard]

class CareerQuizQuestion(BaseModel):
    id: int
    question: str
    category: str
    description: str

class CareerQuizResponse(BaseModel):
    questions: List[CareerQuizQuestion]

class CareerRoadmapLevel(BaseModel):
    title: str
    skills: List[str]
    courses: List[str]
    duration: str
    salary_range: str

class CareerRoadmap(BaseModel):
    entry_level: CareerRoadmapLevel
    mid_level: CareerRoadmapLevel
    senior_level: CareerRoadmapLevel

class EnhancedCareerMatchRequest(BaseModel):
    owner_id: str
    answers: List[int] = Field(..., min_length=10, max_length=10, description="10 quiz answers (1-5)")
    user_profile: Optional[Dict] = Field(default=None, description="Optional user profile with skills, experience_level, salary_preference, growth_preference")
    include_roadmaps: bool = Field(default=True, description="Include career roadmaps in response")

class RoadmapLevel(BaseModel):
    title: str
    description: str
    skills: List[str]
    duration: str
    salary_range: str
    responsibilities: List[str]
    learning_objectives: List[str]
    recommended_lessons: List[Dict] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    estimated_learning_time: str = ""

class DynamicRoadmap(BaseModel):
    foundational: RoadmapLevel
    intermediate: RoadmapLevel
    advanced: RoadmapLevel

class RoadmapRequest(BaseModel):
    target_role: str
    user_skills: Optional[List[str]] = Field(default=None, description="User's current skills")
    user_experience: str = Field(default="entry", description="User's experience level: entry, mid, senior")

class RoadmapResponse(BaseModel):
    target_role: str
    roadmap: DynamicRoadmap
    user_experience: str

class MicroLesson(BaseModel):
    id: str
    category: str
    title: str
    description: str
    duration: str
    difficulty: str
    skills: List[str]
    framework: str

class LessonSearchRequest(BaseModel):
    query: str

class LessonSearchResponse(BaseModel):
    results: List[MicroLesson]

# Advanced Career Coach Schemas
class CareerGuidanceRequest(BaseModel):
    user_id: str
    user_profile: Dict[str, Any]
    query: str

class CareerGuidanceResponse(BaseModel):
    session_id: str
    guidance: str
    timestamp: str
    next_steps: List[str]

class InterviewSimulationRequest(BaseModel):
    user_id: str
    target_role: str
    difficulty: str = Field(default="medium", description="easy, medium, hard")

class InterviewSimulationResponse(BaseModel):
    session_id: str
    target_role: str
    difficulty: str
    total_questions: int
    current_question: int
    question: str
    instructions: str

class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str

class InterviewAnswerResponse(BaseModel):
    status: str  # "continue" or "completed"
    current_question: Optional[int] = None
    question: Optional[str] = None
    total_questions: Optional[int] = None
    feedback: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

class CareerAdviceRequest(BaseModel):
    topic: str
    user_context: Optional[Dict[str, Any]] = None

class CareerAdviceResponse(BaseModel):
    topic: str
    advice: str
    timestamp: str
    related_topics: List[str]

# AI Recommendation Engine Schemas
class UserProfileRequest(BaseModel):
    user_id: str
    user_profile: Dict[str, Any]

class PersonalizedRecommendationsResponse(BaseModel):
    user_id: str
    timestamp: str
    profile_analysis: Dict[str, Any]
    career_recommendations: Dict[str, Any]
    learning_recommendations: Dict[str, Any]
    market_insights: Dict[str, Any]
    skill_gaps: Dict[str, Any]
    timeline: Dict[str, Any]
    confidence_score: float

class MarketTrendsResponse(BaseModel):
    trends: Dict[str, Dict[str, Any]]

class LearningPathsResponse(BaseModel):
    paths: Dict[str, Dict[str, Any]]

# Enhanced Career Roadmap Schemas
class VisualRoadmapRequest(BaseModel):
    target_role: str
    user_skills: List[str]
    user_experience: str
    include_visual: bool = True

class VisualRoadmapResponse(BaseModel):
    target_role: str
    roadmap: Dict[str, Any]
    visual_data: Optional[Dict[str, Any]] = None
    interactive_elements: List[Dict[str, Any]]

class CareerPathNode(BaseModel):
    id: str
    title: str
    level: str
    skills_required: List[str]
    estimated_duration: str
    salary_range: str
    courses: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]

class CareerPathEdge(BaseModel):
    from_node: str
    to_node: str
    transition_skills: List[str]
    difficulty: str

class InteractiveRoadmap(BaseModel):
    nodes: List[CareerPathNode]
    edges: List[CareerPathEdge]
    user_position: str
    recommended_path: List[str]

# Advanced Analytics Schemas
class UserAnalyticsRequest(BaseModel):
    user_id: str
    time_period: str = Field(default="30d", description="7d, 30d, 90d, 1y")

class UserAnalyticsResponse(BaseModel):
    user_id: str
    learning_progress: Dict[str, Any]
    skill_growth: Dict[str, Any]
    career_advancement: Dict[str, Any]
    market_alignment: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

class SkillProgress(BaseModel):
    skill_name: str
    current_level: float
    target_level: float
    progress_percentage: float
    learning_activities: List[Dict[str, Any]]

class CareerAdvancementMetrics(BaseModel):
    current_role: str
    target_role: str
    advancement_score: float
    required_skills: List[str]
    acquired_skills: List[str]
    estimated_time_to_target: str

# Enhanced Career Pathfinder Schemas (Image-based)
class CareerPlanningRequest(BaseModel):
    interests: List[str]
    skills: List[str]

class CareerPlanningResponse(BaseModel):
    interests: List[str]
    skills: List[str]
    matching_careers: List[Dict[str, Any]]
    ai_recommendations: str
    total_matches: int
    timestamp: str

class CareerRoadmapRequest(BaseModel):
    career_title: str
    user_skills: Optional[List[str]] = None

class CareerRoadmapResponse(BaseModel):
    career_title: str
    description: str
    salary_range: str
    growth_rate: str
    skills_required: List[str]
    roadmap_levels: List[str]
    ai_roadmap: str
    user_skills: List[str]
    skill_gaps: List[str]
    timestamp: str

class PredefinedOptionsResponse(BaseModel):
    interests: List[str]
    skills: List[str]

class ComprehensiveCareerPlanRequest(BaseModel):
    user_profile: Dict[str, Any]
    target_role: Optional[str] = None
    user_skills: Optional[List[str]] = None
    user_interests: Optional[List[str]] = None

class ComprehensiveCareerPlanResponse(BaseModel):
    target_role: str
    roadmap: Dict[str, Any]
    skill_gaps: Dict[str, Any]
    learning_plan: Dict[str, Any]
    coaching_advice: Dict[str, Any]
    market_insights: Dict[str, Any]
    timeline: Dict[str, Any]
    confidence_score: float
    estimated_time_to_target: Dict[str, Any]

class SmartCareerRequest(BaseModel):
    selected_interests: List[str]
    selected_skills: List[str]
    user_profile: Optional[Dict[str, Any]] = None
    target_role: Optional[str] = None

class SmartCareerResponse(BaseModel):
    target_role: str
    selected_interests: List[str]
    selected_skills: List[str]
    career_plan: Dict[str, Any]
    interview_preparation: Dict[str, Any]
    confidence_score: float
    next_steps: List[str]

class SkillSuggestionRequest(BaseModel):
    selected_interests: List[str]
    selected_skills: List[str]
    user_profile: Optional[Dict[str, Any]] = None

class SkillSuggestionResponse(BaseModel):
    suggested_skills: List[str]
    categorized_suggestions: Dict[str, List[str]]
    career_paths: List[str]
    message: str

class InterviewPrepRequest(BaseModel):
    target_role: str
    user_profile: Optional[Dict[str, Any]] = None

class InterviewPrepResponse(BaseModel):
    common_questions: List[str]
    technical_skills: List[str]
    behavioral_questions: List[str]
    portfolio_suggestions: List[str]
    interview_tips: List[str]
    salary_negotiation: List[str]

class UnifiedRoadmapRequest(BaseModel):
    user_profile: Optional[Dict[str, Any]] = None
    target_role: Optional[str] = None
    user_skills: Optional[List[str]] = None
    user_interests: Optional[List[str]] = None

class UnifiedRoadmapResponse(BaseModel):
    target_role: str
    career_title: Optional[str] = None
    total_duration: Optional[str] = None
    difficulty_level: Optional[str] = None
    roadmap: Dict[str, Any]
    interview_preparation: Dict[str, Any]
    market_insights: Dict[str, Any]
    learning_plan: Dict[str, Any]
    coaching_advice: Dict[str, Any]
    confidence_score: float
    timeline: Dict[str, Any]
    estimated_time_to_target: Dict[str, Any]
    steps: Optional[List[Dict[str, Any]]] = None

class CareerDiscoveryRequest(BaseModel):
    selected_interests: List[str]
    selected_skills: List[str]
    user_profile: Optional[Dict[str, Any]] = None

class CareerDiscoveryResponse(BaseModel):
    recommended_careers: List[Dict[str, Any]]
    insights: Dict[str, Any]
    skill_analysis: Dict[str, Any]

class WorkflowStep(BaseModel):
    step: int
    action: str
    description: str
    estimated_time: Optional[str] = None
    resources: Optional[List[str]] = None

class WorkflowResponse(BaseModel):
    workflow: List[WorkflowStep]
    total_steps: int
    estimated_duration: str
    difficulty_level: str

class AgentRequest(BaseModel):
    pdf_id: str
    user_id: str
    topic: Optional[str] = ""
    num: Optional[int] = 8
    message: Optional[str] = ""

class AgentResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    message: str

class IntentDetectionRequest(BaseModel):
    message: str
    pdf_id: Optional[str] = None
    user_id: Optional[str] = None

class IntentDetectionResponse(BaseModel):
    intent: str
    confidence: float
    message: str
    context: Dict[str, Any]
    suggestions: Optional[List[str]] = None
