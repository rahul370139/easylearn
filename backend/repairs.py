"""
Repair System for TrainPI Agents
Fixes flawed learning content when validation fails, using existing TrainPI infrastructure
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import uuid
from datetime import datetime
import asyncio

# Import existing functionality
from learn_tools import gen_flashcards, gen_quiz
from validators import qa_flashcards, qa_quiz, get_flashcard_errors, get_quiz_errors


class ContentRepairer:
    """Base class for content repair with TrainPI integration"""
    
    def __init__(self):
        self.repair_strategies = {}
        self.max_repair_attempts = 3
    
    def repair(self, content: Any, pdf_id: str, topic: str = "") -> Any:
        """Base repair method - should be overridden"""
        raise NotImplementedError("Subclasses must implement repair method")
    
    def can_repair(self, content: Any) -> bool:
        """Check if content can be repaired"""
        raise NotImplementedError("Subclasses must implement can_repair method")


class FlashcardRepairer(ContentRepairer):
    """Repairs flawed flashcards using TrainPI generation functions"""
    
    def __init__(self):
        super().__init__()
        self.repair_strategies = {
            "missing_fields": self._repair_missing_fields,
            "length_issues": self._repair_length_issues,
            "duplicates": self._repair_duplicates,
            "quality_issues": self._repair_quality_issues
        }
    
    def can_repair(self, flashcards: List[Dict[str, Any]]) -> bool:
        """Check if flashcards can be repaired"""
        try:
            if not flashcards:
                return False
            
            # Check if we have enough information to attempt repair
            repairable_count = 0
            for flashcard in flashcards:
                if self._is_repairable(flashcard):
                    repairable_count += 1
            
            # Need at least 50% to be repairable
            return repairable_count >= len(flashcards) * 0.5
            
        except Exception as e:
            logger.error(f"Flashcard repairability check failed: {e}")
            return False
    
    async def repair(self, flashcards: List[Dict[str, Any]], pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
        """Repair flawed flashcards using TrainPI generation"""
        try:
            if not self.can_repair(flashcards):
                logger.info("Flashcards cannot be repaired, generating new ones using TrainPI")
                return await self._generate_new_flashcards(pdf_id, topic, count)
            
            repaired_flashcards = []
            
            for flashcard in flashcards:
                if self._is_repairable(flashcard):
                    repaired = self._repair_single_flashcard(flashcard)
                    if repaired:
                        repaired_flashcards.append(repaired)
                else:
                    # Keep good flashcards
                    repaired_flashcards.append(flashcard)
            
            # Fill in missing flashcards if needed
            while len(repaired_flashcards) < count:
                new_flashcard = self._generate_single_flashcard(pdf_id, topic)
                if new_flashcard:
                    repaired_flashcards.append(new_flashcard)
            
            logger.info(f"Repaired {len(repaired_flashcards)} flashcards")
            return repaired_flashcards[:count]
            
        except Exception as e:
            logger.error(f"Flashcard repair failed: {e}")
            return await self._generate_new_flashcards(pdf_id, topic, count)
    
    def _is_repairable(self, flashcard: Dict[str, Any]) -> bool:
        """Check if a single flashcard can be repaired"""
        try:
            # Check if it has at least one valid field
            has_front = bool(flashcard.get("front", "").strip())
            has_back = bool(flashcard.get("back", "").strip())
            
            # Can repair if at least one field is valid
            return has_front or has_back
            
        except Exception as e:
            logger.warning(f"Repairability check failed: {e}")
            return False
    
    def _repair_single_flashcard(self, flashcard: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Repair a single flashcard"""
        try:
            repaired = flashcard.copy()
            
            # Repair missing fields
            if not repaired.get("front"):
                repaired["front"] = self._generate_front_from_back(repaired.get("back", ""))
            
            if not repaired.get("back"):
                repaired["back"] = self._generate_back_from_front(repaired.get("front", ""))
            
            # Repair length issues
            repaired = self._repair_length_issues(repaired)
            
            # Add metadata
            repaired["id"] = repaired.get("id") or str(uuid.uuid4())
            repaired["repaired_at"] = datetime.utcnow().isoformat()
            repaired["repaired"] = True
            
            return repaired
            
        except Exception as e:
            logger.error(f"Single flashcard repair failed: {e}")
            return None
    
    def _repair_missing_fields(self, flashcard: Dict[str, Any]) -> Dict[str, Any]:
        """Repair missing fields in a flashcard"""
        try:
            repaired = flashcard.copy()
            
            if not repaired.get("front") and repaired.get("back"):
                repaired["front"] = f"What is {repaired['back']}?"
            
            if not repaired.get("back") and repaired.get("front"):
                repaired["back"] = "Answer to be provided"
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Missing fields repair failed: {e}")
            return flashcard
    
    def _repair_length_issues(self, flashcard: Dict[str, Any]) -> Dict[str, Any]:
        """Repair length issues in a flashcard"""
        try:
            repaired = flashcard.copy()
            
            # Repair front length
            front = repaired.get("front", "")
            if len(front) < 10:
                repaired["front"] = f"Can you explain: {front}"
            elif len(front) > 200:
                repaired["front"] = front[:200] + "..."
            
            # Repair back length
            back = repaired.get("back", "")
            if len(back) < 5:
                repaired["back"] = f"Answer: {back}"
            elif len(back) > 100:
                repaired["back"] = back[:100] + "..."
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Length issues repair failed: {e}")
            return flashcard
    
    def _repair_duplicates(self, flashcards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate flashcards"""
        try:
            seen_fronts = set()
            unique_flashcards = []
            
            for flashcard in flashcards:
                front = flashcard.get("front", "").lower().strip()
                if front not in seen_fronts:
                    seen_fronts.add(front)
                    unique_flashcards.append(flashcard)
            
            return unique_flashcards
            
        except Exception as e:
            logger.warning(f"Duplicate repair failed: {e}")
            return flashcards
    
    def _repair_quality_issues(self, flashcard: Dict[str, Any]) -> Dict[str, Any]:
        """Repair quality issues in a flashcard"""
        try:
            repaired = flashcard.copy()
            
            # Clean up whitespace
            if repaired.get("front"):
                repaired["front"] = repaired["front"].strip()
            
            if repaired.get("back"):
                repaired["back"] = repaired["back"].strip()
            
            # Ensure proper punctuation
            if repaired.get("front") and not repaired["front"].endswith("?"):
                repaired["front"] += "?"
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Quality issues repair failed: {e}")
            return flashcard
    
    def _generate_front_from_back(self, back: str) -> str:
        """Generate a front from a back"""
        try:
            if not back:
                return "What is this concept?"
            
            # Simple front generation
            if back.lower().startswith(("the ", "a ", "an ")):
                return f"What is {back}?"
            else:
                return f"What is {back}?"
                
        except Exception as e:
            logger.warning(f"Front generation failed: {e}")
            return "What is this concept?"
    
    def _generate_back_from_front(self, front: str) -> str:
        """Generate a back from a front"""
        try:
            if not front:
                return "Answer to be provided"
            
            # Simple back generation
            if front.lower().startswith("what is "):
                return front[8:].rstrip("?")
            else:
                return "Answer to be provided"
                
        except Exception as e:
            logger.warning(f"Back generation failed: {e}")
            return "Answer to be provided"
    
    async def _generate_new_flashcards(self, pdf_id: str, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate completely new flashcards using TrainPI functions"""
        try:
            # Use TrainPI flashcard generation
            flashcards = await gen_flashcards(pdf_id, topic, count)
            
            if flashcards:
                # Mark as regenerated
                for flashcard in flashcards:
                    flashcard["regenerated"] = True
                    flashcard["regenerated_at"] = datetime.utcnow().isoformat()
                
                return flashcards
            else:
                # Fallback to simple flashcards
                return self._generate_fallback_flashcards(topic, count)
            
        except Exception as e:
            logger.error(f"New flashcard generation failed: {e}")
            return self._generate_fallback_flashcards(topic, count)
    
    def _generate_single_flashcard(self, pdf_id: str, topic: str) -> Optional[Dict[str, Any]]:
        """Generate a single flashcard"""
        try:
            # Simple fallback flashcard
            return {
                "id": str(uuid.uuid4()),
                "front": f"What is {topic}?",
                "back": f"{topic} is a concept related to the current topic.",
                "topic": topic,
                "generated_at": datetime.utcnow().isoformat(),
                "fallback": True
            }
        except Exception as e:
            logger.error(f"Single flashcard generation failed: {e}")
            return None
    
    def _generate_fallback_flashcards(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate fallback flashcards when all else fails"""
        try:
            fallback_flashcards = []
            
            for i in range(count):
                flashcard = {
                    "id": str(uuid.uuid4()),
                    "front": f"Question {i+1} about {topic}",
                    "back": f"Answer {i+1} about {topic}",
                    "topic": topic,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True
                }
                fallback_flashcards.append(flashcard)
            
            return fallback_flashcards
            
        except Exception as e:
            logger.error(f"Fallback flashcard generation failed: {e}")
            return []


class QuizRepairer(ContentRepairer):
    """Repairs flawed quiz questions using TrainPI generation functions"""
    
    def __init__(self):
        super().__init__()
        self.repair_strategies = {
            "missing_fields": self._repair_missing_fields,
            "length_issues": self._repair_length_issues,
            "option_issues": self._repair_option_issues,
            "duplicates": self._repair_duplicates
        }
    
    def can_repair(self, quiz_questions: List[Dict[str, Any]]) -> bool:
        """Check if quiz questions can be repaired"""
        try:
            if not quiz_questions:
                return False
            
            # Check if we have enough information to attempt repair
            repairable_count = 0
            for question in quiz_questions:
                if self._is_repairable(question):
                    repairable_count += 1
            
            # Need at least 50% to be repairable
            return repairable_count >= len(quiz_questions) * 0.5
            
        except Exception as e:
            logger.error(f"Quiz repairability check failed: {e}")
            return False
    
    async def repair(self, quiz_questions: List[Dict[str, Any]], pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
        """Repair flawed quiz questions using TrainPI generation"""
        try:
            if not self.can_repair(quiz_questions):
                logger.info("Quiz questions cannot be repaired, generating new ones using TrainPI")
                return await self._generate_new_questions(pdf_id, topic, count)
            
            repaired_questions = []
            
            for question in quiz_questions:
                if self._is_repairable(question):
                    repaired = self._repair_single_question(question)
                    if repaired:
                        repaired_questions.append(repaired)
                else:
                    # Keep good questions
                    repaired_questions.append(question)
            
            # Fill in missing questions if needed
            while len(repaired_questions) < count:
                new_question = self._generate_single_question(pdf_id, topic)
                if new_question:
                    repaired_questions.append(new_question)
            
            logger.info(f"Repaired {len(repaired_questions)} quiz questions")
            return repaired_questions[:count]
            
        except Exception as e:
            logger.error(f"Quiz repair failed: {e}")
            return await self._generate_new_questions(pdf_id, topic, count)
    
    def _is_repairable(self, question: Dict[str, Any]) -> bool:
        """Check if a single question can be repaired"""
        try:
            # Check if it has at least two valid fields
            has_question = bool(question.get("question", "").strip())
            has_options = bool(question.get("options")) and len(question.get("options", [])) >= 2
            has_answer_idx = question.get("answer_idx") is not None
            
            # Can repair if at least two fields are valid
            valid_fields = sum([has_question, has_options, has_answer_idx])
            return valid_fields >= 2
            
        except Exception as e:
            logger.warning(f"Repairability check failed: {e}")
            return False
    
    def _repair_single_question(self, question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Repair a single quiz question"""
        try:
            repaired = question.copy()
            
            # Repair missing fields
            if not repaired.get("question"):
                repaired["question"] = self._generate_question_from_options(repaired.get("options", []))
            
            if not repaired.get("options") or len(repaired.get("options", [])) < 4:
                repaired["options"] = self._generate_options_from_question(repaired.get("question", ""))
            
            if repaired.get("answer_idx") is None:
                repaired["answer_idx"] = self._select_correct_answer_idx(repaired.get("options", []))
            
            # Repair other issues
            repaired = self._repair_length_issues(repaired)
            repaired = self._repair_option_issues(repaired)
            
            # Add metadata
            repaired["id"] = repaired.get("id") or str(uuid.uuid4())
            repaired["repaired_at"] = datetime.utcnow().isoformat()
            repaired["repaired"] = True
            
            return repaired
            
        except Exception as e:
            logger.error(f"Single question repair failed: {e}")
            return None
    
    def _repair_missing_fields(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Repair missing fields in a question"""
        try:
            repaired = question.copy()
            
            if not repaired.get("question") and repaired.get("options"):
                repaired["question"] = "Which of the following is correct?"
            
            if not repaired.get("options") and repaired.get("question"):
                repaired["options"] = ["Option A", "Option B", "Option C", "Option D"]
            
            if repaired.get("answer_idx") is None and repaired.get("options"):
                repaired["answer_idx"] = 0
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Missing fields repair failed: {e}")
            return question
    
    def _repair_length_issues(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Repair length issues in a question"""
        try:
            repaired = question.copy()
            
            # Repair question length
            question_text = repaired.get("question", "")
            if len(question_text) < 15:
                repaired["question"] = f"Question: {question_text}"
            elif len(question_text) > 300:
                repaired["question"] = question_text[:300] + "..."
            
            # Repair option lengths
            options = repaired.get("options", [])
            repaired_options = []
            for option in options:
                if len(option) < 5:
                    repaired_options.append(f"Option: {option}")
                elif len(option) > 150:
                    repaired_options.append(option[:150] + "...")
                else:
                    repaired_options.append(option)
            
            repaired["options"] = repaired_options
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Length issues repair failed: {e}")
            return question
    
    def _repair_option_issues(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Repair option-related issues"""
        try:
            repaired = question.copy()
            
            options = repaired.get("options", [])
            
            # Ensure exactly 4 options (TrainPI standard)
            while len(options) < 4:
                options.append(f"Option {chr(65 + len(options))}")
            
            if len(options) > 4:
                options = options[:4]
            
            # Remove duplicates
            unique_options = []
            seen = set()
            for option in options:
                option_clean = option.strip().lower()
                if option_clean not in seen:
                    seen.add(option_clean)
                    unique_options.append(option)
            
            # Ensure we still have 4 options
            while len(unique_options) < 4:
                unique_options.append(f"Option {chr(65 + len(unique_options))}")
            
            repaired["options"] = unique_options
            
            # Ensure answer_idx is valid
            if repaired.get("answer_idx") is None or repaired["answer_idx"] >= len(unique_options):
                repaired["answer_idx"] = 0
            
            return repaired
            
        except Exception as e:
            logger.warning(f"Option issues repair failed: {e}")
            return question
    
    def _repair_duplicates(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate questions"""
        try:
            seen_questions = set()
            unique_questions = []
            
            for question in questions:
                question_text = question.get("question", "").lower().strip()
                if question_text not in seen_questions:
                    seen_questions.add(question_text)
                    unique_questions.append(question)
            
            return unique_questions
            
        except Exception as e:
            logger.warning(f"Duplicate repair failed: {e}")
            return questions
    
    def _generate_question_from_options(self, options: List[str]) -> str:
        """Generate a question from options"""
        try:
            if not options:
                return "Which of the following is correct?"
            
            return f"Which of the following is correct?"
            
        except Exception as e:
            logger.warning(f"Question generation from options failed: {e}")
            return "Which of the following is correct?"
    
    def _generate_options_from_question(self, question: str) -> List[str]:
        """Generate options from a question"""
        try:
            if not question:
                return ["Option A", "Option B", "Option C", "Option D"]
            
            # Simple option generation
            return ["Option A", "Option B", "Option C", "Option D"]
            
        except Exception as e:
            logger.warning(f"Options generation failed: {e}")
            return ["Option A", "Option B", "Option C", "Option D"]
    
    def _select_correct_answer_idx(self, options: List[str]) -> int:
        """Select a correct answer index from options"""
        try:
            if not options:
                return 0
            
            # Simple selection - first option
            return 0
            
        except Exception as e:
            logger.warning(f"Correct answer selection failed: {e}")
            return 0
    
    async def _generate_new_questions(self, pdf_id: str, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate completely new quiz questions using TrainPI functions"""
        try:
            # Use TrainPI quiz generation
            questions = await gen_quiz(pdf_id, topic, count)
            
            if questions:
                # Mark as regenerated
                for question in questions:
                    question["regenerated"] = True
                    question["regenerated_at"] = datetime.utcnow().isoformat()
                
                return questions
            else:
                # Fallback to simple questions
                return self._generate_fallback_questions(topic, count)
            
        except Exception as e:
            logger.error(f"New question generation failed: {e}")
            return self._generate_fallback_questions(topic, count)
    
    def _generate_single_question(self, pdf_id: str, topic: str) -> Optional[Dict[str, Any]]:
        """Generate a single quiz question"""
        try:
            # Simple fallback question
            return {
                "id": str(uuid.uuid4()),
                "question": f"What is {topic}?",
                "options": [f"Option A about {topic}", f"Option B about {topic}", f"Option C about {topic}", f"Option D about {topic}"],
                "answer_idx": 0,
                "topic": topic,
                "generated_at": datetime.utcnow().isoformat(),
                "fallback": True
            }
        except Exception as e:
            logger.error(f"Single question generation failed: {e}")
            return None
    
    def _generate_fallback_questions(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate fallback questions when all else fails"""
        try:
            fallback_questions = []
            
            for i in range(count):
                question = {
                    "id": str(uuid.uuid4()),
                    "question": f"Question {i+1} about {topic}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer_idx": 0,
                    "topic": topic,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True
                }
                fallback_questions.append(question)
            
            return fallback_questions
            
        except Exception as e:
            logger.error(f"Fallback question generation failed: {e}")
            return []


# Global repairer instances
flashcard_repairer = FlashcardRepairer()
quiz_repairer = QuizRepairer()

# Convenience functions for external use (matching your specification)
async def repair_flashcards(flashcards: List[Dict[str, Any]], pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
    """Repair flawed flashcards using TrainPI generation"""
    return await flashcard_repairer.repair(flashcards, pdf_id, topic, count)

async def repair_quiz(quiz_questions: List[Dict[str, Any]], pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
    """Repair flawed quiz questions using TrainPI generation"""
    return await quiz_repairer.repair(quiz_questions, pdf_id, topic, count)

def can_repair_flashcards(flashcards: List[Dict[str, Any]]) -> bool:
    """Check if flashcards can be repaired"""
    return flashcard_repairer.can_repair(flashcards)

def can_repair_quiz(quiz_questions: List[Dict[str, Any]]) -> bool:
    """Check if quiz questions can be repaired"""
    return quiz_repairer.can_repair(quiz_questions)
