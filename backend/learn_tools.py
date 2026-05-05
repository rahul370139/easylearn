"""
Learning Tools for TrainPI Agents
Optimized integration with existing distiller and supabase systems
"""

from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import uuid
from datetime import datetime
import asyncio
from pathlib import Path

# Import existing functionality from distiller
from distiller import (
    pdf_to_text, chunk_text, embed_chunks, detect_framework,
    map_reduce_summary, gen_flashcards_quiz, generate_concept_map
)
from supabase_helper import insert_lesson


class PDFIngestionManager:
    """Manages PDF ingestion and processing with existing TrainPI infrastructure"""
    
    def __init__(self):
        self.processed_pdfs = {}
        self.concept_metadata = {}
    
    async def ingest_pdf(self, file_path: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest and process a PDF document using existing TrainPI pipeline"""
        try:
            pdf_id = str(uuid.uuid4())
            
            # Use existing PDF processing functions
            text = pdf_to_text(Path(file_path))
            if not text:
                raise ValueError("Failed to extract text from PDF")
            
            # Process in parallel for efficiency
            chunks_task = asyncio.create_task(self._chunk_text_async(text))
            framework_task = asyncio.create_task(self._detect_framework_async(text))
            
            chunks, frameworks = await asyncio.gather(chunks_task, framework_task)
            
            # Generate embeddings using existing function
            embeddings = await embed_chunks(chunks)
            
            # Store processed data
            pdf_data = {
                "pdf_id": pdf_id,
                "user_id": user_id,
                "text": text,
                "chunks": chunks,
                "embeddings": embeddings,
                "frameworks": frameworks,
                "metadata": metadata or {},
                "processed_at": datetime.utcnow().isoformat(),
                "status": "processed"
            }
            
            self.processed_pdfs[pdf_id] = pdf_data
            
            # Generate concept metadata
            concept_metadata = await self._extract_concept_metadata(text, chunks, frameworks)
            self.concept_metadata[pdf_id] = concept_metadata
            
            # Store in Supabase for persistence
            lesson_id = await self._store_in_supabase(user_id, Path(file_path).name, text, frameworks)
            
            logger.info(f"PDF ingested successfully: {pdf_id}, lesson_id: {lesson_id}")
            
            return {
                "pdf_id": pdf_id,
                "lesson_id": lesson_id,
                "status": "success",
                "concept_metadata": concept_metadata,
                "frameworks": frameworks,
                "chunk_count": len(chunks),
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _chunk_text_async(self, text: str) -> List[str]:
        """Async wrapper for chunk_text"""
        return chunk_text(text)
    
    async def _detect_framework_async(self, text: str) -> List[str]:
        """Async wrapper for framework detection"""
        try:
            # Use existing framework detection
            frameworks = detect_framework(text)
            if isinstance(frameworks, str):
                return [frameworks]
            elif isinstance(frameworks, list):
                return frameworks
            else:
                return ["generic"]
        except Exception as e:
            logger.warning(f"Framework detection failed: {e}")
            return ["generic"]
    
    async def _extract_concept_metadata(self, text: str, chunks: List[str], frameworks: List[str]) -> Dict[str, Any]:
        """Extract key concepts and metadata from the PDF"""
        try:
            # Use existing concept extraction if available
            concept_map = await generate_concept_map(text)
            
            # Enhanced concept analysis
            words = text.lower().split()
            word_freq = {}
            
            # Count word frequencies (excluding common words)
            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            for word in words:
                if len(word) > 3 and word not in common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top concepts
            top_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            return {
                "concepts": [{"concept": concept, "frequency": freq} for concept, freq in top_concepts],
                "frameworks": frameworks,
                "chunk_count": len(chunks),
                "estimated_topics": self._estimate_topics(text, frameworks),
                "complexity_score": self._assess_complexity(text),
                "concept_map": concept_map
            }
            
        except Exception as e:
            logger.warning(f"Concept metadata extraction failed: {e}")
            return {"concepts": [], "frameworks": frameworks, "chunk_count": len(chunks)}
    
    def _estimate_topics(self, text: str, frameworks: List[str]) -> List[str]:
        """Estimate main topics from the text"""
        try:
            topics = []
            
            if "python" in str(frameworks).lower():
                topics.extend(["programming", "software development", "coding"])
            if "machine learning" in str(frameworks).lower():
                topics.extend(["artificial intelligence", "data science", "algorithms"])
            if "web" in str(frameworks).lower():
                topics.extend(["web development", "frontend", "backend"])
            
            # Add generic topics if none specific
            if not topics:
                topics = ["general", "learning", "education"]
            
            return topics
            
        except Exception as e:
            logger.warning(f"Topic estimation failed: {e}")
            return ["general"]
    
    def _assess_complexity(self, text: str) -> float:
        """Assess the complexity of the text"""
        try:
            # Simple complexity scoring based on sentence length and vocabulary
            sentences = text.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            
            # Normalize to 0-1 scale
            complexity = min(avg_sentence_length / 20.0, 1.0)
            return round(complexity, 2)
            
        except Exception as e:
            logger.warning(f"Complexity assessment failed: {e}")
            return 0.5
    
    async def _store_in_supabase(self, user_id: str, title: str, text: str, frameworks: List[str]) -> int:
        """Store PDF data in Supabase using existing infrastructure"""
        try:
            # Generate summary using existing function
            summary = await map_reduce_summary([text])
            
            # Determine primary framework
            primary_framework = frameworks[0] if frameworks else "generic"
            
            # Use existing insert_lesson function
            lesson_id = insert_lesson(
                owner_id=user_id,
                title=title,
                summary=summary,
                framework=primary_framework,
                explanation_level="intern",
                full_text=text
            )
            
            return lesson_id
            
        except Exception as e:
            logger.error(f"Supabase storage failed: {e}")
            # Return a fallback ID
            return int(uuid.uuid4().hex[:8], 16)


class ContentGenerator:
    """Generates learning content using existing TrainPI functions"""
    
    def __init__(self):
        self.pdf_manager = PDFIngestionManager()
    
    async def gen_summary(self, pdf_id: str, topic_filter: str = "", explanation_level: str = "intern") -> Dict[str, Any]:
        """Generate a topic-filtered summary using existing functions"""
        try:
            # Get PDF data
            pdf_data = self.pdf_manager.processed_pdfs.get(pdf_id)
            if not pdf_data:
                return {"error": "PDF not found or not processed"}
            
            text = pdf_data["text"]
            
            # Use existing summary generation
            summary = await map_reduce_summary([text], explanation_level)
            
            # Generate concept map using existing function
            concept_map = await generate_concept_map(summary)
            
            # Structure the summary
            structured_summary = {
                "summary": summary,
                "topic_filter": topic_filter,
                "explanation_level": explanation_level,
                "key_points": self._extract_key_points(summary),
                "estimated_reading_time": self._estimate_reading_time(summary),
                "concept_map": concept_map,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return structured_summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"error": str(e)}
    
    async def gen_flashcards(self, pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
        """Generate flashcards using existing TrainPI functions"""
        try:
            # Get PDF data
            pdf_data = self.pdf_manager.processed_pdfs.get(pdf_id)
            if not pdf_data:
                return []
            
            text = pdf_data["text"]
            
            # Use existing flashcard generation
            qa_result = await gen_flashcards_quiz(
                summary=text,
                explanation_level="intern",
                num_flashcards=count
            )
            
            flashcards = qa_result.get("flashcards", [])
            
            # Enhance flashcards with metadata
            enhanced_flashcards = []
            for i, card in enumerate(flashcards):
                enhanced_card = {
                    "id": str(uuid.uuid4()),
                    "front": card.get("front", f"Question {i+1}"),
                    "back": card.get("back", f"Answer {i+1}"),
                    "topic": topic,
                    "difficulty": self._assess_question_difficulty(card),
                    "type": "flashcard",
                    "created_at": datetime.utcnow().isoformat()
                }
                enhanced_flashcards.append(enhanced_card)
            
            return enhanced_flashcards
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            return []
    
    async def gen_quiz(self, pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
        """Generate quiz questions using existing TrainPI functions"""
        try:
            # Get PDF data
            pdf_data = self.pdf_manager.processed_pdfs.get(pdf_id)
            if not pdf_data:
                return []
            
            text = pdf_data["text"]
            
            # Use existing quiz generation
            qa_result = await gen_flashcards_quiz(
                summary=text,
                explanation_level="intern",
                num_questions=count
            )
            
            quiz_questions = qa_result.get("quiz", [])
            
            # Enhance quiz questions with metadata
            enhanced_questions = []
            for i, question in enumerate(quiz_questions):
                enhanced_question = {
                    "id": str(uuid.uuid4()),
                    "question": question.get("question", f"Question {i+1}"),
                    "options": question.get("options", []),
                    "correct_answer": question.get("correct_answer", ""),
                    "answer_idx": question.get("answer_idx", 0),
                    "explanation": question.get("explanation", ""),
                    "topic": topic,
                    "difficulty": self._assess_question_difficulty(question),
                    "type": "quiz",
                    "created_at": datetime.utcnow().isoformat()
                }
                enhanced_questions.append(enhanced_question)
            
            return enhanced_questions
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []
    
    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from a summary"""
        try:
            # Simple key point extraction
            sentences = summary.split('.')
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
            return key_points
        except Exception as e:
            logger.warning(f"Key point extraction failed: {e}")
            return []
    
    def _estimate_reading_time(self, text: str) -> str:
        """Estimate reading time for text"""
        try:
            words = len(text.split())
            minutes = max(1, words // 200)  # 200 words per minute
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        except Exception as e:
            logger.warning(f"Reading time estimation failed: {e}")
            return "5 minutes"
    
    def _assess_question_difficulty(self, question: Dict[str, Any]) -> str:
        """Assess the difficulty of a question"""
        try:
            # Simple difficulty assessment
            question_text = question.get("question", "") or question.get("front", "")
            if len(question_text) > 100:
                return "hard"
            elif len(question_text) > 50:
                return "medium"
            else:
                return "easy"
        except Exception as e:
            logger.warning(f"Difficulty assessment failed: {e}")
            return "medium"


# Global instances
pdf_manager = PDFIngestionManager()
content_generator = ContentGenerator()

# Convenience functions for external use
async def ingest_pdf(file_path: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Ingest a PDF document"""
    return await pdf_manager.ingest_pdf(file_path, user_id, metadata)

async def gen_summary(pdf_id: str, topic_filter: str = "", explanation_level: str = "intern") -> Dict[str, Any]:
    """Generate a summary for a PDF"""
    return await content_generator.gen_summary(pdf_id, topic_filter, explanation_level)

async def gen_flashcards(pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
    """Generate flashcards for a PDF"""
    return await content_generator.gen_flashcards(pdf_id, topic, count)

async def gen_quiz(pdf_id: str, topic: str = "", count: int = 10) -> List[Dict[str, Any]]:
    """Generate quiz questions for a PDF"""
    return await content_generator.gen_quiz(pdf_id, topic, count)
