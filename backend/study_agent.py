"""
Study Agent for TrainPI Agents
Core agent classes for intelligent tutoring and learning management
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import uuid
from datetime import datetime
import asyncio

# Import optimized functionality
from learn_tools import (
    ingest_pdf, gen_summary, gen_flashcards, gen_quiz
)
from validators import qa_flashcards, qa_quiz
from repairs import repair_flashcards, repair_quiz
from mastery import get_mastery, update_mastery


class BaseAgent:
    """Base class for all TrainPI agents"""
    
    def __init__(self, pdf_id: str, user_id: str, topic: str = ""):
        self.pdf_id = pdf_id
        self.user_id = user_id
        self.topic = topic
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.log_actions = True
    
    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log agent actions for debugging and monitoring"""
        if self.log_actions:
            logger.info(f"Agent {self.__class__.__name__} - User {self.user_id} - Action: {action}")
            if details:
                logger.debug(f"Details: {details}")
    
    def get_context(self) -> Dict[str, Any]:
        """Get agent context information"""
        return {
            "pdf_id": self.pdf_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat()
        }


class SummarizerAgent(BaseAgent):
    """Generates topic-filtered summaries with concept maps and page references"""
    
    def __init__(self, pdf_id: str, user_id: str, topic: str = ""):
        super().__init__(pdf_id, user_id, topic)
        self.summary_cache = {}
    
    async def run(self, include_concept_map: bool = True, include_page_refs: bool = True) -> Dict[str, Any]:
        """Generate comprehensive summary for the PDF"""
        try:
            self.log_action("summary_generation_started", {"topic": self.topic})
            
            # Generate summary using optimized learn_tools
            summary_result = await gen_summary(
                pdf_id=self.pdf_id,
                topic_filter=self.topic,
                explanation_level="intern"
            )
            
            if "error" in summary_result:
                self.log_action("summary_generation_failed", {"error": summary_result["error"]})
                return summary_result
            
            # Enhance with additional metadata
            enhanced_summary = {
                "summary": summary_result.get("summary", ""),
                "topic_filter": self.topic,
                "key_points": summary_result.get("key_points", []),
                "estimated_reading_time": summary_result.get("estimated_reading_time", "5 minutes"),
                "concept_map": summary_result.get("concept_map", {}) if include_concept_map else {},
                "page_references": self._generate_page_references() if include_page_refs else [],
                "generated_at": datetime.utcnow().isoformat(),
                "agent_session": self.session_id
            }
            
            # Cache the summary
            self.summary_cache[self.topic] = enhanced_summary
            
            self.log_action("summary_generation_completed", {
                "summary_length": len(enhanced_summary["summary"]),
                "key_points_count": len(enhanced_summary["key_points"])
            })
            
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _generate_page_references(self) -> List[Dict[str, Any]]:
        """Generate page references for key concepts"""
        try:
            # This would integrate with your existing PDF processing
            # For now, return placeholder page references
            return [
                {"concept": "Introduction", "page": 1, "section": "Overview"},
                {"concept": "Key Concepts", "page": 3, "section": "Main Content"},
                {"concept": "Summary", "page": 8, "section": "Conclusion"}
            ]
        except Exception as e:
            logger.warning(f"Page reference generation failed: {e}")
            return []


