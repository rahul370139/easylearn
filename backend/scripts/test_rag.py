"""
test_rag.py — End-to-end smoke test for the TrainPI RAG pipeline.

Runs the following checks in order, stopping on the first hard failure:
  1. Env: Cohere + Supabase URL/key are set.
  2. Cohere: a single embedding call succeeds and returns 384-dim vectors.
  3. Supabase: the `interview_prep_kb` table is reachable. If not, we print
     the migration SQL with copy-paste instructions and exit cleanly.
  4. Chunker: the markdown chunker produces non-empty chunks for the
     interview_prep corpus.
  5. Ingest: chunks are embedded via Cohere and upserted into Supabase
     (idempotent — safe to re-run). Skipped if `--skip-ingest` is passed
     so you can do dry runs.
  6. Retrieval: three sample queries are executed and their top-3 results
     are printed.

Usage:
    cd backend
    python -m scripts.test_rag                              # full run
    python -m scripts.test_rag --skip-ingest                # only verify
    python -m scripts.test_rag --corpus /path/to/markdown   # custom corpus

Exit codes:
    0  all checks passed
    1  blocked on environment / table missing / API failure
    2  ingest produced zero rows
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Make `backend/` importable when run as `python -m scripts.test_rag`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env", override=False)


DEFAULT_CORPUS = ROOT.parent.parent / "interview_prep"
SAMPLE_QUERIES = [
    "What is retrieval-augmented generation and why does it matter?",
    "How do transformers handle long contexts?",
    "Explain LoRA fine-tuning in one paragraph",
]


def _section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


async def step_env() -> None:
    _section("1. Environment")
    missing = [k for k in (
        "COHERE_API_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    ) if not os.getenv(k)]
    if missing:
        print(f"  ✗ missing env vars: {missing}")
        sys.exit(1)
    print(f"  COHERE_API_KEY .................. set")
    print(f"  NEXT_PUBLIC_SUPABASE_URL ........ {os.getenv('NEXT_PUBLIC_SUPABASE_URL')}")
    print(f"  NEXT_PUBLIC_SUPABASE_ANON_KEY ... set")
    if os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print(f"  SUPABASE_SERVICE_ROLE_KEY ....... set (will be used for ingest)")


async def step_cohere() -> None:
    _section("2. Cohere embedding")
    from distiller import cohere_embed
    out = await cohere_embed(["TrainPI smoke test."])
    if not out or not out[0] or len(out[0]) != 384:
        print(f"  ✗ unexpected embedding shape: {len(out)} x {len(out[0]) if out else 0}")
        sys.exit(1)
    print(f"  ✓ embed shape: ({len(out)}, {len(out[0])})")


def step_table() -> None:
    _section("3. Supabase table reachability")
    from rag_kb import SUPA
    if SUPA is None:
        print("  ✗ Supabase client not initialized")
        sys.exit(1)
    try:
        SUPA.table("interview_prep_kb").select("id", count="exact").limit(1).execute()
        print("  ✓ interview_prep_kb table is reachable")
    except Exception as e:
        msg = str(e)
        print(f"  ✗ table check failed: {msg[:300]}")
        if "PGRST205" in msg or "not find" in msg:
            sql_path = ROOT / "migrations" / "20260506_interview_prep_kb.sql"
            print()
            print("  → Apply the migration in Supabase Studio:")
            print(f"    1. Open  https://supabase.com/dashboard/project/{_project_ref()}/sql")
            print("    2. New query → paste the SQL below → Run.")
            print(f"    (Source file: {sql_path})")
            print()
            print("--- copy below ---")
            print(sql_path.read_text(encoding="utf-8"))
            print("--- copy above ---")
        sys.exit(1)


def _project_ref() -> str:
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    return url.split("//", 1)[-1].split(".", 1)[0]


def step_chunker(corpus: Path) -> None:
    _section("4. Markdown chunker")
    from rag_kb import chunk_markdown
    files = sorted(corpus.rglob("*.md"))
    if not files:
        print(f"  ✗ no markdown files at {corpus}")
        sys.exit(1)
    total = 0
    for fp in files:
        chunks = chunk_markdown(fp.read_text(encoding="utf-8", errors="ignore"), str(fp.relative_to(corpus)))
        total += len(chunks)
    print(f"  ✓ {len(files)} files → {total} chunks")


async def step_ingest(corpus: Path) -> int:
    _section("5. Ingest (Cohere → Supabase)")
    from rag_kb import ingest_directory
    print(f"  → corpus: {corpus}")
    print("    (this calls Cohere for every chunk; expect a few minutes on first run)")
    res = await ingest_directory(corpus)
    print(f"  result: {res}")
    if res.get("ingested", 0) <= 0 and res.get("skipped", 0) > 0:
        print("  ✗ all upserts failed — check RLS policies in the migration")
        sys.exit(2)
    return res.get("ingested", 0)


async def step_retrieve() -> None:
    _section("6. Retrieval")
    from rag_kb import retrieve_kb, format_kb_context
    for q in SAMPLE_QUERIES:
        print(f"\n  Q: {q}")
        matches = await retrieve_kb(q, top_k=3)
        if not matches:
            print("    (no matches — embeddings not yet stored?)")
            continue
        for m in matches:
            doc = m.get("doc", "?")
            sec = m.get("section") or "(no heading)"
            sim = m.get("similarity")
            sim_s = f"{sim:.3f}" if isinstance(sim, (int, float)) else "?"
            preview = (m.get("chunk") or "").strip().replace("\n", " ")[:140]
            print(f"    • [{doc} # {sec}] sim={sim_s}")
            print(f"      {preview}…")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--skip-ingest", action="store_true")
    args = ap.parse_args()

    await step_env()
    await step_cohere()
    step_table()
    step_chunker(args.corpus)
    if args.skip_ingest:
        print("\n  --skip-ingest: ingest skipped")
    else:
        await step_ingest(args.corpus)
    await step_retrieve()
    print("\nAll checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
