from typing import List, Dict, Optional, Tuple
from pathlib import Path
import io, os, json, asyncio
import fitz  # PyMuPDF
from loguru import logger
import httpx
from schemas import ExplanationLevel, Framework
import uuid
from datetime import datetime
from dotenv import load_dotenv
from collections import OrderedDict

# Load environment variables
load_dotenv()

CHUNK_WORDS = 400
OVERLAP = 50

# In-memory conversation storage (replace with database in production)
conversation_store: Dict[str, Dict] = {}
# Track the most recent conversation per user to avoid losing context when FE forgets to pass conversation_id
last_conversation_by_user: Dict[str, str] = {}

# In-memory lesson cache with TTL and capacity (LRU)
# Structure: { lesson_id: { 'summary': str, 'bullets': List[str], 'flashcards': List[Dict], 'quiz': List[Dict], 'concept_map': Dict, 'full_text': str, 'title': str, 'framework': str, 'cached_at': iso } }
lesson_store: "OrderedDict[str, Dict]" = OrderedDict()
LESSON_CACHE_TTL_SECONDS = 60 * 60 * 2  # 2 hours
LESSON_CACHE_CAPACITY = 50

def _lesson_cache_evict_if_needed():
    while len(lesson_store) > LESSON_CACHE_CAPACITY:
        lesson_store.popitem(last=False)

def _is_expired(record: Dict) -> bool:
    try:
        ts = record.get("cached_at")
        if not ts:
            return False
        cached = datetime.fromisoformat(ts)
        age = (datetime.utcnow() - cached).total_seconds()
        return age > LESSON_CACHE_TTL_SECONDS
    except Exception:
        return False

def set_lesson_cache(lesson_id: str, data: Dict):
    data = dict(data)
    data["cached_at"] = datetime.utcnow().isoformat()
    # Move to end (LRU)
    if lesson_id in lesson_store:
        lesson_store.pop(lesson_id, None)
    lesson_store[lesson_id] = data
    _lesson_cache_evict_if_needed()

def get_lesson_cache(lesson_id: str) -> Optional[Dict]:
    rec = lesson_store.get(lesson_id)
    if not rec:
        return None
    if _is_expired(rec):
        lesson_store.pop(lesson_id, None)
        return None
    # Touch LRU
    lesson_store.pop(lesson_id, None)
    lesson_store[lesson_id] = rec
    return rec

# Deduplication map for content hashes
content_hash_to_lesson_id: Dict[str, int] = {}

def _hash_text(text: str) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()

# Enhanced conversation metadata for better UX
conversation_metadata = {
    "recent_pdfs": {},  # Store recent PDFs per user
    "user_preferences": {},  # Store user preferences
    "framework_detection": {},  # Store detected frameworks
    "explanation_levels": {}  # Store user's explanation level preference
}

async def cohere_embed(batch: List[str]) -> List[List[float]]:
    """Generate embeddings using Cohere API"""
    url = "https://api.cohere.ai/v1/embed"
    headers = {
        "Authorization": f"Bearer {os.getenv('COHERE_API_KEY')}",
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

def _parse_json_safely(raw: str) -> Optional[Dict]:
    """Best-effort extraction and parsing of JSON from LLM responses.
    - Strips code fences
    - Grabs the largest {...} block
    - Tries simple repairs (single->double quotes, trailing commas)
    Returns dict on success, else None.
    """
    if not raw:
        return None
    text = raw.strip()
    # Remove markdown fences
    if text.startswith("```") and text.endswith("```"):
        text = text.strip('`')
        # Remove first word like json
        parts = text.split('\n', 1)
        text = parts[1] if len(parts) > 1 else text
    # Extract JSON object boundaries
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start:end+1]
    # Simple repairs
    repaired = candidate
    repaired = repaired.replace("\r", " ").replace("\n", " ")
    # Replace single quotes with double if it looks like JSON but with single quotes
    if '"' not in repaired and "'" in repaired:
        repaired = repaired.replace("'", '"')
    # Remove trailing commas before } or ]
    repaired = repaired.replace(', }', ' }').replace(', ]', ' ]')
    try:
        return json.loads(repaired)
    except Exception:
        return None

_LLM_SEMAPHORE = asyncio.Semaphore(2)

async def call_groq(messages: List[Dict]) -> str:
    """Call Groq API with optimized model and fallback to GROQ_API_KEY_2"""
    # Try primary API key first
    primary_key = os.getenv('GROQ_API_KEY')
    fallback_key = os.getenv('GROQ_API_KEY_2')
    
    if not primary_key and not fallback_key:
        logger.error("No GROQ API keys found in environment variables")
        return ""
    
    # Try primary key first
    if primary_key:
        result = await _call_groq_with_key(messages, primary_key, "primary")
        if result:
            return result
    
    # Try fallback key if primary failed
    if fallback_key:
        logger.info("Primary GROQ API key failed, trying fallback key")
        result = await _call_groq_with_key(messages, fallback_key, "fallback")
        if result:
            return result
    
    logger.error("All GROQ API keys failed")
    return ""

async def _call_groq_with_key(messages: List[Dict], api_key: str, key_type: str) -> str:
    """Call Groq API with specific key"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # High-quality model for best performance
        "messages": messages,
        "temperature": 0.3,  # Stricter JSON adherence
        "stream": False
    }

    # Retry with basic backoff on rate limits (slightly higher for first-run reliability)
    max_retries = 2
    backoff = 1.5
    attempt = 0
    async with _LLM_SEMAPHORE:
        while True:
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
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                text = e.response.text
                logger.error(f"Groq API HTTP error ({key_type} key): {status} - {text}")
                # Handle 429 rate limit with backoff
                if status == 429 and attempt < max_retries:
                    wait_s = backoff
                    try:
                        data = e.response.json()
                        msg = data.get("error", {}).get("message", "")
                        # Extract 'try again in Xs' if present
                        import re
                        m = re.search(r"try again in ([0-9.]+)s", msg)
                        if m:
                            wait_s = min(float(m.group(1)) + 0.5, 15.0)
                    except Exception:
                        pass
                    await asyncio.sleep(wait_s)
                    attempt += 1
                    backoff *= 2
                    continue
                return ""
            except httpx.TimeoutException:
                logger.error(f"Groq API request timed out ({key_type} key)")
                if attempt < max_retries:
                    await asyncio.sleep(backoff)
                    attempt += 1
                    backoff *= 2
                    continue
                return ""
            except Exception as e:
                logger.error(f"Groq API call failed ({key_type} key): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(backoff)
                    attempt += 1
                    backoff *= 2
                    continue
                return ""

def pdf_to_text(path: Path) -> str:
    try:
        doc = fitz.open(str(path))
        text = "\n\n".join(page.get_text() for page in doc)
        
        # Check if we got meaningful text
        if not text or len(text.strip()) < 10:
            raise ValueError("No selectable text found in PDF - file might be scanned")
        
        return text
    except (fitz.FileDataError, fitz.PdfReadError, ValueError) as e:
        logger.error(f"PDF extraction failed: {e}")
        raise RuntimeError("Failed to extract text from PDF - the file might be scanned or corrupted")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise RuntimeError("Failed to extract text from PDF.")

def chunk_text(text: str) -> List[str]:
    words = text.split()
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        if len(cur) >= CHUNK_WORDS:
            chunks.append(" ".join(cur))
            cur = cur[-OVERLAP:]  # overlap
    if cur:
        chunks.append(" ".join(cur))
    return chunks

async def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for text chunks using Cohere API.
    Creates semantic vector representations for similarity search and content understanding.
    """
    try:
        # Use Cohere API for embeddings
        embeddings = await cohere_embed(chunks)
        logger.info(f"Successfully generated {len(embeddings)} embeddings using Cohere")
        return embeddings
        
    except Exception as e:
        logger.error(f"Cohere embedding generation failed: {e}")
        # Return fallback embeddings
        return [_generate_fallback_embedding(chunk) for chunk in chunks]