class DiagnosticAgent(BaseAgent):
    """Adaptive diagnostic agent with plan, validate, repair steps"""
    
    def __init__(self, pdf_id: str, user_id: str, topic: str = ""):
        super().__init__(pdf_id, user_id, topic)
        self.diagnostic_plan = {}
        self.remediation_content = {}
    
    async def run(self, num_questions: int = 10, adaptive: bool = True) -> Dict[str, Any]:
        """Run full diagnostic cycle"""
        try:
            self.log_action("diagnostic_started", {"num_questions": num_questions, "adaptive": adaptive})
            
            # Get baseline mastery
            mastery_before = get_mastery(self.user_id)
            
            # Plan diagnostic: cover skills with lowest mastery first
            if adaptive:
                self.diagnostic_plan = self._create_adaptive_plan(mastery_before, num_questions)
            else:
                self.diagnostic_plan = self._create_standard_plan(num_questions)
            
            # Generate questions using optimized learn_tools
            questions = await gen_quiz(
                pdf_id=self.pdf_id,
                topic=self.topic,
                count=num_questions
            )
            
            # Validate & repair questions if needed
            if not qa_quiz(questions):
                self.log_action("quiz_validation_failed", {"question_count": len(questions)})
                questions = await repair_quiz(
                    quiz_questions=questions,
                    pdf_id=self.pdf_id,
                    topic=self.topic,
                    count=num_questions
                )
            
            # Prepare diagnostic session
            diagnostic_session = {
                "questions": questions,
                "mastery_before": mastery_before,
                "diagnostic_plan": self.diagnostic_plan,
                "session_id": self.session_id,
                "created_at": datetime.utcnow().isoformat(),
                "adaptive": adaptive
            }
            
            self.log_action("diagnostic_ready", {
                "question_count": len(questions),
                "adaptive": adaptive
            })
            
            return diagnostic_session
            
        except Exception as e:
            logger.error(f"Diagnostic generation failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _create_adaptive_plan(self, mastery_data: Dict[str, float], num_questions: int) -> Dict[str, Any]:
        """Create adaptive diagnostic plan based on mastery levels"""
        try:
            # Sort skills by mastery (lowest first)
            sorted_skills = sorted(mastery_data.items(), key=lambda x: x[1])
            
            # Allocate questions based on mastery gaps
            plan = {
                "skill_distribution": {},
                "focus_areas": [],
                "estimated_duration": "15-20 minutes"
            }
            
            # Focus more questions on weaker skills
            for i, (skill, mastery) in enumerate(sorted_skills[:5]):  # Top 5 weakest skills
                if mastery < 0.5:
                    questions_for_skill = max(2, num_questions // 5)
                    plan["skill_distribution"][skill] = questions_for_skill
                    plan["focus_areas"].append({
                        "skill": skill,
                        "current_mastery": mastery,
                        "target_mastery": 0.7,
                        "questions": questions_for_skill
                    })
            
            return plan
            
        except Exception as e:
            logger.warning(f"Adaptive plan creation failed: {e}")
            return {"skill_distribution": {}, "focus_areas": [], "estimated_duration": "15-20 minutes"}
    
    def _create_standard_plan(self, num_questions: int) -> Dict[str, Any]:
        """Create standard diagnostic plan"""
        return {
            "skill_distribution": {"general": num_questions},
            "focus_areas": [{"skill": "general", "questions": num_questions}],
            "estimated_duration": "15-20 minutes"
        }
    
    async def process_results(self, user_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process diagnostic results and update mastery"""
        try:
            logger.debug(f"process_results called with user_answers: {user_answers}")
            logger.debug(f"user_answers type: {type(user_answers)}")
            logger.debug(f"user_answers length: {len(user_answers) if user_answers else 'None'}")
            self.log_action("results_processing_started", {"answer_count": len(user_answers)})
            
            # Calculate results
            results = self._calculate_results(user_answers)
            logger.debug(f"Calculated results: {results}")
            
            # Update mastery using optimized mastery system
            mastery_update = update_mastery(self.user_id, {self.topic: results["overall_score"]})
            logger.debug(f"Mastery update: {mastery_update}")
            
            # Generate remediation recommendations
            remediation = await self._generate_remediation(results)
            logger.debug(f"Remediation: {remediation}")
            
            # Prepare comprehensive results
            diagnostic_results = {
                "results": results,
                "mastery_update": mastery_update,
                "remediation": remediation,
                "session_id": self.session_id,
                "completed_at": datetime.utcnow().isoformat(),
                "next_steps": self._generate_next_steps(results, mastery_update)
            }
            
            self.log_action("results_processing_completed", {
                "overall_score": results["overall_score"],
                "mastery_change": mastery_update.get("mastery_change", 0) if mastery_update else 0
            })
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"Results processing failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _calculate_results(self, user_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate diagnostic results from user answers"""
        try:
            logger.debug(f"Calculating results for user_answers: {user_answers}")
            total_questions = len(user_answers)
            correct_answers = 0
            
            for answer in user_answers:
                logger.debug(f"Processing answer: {answer}")
                if answer.get("is_correct", False):
                    correct_answers += 1
            
            overall_score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            return {
                "overall_score": round(overall_score, 2),
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "incorrect_answers": total_questions - correct_answers,
                "accuracy_percentage": round(overall_score, 1),
                "performance_level": self._get_performance_level(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Results calculation failed: {e}")
            return {"overall_score": 0, "total_questions": 0, "correct_answers": 0}
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Satisfactory"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Requires Remediation"
    
    async def _generate_remediation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate remediation content based on results"""
        try:
            if results["overall_score"] >= 80:
                return {"needed": False, "message": "Great performance! Continue with advanced topics."}
            
            # Generate remedial flashcards
            logger.debug(f"Generating flashcards for pdf_id: {self.pdf_id}, topic: {self.topic}")
            remedial_flashcards = await gen_flashcards(
                pdf_id=self.pdf_id,
                topic=self.topic,
                count=5
            )
            logger.debug(f"Generated flashcards: {remedial_flashcards}")
            
            # Generate remedial quiz
            logger.debug(f"Generating quiz for pdf_id: {self.pdf_id}, topic: {self.topic}")
            remedial_quiz = await gen_quiz(
                pdf_id=self.pdf_id,
                topic=self.topic,
                count=3
            )
            logger.debug(f"Generated quiz: {remedial_quiz}")
            
            return {
                "needed": True,
                "message": "Focus on these areas to improve your understanding.",
                "flashcards": remedial_flashcards,
                "quiz": remedial_quiz,
                "focus_topics": self._identify_focus_topics(results)
            }
            
        except Exception as e:
            logger.error(f"Remediation generation failed: {e}")
            return {"needed": False, "message": "Remediation generation failed."}
    
    def _identify_focus_topics(self, results: Dict[str, Any]) -> List[str]:
        """Identify topics that need focus based on results"""
        try:
            # This would analyze specific question performance
            # For now, return general focus areas
            if results["overall_score"] < 60:
                return ["Basic concepts", "Fundamental principles", "Core terminology"]
            elif results["overall_score"] < 80:
                return ["Intermediate concepts", "Application examples", "Problem-solving"]
            else:
                return ["Advanced topics", "Complex scenarios", "Integration concepts"]
        except Exception as e:
            logger.warning(f"Focus topic identification failed: {e}")
            return ["General review"]
    
    def _generate_next_steps(self, results: Dict[str, Any], mastery_update: Dict[str, Any]) -> List[str]:
        """Generate next steps for the user"""
        try:
            next_steps = []
            
            # Debug logging
            logger.debug(f"Next steps generation - results: {results}, mastery_update: {mastery_update}")
            
            if not results or "overall_score" not in results:
                logger.warning("Invalid results structure for next steps generation")
                return ["Continue learning and practicing"]
            
            if results["overall_score"] < 70:
                next_steps.extend([
                    "Review the remedial flashcards",
                    "Take the remedial quiz",
                    "Focus on identified weak areas"
                ])
            else:
                next_steps.extend([
                    "Continue with advanced topics",
                    "Practice with more challenging questions",
                    "Apply knowledge to real-world scenarios"
                ])
            
            # Add mastery-specific recommendations
            if mastery_update and mastery_update.get("next_milestone"):
                milestone = mastery_update["next_milestone"]
                next_steps.append(f"Work toward {milestone['description']} (need {milestone['points_needed']} more points)")
            
            return next_steps
            
        except Exception as e:
            logger.warning(f"Next steps generation failed: {e}")
            return ["Continue learning and practicing"]


class AgentRouter:
    """Intelligent router that chooses which agent to invoke based on user intent"""
    
    def __init__(self):
        self.intent_patterns = {
            "summary": ["summary", "summarize", "tl;dr", "overview", "key points"],
            "diagnostic": ["diagnostic", "test", "quiz me", "practice", "assessment", "evaluate"],
            "flashcards": ["flashcards", "cards", "study cards", "memorize"],
            "explanation": ["explain", "clarify", "help me understand", "what is"],
            "workflow": ["workflow", "process", "steps", "how to", "procedure"]
        }
        self.confidence_threshold = 0.15  # Lower threshold for better detection
    
    def detect_intent(self, message: str, pdf_present: bool = False) -> Dict[str, Any]:
        """Detect user intent from message and context"""
        try:
            message_lower = message.lower().strip()
            
            # Calculate confidence scores for each intent
            intent_scores = {}
            for intent, patterns in self.intent_patterns.items():
                score = 0
                for pattern in patterns:
                    if pattern in message_lower:
                        score += 1
                    # Also check for variations like "want a summary", "need summary", etc.
                    if any(variation in message_lower for variation in [f"want {pattern}", f"need {pattern}", f"get {pattern}", f"create {pattern}"]):
                        score += 0.5
                
                # Calculate final score with better weighting
                if score > 0:
                    # Use a more lenient scoring: base score + bonus for exact matches
                    base_score = score / len(patterns)
                    # Bonus for having multiple patterns or variations
                    if score >= 2:
                        base_score += 0.2
                    intent_scores[intent] = min(1.0, base_score)
            
            # Find highest scoring intent
            if intent_scores:
                best_intent = max(intent_scores.items(), key=lambda x: x[1])
                confidence = best_intent[1]
                
                if confidence >= self.confidence_threshold:
                    return {
                        "intent": best_intent[0],
                        "confidence": confidence,
                        "message": message,
                        "pdf_present": pdf_present
                    }
            
            # Check for empty message with PDF context
            if not message_lower and pdf_present:
                return {
                    "intent": "diagnostic",
                    "confidence": 0.8,
                    "message": message,
                    "pdf_present": pdf_present,
                    "reason": "Default diagnostic for PDF upload"
                }
            
            # Ambiguous or unclear intent
            return {
                "intent": "clarify",
                "confidence": 0.0,
                "message": message,
                "pdf_present": pdf_present,
                "suggestions": self._generate_clarification_suggestions()
            }
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return {
                "intent": "clarify",
                "confidence": 0.0,
                "message": message,
                "pdf_present": pdf_present,
                "error": str(e)
            }
    
    def _generate_clarification_suggestions(self) -> List[str]:
        """Generate suggestions for clarifying user intent"""
        return [
            "What would you like me to help you with?",
            "I can create summaries, quizzes, flashcards, or explain concepts.",
            "Try asking for a 'summary', 'quiz', or 'flashcards'.",
            "Or ask me to explain something specific."
        ]
    
    def route_request(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route the request to appropriate agent or action"""
        try:
            routing_plan = {
                "summary": {
                    "agent": "SummarizerAgent",
                    "action": "generate_summary",
                    "description": "Generate topic-filtered summary with concept map",
                    "estimated_time": "2-3 minutes"
                },
                "diagnostic": {
                    "agent": "DiagnosticAgent",
                    "action": "run_diagnostic",
                    "description": "Run adaptive diagnostic test with remediation",
                    "estimated_time": "15-20 minutes"
                },
                "flashcards": {
                    "agent": "ContentGenerator",
                    "action": "generate_flashcards",
                    "description": "Create study flashcards for the topic",
                    "estimated_time": "1-2 minutes"
                },
                "explanation": {
                    "agent": "ExplanationAgent",
                    "action": "explain_concept",
                    "description": "Provide detailed explanation of concepts",
                    "estimated_time": "3-5 minutes"
                },
                "workflow": {
                    "agent": "WorkflowAgent",
                    "action": "create_workflow",
                    "description": "Generate step-by-step workflow or process",
                    "estimated_time": "2-4 minutes"
                }
            }
            
            if intent in routing_plan:
                route = routing_plan[intent].copy()
                route["intent"] = intent
                route["context"] = context
                route["routing_timestamp"] = datetime.utcnow().isoformat()
                
                return route
            else:
                return {
                    "intent": intent,
                    "error": "Unknown intent",
                    "available_intents": list(routing_plan.keys()),
                    "context": context
                }
                
        except Exception as e:
            logger.error(f"Request routing failed: {e}")
            return {
                "intent": intent,
                "error": str(e),
                "context": context
            }
    
    def get_agent_recommendations(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized agent recommendations based on user history and context"""
        try:
            recommendations = []
            
            # Get user mastery to recommend appropriate actions
            mastery_data = get_mastery(user_id)
            
            # Recommend diagnostic if mastery is low
            if mastery_data:
                avg_mastery = sum(mastery_data.values()) / len(mastery_data)
                if avg_mastery < 0.6:
                    recommendations.append({
                        "agent": "DiagnosticAgent",
                        "priority": "high",
                        "reason": "Low mastery detected - assessment recommended",
                        "estimated_benefit": "Identify weak areas and create learning plan"
                    })
            
            # Recommend summary for new topics
            if context and context.get("new_topic"):
                recommendations.append({
                    "agent": "SummarizerAgent",
                    "priority": "medium",
                    "reason": "New topic detected - summary would be helpful",
                    "estimated_benefit": "Get overview and key concepts quickly"
                })
            
            # Recommend flashcards for active learning
            recommendations.append({
                "agent": "ContentGenerator",
                "priority": "medium",
                "reason": "Active learning through flashcards",
                "estimated_benefit": "Improve retention and recall"
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Agent recommendations failed: {e}")
            return []


# Convenience functions for external use
async def create_summarizer_agent(pdf_id: str, user_id: str, topic: str = "") -> SummarizerAgent:
    """Create a SummarizerAgent instance"""
    return SummarizerAgent(pdf_id, user_id, topic)

async def create_diagnostic_agent(pdf_id: str, user_id: str, topic: str = "") -> DiagnosticAgent:
    """Create a DiagnosticAgent instance"""
    return DiagnosticAgent(pdf_id, user_id, topic)

def create_agent_router() -> AgentRouter:
    """Create an AgentRouter instance"""
    return AgentRouter()
