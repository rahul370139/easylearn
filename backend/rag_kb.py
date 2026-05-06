"""
rag_kb.py — Knowledge-base RAG over the `interview_prep` markdown corpus.

Architecture:
    interview_prep/*.md  ──► chunk_markdown ──► cohere_embed (384-dim)
                                             └─► Supabase table `interview_prep_kb`
                                                    columns: id, doc, section, chunk, embedding(vector(384))

    user query  ──► generate_content_embedding ──► Supabase RPC `match_interview_prep`
                                                  └─► top-k chunks + score

The ingestion is idempotent: each row's `chunk_hash` is unique so re-running
`python -m rag_kb ingest` will update existing rows in place rather than
duplicating them.

We deliberately keep the Cohere model (`embed-english-light-v3.0`, 384 dim)
identical to what `distiller.py` already uses, so the same query embedding
function works for both PDF chunks and the KB.

Supabase setup (run once in the SQL editor):

    create extension if not exists vector;

    create table if not exists interview_prep_kb (
      id            bigserial primary key,
      doc           text not null,
      section       text,
      chunk         text not null,
      chunk_hash    text not null unique,
      embedding     vector(384),
      created_at    timestamptz default now()
    );

    create index if not exists interview_prep_kb_embedding_idx
      on interview_prep_kb using ivfflat (embedding vector_cosine_ops)
      with (lists = 100);

    create or replace function match_interview_prep(
      query_embedding vector(384),
      match_count int default 6
    )
    returns table (id bigint, doc text, section text, chunk text, similarity float)
    language sql stable
    as $$
      select id, doc, section, chunk,
             1 - (embedding <=> query_embedding) as similarity
      from interview_prep_kb
      where embedding is not null
      order by embedding <=> query_embedding
      limit match_count;
    $$;

CLI usage:

    # Ingest the entire interview_prep folder (idempotent)
    python -m rag_kb ingest /path/to/interview_prep

    # Quick retrieval test
    python -m rag_kb query "What is RAG?"
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from distiller import cohere_embed, generate_content_embedding
from supabase_helper import SUPA as _SUPA_ANON

# Prefer a service-role client for ingestion when available (bypasses RLS).
# Falls back to the anon client used elsewhere in the backend.
def _get_supa():
    try:
        import supabase
        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        sr_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if url and sr_key:
            return supabase.create_client(url, sr_key)
    except Exception as e:
        logger.warning(f"Service-role client unavailable, using anon: {e}")
    return _SUPA_ANON

SUPA = _get_supa()


# ---------------------------------------------------------------------------
# Chunking — markdown-aware: split by `## ` headings, then enforce a max size.
# ---------------------------------------------------------------------------

CHUNK_TARGET_CHARS = 1800
CHUNK_OVERLAP_CHARS = 250
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


def chunk_markdown(text: str, doc_name: str) -> List[Dict]:
    """Split a markdown document into RAG-friendly chunks.

    Returns: [{doc, section, chunk}]
    """
    if not text:
        return []

    # Find heading positions; keep tuples of (offset, level, title)
    sections: List[Tuple[int, int, str]] = []
    for m in HEADING_RE.finditer(text):
        sections.append((m.start(), len(m.group(1)), m.group(2).strip()))
    sections.append((len(text), 0, ""))  # sentinel

    chunks: List[Dict] = []
    if len(sections) <= 1:
        # No headings → fall back to paragraph windowing
        for c in _windowed(text):
            chunks.append({"doc": doc_name, "section": None, "chunk": c})
        return chunks

    # Walk section-by-section
    for i in range(len(sections) - 1):
        start, _level, title = sections[i]
        end, _, _ = sections[i + 1]
        body = text[start:end].strip()
        if not body:
            continue
        for c in _windowed(body):
            chunks.append({"doc": doc_name, "section": title, "chunk": c})
    return chunks


def _windowed(text: str) -> List[str]:
    """Return overlapping windows of `text`, each ≤ CHUNK_TARGET_CHARS."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= CHUNK_TARGET_CHARS:
        return [text]

    pieces: List[str] = []
    i = 0
    while i < len(text):
        end = min(i + CHUNK_TARGET_CHARS, len(text))
        # Snap to nearest paragraph break if possible
        if end < len(text):
            nl = text.rfind("\n\n", i + CHUNK_TARGET_CHARS // 2, end)
            if nl != -1:
                end = nl
        pieces.append(text[i:end].strip())
        if end >= len(text):
            break
        i = max(end - CHUNK_OVERLAP_CHARS, i + 1)
    return [p for p in pieces if p]


def _chunk_hash(doc: str, section: Optional[str], chunk: str) -> str:
    h = hashlib.sha256()
    h.update((doc or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((section or "").encode("utf-8"))
    h.update(b"\x00")
    h.update(chunk.encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

async def _embed_in_batches(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """Embed `texts` in fixed batches, respecting Cohere rate limits."""
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            embeds = await cohere_embed(batch)
        except Exception as e:
            logger.error(f"Embedding batch {i} failed: {e}")
            embeds = [[] for _ in batch]
        out.extend(embeds)
        await asyncio.sleep(0.2)  # gentle pacing
    return out


async def ingest_directory(directory: Path) -> Dict:
    """Walk a directory of markdown files and upsert chunks into Supabase.

    Idempotent — `chunk_hash` is unique so re-running the same content is a no-op.
    """
    if SUPA is None:
        raise RuntimeError(
            "Supabase client not initialized. Set NEXT_PUBLIC_SUPABASE_URL and "
            "NEXT_PUBLIC_SUPABASE_ANON_KEY (or the service role key) in the env."
        )

    md_files = sorted(directory.rglob("*.md"))
    if not md_files:
        return {"ingested": 0, "files": 0, "skipped": 0, "message": "No markdown files found"}

    all_rows: List[Dict] = []
    for fp in md_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Skipping {fp}: {e}")
            continue
        rel = str(fp.relative_to(directory)) if fp.is_relative_to(directory) else fp.name
        for chunk_dict in chunk_markdown(text, doc_name=rel):
            chunk_dict["chunk_hash"] = _chunk_hash(
                chunk_dict["doc"], chunk_dict.get("section"), chunk_dict["chunk"]
            )
            all_rows.append(chunk_dict)

    if not all_rows:
        return {"ingested": 0, "files": len(md_files), "skipped": 0, "message": "No chunks produced"}

    logger.info(f"Embedding {len(all_rows)} chunks from {len(md_files)} files…")
    embeddings = await _embed_in_batches([r["chunk"] for r in all_rows])

    rows_with_embed = []
    for row, emb in zip(all_rows, embeddings):
        if not emb:
            continue
        rows_with_embed.append({
            "doc": row["doc"],
            "section": row.get("section"),
            "chunk": row["chunk"],
            "chunk_hash": row["chunk_hash"],
            "embedding": emb,
        })

    inserted = 0
    skipped = 0
    # Upsert in moderate batches; Supabase has a payload size cap.
    for i in range(0, len(rows_with_embed), 100):
        batch = rows_with_embed[i : i + 100]
        try:
            SUPA.table("interview_prep_kb").upsert(batch, on_conflict="chunk_hash").execute()
            inserted += len(batch)
        except Exception as e:
            logger.error(f"Upsert batch {i} failed: {e}")
            skipped += len(batch)

    return {
        "ingested": inserted,
        "skipped": skipped,
        "files": len(md_files),
        "chunks": len(rows_with_embed),
    }


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

async def retrieve_kb(query: str, top_k: int = 6) -> List[Dict]:
    """Return the top-k KB chunks for a natural-language query.

    Each item: { doc, section, chunk, similarity }
    Empty list on any failure (callers MUST handle empty gracefully).
    """
    if SUPA is None or not query or not query.strip():
        return []

    try:
        q_embed = await generate_content_embedding(query)
    except Exception as e:
        logger.warning(f"KB retrieval embedding failed: {e}")
        return []
    if not q_embed:
        return []

    try:
        res = SUPA.rpc(
            "match_interview_prep",
            {"query_embedding": q_embed, "match_count": top_k},
        ).execute()
        return res.data or []
    except Exception as e:
        # If the RPC is not installed, fall back to a naive client-side scan.
        logger.warning(f"KB RPC failed ({e}); using client-side scan fallback.")
        try:
            res = SUPA.table("interview_prep_kb").select("doc,section,chunk,embedding").limit(2000).execute()
            rows = res.data or []
        except Exception:
            return []
        return _client_side_topk(rows, q_embed, top_k)


def _client_side_topk(rows: List[Dict], q_embed: List[float], k: int) -> List[Dict]:
    import math
    if not rows:
        return []
    scored: List[Tuple[float, Dict]] = []
    qmag = math.sqrt(sum(x * x for x in q_embed)) or 1.0
    for r in rows:
        e = r.get("embedding") or []
        if not e or len(e) != len(q_embed):
            continue
        emag = math.sqrt(sum(x * x for x in e)) or 1.0
        dot = sum(a * b for a, b in zip(q_embed, e))
        sim = dot / (qmag * emag)
        scored.append((sim, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {"doc": r["doc"], "section": r.get("section"), "chunk": r["chunk"], "similarity": float(s)}
        for s, r in scored[:k]
    ]


def format_kb_context(matches: List[Dict], max_chars: int = 6000) -> str:
    """Render KB matches into a single retrieval-context string for the LLM.

    Each chunk is prefixed with its source so the model can cite:
        [doc#section] <chunk text>
    """
    out: List[str] = []
    used = 0
    for m in matches:
        head = f"[{m.get('doc', 'kb')}"
        if m.get("section"):
            head += f"#{m['section']}"
        head += "]"
        block = f"{head}\n{m.get('chunk', '').strip()}"
        if used + len(block) > max_chars:
            break
        out.append(block)
        used += len(block)
    return "\n\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help() -> None:
    print(
        "Usage:\n"
        "  python -m rag_kb ingest <path-to-interview_prep>\n"
        "  python -m rag_kb query  <natural language question>\n"
    )


async def _main_async() -> int:
    if len(sys.argv) < 2:
        _print_help()
        return 1
    cmd = sys.argv[1]
    if cmd == "ingest":
        if len(sys.argv) < 3:
            _print_help()
            return 1
        path = Path(sys.argv[2]).expanduser().resolve()
        if not path.exists():
            print(f"Path does not exist: {path}")
            return 1
        result = await ingest_directory(path)
        print(result)
        return 0
    if cmd == "query":
        q = " ".join(sys.argv[2:]).strip()
        if not q:
            _print_help()
            return 1
        matches = await retrieve_kb(q, top_k=5)
        for m in matches:
            print(f"\n— {m.get('doc')} #{m.get('section')} (sim={m.get('similarity'):.3f})")
            print(m.get("chunk", "")[:400])
        return 0
    _print_help()
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main_async()))