def _generate_fallback_embedding(text: str) -> List[float]:
    """
    Generate a fallback embedding based on text characteristics.
    Uses simple heuristics to create meaningful vector representations.
    """
    embedding = [0.0] * 384
    
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
    embedding[0] = min(technical_score, 1.0)  # Technical complexity
    embedding[1] = min(framework_score, 1.0)  # Framework usage
    embedding[2] = min(learning_score, 1.0)   # Learning focus
    embedding[3] = min(char_count / 1000, 1.0)  # Content length
    embedding[4] = min(word_count / 100, 1.0)   # Word density
    
    # Add some randomness for uniqueness
    import random
    random.seed(hash(text) % 10000)
    for i in range(5, 384):
        embedding[i] = random.uniform(-0.1, 0.1)
    
    return embedding

def _normalize_embedding(embedding: List[float]) -> List[float]:
    """
    Normalize embedding values to [-1, 1] range.
    """
    if not embedding:
        return [0.0] * 384
    
    # Clip values to [-1, 1]
    normalized = [max(-1.0, min(1.0, float(val))) for val in embedding]
    
    # Ensure we have exactly 384 values
    while len(normalized) < 384:
        normalized.append(0.0)
    
    return normalized[:384]

def calculate_embedding_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    Returns a value between -1 and 1, where 1 means identical.
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    # Ensure both embeddings have the same length
    min_length = min(len(embedding1), len(embedding2))
    if min_length == 0:
        return 0.0
    
    # Calculate dot product and magnitudes
    dot_product = sum(embedding1[i] * embedding2[i] for i in range(min_length))
    magnitude1 = sum(val ** 2 for val in embedding1[:min_length]) ** 0.5
    magnitude2 = sum(val ** 2 for val in embedding2[:min_length]) ** 0.5
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)
    
    # Ensure result is in [-1, 1] range
    return max(-1.0, min(1.0, similarity))

def find_similar_content(query_embedding: List[float], content_embeddings: List[List[float]], top_k: int = 5) -> List[tuple]:
    """
    Find the most similar content based on embedding similarity.
    Returns list of (index, similarity_score) tuples sorted by similarity.
    """
    similarities = []
    
    for i, content_embedding in enumerate(content_embeddings):
        similarity = calculate_embedding_similarity(query_embedding, content_embedding)
        similarities.append((i, similarity))
    
    # Sort by similarity (descending) and return top_k results
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# Micro-lesson semantic index
_MICRO_LESSONS_RAW: List[Dict] = []
_MICRO_LESSONS_EMBEDS: List[List[float]] = []

def _load_micro_lessons_raw() -> List[Dict]:
    global _MICRO_LESSONS_RAW
    if _MICRO_LESSONS_RAW:
        return _MICRO_LESSONS_RAW
    try:
        data_path = Path(__file__).parent / 'data' / 'micro_lessons.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        lessons: List[Dict] = []
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
        _MICRO_LESSONS_RAW = lessons
        return lessons
    except Exception as e:
        logger.error(f"Failed to load micro_lessons.json: {e}")
        _MICRO_LESSONS_RAW = []
        return _MICRO_LESSONS_RAW

async def precompute_micro_lessons_embeddings() -> Tuple[int, int]:
    """Precompute embeddings for micro-lessons (title + description)."""
    global _MICRO_LESSONS_EMBEDS
    lessons = _load_micro_lessons_raw()
    if not lessons:
        _MICRO_LESSONS_EMBEDS = []
        return 0, 0
    texts = [f"{ml.get('title','')}\n{ml.get('description','')}" for ml in lessons]
    try:
        # Batch using cohere_embed in chunks to avoid size limits
        embeds: List[List[float]] = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            e = await cohere_embed(batch)
            embeds.extend([_normalize_embedding(v) for v in e])
        _MICRO_LESSONS_EMBEDS = embeds
        return len(lessons), len(embeds)
    except Exception as e:
        logger.error(f"Failed micro-lesson precompute: {e}")
        _MICRO_LESSONS_EMBEDS = []
        return len(lessons), 0

async def select_top_micro_lessons_by_text(text: str, top_k: int = 6) -> List[Dict]:
    """Select top micro-lessons for the given text using cosine similarity."""
    if not text:
        return []
    lessons = _load_micro_lessons_raw()
    if not lessons:
        return []
    if not _MICRO_LESSONS_EMBEDS:
        await precompute_micro_lessons_embeddings()
    if not _MICRO_LESSONS_EMBEDS:
        return []
    q = await generate_content_embedding(text)
    sims = find_similar_content(q, _MICRO_LESSONS_EMBEDS, top_k=top_k)
    indices = [i for i, _ in sims]
    results = [lessons[i] for i in indices if i < len(lessons)]
    return results

async def generate_retrieval_based_lesson_plan_for_lesson(
    lesson_id: int,
    explanation_level: ExplanationLevel = ExplanationLevel.INTERN,
    framework: str = "generic"
) -> Dict:
    """Generate a retrieval-grounded learning plan (topics + path) for the Learn page.
    Uses cached chunks/embeddings from lesson_store populated at upload time.
    """
    cached = get_lesson_cache(str(lesson_id))
    if not cached:
        # Fallback minimal structure
        return {
            "title": "Learning Plan",
            "overview": "Learning topics based on the document",
            "difficulty_level": "intermediate",
            "learning_topics": [],
            "learning_path": []
        }
    chunks = cached.get("chunks") or []
    embeds = cached.get("chunk_embeddings") or []
    summary = cached.get("summary") or ""
    # Retrieve most representative chunks using the summary as a query
    retrieval = ""
    if chunks and embeds and summary:
        try:
            q_embed = await generate_content_embedding(summary)
            sims = find_similar_content(q_embed, embeds, top_k=8)
            top_indices = [i for i, _ in sims]
            top_texts = [chunks[i] for i in top_indices if i < len(chunks)]
            retrieval = "\n\n".join(top_texts)
        except Exception:
            retrieval = ""
    plan_prompt = (
        f"Create a micro-learning plan that teaches the user the concepts in this document.\n"
        f"Framework Context: {framework}\n{get_explanation_prompt(explanation_level)}\n"
        f"Document summary:\n{summary}\n\nRelevant content:\n{retrieval}\n\n"
        "Return JSON: {\n"
        "  \"title\": str, \"overview\": str, \"difficulty_level\": \"beginner|intermediate|advanced\",\n"
        "  \"learning_topics\": [ { \"topic\": str, \"description\": str, \"estimated_time\": str, \"prerequisites\": [str], \"key_concepts\": [str] } ],\n"
        "  \"learning_path\": [str]\n"
        "}"
    )
    raw = await call_groq([{ "role": "user", "content": plan_prompt }])
    data = _parse_json_safely(raw)
    if isinstance(data, dict):
        return data
    # Fallback minimal plan
    return {
        "title": "Learning Plan",
        "overview": "Learning topics based on the document",
        "difficulty_level": "intermediate",
        "learning_topics": [],
        "learning_path": []
    }

