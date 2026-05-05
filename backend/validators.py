"""
Validators for TrainPI Agents
Quality assurance for generated learning content with existing system integration
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import re


class ContentValidator:
    """Base class for content validation with TrainPI integration"""
    
    def __init__(self):
        self.validation_rules = {}
        self.quality_thresholds = {
            "min_length": 10,
            "max_length": 500,
            "min_options": 2,
            "max_options": 5
        }
    
    def validate(self, content: Any) -> bool:
        """Base validation method - should be overridden"""
        raise NotImplementedError("Subclasses must implement validate method")
    
    def get_validation_errors(self, content: Any) -> List[str]:
        """Get list of validation errors - should be overridden"""
        raise NotImplementedError("Subclasses must implement get_validation_errors method")


class FlashcardValidator(ContentValidator):
    """Validates flashcard quality and structure for TrainPI system"""
    
    def __init__(self):
        super().__init__()
        self.validation_rules = {
            "question_required": True,
            "answer_required": True,
            "min_question_length": 10,
            "max_question_length": 200,
            "min_answer_length": 5,
            "max_answer_length": 100,
            "no_duplicate_questions": True,
            "use_front_back_format": True  # TrainPI uses front/back format
        }
    
    def validate(self, flashcards: List[Dict[str, Any]]) -> bool:
        """Validate a list of flashcards using TrainPI format"""
        try:
            if not flashcards:
                return False
            
            for flashcard in flashcards:
                if not self._validate_single_flashcard(flashcard):
                    return False
            
            # Check for duplicates if required
            if self.validation_rules["no_duplicate_questions"]:
                questions = [f.get("front", "").lower().strip() for f in flashcards]
                if len(questions) != len(set(questions)):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Flashcard validation failed: {e}")
            return False
    
    def _validate_single_flashcard(self, flashcard: Dict[str, Any]) -> bool:
        """Validate a single flashcard in TrainPI format"""
        try:
            # Check required fields (TrainPI uses front/back)
            if not flashcard.get("front") or not flashcard.get("back"):
                return False
            
            front = flashcard["front"].strip()
            back = flashcard["back"].strip()
            
            # Check lengths
            if (len(front) < self.validation_rules["min_question_length"] or
                len(front) > self.validation_rules["max_question_length"]):
                return False
            
            if (len(back) < self.validation_rules["min_answer_length"] or
                len(back) > self.validation_rules["max_answer_length"]):
                return False
            
            # Check for empty or whitespace-only content
            if not front or not back:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Single flashcard validation failed: {e}")
            return False
    
    def get_validation_errors(self, flashcards: List[Dict[str, Any]]) -> List[str]:
        """Get detailed validation errors for flashcards"""
        errors = []
        
        try:
            if not flashcards:
                errors.append("No flashcards provided")
                return errors
            
            for i, flashcard in enumerate(flashcards):
                flashcard_errors = self._get_single_flashcard_errors(flashcard, i)
                errors.extend(flashcard_errors)
            
            # Check for duplicates
            if self.validation_rules["no_duplicate_questions"]:
                questions = [f.get("front", "").lower().strip() for f in flashcards]
                duplicates = [q for q in set(questions) if questions.count(q) > 1]
                if duplicates:
                    errors.append(f"Duplicate questions found: {duplicates}")
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return errors
    
    def _get_single_flashcard_errors(self, flashcard: Dict[str, Any], index: int) -> List[str]:
        """Get validation errors for a single flashcard"""
        errors = []
        
        try:
            # Check required fields
            if not flashcard.get("front"):
                errors.append(f"Flashcard {index + 1}: Missing front (question)")
            if not flashcard.get("back"):
                errors.append(f"Flashcard {index + 1}: Missing back (answer)")
            
            front = flashcard.get("front", "").strip()
            back = flashcard.get("back", "").strip()
            
            # Check front length
            if front:
                if len(front) < self.validation_rules["min_question_length"]:
                    errors.append(f"Flashcard {index + 1}: Front too short (min {self.validation_rules['min_question_length']} chars)")
                elif len(front) > self.validation_rules["max_question_length"]:
                    errors.append(f"Flashcard {index + 1}: Front too long (max {self.validation_rules['max_question_length']} chars)")
            
            # Check back length
            if back:
                if len(back) < self.validation_rules["min_answer_length"]:
                    errors.append(f"Flashcard {index + 1}: Back too short (min {self.validation_rules['min_answer_length']} chars)")
                elif len(back) > self.validation_rules["max_answer_length"]:
                    errors.append(f"Flashcard {index + 1}: Back too long (max {self.validation_rules['max_answer_length']} chars)")
            
            # Check for empty content
            if not front:
                errors.append(f"Flashcard {index + 1}: Empty front")
            if not back:
                errors.append(f"Flashcard {index + 1}: Empty back")
            
            return errors
            
        except Exception as e:
            errors.append(f"Flashcard {index + 1}: Validation error - {str(e)}")
            return errors


class QuizValidator(ContentValidator):
    """Validates quiz question quality and structure for TrainPI system"""
    
    def __init__(self):
        super().__init__()
        self.validation_rules = {
            "question_required": True,
            "options_required": True,
            "correct_answer_required": True,
            "min_question_length": 15,
            "max_question_length": 300,
            "min_options": 4,  # TrainPI uses 4 options
            "max_options": 4,  # TrainPI uses 4 options
            "min_option_length": 5,
            "max_option_length": 150,
            "no_duplicate_options": True,
            "correct_answer_in_options": True,
            "use_answer_idx": True  # TrainPI uses answer_idx
        }
    
    def validate(self, quiz_questions: List[Dict[str, Any]]) -> bool:
        """Validate a list of quiz questions using TrainPI format"""
        try:
            if not quiz_questions:
                return False
            
            for question in quiz_questions:
                if not self._validate_single_question(question):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Quiz validation failed: {e}")
            return False
    
    def _validate_single_question(self, question: Dict[str, Any]) -> bool:
        """Validate a single quiz question in TrainPI format"""
        try:
            # Check required fields
            if not question.get("question") or not question.get("options") or question.get("answer_idx") is None:
                return False
            
            question_text = question["question"].strip()
            options = question.get("options", [])
            answer_idx = question.get("answer_idx")
            
            # Check question length
            if (len(question_text) < self.validation_rules["min_question_length"] or
                len(question_text) > self.validation_rules["max_question_length"]):
                return False
            
            # Check options
            if not isinstance(options, list) or len(options) != 4:  # TrainPI uses exactly 4 options
                return False
            
            # Validate each option
            for option in options:
                if not self._validate_option(option):
                    return False
            
            # Check answer_idx is valid
            if not isinstance(answer_idx, int) or answer_idx < 0 or answer_idx >= 4:
                return False
            
            # Check for duplicate options
            if self.validation_rules["no_duplicate_options"]:
                option_texts = [opt.strip().lower() for opt in options]
                if len(option_texts) != len(set(option_texts)):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Single question validation failed: {e}")
            return False
    
    def _validate_option(self, option: str) -> bool:
        """Validate a single option"""
        try:
            if not isinstance(option, str):
                return False
            
            option = option.strip()
            
            if (len(option) < self.validation_rules["min_option_length"] or
                len(option) > self.validation_rules["max_option_length"]):
                return False
            
            if not option:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Option validation failed: {e}")
            return False
    
    def get_validation_errors(self, quiz_questions: List[Dict[str, Any]]) -> List[str]:
        """Get detailed validation errors for quiz questions"""
        errors = []
        
        try:
            if not quiz_questions:
                errors.append("No quiz questions provided")
                return errors
            
            for i, question in enumerate(quiz_questions):
                question_errors = self._get_single_question_errors(question, i)
                errors.extend(question_errors)
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return errors
    
    def _get_single_question_errors(self, question: Dict[str, Any], index: int) -> List[str]:
        """Get validation errors for a single quiz question"""
        errors = []
        
        try:
            # Check required fields
            if not question.get("question"):
                errors.append(f"Question {index + 1}: Missing question text")
            if not question.get("options"):
                errors.append(f"Question {index + 1}: Missing options")
            if question.get("answer_idx") is None:
                errors.append(f"Question {index + 1}: Missing answer_idx")
            
            question_text = question.get("question", "").strip()
            options = question.get("options", [])
            answer_idx = question.get("answer_idx")
            
            # Check question length
            if question_text:
                if len(question_text) < self.validation_rules["min_question_length"]:
                    errors.append(f"Question {index + 1}: Question too short (min {self.validation_rules['min_question_length']} chars)")
                elif len(question_text) > self.validation_rules["max_question_length"]:
                    errors.append(f"Question {index + 1}: Question too long (max {self.validation_rules['max_question_length']} chars)")
            
            # Check options
            if options:
                if not isinstance(options, list):
                    errors.append(f"Question {index + 1}: Options must be a list")
                elif len(options) != 4:
                    errors.append(f"Question {index + 1}: Must have exactly 4 options (got {len(options)})")
                else:
                    # Validate individual options
                    for j, option in enumerate(options):
                        option_errors = self._get_option_errors(option, j, index)
                        errors.extend(option_errors)
                    
                    # Check for duplicate options
                    if self.validation_rules["no_duplicate_options"]:
                        option_texts = [opt.strip().lower() for opt in options if isinstance(opt, str)]
                        duplicates = [opt for opt in set(option_texts) if option_texts.count(opt) > 1]
                        if duplicates:
                            errors.append(f"Question {index + 1}: Duplicate options found: {duplicates}")
            
            # Check answer_idx
            if answer_idx is not None:
                if not isinstance(answer_idx, int):
                    errors.append(f"Question {index + 1}: answer_idx must be an integer")
                elif answer_idx < 0 or answer_idx >= 4:
                    errors.append(f"Question {index + 1}: answer_idx must be between 0 and 3 (got {answer_idx})")
            
            return errors
            
        except Exception as e:
            errors.append(f"Question {index + 1}: Validation error - {str(e)}")
            return errors
    
    def _get_option_errors(self, option: str, option_index: int, question_index: int) -> List[str]:
        """Get validation errors for a single option"""
        errors = []
        
        try:
            if not isinstance(option, str):
                errors.append(f"Question {question_index + 1}, Option {option_index + 1}: Must be a string")
                return errors
            
            option = option.strip()
            
            if len(option) < self.validation_rules["min_option_length"]:
                errors.append(f"Question {question_index + 1}, Option {option_index + 1}: Too short (min {self.validation_rules['min_option_length']} chars)")
            elif len(option) > self.validation_rules["max_option_length"]:
                errors.append(f"Question {question_index + 1}, Option {option_index + 1}: Too long (max {self.validation_rules['max_option_length']} chars)")
            
            if not option:
                errors.append(f"Question {question_index + 1}, Option {option_index + 1}: Empty option")
            
            return errors
            
        except Exception as e:
            errors.append(f"Question {question_index + 1}, Option {option_index + 1}: Validation error - {str(e)}")
            return errors


class SummaryValidator(ContentValidator):
    """Validates summary quality and structure for TrainPI system"""
    
    def __init__(self):
        super().__init__()
        self.validation_rules = {
            "min_length": 50,
            "max_length": 2000,
            "min_sentences": 3,
            "max_sentences": 20,
            "no_repetition": True,
            "coherent_structure": True
        }
    
    def validate(self, summary: Dict[str, Any]) -> bool:
        """Validate a summary"""
        try:
            if not summary or not isinstance(summary, dict):
                return False
            
            summary_text = summary.get("summary", "")
            if not summary_text:
                return False
            
            # Check length
            if (len(summary_text) < self.validation_rules["min_length"] or
                len(summary_text) > self.validation_rules["max_length"]):
                return False
            
            # Check sentence count
            sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
            if (len(sentences) < self.validation_rules["min_sentences"] or
                len(sentences) > self.validation_rules["max_sentences"]):
                return False
            
            # Check for repetition
            if self.validation_rules["no_repetition"]:
                words = summary_text.lower().split()
                word_freq = {}
                for word in words:
                    if len(word) > 3:  # Only check meaningful words
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Check for excessive repetition
                for word, freq in word_freq.items():
                    if freq > len(words) * 0.1:  # More than 10% of words
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Summary validation failed: {e}")
            return False
    
    def get_validation_errors(self, summary: Dict[str, Any]) -> List[str]:
        """Get validation errors for a summary"""
        errors = []
        
        try:
            if not summary or not isinstance(summary, dict):
                errors.append("Invalid summary format")
                return errors
            
            summary_text = summary.get("summary", "")
            if not summary_text:
                errors.append("Missing summary text")
                return errors
            
            # Check length
            if len(summary_text) < self.validation_rules["min_length"]:
                errors.append(f"Summary too short (min {self.validation_rules['min_length']} chars)")
            elif len(summary_text) > self.validation_rules["max_length"]:
                errors.append(f"Summary too long (max {self.validation_rules['max_length']} chars)")
            
            # Check sentence count
            sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
            if len(sentences) < self.validation_rules["min_sentences"]:
                errors.append(f"Too few sentences (min {self.validation_rules['min_sentences']})")
            elif len(sentences) > self.validation_rules["max_sentences"]:
                errors.append(f"Too many sentences (max {self.validation_rules['max_sentences']})")
            
            # Check for repetition
            if self.validation_rules["no_repetition"]:
                words = summary_text.lower().split()
                word_freq = {}
                for word in words:
                    if len(word) > 3:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                repetitive_words = [word for word, freq in word_freq.items() if freq > len(words) * 0.1]
                if repetitive_words:
                    errors.append(f"Excessive word repetition: {repetitive_words}")
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return errors


# Global validator instances
flashcard_validator = FlashcardValidator()
quiz_validator = QuizValidator()
summary_validator = SummaryValidator()

# Convenience functions for external use (matching your specification)
def qa_flashcards(cards: List[Dict]) -> bool:
    """Quality assurance for flashcards - checks for duplicates, missing answers, low quality"""
    return flashcard_validator.validate(cards)

def qa_quiz(questions: List[Dict]) -> bool:
    """Quality assurance for quiz - ensures 4 options, one correct answer, no duplicates"""
    return quiz_validator.validate(questions)

def qa_summary(summary: Dict[str, Any]) -> bool:
    """Quality assurance for summaries"""
    return summary_validator.validate(summary)

# Additional utility functions
def get_flashcard_errors(flashcards: List[Dict[str, Any]]) -> List[str]:
    """Get validation errors for flashcards"""
    return flashcard_validator.get_validation_errors(flashcards)

def get_quiz_errors(quiz_questions: List[Dict[str, Any]]) -> List[str]:
    """Get validation errors for quiz questions"""
    return quiz_validator.get_validation_errors(quiz_questions)

def get_summary_errors(summary: Dict[str, Any]) -> List[str]:
    """Get validation errors for summaries"""
    return summary_validator.get_validation_errors(summary)
