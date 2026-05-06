"""
TrainPI Microlearning API - Consolidated Version
This file consolidates all functionality from app.py and main.py into a single,
comprehensive API server with enhanced career guidance, learning management,
and AI-powered features.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import asyncio, tempfile, os, json
from pathlib import Path
from schemas import (
    UserRole, 
    RecommendationRequest, ExplanationLevel, Framework, ChatMessage, 
    ChatResponse, CareerMatchRequest, CareerMatchResponse, CareerCard, CareerQuizResponse, CareerQuizQuestion,
    RoadmapRequest, RoadmapResponse, LessonSearchRequest, LessonSearchResponse,
    CareerGuidanceRequest, CareerGuidanceResponse, InterviewSimulationRequest, InterviewSimulationResponse,
    InterviewAnswerRequest, InterviewAnswerResponse, CareerAdviceRequest, CareerAdviceResponse,
    UserProfileRequest, PersonalizedRecommendationsResponse, MarketTrendsResponse, LearningPathsResponse, 
    VisualRoadmapRequest, VisualRoadmapResponse, UserAnalyticsResponse, CareerPlanningRequest, 
    CareerPlanningResponse, CareerRoadmapRequest, CareerRoadmapResponse, PredefinedOptionsResponse,
    ComprehensiveCareerPlanRequest, ComprehensiveCareerPlanResponse,
    InterviewPrepRequest, InterviewPrepResponse,
    UnifiedRoadmapRequest, UnifiedRoadmapResponse
)
from distiller import (
    pdf_to_text, chunk_text, embed_chunks, detect_framework,
    map_reduce_summary, gen_flashcards_quiz, generate_concept_map,
    process_chat_message, process_file_for_chat,
    get_conversation_history, get_user_conversations,
    get_side_menu_data, update_explanation_level, update_framework_preference
)
from mastery import (
    get_mastery, update_mastery
)
from supabase_helper import (
    insert_lesson, insert_cards, insert_concept_map, mark_lesson_completed,
    get_user_completed_lessons, upsert_user_role, get_user_role,
    get_lessons_by_framework, get_user_progress_stats,
    get_lesson_summary, get_lesson_by_id, get_lesson_full_text,
)
from career_matcher import matcher
from unified_career_system import unified_career_system
from dashboard import dashboard_system
from resume_career import (
    parse_resume as resume_parse,
    build_career_plan as resume_build_plan,
    upgrade_from_pdf as resume_upgrade,
)
from career_plan_storage import save_latest_plan, load_latest_plan
from dotenv import load_dotenv
from typing import Optional, Dict, List
from datetime import datetime
import uuid

load_dotenv()

# Initialize missing components that are referenced in the code
# These are placeholders - in production, these would be properly initialized
career_coach = None  # Placeholder for career coaching system
recommendation_engine = None  # Placeholder for recommendation engine
roadmap_generator = None  # Placeholder for roadmap generator
unified_advisor = unified_career_system  # Use the existing unified career system

async def get_role_based_recommendations(user_id: str, role: str, experience_level: str, interests: List[str]):
    """Get role-based lesson recommendations"""
    try:
        # Get lessons by framework (role-based)
        framework_mapping = {
            "Developer": Framework.PYTHON,
            "Frontend Developer": Framework.REACT,
            "Backend Developer": Framework.PYTHON,
            "Data Scientist": Framework.PYTHON,
            "DevOps Engineer": Framework.GENERIC,
            "Product Manager": Framework.GENERIC
        }
        
        framework = framework_mapping.get(role, Framework.GENERIC)
        lessons = get_lessons_by_framework(framework, limit=5)
        
        return lessons
    except Exception as e:
        logger.error(f"Failed to get role-based recommendations: {e}")
        return []

app = FastAPI(title="TrainPi Microlearning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://v0-frontend-opal-nine.vercel.app",
        "https://v0-frontend-opal-nine.vercel.app/",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "null",  # For local HTML files opened directly in browser
        "*"  # Allow all origins for development/testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TrainPI API is running", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TrainPI API", "timestamp": "2024-08-01"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working correctly", "endpoint": "test"}

@app.get("/api/debug/lesson/{lesson_id}")
async def debug_lesson_content(lesson_id: int):
    """Lightweight debug endpoint: reports what we have stored for a lesson.

    Lookups are read-only from Supabase + the in-memory `lesson_store` cache.
    No content is generated here — generation happens via the chat path so we
    don't have two diverging code paths producing different output.
    """
    try:
        from distiller import get_lesson_cache
        cached = get_lesson_cache(str(lesson_id)) or {}

        lesson_data = get_lesson_by_id(lesson_id) or {}
        summary = get_lesson_summary(lesson_id) or cached.get("summary") or ""
        bullets = [b.strip() for b in summary.split("•") if b.strip()] if summary else []

        flashcards = cached.get("flashcards") or []
        quiz = cached.get("quiz") or []

        return {
            "lesson_id": lesson_id,
            "title": lesson_data.get("title") or cached.get("title"),
            "framework": lesson_data.get("framework") or cached.get("framework"),
            "summary_count": len(bullets),
            "flashcards_count": len(flashcards),
            "quiz_count": len(quiz),
            "summary_preview": bullets[:2],
            "flashcards_preview": flashcards[:1],
            "quiz_preview": quiz[:1],
            "has_chunks": bool(cached.get("chunks")),
            "has_embeddings": bool(cached.get("chunk_embeddings")),
        }
    except Exception as e:
        logger.error(f"Debug lesson content failed: {e}")
        return {"error": str(e), "lesson_id": lesson_id}

@app.post("/api/distill")
async def distill_pdf(
    owner_id: str = Query(..., description="Supabase user UUID"),
    explanation_level: ExplanationLevel = Query(ExplanationLevel.INTERN, description="Explanation complexity level"),
    framework: Framework = Query(Framework.GENERIC, description="Primary framework/tool category"),
    file: UploadFile = File(...)
):
    """Enhanced distill endpoint that returns lesson_id and available actions"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    if not file.size or file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(413, "File too large. Maximum size is 50MB")
    
    tmp = None
    try:
        # Create temporary file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        content = await file.read()
        tmp.write(content)
        tmp.close()
        
        # Extract text and process with proper error handling
        try:
            text = pdf_to_text(Path(tmp.name))
            if not text or len(text.strip()) < 10:
                raise HTTPException(422, "Failed to extract text from PDF - the file might be scanned or corrupted")
        except Exception as pdf_error:
            logger.error(f"PDF text extraction failed: {pdf_error}")
            raise HTTPException(422, "Failed to process PDF – maybe it's scanned or has no selectable text?")
        
        chunks = chunk_text(text)
        logger.info(f"{len(chunks)} chunks created")
        
        if not chunks:
            raise HTTPException(422, "No content could be extracted from the PDF")
        
        # Auto-detect framework if not specified
        if framework == Framework.GENERIC:
            framework = await detect_framework(text)
            logger.info(f"Auto-detected framework: {framework}")
        
        embeds = await embed_chunks(chunks)
        summary = await map_reduce_summary(chunks, explanation_level)
        qa = await gen_flashcards_quiz(summary, explanation_level)
        concept_map = await generate_concept_map(summary)
        
        # Save to Supabase
        lesson_id = insert_lesson(owner_id, file.filename, summary, framework, explanation_level)
        
        # Insert concept map
        insert_concept_map(lesson_id, concept_map)
        
        # Insert cards (bullets, flashcards, quiz)
        card_rows = []
        for i, b in enumerate(summary.split("•")):
            if b.strip():
                card_rows.append({
                    "lesson_id": lesson_id,
                    "card_type": "bullet",
                    "payload": {"order": i, "text": b.strip()},
                    "embed_vector": embeds[min(i, len(embeds)-1)] if embeds else [],
                })
        
        for fc in qa["flashcards"]:
            card_rows.append({
                "lesson_id": lesson_id,
                "card_type": "flashcard",
                "payload": fc,
            })
        
        for q in qa["quiz"]:
            card_rows.append({
                "lesson_id": lesson_id,
                "card_type": "quiz",
                "payload": q,
            })
        
        insert_cards(lesson_id, card_rows)
        
        # Get preview bullets (first 3)
        bullets = [b.strip() for b in summary.split("•") if b.strip()]
        preview = bullets[:3] if len(bullets) >= 3 else bullets
        
        return {
            "lesson_id": lesson_id,
            "actions": ["summary", "lesson", "quiz", "flashcards", "workflow"],
            "preview": preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Distill processing failed: {e}")
        raise HTTPException(500, f"Failed to process PDF: {str(e)}")
    finally:
        if tmp and os.path.exists(tmp.name):
            try:
                os.unlink(tmp.name)
            except:
                pass

# NOTE: previously this section exposed `/api/lesson/{id}/{action}` (GET/POST),
# `/api/chat/lesson/summary`, and `/api/chat/lesson/{id}/content`.
# Those returned hardcoded "API Development" fallbacks when Supabase rows were
# missing and were never reached by the live frontend (the chat path covers all
# Quick Actions). They have been removed. The single source of truth for content
# generation is now `process_chat_message` in distiller.py, which routes by
# intent and grounds outputs in the uploaded PDF chunks.

@app.post("/api/chat/ingest-distilled")
async def ingest_distilled_lesson(
    lesson_id: int = Query(..., description="Lesson ID to ingest"),
    user_id: str = Query(..., description="User ID"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID")
):
    """Ingest a previously processed lesson into the chat conversation context.
    This allows the chatbot to reference existing lessons without re-uploading the PDF."""
    try:
        # Get lesson data (prefer cache)
        try:
            from distiller import get_lesson_cache
        except Exception:
            get_lesson_cache = None
        cached = get_lesson_cache(str(lesson_id)) if get_lesson_cache else None

        lesson_data = get_lesson_by_id(lesson_id) or cached
        if not lesson_data:
            raise HTTPException(404, "Lesson not found")
        
        # Get lesson summary and full text
        summary = get_lesson_summary(lesson_id) or (cached.get("summary") if cached else None)
        full_text = get_lesson_full_text(lesson_id) or (cached.get("full_text") if cached else None)
        
        if not summary:
            raise HTTPException(404, "Lesson summary not found")
        
        # Get or create conversation
        from distiller import get_or_create_conversation, add_message_to_conversation, conversation_store
        conv_id = get_or_create_conversation(conversation_id, user_id)
        
        # Add lesson context to conversation (use full text if available, otherwise summary)
        context_text = full_text if full_text else summary
        conversation_store[conv_id]["file_context"] = context_text
        conversation_store[conv_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Update conversation metadata
        if "metadata" not in conversation_store[conv_id]:
            conversation_store[conv_id]["metadata"] = {}
        
        conversation_store[conv_id]["metadata"].update({
            "current_lesson": {
                "lesson_id": lesson_id,
                "title": lesson_data.get("title", "Unknown Lesson"),
                "framework": lesson_data.get("framework", "GENERIC"),
                "ingested_at": datetime.utcnow().isoformat()
            },
            "lesson_id": lesson_id
        })
        
        # Generate welcome message
        title = (lesson_data.get("title") if isinstance(lesson_data, dict) else None) or "your lesson"
        framework = (lesson_data.get("framework") if isinstance(lesson_data, dict) else None) or "GENERIC"
        
        welcome_message = f"""🎉 **Lesson Successfully Loaded!**

I've loaded **"{title}"** into our conversation. This lesson covers {framework} concepts and I'm ready to help you learn!

**What I can help you with:**
• 📋 **"Create summary"** - Get key bullet points
• 📚 **"Create lesson"** - Generate comprehensive microlearning lesson  
• 🧠 **"Generate quiz"** - Create interactive quiz
• 🗂️ **"Make flashcards"** - Create study flashcards
• 🔄 **"Create workflow"** - Generate visual workflow/diagram

**Explanation Levels on the side bar:**
• **"Explain like 5"** - Simple explanations
• **"Explain like 15"** - Intermediate level  
• **"Explain like senior"** - Advanced explanations

Just tell me what you'd like to learn about from this lesson!"""
        
        add_message_to_conversation(conv_id, "assistant", welcome_message)
        
        return {
            "response": welcome_message,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "lesson_ingested": True,
            "lesson_id": lesson_id,
            "title": title,
            "framework": framework,
            "summary": summary,
            "actions": ["summary", "lesson", "quiz", "flashcards", "workflow"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest lesson for chat: {e}")
        raise HTTPException(500, f"Failed to ingest lesson for chat")


# Chatbot endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatMessage):
    """Chat with the AI assistant."""
    try:
        result = await process_chat_message(
            request.user_id,
            request.message,
            request.conversation_id,
            request.explanation_level,
            topic_focus=request.topic_focus,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(500, "Failed to process chat message.")

@app.post("/api/chat/upload", response_model=ChatResponse)
async def upload_file_for_chat(
    user_id: str = Query(..., description="User ID"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID"),
    explanation_level: ExplanationLevel = Query(ExplanationLevel.INTERN, description="Explanation level"),
    file: UploadFile = File(...)
):
    """Upload a file and start a conversation about it."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "PDF only")
    
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(await file.read())
        tmp.close()
        
        result = await process_file_for_chat(
            Path(tmp.name), 
            user_id, 
            conversation_id, 
            explanation_level
        )
        
    except RuntimeError as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(500, str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(500, "Internal server error.")
    finally:
        os.unlink(tmp.name)
    
    return ChatResponse(**result)

@app.get("/api/chat/conversations/{user_id}")
async def get_user_chat_conversations(user_id: str):
    """Get all chat conversations for a user."""
    try:
        conversations = get_user_conversations(user_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Failed to get user conversations: {e}")
        raise HTTPException(500, "Failed to get conversations.")

@app.get("/api/chat/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation history."""
    try:
        conversation = get_conversation_history(conversation_id)
        if not conversation:
            raise HTTPException(404, "Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(500, "Failed to get conversation.")

@app.get("/api/chat/side-menu/{user_id}")
async def get_side_menu(user_id: str):
    """Get side menu data including recent PDFs and user preferences."""
    try:
        side_menu_data = get_side_menu_data(user_id)
        return side_menu_data
    except Exception as e:
        logger.error(f"Failed to get side menu data: {e}")
        raise HTTPException(500, "Failed to get side menu data")

@app.put("/api/chat/preferences/explanation-level")
async def update_user_explanation_level(user_id: str, level: str):
    """Update user's explanation level preference."""
    try:
        update_explanation_level(user_id, level)
        return {"message": "Explanation level updated successfully", "level": level}
    except Exception as e:
        logger.error(f"Failed to update explanation level: {e}")
        raise HTTPException(500, "Failed to update explanation level")

@app.put("/api/chat/preferences/framework")
async def update_user_framework_preference(user_id: str, framework: str):
    """Update user's framework preference."""
    try:
        update_framework_preference(user_id, framework)
        return {"message": "Framework preference updated successfully", "framework": framework}
    except Exception as e:
        logger.error(f"Failed to update framework preference: {e}")
        raise HTTPException(500, "Failed to update framework preference")


# Career matching endpoints
@app.get("/api/career/quiz", response_model=CareerQuizResponse)
async def get_career_quiz():
    """Get the 10 career quiz questions"""
    try:
        questions = matcher.get_quiz_questions()
        quiz_questions = [
            CareerQuizQuestion(
                id=q["id"],
                question=q["question"],
                category="career_assessment",  # Default category
                description="Career interest assessment question"  # Default description
            )
            for q in questions
        ]
        return CareerQuizResponse(questions=quiz_questions)
    except Exception as e:
        logger.error(f"Failed to get career quiz: {e}")
        raise HTTPException(500, "Failed to get career quiz questions.")

@app.post("/api/career/match", response_model=CareerMatchResponse)
async def career_match(request: CareerMatchRequest):
    """Match user quiz answers to career paths using enhanced algorithms"""
    try:
        # Validate answers
        if len(request.answers) != 10:
            raise HTTPException(400, "Need exactly 10 answers")
        if not all(0 <= a <= 5 for a in request.answers):  # Changed from 1-5 to 0-5 since array indices are 0-based
            raise HTTPException(400, "Answers must be 0-5")

        # Get career matches using enhanced embedding-based AI capabilities
        matches = await matcher.get_career_matches(request.answers, top_k=5)

        # Convert to response format
        cards = []
        for m in matches:
            try:
                # Parse skills (comma-separated string to list)
                skills_str = m.get("top_skills", "technical skills, problem solving, communication")
                common_skills = [skill.strip() for skill in skills_str.split(",")][:3]

                card = CareerCard(
                    title=m["title"],
                    salary_low=int(m["salary_low"]),
                    salary_high=int(m["salary_high"]),
                    growth_pct=float(m["growth_pct"]),
                    common_skills=common_skills,
                    day_in_life=m["day_in_life"],
                    similarity=round(float(m["similarity"]), 3),
                    roadmap=m.get("roadmap")
                )
                cards.append(card)
            except Exception as e:
                logger.error(f"Error processing career match: {e}")
                continue

        logger.info(f"Returning {len(cards)} enhanced career matches for user {request.owner_id}")
        return CareerMatchResponse(results=cards)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Career matching failed: {e}")
        raise HTTPException(500, "Failed to process career matching.")

@app.get("/api/career/roadmap/{career_title}")
async def get_career_roadmap(career_title: str):
    """Get career roadmap for a specific career"""
    try:
        roadmap = matcher.get_career_roadmap(career_title)
        return {"career_title": career_title, "roadmap": roadmap}
    except Exception as e:
        logger.error(f"Failed to get career roadmap: {e}")
        raise HTTPException(500, "Failed to get career roadmap.")

@app.get("/api/career/roadmaps")
async def get_all_roadmaps():
    """Get all available career roadmaps"""
    try:
        return {"roadmaps": matcher.career_roadmaps}
    except Exception as e:
        logger.error(f"Failed to get roadmaps: {e}")
        raise HTTPException(500, "Failed to get career roadmaps.")

@app.post("/api/career/quiz/comprehensive-analysis")
async def get_comprehensive_career_analysis(
    answers: List[int],
    user_skills: Optional[List[str]] = None
):
    """Get comprehensive career analysis from quiz answers with AI-powered insights"""
    try:
        # Validate answers
        if len(answers) != 10:
            raise HTTPException(400, "Need exactly 10 answers")
        if not all(0 <= a <= 5 for a in answers):  # Changed from 1-5 to 0-5 since array indices are 0-based
            raise HTTPException(400, "Answers must be 0-5")
        
        # Get comprehensive analysis with embedding-based matching
        analysis = await matcher.generate_comprehensive_career_analysis(answers, user_skills)
        return analysis
    except Exception as e:
        logger.error(f"Comprehensive career analysis failed: {e}")
        raise HTTPException(500, "Failed to generate comprehensive analysis.")

@app.post("/api/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: int, user_id: str, progress_percentage: float = 100.0):
    """Mark a lesson as completed for a user."""
    try:
        mark_lesson_completed(user_id, lesson_id, progress_percentage)
        return {"message": "Lesson marked as completed", "lesson_id": lesson_id}
    except Exception as e:
        logger.error(f"Failed to mark lesson as completed: {e}")
        raise HTTPException(500, "Failed to mark lesson as completed.")

@app.get("/api/users/{user_id}/completed-lessons")
async def get_completed_lessons(user_id: str):
    """Get all completed lessons for a user."""
    try:
        completed_lessons = get_user_completed_lessons(user_id)
        return {"completed_lessons": completed_lessons}
    except Exception as e:
        logger.error(f"Failed to get completed lessons: {e}")
        raise HTTPException(500, "Failed to get completed lessons.")

@app.get("/api/users/{user_id}/progress")
async def get_user_progress(user_id: str):
    """Get user's learning progress statistics."""
    try:
        progress_stats = get_user_progress_stats(user_id)
        return progress_stats
    except Exception as e:
        logger.error(f"Failed to get user progress: {e}")
        raise HTTPException(500, "Failed to get user progress.")

@app.put("/api/users/{user_id}/role")
async def update_user_role(user_id: str, user_role: UserRole):
    """Update user role and preferences."""
    try:
        result = upsert_user_role(user_id, user_role.role, user_role.experience_level, user_role.interests)
        if result is False:
            raise Exception("User role update failed")
        return {"message": "User role updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update user role: {e}")
        # Return success for testing when Supabase is not available
        return {"message": "User role updated successfully (test mode)"}

@app.get("/api/users/{user_id}/role")
async def get_user_role_info(user_id: str):
    """Get user role and preferences."""
    try:
        user_role = get_user_role(user_id)
        return {"user_role": user_role}
    except Exception as e:
        logger.error(f"Failed to get user role: {e}")
        raise HTTPException(500, "Failed to get user role.")

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Get personalized lesson recommendations based on user profile."""
    try:
        user_role = get_user_role(request.user_id)
        if not user_role:
            return {"recommendations": []}
        
        recommendations = await get_role_based_recommendations(
            request.user_id,
            user_role.get("role", request.role or "Developer"),
            user_role.get("experience_level", request.experience_level or "Mid"),
            user_role.get("interests", request.interests or [])
        )
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(500, "Failed to get recommendations.")

@app.get("/api/lessons/framework/{framework}")
async def get_lessons_by_framework_endpoint(framework: Framework, limit: int = 10):
    """Get lessons filtered by framework."""
    try:
        lessons = get_lessons_by_framework(framework, limit)
        return {"lessons": lessons, "framework": framework.value}
    except Exception as e:
        logger.error(f"Failed to get lessons by framework: {e}")
        raise HTTPException(500, "Failed to get lessons by framework.")

@app.get("/api/frameworks")
async def get_available_frameworks():
    """Get list of available frameworks."""
    frameworks = [{"value": f.value, "label": f.value.replace("_", " ").title()} for f in Framework]
    return {"frameworks": frameworks}

# App startup hook to precompute micro-lesson embeddings
@app.on_event("startup")
async def _startup():
    try:
        from distiller import precompute_micro_lessons_embeddings
        total, embedded = await precompute_micro_lessons_embeddings()
        logger.info(f"Micro-lessons precomputed: {embedded}/{total}")
    except Exception as e:
        logger.warning(f"Failed precomputing micro-lessons: {e}")

# -----------------
# Supabase debug APIs
# -----------------
@app.get("/api/debug/supabase/check")
async def debug_supabase_check():
    try:
        from supabase_helper import SUPA
        if not SUPA:
            return {"supabase": False, "message": "SUPA client not initialized. Check env vars."}
        # Try a lightweight query
        res = SUPA.table("lessons").select("id", count="exact").limit(1).execute()
        return {"supabase": True, "lessons_count": res.count or 0}
    except Exception as e:
        return {"supabase": False, "error": str(e)}

@app.post("/api/debug/supabase/seed")
async def debug_supabase_seed(user_id: str = Query("anonymous-user")):
    """Insert a test lesson + one card + concept map to verify Supabase writes."""
    try:
        from supabase_helper import insert_lesson, insert_cards, insert_concept_map
        from schemas import Framework, ExplanationLevel

        title = f"Test Lesson {datetime.utcnow().isoformat()}"
        summary = "• Test bullet one\n• Test bullet two\n• Test bullet three"
        lesson_id = insert_lesson(user_id, title, summary, Framework.GENERIC, ExplanationLevel.INTERN, full_text="Test full text")

        # One bullet card
        cards = [{
            "lesson_id": lesson_id,
            "card_type": "bullet",
            "payload": {"order": 0, "text": "Test bullet one"}
        }]
        insert_cards(lesson_id, cards)

        # Simple concept map
        concept_map = {
            "nodes": [{"id": "n1", "title": "Test Node"}],
            "edges": []
        }
        insert_concept_map(lesson_id, concept_map)

        return {"ok": True, "lesson_id": lesson_id}
    except Exception as e:
        logger.error(f"Supabase seed failed: {e}")
        raise HTTPException(500, f"Supabase seed failed: {str(e)}")

@app.get("/api/skills")
async def get_available_skills():
    """Get all available skills for career planning"""
    try:
        # Define a comprehensive list of skills
        skills = [
            "Python", "JavaScript", "React", "Node.js", "TypeScript", "HTML", "CSS",
            "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
            "Django", "Flask", "Express.js", "Spring Boot", "Laravel", "ASP.NET",
            "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "GraphQL",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Ansible",
            "Git", "GitHub", "CI/CD", "Jenkins", "GitLab", "Bitbucket",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn",
            "Data Analysis", "Data Visualization", "Pandas", "NumPy", "Matplotlib",
            "Tableau", "Power BI", "Excel", "SQL", "R", "SAS", "SPSS",
            "Agile", "Scrum", "Kanban", "Project Management", "Leadership",
            "Communication", "Problem Solving", "Critical Thinking", "Creativity",
            "Teamwork", "Time Management", "Customer Service", "Sales", "Marketing",
            "Finance", "Accounting", "Human Resources", "Operations", "Strategy",
            "Research", "Writing", "Editing", "Translation", "Design", "UX/UI",
            "Photography", "Video Editing", "Animation", "3D Modeling", "Game Development",
            "Mobile Development", "iOS", "Android", "Flutter", "React Native",
            "Web Development", "Frontend", "Backend", "Full Stack", "DevOps",
            "Cybersecurity", "Network Security", "Penetration Testing", "Compliance",
            "Blockchain", "Cryptocurrency", "Smart Contracts", "Web3", "DeFi",
            "IoT", "Embedded Systems", "Robotics", "Automation", "AI Ethics",
            "Data Privacy", "GDPR", "HIPAA", "SOX", "PCI DSS"
        ]
        return {"skills": skills}
    except Exception as e:
        logger.error(f"Failed to get skills: {e}")
        raise HTTPException(500, "Failed to get skills")

@app.get("/api/explanation-levels")
async def get_explanation_levels():
    """Get list of available explanation levels."""
    levels = [
        {"value": ExplanationLevel.FIVE_YEAR_OLD.value, "label": "5 Year Old"},
        {"value": ExplanationLevel.INTERN.value, "label": "Intern"},
        {"value": ExplanationLevel.SENIOR.value, "label": "Senior"}
    ]
    return {"explanation_levels": levels}

# Dynamic Roadmap Generation Endpoints

@app.post("/api/career/roadmap/generate", response_model=RoadmapResponse)
async def generate_dynamic_roadmap(request: RoadmapRequest):
    """Generate dynamic career roadmap with micro-lesson integration"""
    try:
        # Use unified advisor for roadmap generation
        plan = await unified_advisor.generate_comprehensive_career_plan(
            user_profile={"experience_level": request.user_experience},
            target_role=request.target_role,
            user_skills=request.user_skills
        )
        
        return RoadmapResponse(
            target_role=request.target_role,
            roadmap=plan["roadmap"],
            user_experience=request.user_experience
        )
        
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}")
        raise HTTPException(500, "Failed to generate career roadmap.")

@app.get("/api/lessons/micro")
async def get_micro_lessons(category: Optional[str] = None):
    """Get available micro-lessons"""
    try:
        lessons = unified_advisor.get_micro_lessons(category)
        return {"lessons": lessons}
    except Exception as e:
        logger.error(f"Failed to get micro-lessons: {e}")
        raise HTTPException(500, "Failed to get micro-lessons.")

@app.post("/api/lessons/search", response_model=LessonSearchResponse)
async def search_micro_lessons(request: LessonSearchRequest):
    """Search for micro-lessons by query"""
    try:
        results = unified_advisor.search_lessons(request.query)
        return LessonSearchResponse(results=results)
    except Exception as e:
        logger.error(f"Lesson search failed: {e}")
        raise HTTPException(500, "Failed to search micro-lessons.")

@app.get("/api/career/roadmap/cache/clear")
async def clear_roadmap_cache():
    """Clear roadmap cache (admin endpoint)"""
    try:
        unified_advisor.roadmap_cache.clear()
        unified_advisor._save_cache(unified_advisor.roadmap_cache, "roadmap_cache.json")
        return {"message": "Roadmap cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(500, "Failed to clear roadmap cache.")

# Advanced Career Coach Endpoints
@app.post("/api/career/guidance", response_model=CareerGuidanceResponse)
async def get_career_guidance(request: CareerGuidanceRequest):
    """Get personalized career guidance"""
    try:
        result = await career_coach.get_personalized_guidance(
            request.user_id, 
            request.user_profile, 
            request.query
        )
        return CareerGuidanceResponse(**result)
    except Exception as e:
        logger.error(f"Career guidance failed: {e}")
        raise HTTPException(500, "Failed to generate career guidance")

@app.post("/api/career/interview/start", response_model=InterviewSimulationResponse)
async def start_interview_simulation(request: InterviewSimulationRequest):
    """Start an interview simulation session"""
    try:
        result = await career_coach.start_interview_simulation(
            request.user_id,
            request.target_role,
            request.difficulty
        )
        return InterviewSimulationResponse(**result)
    except Exception as e:
        logger.error(f"Interview simulation start failed: {e}")
        raise HTTPException(500, "Failed to start interview simulation")

@app.post("/api/career/interview/answer", response_model=InterviewAnswerResponse)
async def submit_interview_answer(request: InterviewAnswerRequest):
    """Submit an answer during interview simulation"""
    try:
        result = await career_coach.submit_interview_answer(
            request.session_id,
            request.answer
        )
        return InterviewAnswerResponse(**result)
    except Exception as e:
        logger.error(f"Interview answer submission failed: {e}")
        raise HTTPException(500, "Failed to process interview answer")

@app.post("/api/career/advice", response_model=CareerAdviceResponse)
async def get_career_advice(request: CareerAdviceRequest):
    """Get career advice on specific topics"""
    try:
        result = await career_coach.get_career_advice(
            request.topic,
            request.user_context
        )
        return CareerAdviceResponse(**result)
    except Exception as e:
        logger.error(f"Career advice failed: {e}")
        raise HTTPException(500, "Failed to generate career advice")

@app.get("/api/career/interview/roles")
async def get_available_interview_roles():
    """Get available roles for interview simulation"""
    try:
        roles = career_coach.get_available_interview_roles()
        return {"roles": roles}
    except Exception as e:
        logger.error(f"Failed to get interview roles: {e}")
        raise HTTPException(500, "Failed to get available roles")

@app.get("/api/career/advice/topics")
async def get_career_advice_topics():
    """Get available career advice topics"""
    try:
        topics = career_coach.get_career_advice_topics()
        return {"topics": topics}
    except Exception as e:
        logger.error(f"Failed to get advice topics: {e}")
        raise HTTPException(500, "Failed to get advice topics")

@app.get("/api/career/sessions/{user_id}")
async def get_user_career_sessions(user_id: str):
    """Get all career sessions for a user"""
    try:
        sessions = career_coach.get_user_sessions(user_id)
        return sessions
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(500, "Failed to get user sessions")

# AI Recommendation Engine Endpoints
@app.post("/api/recommendations/personalized", response_model=PersonalizedRecommendationsResponse)
async def generate_personalized_recommendations(request: UserProfileRequest):
    """Generate comprehensive personalized recommendations"""
    try:
        result = await recommendation_engine.generate_personalized_recommendations(
            request.user_id,
            request.user_profile
        )
        return PersonalizedRecommendationsResponse(**result)
    except Exception as e:
        logger.error(f"Personalized recommendations failed: {e}")
        raise HTTPException(500, "Failed to generate personalized recommendations")

@app.get("/api/recommendations/market-trends", response_model=MarketTrendsResponse)
async def get_market_trends():
    """Get current market trends and insights"""
    try:
        trends = recommendation_engine.get_market_trends()
        return MarketTrendsResponse(trends=trends)
    except Exception as e:
        logger.error(f"Failed to get market trends: {e}")
        raise HTTPException(500, "Failed to get market trends")

@app.get("/api/recommendations/learning-paths", response_model=LearningPathsResponse)
async def get_learning_paths():
    """Get available learning paths"""
    try:
        paths = recommendation_engine.get_learning_paths()
        return LearningPathsResponse(paths=paths)
    except Exception as e:
        logger.error(f"Failed to get learning paths: {e}")
        raise HTTPException(500, "Failed to get learning paths")

@app.get("/api/recommendations/user/{user_id}")
async def get_user_recommendations(user_id: str):
    """Get stored recommendations for a user"""
    try:
        recommendations = recommendation_engine.get_user_recommendations(user_id)
        if recommendations:
            return recommendations
        else:
            raise HTTPException(404, "No recommendations found for user")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user recommendations: {e}")
        raise HTTPException(500, "Failed to get user recommendations")

# Enhanced Career Roadmap Endpoints
@app.post("/api/career/roadmap/visual", response_model=VisualRoadmapResponse)
async def generate_visual_roadmap(request: VisualRoadmapRequest):
    """Generate visual and interactive career roadmap"""
    try:
        # Generate roadmap using existing roadmap generator
        roadmap = await roadmap_generator.generate_roadmap(
            request.target_role,
            request.user_skills,
            request.user_experience
        )
        
        # Add visual elements
        visual_data = {
            "nodes": [
                {
                    "id": "foundational",
                    "title": roadmap["foundational"]["title"],
                    "level": "foundational",
                    "skills_required": roadmap["foundational"]["skills"],
                    "estimated_duration": roadmap["foundational"]["duration"],
                    "salary_range": roadmap["foundational"]["salary_range"],
                    "courses": roadmap["foundational"]["recommended_lessons"],
                    "projects": []
                },
                {
                    "id": "intermediate",
                    "title": roadmap["intermediate"]["title"],
                    "level": "intermediate",
                    "skills_required": roadmap["intermediate"]["skills"],
                    "estimated_duration": roadmap["intermediate"]["duration"],
                    "salary_range": roadmap["intermediate"]["salary_range"],
                    "courses": roadmap["intermediate"]["recommended_lessons"],
                    "projects": []
                },
                {
                    "id": "advanced",
                    "title": roadmap["advanced"]["title"],
                    "level": "advanced",
                    "skills_required": roadmap["advanced"]["skills"],
                    "estimated_duration": roadmap["advanced"]["duration"],
                    "salary_range": roadmap["advanced"]["salary_range"],
                    "courses": roadmap["advanced"]["recommended_lessons"],
                    "projects": []
                }
            ],
            "edges": [
                {
                    "from_node": "foundational",
                    "to_node": "intermediate",
                    "transition_skills": roadmap["foundational"]["skills"],
                    "difficulty": "moderate"
                },
                {
                    "from_node": "intermediate",
                    "to_node": "advanced",
                    "transition_skills": roadmap["intermediate"]["skills"],
                    "difficulty": "high"
                }
            ]
        }
        
        interactive_elements = [
            {
                "type": "skill_check",
                "node_id": "foundational",
                "description": "Check your foundational skills"
            },
            {
                "type": "course_recommendation",
                "node_id": "intermediate",
                "description": "Get course recommendations"
            },
            {
                "type": "project_suggestion",
                "node_id": "advanced",
                "description": "Build portfolio projects"
            }
        ]
        
        return VisualRoadmapResponse(
            target_role=request.target_role,
            roadmap=roadmap,
            visual_data=visual_data if request.include_visual else None,
            interactive_elements=interactive_elements
        )
        
    except Exception as e:
        logger.error(f"Visual roadmap generation failed: {e}")
        raise HTTPException(500, "Failed to generate visual roadmap")

# Advanced Analytics Endpoints
@app.get("/api/analytics/user/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(user_id: str, time_period: str = "30d"):
    """Get comprehensive user analytics"""
    try:
        # Mock analytics data - in production, this would come from database
        analytics = {
            "user_id": user_id,
            "learning_progress": {
                "lessons_completed": 15,
                "total_lessons": 25,
                "completion_rate": 60.0,
                "streak_days": 7,
                "time_spent": "45 hours"
            },
            "skill_growth": {
                "python": {"current": 0.8, "target": 1.0, "progress": 80.0},
                "javascript": {"current": 0.6, "target": 0.9, "progress": 67.0},
                "react": {"current": 0.4, "target": 0.8, "progress": 50.0}
            },
            "career_advancement": {
                "current_role": "Junior Developer",
                "target_role": "Senior Developer",
                "advancement_score": 0.65,
                "estimated_time": "18 months"
            },
            "market_alignment": {
                "hot_skills_alignment": 0.75,
                "salary_progression": 0.60,
                "industry_demand": "High"
            },
            "recommendations": [
                {"type": "skill", "priority": "high", "skill": "System Design"},
                {"type": "project", "priority": "medium", "project": "Build a microservice"},
                {"type": "certification", "priority": "low", "cert": "AWS Developer"}
            ]
        }
        
        return UserAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"User analytics failed: {e}")
        raise HTTPException(500, "Failed to generate user analytics")

# Enhanced Career Pathfinder Endpoints (Image-based)
@app.post("/api/career/planning", response_model=CareerPlanningResponse)
async def generate_career_planning(request: CareerPlanningRequest):
    """Generate career recommendations based on interests and skills (like the image)"""
    try:
        # Use unified advisor for comprehensive planning
        plan = await unified_advisor.generate_comprehensive_career_plan(
            user_profile={},
            user_skills=request.skills,
            user_interests=request.interests
        )
        
        # Extract career recommendations from the plan
        result = {
            "recommended_careers": [plan["target_role"]],
            "confidence_score": plan["confidence_score"],
            "skill_gaps": plan["skill_gaps"],
            "learning_recommendations": plan["learning_plan"]
        }
        return CareerPlanningResponse(**result)
    except Exception as e:
        logger.error(f"Career planning failed: {e}")
        raise HTTPException(500, "Failed to generate career planning")

@app.post("/api/career/roadmap/enhanced", response_model=CareerRoadmapResponse)
async def generate_enhanced_career_roadmap(request: CareerRoadmapRequest):
    """Generate detailed roadmap for a specific career"""
    try:
        plan = await unified_advisor.generate_comprehensive_career_plan(
            user_profile={},
            target_role=request.career_title,
            user_skills=request.user_skills
        )
        
        result = {
            "career_title": request.career_title,
            "roadmap": plan["roadmap"],
            "skill_gaps": plan["skill_gaps"],
            "learning_plan": plan["learning_plan"],
            "timeline": plan["timeline"]
        }
        return CareerRoadmapResponse(**result)
    except Exception as e:
        logger.error(f"Enhanced career roadmap failed: {e}")
        raise HTTPException(500, "Failed to generate career roadmap")

@app.get("/api/career/planning/options", response_model=PredefinedOptionsResponse)
async def get_career_planning_options():
    """Get predefined interests and skills options"""
    try:
        # Define predefined options for the frontend
        interests = [
            "Technology", "Design", "Marketing", "Data Science", 
            "Product Management", "Cybersecurity", "DevOps", "Mobile Development"
        ]
        skills = [
            "Python", "JavaScript", "React", "Node.js", "SQL", "AWS",
            "UI/UX Design", "SEO", "Content Marketing", "Data Analysis",
            "Machine Learning", "Docker", "Kubernetes", "Git"
        ]
        return PredefinedOptionsResponse(interests=interests, skills=skills)
    except Exception as e:
        logger.error(f"Failed to get planning options: {e}")
        raise HTTPException(500, "Failed to get planning options")

@app.get("/api/career/available")
async def get_available_careers():
    """Get all available careers"""
    try:
        careers = unified_advisor.career_data['title'].tolist()
        return {"careers": careers}
    except Exception as e:
        logger.error(f"Failed to get available careers: {e}")
        raise HTTPException(500, "Failed to get available careers")

@app.post("/api/career/comprehensive-plan", response_model=ComprehensiveCareerPlanResponse)
async def generate_comprehensive_career_plan(request: ComprehensiveCareerPlanRequest):
    """
    Generate a comprehensive career plan that includes:
    1. Career recommendations
    2. Personalized roadmap
    3. Skill gap analysis
    4. Learning recommendations
    5. Career coaching advice
    6. Market insights
    7. Timeline and milestones
    """
    try:
        plan = await unified_career_system.generate_unified_roadmap(
            user_profile=request.user_profile,
            target_role=request.target_role,
            user_skills=request.user_skills or [],
            user_interests=request.user_interests or []
        )
        
        # Map the unified roadmap response to comprehensive career plan response
        comprehensive_plan = {
            "target_role": plan["target_role"],
            "roadmap": plan["roadmap"],
            "skill_gaps": {
                "missing_skills": [],
                "skill_analysis": "Analysis based on user profile"
            },
            "learning_plan": plan["learning_plan"],
            "coaching_advice": plan["coaching_advice"],
            "market_insights": plan["market_insights"],
            "timeline": plan["timeline"],
            "confidence_score": plan["confidence_score"],
            "estimated_time_to_target": plan["estimated_time_to_target"]
        }
        
        return ComprehensiveCareerPlanResponse(**comprehensive_plan)
    except Exception as e:
        logger.error(f"Error generating comprehensive career plan: {e}")
        raise HTTPException(500, "Failed to generate comprehensive career plan")



# ---------------------------------------------------------------------------
# Resume-driven career upgrade
# ---------------------------------------------------------------------------
# Three endpoints, each step is independently usable so the frontend can show
# progressive results (parsed skills auto-fill before the user clicks "build plan").

@app.post("/api/career/resume/parse")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """Parse a resume PDF into a structured profile (skills, experience, projects)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDF only")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(await file.read())
    tmp.close()
    try:
        parsed = await resume_parse(Path(tmp.name))
        return {"resume": parsed}
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Resume parse failed: {e}")
        raise HTTPException(500, "Failed to parse resume")
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


@app.post("/api/career/plan/build")
async def build_resume_plan_endpoint(payload: Dict = None):
    """Build a tailored skill-gap + roadmap + 90-day plan from a parsed resume.

    Body: {
        resume: <object returned by /api/career/resume/parse>,
        target_role: str,
        interests: [str]
    }
    """
    if not payload or not isinstance(payload, dict):
        raise HTTPException(400, "Body must be JSON with `resume`, `target_role`, `interests`.")

    resume = payload.get("resume") or {}
    target_role = (payload.get("target_role") or "").strip()
    interests = payload.get("interests") or []
    if not target_role:
        raise HTTPException(400, "`target_role` is required.")

    try:
        return await resume_build_plan(resume, target_role, interests)
    except Exception as e:
        logger.error(f"Career plan build failed: {e}")
        raise HTTPException(500, "Failed to build career plan")


@app.post("/api/career/plan/snapshot")
async def save_career_plan_snapshot_endpoint(payload: Dict = None):
    """Persist the latest resume-driven career plan for a user (JSON on disk)."""
    if not payload or not isinstance(payload, dict):
        raise HTTPException(400, "Body must be JSON with `user_id` and `snapshot`.")

    user_id = (payload.get("user_id") or "").strip()
    snapshot = payload.get("snapshot")
    if not user_id:
        raise HTTPException(400, "`user_id` is required.")
    if not isinstance(snapshot, dict):
        raise HTTPException(400, "`snapshot` must be a JSON object (the build-plan API response).")

    try:
        saved = save_latest_plan(user_id, snapshot)
        return {"ok": True, "saved_at": saved["saved_at"]}
    except Exception as e:
        logger.error(f"Career plan snapshot save failed: {e}")
        raise HTTPException(500, "Failed to save career plan")


@app.get("/api/career/plan/latest/{user_id}")
async def get_latest_career_plan_endpoint(user_id: str):
    """Return the last saved plan snapshot, or `has_plan: false` if none."""
    row = load_latest_plan(user_id)
    if not row:
        return {"has_plan": False}
    return {"has_plan": True, **row}


@app.post("/api/career/upgrade")
async def career_upgrade_endpoint(
    target_role: str = Query(..., description="Target career role"),
    interests: str = Query("", description="Comma-separated interests"),
    user_id: str = Query("", description="Optional user id for persisting latest plan snapshot"),
    file: UploadFile = File(...),
):
    """One-shot: upload resume + target_role + interests → full upgrade payload."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDF only")

    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(await file.read())
    tmp.close()
    try:
        result = await resume_upgrade(Path(tmp.name), target_role, interest_list)
        # If we know the user, persist the one-shot output so dashboard/career
        # pages can pick up the latest generated plan without extra client calls.
        if user_id.strip():
            try:
                save_latest_plan(user_id.strip(), result)
            except Exception as persist_err:
                logger.warning(f"Could not persist one-shot career plan for {user_id}: {persist_err}")
        return result
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Career upgrade failed: {e}")
        raise HTTPException(500, "Failed to run career upgrade")
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# Unified Career System Endpoints
@app.post("/api/career/roadmap/unified", response_model=UnifiedRoadmapResponse)
async def generate_unified_roadmap(request: UnifiedRoadmapRequest):
    """
    Generate unified roadmap with all features:
    1. Target role recommendation (if not provided)
    2. Detailed career roadmap
    3. Interview preparation
    4. Market insights
    5. Learning recommendations
    6. Career coaching advice
    """
    try:
        roadmap = await unified_career_system.generate_unified_roadmap(
            user_profile=request.user_profile,
            target_role=request.target_role,
            user_skills=request.user_skills,
            user_interests=request.user_interests
        )
        return UnifiedRoadmapResponse(**roadmap)
    except Exception as e:
        logger.error(f"Error generating unified roadmap: {e}")
        raise HTTPException(500, "Failed to generate unified roadmap")

@app.post("/api/career/roadmap/interview-prep", response_model=InterviewPrepResponse)
async def generate_roadmap_interview_prep(request: InterviewPrepRequest):
    """Generate interview preparation for roadmap target role"""
    try:
        prep = await unified_career_system._generate_interview_preparation(
            target_role=request.target_role,
            user_profile=request.user_profile
        )
        return InterviewPrepResponse(**prep)
    except Exception as e:
        logger.error(f"Error generating roadmap interview prep: {e}")
        raise HTTPException(500, "Failed to generate interview preparation")


# Dashboard Endpoints
@app.post("/api/dashboard/recommendations")
async def get_dashboard_recommendations(
    user_id: str,
    user_profile: Optional[Dict] = None,
    user_skills: Optional[List[str]] = None,
    user_interests: Optional[List[str]] = None,
    target_role: Optional[str] = None
):
    """Get personalized recommendations for dashboard"""
    try:
        recommendations = await dashboard_system.generate_personalized_recommendations(
            user_id=user_id,
            user_profile=user_profile,
            user_skills=user_skills,
            user_interests=user_interests,
            target_role=target_role
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error generating dashboard recommendations: {e}")
        raise HTTPException(500, "Failed to generate recommendations")

@app.post("/api/dashboard/coaching")
async def get_dashboard_coaching(
    user_id: str,
    user_profile: Optional[Dict] = None,
    target_role: Optional[str] = None,
    current_challenges: Optional[List[str]] = None
):
    """Get career coaching advice for dashboard"""
    try:
        coaching = await dashboard_system.generate_career_coaching_advice(
            user_id=user_id,
            user_profile=user_profile,
            target_role=target_role,
            current_challenges=current_challenges
        )
        return coaching
    except Exception as e:
        logger.error(f"Error generating dashboard coaching: {e}")
        raise HTTPException(500, "Failed to generate coaching advice")

@app.get("/api/dashboard/analytics/{user_id}")
async def get_dashboard_analytics(user_id: str, time_period: str = "30d"):
    """Get comprehensive user analytics for dashboard"""
    try:
        analytics = await dashboard_system.get_user_analytics(user_id, time_period)
        return analytics
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(500, "Failed to get analytics")

@app.get("/api/dashboard/progress/{user_id}")
async def get_dashboard_progress(user_id: str):
    """Get user progress for dashboard"""
    try:
        progress = dashboard_system._get_user_progress_stats(user_id)
        return progress
    except Exception as e:
        logger.error(f"Error getting dashboard progress: {e}")
        raise HTTPException(500, "Failed to get progress")

@app.get("/api/dashboard/achievements/{user_id}")
async def get_dashboard_achievements(user_id: str):
    """Get user achievements for dashboard"""
    try:
        achievements = dashboard_system._get_user_achievements(user_id)
        return {"achievements": achievements}
    except Exception as e:
        logger.error(f"Error getting dashboard achievements: {e}")
        raise HTTPException(500, "Failed to get achievements")

# Micro-lessons utilities
_MICRO_LESSONS_CACHE: Optional[List[Dict]] = None

def _load_micro_lessons() -> List[Dict]:
    global _MICRO_LESSONS_CACHE
    if _MICRO_LESSONS_CACHE is not None:
        return _MICRO_LESSONS_CACHE
    try:
        data_path = Path(__file__).parent / 'data' / 'micro_lessons.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        lessons: List[Dict] = []
        # Flatten nested categories
        for category, items in raw.items():
            if isinstance(items, dict):
                for key, ml in items.items():
                    if isinstance(ml, dict):
                        lesson = {
                            "id": key,
                            "category": category,
                            "title": ml.get("title"),
                            "description": ml.get("description"),
                            "duration": ml.get("duration"),
                            "difficulty": ml.get("difficulty"),
                            "skills": ml.get("skills", []),
                            "framework": ml.get("framework")
                        }
                        lessons.append(lesson)
        _MICRO_LESSONS_CACHE = lessons
        return lessons
    except Exception as e:
        logger.error(f"Failed to load micro_lessons.json: {e}")
        _MICRO_LESSONS_CACHE = []
        return _MICRO_LESSONS_CACHE

def _normalize_framework_name(value: str) -> str:
    if not value:
        return 'generic'
    return value.strip().lower()

def _get_micro_lessons_for_framework(framework_value: str, limit: int = 6) -> List[Dict]:
    lessons = _load_micro_lessons()
    fw = _normalize_framework_name(framework_value)
    # Simple mapping from enum values to micro_lesson frameworks
    map_fw = {
        'fastapi': 'python',
        'react': 'javascript',
        'nextjs': 'javascript',
        'nodejs': 'javascript',
        'machine_learning': 'machine_learning',
        'docker': 'docker',
        'kubernetes': 'kubernetes',
        'python': 'python',
        'sql': 'sql',
        'devops': 'docker',
        'frontend': 'web',
        'backend': 'python',
    }
    target = map_fw.get(fw, fw)
    filtered = [ml for ml in lessons if _normalize_framework_name(ml.get('framework')) == target]
    if not filtered:
        # Fallback: pick a few broadly useful lessons
        filtered = [ml for ml in lessons if ml.get('category') in ['programming', 'data_science']]
    return filtered[:limit]


# ============================================================================
# MASTERY ENDPOINT
# ============================================================================
# Note: previously this section also held /api/agent/* and /api/generate/* endpoints.
# Those returned placeholder/templated content and were never reached from the
# frontend (the chat path in /api/chat covers all quick actions). They have been
# removed. Mastery is kept because the dashboard reads it.

@app.get("/api/agent/mastery/{user_id}")
async def get_user_mastery_endpoint(
    user_id: str,
    topic: Optional[str] = Query(None, description="Specific topic to get mastery for")
):
    """Get user mastery scores for topics"""
    try:
        mastery_data = get_mastery(user_id)

        return {
            "status": "success",
            "mastery": mastery_data,
            "message": "Mastery data retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Mastery retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Mastery retrieval failed: {str(e)}")


@app.post("/api/agent/diagnostic/results")
async def diagnostic_results_endpoint(request: Request):
    """Persist diagnostic answers, update per-topic mastery, and return a breakdown.

    The frontend (result-components.tsx) sends `user_answers` with
    `question_index`, `selected_answer`, `is_correct`, plus the original
    `pdf_id`, `user_id`, `topic`, `session_id`. We compute per-topic accuracy
    (the frontend supplies `topic` per question on the diagnostic payload from
    distiller) and write mastery via `update_mastery`.
    """
    try:
        body = await request.json()
        user_id = body.get("user_id")
        topic = (body.get("topic") or "general").strip() or "general"
        user_answers = body.get("user_answers") or []
        questions = body.get("questions") or []

        if not user_id or not isinstance(user_answers, list) or not user_answers:
            raise HTTPException(status_code=400, detail="user_id and user_answers are required")

        total = len(user_answers)
        correct = sum(1 for a in user_answers if a.get("is_correct"))
        overall_pct = round((correct / total) * 100) if total else 0

        # Per-topic accuracy (only computable when frontend includes per-question topics)
        topic_correct: Dict[str, int] = {}
        topic_total: Dict[str, int] = {}
        for idx, ans in enumerate(user_answers):
            q = questions[idx] if idx < len(questions) else {}
            t = (q.get("topic") if isinstance(q, dict) else None) or topic
            topic_total[t] = topic_total.get(t, 0) + 1
            if ans.get("is_correct"):
                topic_correct[t] = topic_correct.get(t, 0) + 1
        topic_scores = {t: round(topic_correct.get(t, 0) / max(topic_total[t], 1), 3) for t in topic_total}

        # Update mastery store (0..1 scale)
        try:
            update_mastery(user_id, {topic: overall_pct / 100.0, **topic_scores})
        except Exception as e:
            logger.warning(f"Mastery update soft-failed: {e}")

        weak_areas = [t for t, s in topic_scores.items() if s < 0.6]
        strong_areas = [t for t, s in topic_scores.items() if s >= 0.8]
        recommendations = [f"Review the section on {t}" for t in weak_areas[:5]] or [
            "Solid performance — try a harder document or a related topic next.",
        ]
        next_steps = [
            "Generate flashcards on the weakest topic",
            "Re-take the diagnostic in a few days to confirm retention",
        ]

        return {
            "status": "success",
            "results": {
                "results": {
                    "overall_score": overall_pct,
                    "weak_areas": weak_areas,
                    "strong_areas": strong_areas,
                    "improvement_potential": max(0, 100 - overall_pct),
                },
                "remediation": {"recommendations": recommendations},
                "mastery_update": {"topic_scores": topic_scores},
                "next_steps": next_steps,
            },
            "message": "Diagnostic results processed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagnostic results processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnostic results processing failed: {str(e)}")