async def generate_content_embedding(text: str) -> List[float]:
    """
    Generate a single embedding for a piece of content using Cohere API.
    Useful for querying and similarity search.
    """
    try:
        # Use Cohere API for single text embedding
        embeddings = await cohere_embed([text])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        else:
            return _generate_fallback_embedding(text)
            
    except Exception as e:
        logger.error(f"Failed to generate content embedding: {e}")
        return _generate_fallback_embedding(text)

def get_explanation_prompt(level: ExplanationLevel) -> str:
    """Get the appropriate prompt based on explanation level."""
    prompts = {
        ExplanationLevel.FIVE_YEAR_OLD: "Explain this like you're talking to a 5-year-old. Use simple words, analogies, and avoid technical jargon.",
        ExplanationLevel.INTERN: "Explain this for someone who is learning and has basic knowledge. Use clear examples and step-by-step explanations.",
        ExplanationLevel.SENIOR: "Explain this for an experienced professional. You can use technical terms and assume advanced knowledge."
    }
    return prompts.get(level, prompts[ExplanationLevel.INTERN])

def _normalize_framework_value(name: str) -> Framework:
    """Normalize arbitrary framework names to our Framework enum values."""
    if not name:
        return Framework.GENERIC
    normalized = name.strip().lower()
    aliases = {
        'fast api': 'fastapi',
        'fastapi': 'fastapi',
        'reactjs': 'react',
        'react': 'react',
        'python': 'python',
        'node': 'nodejs',
        'nodejs': 'nodejs',
        'node.js': 'nodejs',
        'docker': 'docker',
        'k8s': 'kubernetes',
        'kubernetes': 'kubernetes',
        'ml': 'machine_learning',
        'machine_learning': 'machine_learning',
        'ai': 'ai',
        'langchain': 'langchain',
        'nextjs': 'nextjs',
        'typescript': 'typescript',
        'frontend': 'frontend',
        'backend': 'backend',
        'database': 'database',
        'cloud': 'cloud',
        'devops': 'devops',
        'generic': 'generic'
    }
    value = aliases.get(normalized, normalized)
    try:
        return Framework(value)
    except ValueError:
        return Framework.GENERIC

async def detect_framework(text: str) -> Framework:
    """Enhanced framework detection with confidence scoring"""
    try:
        prompt = f"""
        Analyze this text and identify the primary framework, tool, or technology being discussed.
        
        Text: {text[:2000]}
        
        Return a JSON object with this structure:
        {{
            "primary_framework": "FASTAPI|REACT|PYTHON|NODEJS|DOCKER|LANGCHAIN|ML_AI|GENERIC",
            "confidence": 0.85,
            "detected_frameworks": [
                {{
                    "name": "FASTAPI",
                    "confidence": 0.9,
                    "mentions": 5
                }},
                {{
                    "name": "PYTHON", 
                    "confidence": 0.7,
                    "mentions": 3
                }}
            ],
            "reasoning": "Brief explanation of why this framework was chosen"
        }}
        
        If multiple frameworks are mentioned, choose the most prominent one as primary.
        If no specific framework is clear, return GENERIC.
        """
        messages = [{"role": "user", "content": prompt}]
        result = await call_groq(messages)
        
        data = _parse_json_safely(result)
        if isinstance(data, dict):
            primary = data.get("primary_framework") or data.get("primary") or "generic"
            return _normalize_framework_value(primary)
        # Fallback to simple detection
        return _normalize_framework_value(result)
            
    except Exception as e:
        logger.error(f"Framework detection failed: {e}")
        return Framework.GENERIC

async def detect_multiple_frameworks(text: str) -> Dict:
    """Detect multiple frameworks with confidence scores"""
    try:
        prompt = f"""
        Analyze this text and identify ALL frameworks, tools, or technologies mentioned.
        
        Text: {text[:2000]}
        
        Return a JSON object with this structure:
        {{
            "frameworks": [
                {{
                    "name": "FASTAPI",
                    "confidence": 0.9,
                    "mentions": 5,
                    "context": "API development framework"
                }},
                {{
                    "name": "PYTHON",
                    "confidence": 0.7,
                    "mentions": 3,
                    "context": "Programming language"
                }}
            ],
            "primary_framework": "FASTAPI",
            "total_frameworks": 2
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        result = await call_groq(messages)
        
        data = _parse_json_safely(result)
        if isinstance(data, dict):
            # Normalize values to our enum values (lowercase)
            primary = data.get("primary_framework") or data.get("primary") or "generic"
            frameworks = data.get("frameworks", [])
            normalized_list = []
            for item in frameworks:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("framework") or ""
                    item["name"] = _normalize_framework_value(name).value
                    normalized_list.append(item)
                elif isinstance(item, str):
                    normalized_list.append({"name": _normalize_framework_value(item).value})
            return {
                "frameworks": normalized_list,
                "primary_framework": _normalize_framework_value(primary).value,
                "total_frameworks": len(normalized_list)
            }
        return {"frameworks": [], "primary_framework": "generic", "total_frameworks": 0}
            
    except Exception as e:
        logger.error(f"Multiple framework detection failed: {e}")
        return {"frameworks": [], "primary_framework": "GENERIC", "total_frameworks": 0}

async def map_reduce_summary(chunks: List[str], explanation_level: ExplanationLevel = ExplanationLevel.INTERN) -> str:
    explanation_prompt = get_explanation_prompt(explanation_level)
    
    async def summarize_chunk(chunk):
        try:
            messages = [
                {"role": "system", "content": f"Summarize the text into 3 concise bullets. {explanation_prompt}"},
                {"role": "user", "content": chunk},
            ]
            return await call_groq(messages)
        except Exception as e:
            logger.error(f"LLM summarize_chunk failed: {e}")
            raise RuntimeError("LLM summarization failed.")
    
    try:
        mapped = await asyncio.gather(*[summarize_chunk(ch) for ch in chunks])
        reduce_prompt = (
            f"You are creating a training cheat-sheet. {explanation_prompt} "
            "Merge these bullet groups into **max 10 key bullets**:\n"
            + "\n".join(mapped)
        )
        messages = [{"role": "user", "content": reduce_prompt}]
        raw = await call_groq(messages)
        # Ensure bulletized output using '• ' separator
        text = raw.strip()
        if '•' not in text:
            # Convert lines or hyphens to bullets
            lines = [line.strip(' -\t') for line in text.splitlines() if line.strip()]
            if not lines:
                return ""
            bullets = [f"• {line}" for line in lines[:10]]
            return "\n".join(bullets)
        return raw
    except Exception as e:
        logger.error(f"LLM map_reduce_summary failed: {e}")
        # Return a simple summary instead of failing
        return "• " + " • ".join([chunk[:100] + "..." for chunk in chunks[:5]])

async def gen_flashcards_quiz(summary: str, explanation_level: ExplanationLevel = ExplanationLevel.INTERN, *, retrieval_context: Optional[str] = None, num_items: int = 5) -> Dict[str, list]:
    """Generate flashcards and quiz using summary and optional retrieved context.
    num_items controls how many flashcards and quiz questions to generate.
    """
    explanation_prompt = get_explanation_prompt(explanation_level)
    context_part = f"\nContext (retrieved from document):\n{retrieval_context}\n" if retrieval_context else "\n"
    # Clamp num_items
    try:
        n_items = max(1, min(int(num_items), 20))
    except Exception:
        n_items = 5

    prompt = (
        f"Create high-quality learning materials. {explanation_prompt}\n"
        f"Summary of document:\n{summary}{context_part}"
        "Return ONLY valid JSON with this exact structure (no prose, no markdown):\n"
        "{\n"
        f"  \"flashcards\": [ {{ \"front\": string, \"back\": string }} ] (length: {n_items}),\n"
        f"  \"quiz\": [ {{ \"question\": string, \"options\": [\"A\",\"B\",\"C\",\"D\"], \"answer\": \"A\"|\"B\"|\"C\"|\"D\" }} ] (length: {n_items})\n"
        "}\n"
    )
    # Lighten prompt on rate-limit retries by truncating context
    try:
        ctx = retrieval_context or ""
        if len(ctx) > 4000:
            ctx = ctx[:4000]
        messages = [{"role": "user", "content": prompt.replace(retrieval_context or "", ctx)}]
        response = await call_groq(messages)
        data = _parse_json_safely(response)
        if isinstance(data, dict) and ("flashcards" in data and "quiz" in data):
            return data
        return _get_fallback_flashcards_quiz(summary, n_items)
    except Exception as e:
        logger.error(f"LLM flashcards/quiz failed: {e}")
        return _get_fallback_flashcards_quiz(summary, n_items)

def _get_fallback_flashcards_quiz(summary: str, num_items: int = 5) -> Dict[str, list]:
    """Generate fallback flashcards and quiz when LLM fails"""
    # Extract key concepts from summary
    words = summary.split()
    key_concepts = [word for word in words if len(word) > 5][:max(1, num_items)]
    
    flashcards = []
    for i, concept in enumerate(key_concepts):
        flashcards.append({
            "front": f"What is {concept}?",
            "back": f"{concept} is a key concept from the document."
        })
    
    quiz = []
    for i, concept in enumerate(key_concepts):
        quiz.append({
            "question": f"Which of the following relates to {concept}?",
            "options": [f"Option {j+1}" for j in range(4)],
            "answer": "a"
        })
    
    return {
        "flashcards": flashcards,
        "quiz": quiz
    }

async def generate_concept_map(summary: str) -> Dict:
    """Generate a concept map showing relationships between key concepts."""
    try:
        prompt = f"""
Create a concept map from this summary.
Return ONLY valid JSON with this exact structure (no prose, no markdown):
{{
  "nodes": [
    {{"id": "concept1", "label": "Concept Name", "level": 1}}
  ],
  "edges": [
    {{"from": "concept1", "to": "concept2", "label": "relationship"}}
  ]
}}

Summary: {summary}
"""
        messages = [{"role": "user", "content": prompt}]
        response = await call_groq(messages)
        data = _parse_json_safely(response)
        if isinstance(data, dict) and "nodes" in data:
            # Normalize node key to include 'title' for downstream compatibility
            for node in data.get("nodes", []):
                if isinstance(node, dict):
                    if "label" in node and "title" not in node:
                        node["title"] = node["label"]
            return data
        return _get_fallback_concept_map(summary)
            
    except Exception as e:
        logger.error(f"Concept map generation failed: {e}")
        return _get_fallback_concept_map(summary)

def _get_fallback_concept_map(summary: str) -> Dict:
    """Generate fallback concept map when LLM fails"""
    # Extract key concepts from summary
    words = summary.split()
    key_concepts = [word for word in words if len(word) > 5][:3]
    
    nodes = []
    edges = []
    
    for i, concept in enumerate(key_concepts):
        nodes.append({
            "id": f"concept{i+1}",
            "label": concept,
            "level": 1
        })
        
        if i > 0:
            edges.append({
                "from": f"concept{i}",
                "to": f"concept{i+1}",
                "label": "related to"
            })
    
    return {
        "nodes": nodes,
        "edges": edges
    }



# Chatbot functions
def get_or_create_conversation(conversation_id: Optional[str], user_id: str) -> str:
    """Get existing conversation or create new one with enhanced metadata."""
    if conversation_id and conversation_id in conversation_store:
        last_conversation_by_user[user_id] = conversation_id
        return conversation_id
    # If FE didn't pass conversation_id, try to reuse the last conversation for this user
    existing = last_conversation_by_user.get(user_id)
    if existing and existing in conversation_store:
        return existing
    
    new_conversation_id = str(uuid.uuid4())
    conversation_store[new_conversation_id] = {
        "user_id": user_id,
        "messages": [],
        "file_context": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {
            "recent_pdfs": [],
            "framework_preferences": [],
            "explanation_level": "INTERN",
            "user_skills": [],
            "interaction_history": []
        }
    }
    last_conversation_by_user[user_id] = new_conversation_id
    return new_conversation_id

def update_user_preferences(user_id: str, preferences: Dict):
    """Update user preferences for personalized experience."""
    if user_id not in conversation_metadata["user_preferences"]:
        conversation_metadata["user_preferences"][user_id] = {}
    
    conversation_metadata["user_preferences"][user_id].update(preferences)

def get_user_preferences(user_id: str) -> Dict:
    """Get user preferences for personalized experience."""
    return conversation_metadata["user_preferences"].get(user_id, {})

def store_recent_pdf(user_id: str, pdf_name: str, framework: str, summary: str):
    """Store recent PDF information for quick access."""
    if user_id not in conversation_metadata["recent_pdfs"]:
        conversation_metadata["recent_pdfs"][user_id] = []
    
    pdf_info = {
        "name": pdf_name,
        "framework": framework,
        "summary": summary,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    # Keep only last 5 PDFs
    recent_pdfs = conversation_metadata["recent_pdfs"][user_id]
    recent_pdfs.append(pdf_info)
    if len(recent_pdfs) > 5:
        recent_pdfs.pop(0)
    
    conversation_metadata["recent_pdfs"][user_id] = recent_pdfs

def get_recent_pdfs(user_id: str) -> List[Dict]:
    """Get recent PDFs for user."""
    return conversation_metadata["recent_pdfs"].get(user_id, [])

def add_message_to_conversation(conversation_id: str, role: str, content: str):
    """Add a message to the conversation history."""
    if conversation_id not in conversation_store:
        return
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    conversation_store[conversation_id]["messages"].append(message)
    conversation_store[conversation_id]["updated_at"] = datetime.utcnow().isoformat()
    # Update last mapping for this user as well
    try:
        uid = conversation_store[conversation_id]["user_id"]
        last_conversation_by_user[uid] = conversation_id
    except Exception:
        pass

async def process_chat_message(user_id: str, message: str, conversation_id: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Process a chat message and generate a response with enhanced learning content options."""
    try:
        conv_id = get_or_create_conversation(conversation_id, user_id)
        add_message_to_conversation(conv_id, "user", message)
        
        # Get conversation context
        conversation = conversation_store[conv_id]
        messages = conversation["messages"]
        file_context = conversation.get("file_context")
        
        # Check for special commands
        message_lower = message.lower().strip()
        
        # Enhanced command detection (broader patterns: singular/plural variants)
        if any(cmd in message_lower for cmd in [
            "create lesson", "generate lesson", "make lesson", "lesson about", "create microlearning", "create a lesson", "make a lesson"
        ]):
            return await _handle_lesson_generation(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in [
            "create quiz", "generate quiz", "make quiz", "quiz about", "quiz questions", "more quiz", "more questions"
        ]):
            return await _handle_quiz_generation(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in [
            "create flashcards", "generate flashcards", "make flashcards", "flashcards about", "flashcard", "more flashcards", "more cards"
        ]):
            return await _handle_flashcard_generation(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in [
            "create workflow", "generate workflow", "make diagram", "create chart", "workflow about", "diagram", "flowchart"
        ]):
            return await _handle_workflow_generation(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in [
            "create summary", "generate summary", "make summary", "summarize", "bullet points", "summary"
        ]):
            return await _handle_summary_generation(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in ["explain like 5", "explain like 15", "explain like senior", "explain for beginner", "explain for expert"]):
            return await _handle_explanation_level_change(message, conv_id, file_context, explanation_level)
        
        elif any(cmd in message_lower for cmd in ["help", "commands", "what can you do", "options"]):
            return await _handle_help_command(conv_id, file_context)
        
        # Regular chat message
        else:
            return await _handle_regular_chat(message, conv_id, file_context, explanation_level)
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}")
        raise RuntimeError("Failed to process chat message.")

async def _handle_lesson_generation(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Enhanced lesson generation with microlearning focus."""
    try:
        # Extract topic from message
        topic = _extract_topic_from_message(message, ["lesson about", "create lesson", "generate lesson", "make lesson", "create microlearning"])
        
        # Get conversation metadata for context
        conversation = conversation_store.get(conv_id, {})
        metadata = conversation.get("metadata", {})
        current_pdf = metadata.get("current_pdf", {})
        framework = current_pdf.get("framework", "GENERIC")
        
        # Retrieval-augmented learning plan: use top chunks
        chunks = conversation_store.get(conv_id, {}).get("chunks", [])
        embeds = conversation_store.get(conv_id, {}).get("chunk_embeddings", [])
        retrieval = ""
        if chunks and embeds:
            q_embed = await generate_content_embedding(topic)
            sims = find_similar_content(q_embed, embeds, top_k=6)
            top_indices = [i for i, _ in sims]
            top_texts = [chunks[i] for i in top_indices if i < len(chunks)]
            retrieval = "\n\n".join(top_texts)
        plan_prompt = (
            f"Based on the following content, create a micro-learning plan to understand: {topic}\n"
            f"Framework Context: {framework}\n{get_explanation_prompt(explanation_level)}\n"
            f"Retrieved content:\n{retrieval}\n"
            "Return JSON: {\n"
            "  \"title\": str, \"overview\": str, \"difficulty_level\": \"beginner|intermediate|advanced\",\n"
            "  \"learning_topics\": [ { \"topic\": str, \"description\": str, \"estimated_time\": str, \"prerequisites\": [str], \"key_concepts\": [str] } ],\n"
            "  \"learning_path\": [str]\n"
            "}"
        )
        lesson_raw = await call_groq([{ "role": "user", "content": plan_prompt }])
        lesson_data = _parse_json_safely(lesson_raw) or {"title": f"Learning Topics: {topic}", "learning_topics": [], "learning_path": []}
        
        # Create engaging response
        response_text = f"I've generated lesson topics for {topic}."
        
        add_message_to_conversation(conv_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "lesson_data": lesson_data,
            "type": "lesson",
            "framework": framework
        }
        
    except Exception as e:
        logger.error(f"Lesson generation failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

async def _handle_quiz_generation(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle quiz generation command."""
    try:
        topic = _extract_topic_from_message(message, ["quiz about", "create quiz", "generate quiz", "make quiz"])
        if not topic or not topic.strip():
            topic = "your document"
        
        # Retrieval-augmented quiz: pick top chunks
        chunks = conversation_store.get(conv_id, {}).get("chunks", [])
        embeds = conversation_store.get(conv_id, {}).get("chunk_embeddings", [])
        retrieval = ""
        if chunks and embeds:
            # Build a quick query embedding from topic
            q_embed = await generate_content_embedding(topic)
            sims = find_similar_content(q_embed, embeds, top_k=4)
            top_indices = [i for i, _ in sims]
            top_texts = [chunks[i] for i in top_indices if i < len(chunks)]
            retrieval = "\n\n".join(top_texts)
        # Support variable count requests, default 5
        desired_count = _extract_desired_count(message) or 5
        qa = await gen_flashcards_quiz(
            summary=f"Topic: {topic}\n{file_context or ''}",
            explanation_level=explanation_level,
            retrieval_context=retrieval,
            num_items=desired_count
        )
        response = f"I've created a quiz about {topic} for you!"
        
        add_message_to_conversation(conv_id, "assistant", response)
        
        # Normalize shape to match /api/lesson/{id}/quiz -> { content: { questions: [...] } }
        normalized_quiz = {"questions": qa.get("quiz", qa.get("questions", []))}
        # Build a textual preview to ensure FE shows content immediately
        preview_lines = []
        for i, q in enumerate(normalized_quiz.get("questions", [])[:min(len(normalized_quiz.get("questions", [])), 10)], start=1):
            try:
                opts = q.get("options") or []
                opts_txt = f" A) {opts[0]}  B) {opts[1]}  C) {opts[2]}  D) {opts[3]}" if len(opts) >= 4 else ""
                preview_lines.append(f"{i}. {q.get('question','')}\n{opts_txt}")
            except Exception:
                preview_lines.append(f"{i}. {q}")
        response_with_preview = response + ("\n\n" + "\n".join(preview_lines) if preview_lines else "")
        return {
            "response": response_with_preview,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "quiz_data": normalized_quiz,
            "quiz": normalized_quiz.get("questions", []),
            "type": "quiz"
        }
        
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

async def _handle_flashcard_generation(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle flashcard generation command."""
    try:
        topic = _extract_topic_from_message(message, ["flashcards about", "create flashcards", "generate flashcards", "make flashcards"])
        if not topic or not topic.strip():
            topic = "your document"
        
        # Retrieval-augmented flashcards
        chunks = conversation_store.get(conv_id, {}).get("chunks", [])
        embeds = conversation_store.get(conv_id, {}).get("chunk_embeddings", [])
        retrieval = ""
        if chunks and embeds:
            q_embed = await generate_content_embedding(topic)
            sims = find_similar_content(q_embed, embeds, top_k=4)
            top_indices = [i for i, _ in sims]
            top_texts = [chunks[i] for i in top_indices if i < len(chunks)]
            retrieval = "\n\n".join(top_texts)
        # Support variable count requests, default 5
        desired_count = _extract_desired_count(message) or 5
        qa = await gen_flashcards_quiz(
            summary=f"Topic: {topic}\n{file_context or ''}",
            explanation_level=explanation_level,
            retrieval_context=retrieval,
            num_items=desired_count
        )
        response = f"I've created flashcards about {topic} for you!"
        
        add_message_to_conversation(conv_id, "assistant", response)
        
        # Normalize shape to match /api/lesson/{id}/flashcards -> { content: { cards: [...] } }
        normalized_cards = {"cards": qa.get("flashcards", qa.get("cards", []))}
        # Build textual preview to ensure FE shows content immediately
        preview_lines = []
        for i, c in enumerate(normalized_cards.get("cards", [])[:min(len(normalized_cards.get("cards", [])), 12)], start=1):
            try:
                preview_lines.append(f"Card {i}:\nFront: {c.get('front','')}\nBack: {c.get('back','')}")
            except Exception:
                preview_lines.append(f"Card {i}: {c}")
        response_with_preview = response + ("\n\n" + "\n\n".join(preview_lines) if preview_lines else "")
        return {
            "response": response_with_preview,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "flashcard_data": normalized_cards,
            "flashcards": normalized_cards.get("cards", []),
            "type": "flashcards"
        }
        
    except Exception as e:
        logger.error(f"Flashcard generation failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

async def _handle_help_command(conv_id: str, file_context: Optional[str] = None) -> Dict:
    """Handle help command with enhanced options."""
    
    # Check if file has been uploaded
    if file_context:
        help_text = """🎉 **Great! I've processed your uploaded document.** 

Here are the interactive options I can create for you:

**📋 Content Generation Options:**
🔹 **"Create summary"** - Generate bullet-point summary of your document
🔹 **"Create lesson"** - Generate comprehensive microlearning lesson
🔹 **"Generate quiz"** - Create interactive quiz from your content
🔹 **"Make flashcards"** - Create study flashcards
🔹 **"Create workflow"** - Generate workflow/diagram from your content

**🎯 Explanation Levels:**
🔹 **"Explain like 5"** - Simple, beginner-friendly explanations
🔹 **"Explain like 15"** - Intermediate level explanations  
🔹 **"Explain like senior"** - Advanced, expert-level explanations

**💬 General Learning:**
🔹 Ask me questions about your document
🔹 Get clarification on any concepts
🔹 Request specific examples or use cases

**📖 Example Commands:**
- "Create summary" - Get key points from your document
- "Generate quiz about [topic]" - Quiz on specific topic
- "Make flashcards about [concept]" - Flashcards for study
- "Create workflow for [process]" - Visual workflow diagram
- "Explain like 5: [concept]" - Simple explanation

Just tell me what you'd like to create!"""
    else:
        help_text = """🤖 **I'm TrainPI, your AI learning assistant!**

Here's what I can help you with:

**📚 Learning Content Generation:**
🔹 **"Create lesson about [topic]"** - Generate comprehensive microlearning lessons
🔹 **"Generate quiz about [topic]"** - Create interactive quizzes
🔹 **"Make flashcards about [topic]"** - Create study flashcards
🔹 **"Create workflow about [topic]"** - Generate workflow/diagram
🔹 **"Create summary about [topic]"** - Generate bullet-point summaries

**🎯 Explanation Levels:**
🔹 **"Explain like 5"** - Simple, beginner-friendly explanations
🔹 **"Explain like 15"** - Intermediate level explanations  
🔹 **"Explain like senior"** - Advanced, expert-level explanations

**📖 PDF Processing:**
🔹 Upload PDFs to get context-aware learning materials
🔹 I'll analyze your document and create personalized content

**💬 General Learning Support:**
🔹 Ask me questions about any topic
🔹 Get step-by-step explanations
🔹 Request examples and use cases

**📋 Example Commands:**
- "Create lesson about Python functions"
- "Generate quiz about React hooks"
- "Make flashcards about SQL basics"
- "Create workflow for user authentication"
- "Explain like 5: machine learning"

**📎 Upload a PDF first to get the most out of my features!**

Just ask me anything or use the commands above to get started!"""
    
    add_message_to_conversation(conv_id, "assistant", help_text)
    
    return {
        "response": help_text,
        "conversation_id": conv_id,
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "help",
        "has_file_context": file_context is not None
    }

async def _handle_regular_chat(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle regular chat messages."""
    # Build system prompt
    system_prompt = f"""You are TrainPI, an AI learning assistant. {get_explanation_prompt(explanation_level)}

Your role is to help users learn and understand concepts. Be helpful, encouraging, and educational.

If a file has been uploaded, you can reference its content to provide more specific answers.

You can also generate lessons, quizzes, and flashcards when asked."""
    
    # Retrieval-augmented chat
    llm_messages = [{"role": "system", "content": system_prompt}]
    retrieval = ""
    chunks = conversation_store.get(conv_id, {}).get("chunks", [])
    embeds = conversation_store.get(conv_id, {}).get("chunk_embeddings", [])
    if chunks and embeds:
        try:
            q_embed = await generate_content_embedding(message)
            sims = find_similar_content(q_embed, embeds, top_k=6)
            top_indices = [i for i, _ in sims]
            top_texts = [chunks[i] for i in top_indices if i < len(chunks)]
            retrieval = "\n\n".join(top_texts)
        except Exception:
            retrieval = ""
    if retrieval:
        llm_messages.append({"role": "system", "content": f"Relevant document context:\n{retrieval}"})
    # Add conversation history
    conversation = conversation_store[conv_id]
    messages = conversation["messages"]
    for msg in messages[-10:]:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})
    # User message last
    llm_messages.append({"role": "user", "content": message})
    response = await call_groq(llm_messages)
    add_message_to_conversation(conv_id, "assistant", response)
    
    return {
        "response": response,
        "conversation_id": conv_id,
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chat"
    }

async def _handle_workflow_generation(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle workflow/diagram generation command."""
    try:
        topic = _extract_topic_from_message(message, ["workflow about", "create workflow", "generate workflow", "make diagram", "create chart"])
        
        # Build the prompt without f-string to avoid brace issues
        context_part = f"Use this context if relevant: {file_context}" if file_context else ""
        
        prompt = f"""
        Create a comprehensive workflow/diagram for: {topic}
        
        {context_part}
        
        Explanation Level: {explanation_level.value}
        
        {get_explanation_prompt(explanation_level)}
        
        Create an engaging, visual workflow that includes:
        - Clear process steps with decision points
        - Visual flow diagram using Mermaid syntax
        - Time estimates for each step
        - Best practices and tips
        - Error handling and alternative paths
        
        IMPORTANT: Generate a proper Mermaid diagram code that can be rendered as a visual flowchart.
        Use different shapes for different types of steps (rectangles for processes, diamonds for decisions, etc.)
        
        Return ONLY valid JSON (no prose, no markdown) with this structure:
        {{
            "title": "Workflow Title",
            "description": "Comprehensive workflow description",
            "type": "flowchart|process|decision_tree|timeline|sequence",
            "mermaid_code": "graph TD\\n    A[Start] --> B{{Decision?}}\\n    B -->|Yes| C[Process 1]\\n    B -->|No| D[Process 2]\\n    C --> E[End]\\n    D --> E",
            "visual_elements": {{
                "start_node": "green",
                "process_nodes": "blue", 
                "decision_nodes": "yellow",
                "end_node": "red"
            }},
            "nodes": [
                {{
                    "id": "node1",
                    "label": "Start",
                    "type": "start",
                    "description": "Initial step description",
                    "duration": "5 minutes",
                    "tips": ["Tip 1", "Tip 2"],
                    "color": "green"
                }},
                {{
                    "id": "node2",
                    "label": "Process Step",
                    "type": "process",
                    "description": "Process step description",
                    "duration": "10 minutes",
                    "tips": ["Best practice 1", "Best practice 2"],
                    "color": "blue"
                }}
            ],
            "edges": [
                {{
                    "from": "node1",
                    "to": "node2",
                    "label": "Next",
                    "condition": "When ready to proceed",
                    "style": "solid"
                }}
            ],
            "steps": [
                {{
                    "step": 1,
                    "title": "Step Title",
                    "description": "Detailed step description",
                    "duration": "5 minutes",
                    "best_practices": ["Practice 1", "Practice 2"],
                    "common_mistakes": ["Mistake 1", "Mistake 2"],
                    "error_handling": "What to do if this step fails"
                }}
            ],
            "estimated_duration": "30-45 minutes",
            "difficulty_level": "beginner|intermediate|advanced",
            "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
            "tools_needed": ["Tool 1", "Tool 2"],
            "alternative_paths": [
                {{
                    "condition": "If step fails",
                    "action": "Alternative action",
                    "description": "What to do instead"
                }}
            ]
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await call_groq(messages)
        parsed = _parse_json_safely(response)
        workflow_data = parsed if isinstance(parsed, dict) else {
            "title": f"Workflow: {topic}",
            "description": "Generated workflow",
            "type": "flowchart",
            "mermaid_code": "graph TD\nA[Start]-->B[Process]-->C[End]",
            "nodes": [],
            "edges": [],
            "steps": []
        }
        response_text = f"I've created a workflow for {topic}! Here's what I've prepared:\n\n**{workflow_data['title']}**\n{workflow_data['description']}"
        
        add_message_to_conversation(conv_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_data": workflow_data,
            "type": "workflow"
        }
        
    except Exception as e:
        logger.error(f"Workflow generation failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

async def _handle_summary_generation(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle summary/bullet points generation command."""
    try:
        topic = _extract_topic_from_message(message, ["summary about", "create summary", "generate summary", "make summary", "summarize", "bullet points"])
        if not topic or not topic.strip():
            topic = "your document"
        
        if file_context:
            # Use existing file context for summary
            prompt = f"""
            Create a CONCISE summary with exactly 10 bullet points for the uploaded document.
            
            {get_explanation_prompt(explanation_level)}
            
            Document content: {file_context}
            
            IMPORTANT: Create a brief, focused summary with exactly 10 key bullet points.
            Focus on the most important information from the document.
            
            Return the summary as JSON with this structure:
            {{
                "title": "Document Summary",
                "overview": "Brief 1-2 sentence overview",
                "key_points": [
                    "Bullet point 1",
                    "Bullet point 2",
                    "Bullet point 3",
                    "Bullet point 4", 
                    "Bullet point 5",
                    "Bullet point 6",
                    "Bullet point 7",
                    "Bullet point 8",
                    "Bullet point 9",
                    "Bullet point 10"
                ],
                "estimated_reading_time": "5-10 minutes"
            }}
            """
        else:
            # Generate summary for a specific topic
            prompt = f"""
            Create a comprehensive summary with bullet points for: {topic}
            
            {get_explanation_prompt(explanation_level)}
            
            Return the summary as JSON with this structure:
            {{
                "title": "Summary: {topic}",
                "overview": "Brief overview",
                "key_points": [
                    "Key point 1",
                    "Key point 2",
                    "Key point 3"
                ],
                "main_topics": [
                    {{
                        "topic": "Topic Name",
                        "description": "Topic description",
                        "key_concepts": ["Concept 1", "Concept 2"]
                    }}
                ],
                "action_items": [
                    "Action item 1",
                    "Action item 2"
                ],
                "estimated_reading_time": "10-15 minutes"
            }}
            """
        
        messages = [{"role": "user", "content": prompt}]
        response = await call_groq(messages)
        # Be more tolerant to non-JSON responses
        parsed = _parse_json_safely(response)
        summary_data = parsed if isinstance(parsed, dict) else {"title": f"Summary: {topic}", "overview": "", "key_points": []}
        response_text = f"I've created a summary for {topic}! Here's what I've prepared:\n\n**{summary_data['title']}**\n{summary_data['overview']}"
        
        add_message_to_conversation(conv_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "summary_data": summary_data,
            "type": "summary"
        }
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

async def _handle_explanation_level_change(message: str, conv_id: str, file_context: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Handle explanation level change command."""
    try:
        message_lower = message.lower()
        
        # Determine new explanation level
        if any(level in message_lower for level in ["explain like 5", "explain for beginner", "simple", "basic"]):
            new_level = ExplanationLevel.FIVE_YEAR_OLD
            level_name = "5 Year Old"
        elif any(level in message_lower for level in ["explain like 15", "explain for intermediate", "moderate"]):
            new_level = ExplanationLevel.INTERN
            level_name = "Intermediate (Age 15)"
        elif any(level in message_lower for level in ["explain like senior", "explain for expert", "advanced", "detailed"]):
            new_level = ExplanationLevel.SENIOR
            level_name = "Senior/Expert"
        else:
            new_level = explanation_level
            level_name = "Current level"
        
        # Generate explanation with new level
        topic = _extract_topic_from_message(message, ["explain like 5", "explain like 15", "explain like senior", "explain for beginner", "explain for expert"])
        
        prompt = f"""
        Explain {topic} at a {level_name} level.
        
        {f"Use this context if relevant: {file_context}" if file_context else ""}
        
        {get_explanation_prompt(new_level)}
        
        Make sure the explanation is appropriate for the specified level.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await call_groq(messages)
        
        response_text = f"I've explained {topic} at a {level_name} level:\n\n{response}"
        add_message_to_conversation(conv_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "explanation_level": new_level.value,
            "type": "explanation"
        }
        
    except Exception as e:
        logger.error(f"Explanation level change failed: {e}")
        return await _handle_regular_chat(message, conv_id, file_context, explanation_level)

def _extract_topic_from_message(message: str, commands: List[str]) -> str:
    """Extract topic from message after removing command words."""
    message_lower = message.lower()
    
    for cmd in commands:
        if cmd in message_lower:
            # Remove the command and clean up
            topic = message_lower.replace(cmd, "").strip()
            # Capitalize first letter of each word
            topic = " ".join(word.capitalize() for word in topic.split())
            return topic
    
    # Fallback: return the message itself
    return message.strip()

def _extract_desired_count(message: str) -> Optional[int]:
    """Extract a desired number of items from user text, e.g., 'make 10 flashcards' -> 10."""
    try:
        import re
        m = re.search(r"(\d{1,2})\s*(flashcard|quiz|question|cards|problems)?", message.lower())
        if m:
            return int(m.group(1))
        return None
    except Exception:
        return None

async def process_file_for_chat(file_path: Path, user_id: str, conversation_id: Optional[str], explanation_level: ExplanationLevel) -> Dict:
    """Enhanced PDF processing with dynamic action buttons and framework detection.
    Now also saves to Supabase to create lesson_id for dashboard integration."""
    try:
        # Extract text from file
        text = pdf_to_text(file_path)
        chunks = chunk_text(text)

        # Concurrency: embeddings + summary in parallel
        summary_task = asyncio.create_task(map_reduce_summary(chunks, explanation_level))
        embeds_task = asyncio.create_task(embed_chunks(chunks))
        summary, embeds = await asyncio.gather(summary_task, embeds_task)
        
        # Detect frameworks with enhanced detection
        framework_detection = await detect_multiple_frameworks(text)
        primary_framework = framework_detection.get("primary_framework", "GENERIC")
        
        # Get or create conversation
        conv_id = get_or_create_conversation(conversation_id, user_id)
        
        # Store PDF information
        pdf_name = file_path.name
        store_recent_pdf(user_id, pdf_name, primary_framework, summary)
        
        # Add file context and retrieval data to conversation
        conversation_store[conv_id]["file_context"] = text
        conversation_store[conv_id]["chunks"] = chunks
        conversation_store[conv_id]["chunk_embeddings"] = embeds
        conversation_store[conv_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Update conversation metadata
        if "metadata" not in conversation_store[conv_id]:
            conversation_store[conv_id]["metadata"] = {}
        
        conversation_store[conv_id]["metadata"].update({
            "current_pdf": {
                "name": pdf_name,
                "framework": primary_framework,
                "detected_frameworks": framework_detection.get("frameworks", []),
                "uploaded_at": datetime.utcnow().isoformat()
            },
            "explanation_level": explanation_level.value
        })
        
        # NEW: Save to Supabase to create lesson_id for dashboard integration
        from supabase_helper import insert_lesson, insert_cards, insert_concept_map
        
        # Convert framework string to Framework enum if needed
        framework_enum = Framework.GENERIC
        if primary_framework != "GENERIC":
            try:
                framework_enum = Framework(primary_framework)
            except ValueError:
                framework_enum = Framework.GENERIC
        
        # Deduplicate uploads by content hash
        txt_hash = _hash_text(text)
        existing_id = content_hash_to_lesson_id.get(txt_hash)
        if existing_id:
            lesson_id = existing_id
        else:
            # Insert lesson to get lesson_id (including full text for chatbot access)
            lesson_id = insert_lesson(user_id, pdf_name, summary, framework_enum, explanation_level, text)
            content_hash_to_lesson_id[txt_hash] = lesson_id
        
        # Generate additional content concurrently
        qa_task = asyncio.create_task(gen_flashcards_quiz(summary, explanation_level))
        concept_task = asyncio.create_task(generate_concept_map(summary))
        qa, concept_map = await asyncio.gather(qa_task, concept_task)
        
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

        # Populate in-memory lesson store for Learn page
        set_lesson_cache(str(lesson_id), {
            "title": pdf_name,
            "summary": summary,
            "full_text": text,
            "framework": framework_enum.value if hasattr(framework_enum, 'value') else str(framework_enum),
            "bullets": [b.strip() for b in summary.split("•") if b.strip()],
            "flashcards": qa.get("flashcards", []),
            "quiz": qa.get("quiz", []),
            "concept_map": concept_map,
            "chunks": chunks,
            "chunk_embeddings": embeds
        })
        
        # Store lesson_id in conversation metadata for future reference
        conversation_store[conv_id]["metadata"]["lesson_id"] = lesson_id
        
        # Generate personalized response based on framework and content
        system_prompt = f"""You are TrainPI, an AI learning assistant. {get_explanation_prompt(explanation_level)}

A file has been uploaded and processed. Here's what I found:

**Document:** {pdf_name}
**Primary Framework:** {primary_framework}
**Summary:** {summary}

Provide a helpful, encouraging response about what you found in the file and suggest specific learning actions. Be enthusiastic and make the user excited about learning!"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "I've uploaded a file. What can you tell me about it and what interactive learning options can you create for me?"}
        ]
        response = await call_groq(messages)
        
        # Create natural language response only (no action buttons)
        assistant_msg = f"""{response}

I can create learning materials from your document when you ask, for example:
- "Create summary"
- "Create lesson"
- "Generate quiz" (you can say how many, e.g., "Generate 10 quiz questions")
- "Make flashcards" (e.g., "Make 15 flashcards")
- "Create workflow"

Tell me what you'd like to create next!"""

        add_message_to_conversation(conv_id, "assistant", assistant_msg)

        return {
            "response": assistant_msg,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "file_processed": True,
            "summary": summary,
            "framework_detection": framework_detection,
            "interactive_options": False,
            "pdf_name": pdf_name,
            "lesson_id": lesson_id
        }
        
    except Exception as e:
        logger.error(f"File processing for chat failed: {e}")
        raise RuntimeError("Failed to process file for chat.")

def get_conversation_history(conversation_id: str) -> Optional[Dict]:
    """Get conversation history."""
    if conversation_id not in conversation_store:
        return None
    
    conversation = conversation_store[conversation_id]
    return {
        "conversation_id": conversation_id,
        "user_id": conversation["user_id"],
        "messages": conversation["messages"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
        "has_file_context": conversation.get("file_context") is not None
    }

def get_user_conversations(user_id: str) -> List[Dict]:
    """Get all conversations for a user."""
    user_conversations = []
    for conv_id, conversation in conversation_store.items():
        if conversation["user_id"] == user_id:
            user_conversations.append({
                "conversation_id": conv_id,
                "created_at": conversation["created_at"],
                "updated_at": conversation["updated_at"],
                "message_count": len(conversation["messages"]),
                "has_file_context": conversation.get("file_context") is not None
            })
    return user_conversations

def get_side_menu_data(user_id: str) -> Dict:
    """Get data for the side menu including recent PDFs and user preferences."""
    try:
        # Get recent PDFs
        recent_pdfs = get_recent_pdfs(user_id)
        
        # Get user preferences
        user_prefs = get_user_preferences(user_id)
        
        # Get current conversation metadata
        current_conversation = None
        for conv_id, conv_data in conversation_store.items():
            if conv_data["user_id"] == user_id:
                current_conversation = conv_data.get("metadata", {})
                break
        
        return {
            "recent_pdfs": recent_pdfs,
            "user_preferences": user_prefs,
            "current_conversation": current_conversation,
            "available_frameworks": [
                {"name": "FASTAPI", "icon": "🚀"},
                {"name": "REACT", "icon": "⚛️"},
                {"name": "PYTHON", "icon": "🐍"},
                {"name": "NODEJS", "icon": "🟢"},
                {"name": "DOCKER", "icon": "🐳"},
                {"name": "LANGCHAIN", "icon": "🔗"},
                {"name": "ML_AI", "icon": "🤖"},
                {"name": "GENERIC", "icon": "📚"}
            ],
            "explanation_levels": [
                {"value": "5_year_old", "label": "5-year-old", "description": "Simple explanations"},
                {"value": "intern", "label": "Intern", "description": "Intermediate level"},
                {"value": "senior", "label": "Senior Expert", "description": "Advanced explanations"}
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get side menu data: {e}")
        return {
            "recent_pdfs": [],
            "user_preferences": {},
            "current_conversation": {},
            "available_frameworks": [],
            "explanation_levels": []
        }

def update_explanation_level(user_id: str, level: str):
    """Update user's explanation level preference."""
    update_user_preferences(user_id, {"explanation_level": level})

def update_framework_preference(user_id: str, framework: str):
    """Update user's framework preference."""
    update_user_preferences(user_id, {"preferred_framework": framework})
