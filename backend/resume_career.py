"""
resume_career.py — Resume-driven career upgrade.

Pipeline:
    PDF resume ──► pdf_to_text (distiller) ──► call_groq (structured extract)
                                            └─► parsed resume JSON

    parsed resume + target_role + interests
                ──► O*NET row lookup (career_matcher.matcher.career_data)
                ──► call_groq (skill gap analysis, grounded in resume + O*NET)
                ──► call_groq (3-stage roadmap + 90-day plan + concrete projects)

The whole thing lives in one module so career-page logic is independent
from the Learn page chat machinery, and so a future migration (e.g. adding
a fine-tuned skill-gap model) only changes one file.

Public functions:
    parse_resume(file_path) -> dict
    build_career_plan(parsed_resume, target_role, interests) -> dict
    upgrade_from_pdf(file_path, target_role, interests) -> dict   # one-shot

All LLM calls return JSON-only and are wrapped in `_parse_json_safely`,
so a malformed model response degrades to an empty dict rather than crashing.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from distiller import (
    call_groq,
    pdf_to_text,
    _parse_json_safely,
)
from career_matcher import matcher  # already loads onet_bls_trimmed.csv


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

_RESUME_EXTRACT_PROMPT = """You are an expert resume parser. Read the resume text below and extract a structured JSON profile.

Resume text:
\"\"\"
{resume_text}
\"\"\"

Return ONLY valid JSON (no prose, no markdown fences). Use this exact schema:

{{
  "name": str | null,
  "headline": str | null,                     // current role / summary line
  "years_of_experience": number | null,        // estimate from work history
  "current_role": str | null,
  "current_company": str | null,
  "skills": [str],                              // technical + soft skills, deduped, lowercase preferred
  "experience": [
    {{
      "role": str,
      "company": str,
      "start": str | null,
      "end": str | null,
      "achievements": [str]                     // 1-3 bullet points, only if explicitly written
    }}
  ],
  "education": [
    {{ "degree": str, "school": str, "year": str | null }}
  ],
  "projects": [
    {{ "name": str, "description": str, "stack": [str] }}
  ],
  "certifications": [str],
  "languages": [str]
}}

Rules:
- If a field is missing in the resume, use null or [] — DO NOT invent.
- Skills MUST come from the resume body (skills section, projects, experience), not from the job titles alone.
- Keep achievements grounded; never paraphrase missing content."""


async def parse_resume(file_path: Path) -> Dict:
    """Parse a resume PDF into a structured JSON profile."""
    try:
        text = pdf_to_text(file_path)
    except Exception as e:
        logger.error(f"Resume PDF extraction failed: {e}")
        raise RuntimeError("Could not read resume PDF (it may be scanned/image-only).")

    # Truncate to keep LLM input bounded — most resumes are <2 pages
    text = text[:18000]

    raw = await call_groq([
        {"role": "user", "content": _RESUME_EXTRACT_PROMPT.format(resume_text=text)}
    ])
    parsed = _parse_json_safely(raw) or {}

    # Light normalization so downstream code can rely on shape
    parsed.setdefault("skills", [])
    parsed.setdefault("experience", [])
    parsed.setdefault("education", [])
    parsed.setdefault("projects", [])
    parsed.setdefault("certifications", [])
    parsed.setdefault("languages", [])
    parsed["skills"] = [s.strip() for s in parsed.get("skills", []) if isinstance(s, str) and s.strip()]
    return parsed


# ---------------------------------------------------------------------------
# O*NET match
# ---------------------------------------------------------------------------

def _find_onet_row(target_role: str) -> Optional[Dict]:
    """Pick the closest O*NET career row by title.

    Strategy:
      1. exact case-insensitive match on title
      2. substring match (target ⊂ title or title ⊂ target)
      3. fall back to None — the LLM still gets the best lexical guess via
         word-overlap scoring so we don't return a totally unrelated row.
    """
    if not target_role:
        return None

    df: pd.DataFrame = matcher.career_data  # type: ignore[attr-defined]
    if df is None or df.empty:
        return None

    target_norm = target_role.strip().lower()

    # 1. exact
    exact = df[df["title"].str.lower() == target_norm]
    if len(exact):
        return exact.iloc[0].to_dict()

    # 2. substring
    contains = df[df["title"].str.lower().str.contains(re.escape(target_norm), na=False)]
    if len(contains):
        return contains.iloc[0].to_dict()

    # 3. word-overlap scoring (cheap heuristic, no embeddings)
    target_words = set(re.findall(r"[a-z]+", target_norm))
    if not target_words:
        return None

    def score(title: str) -> int:
        return len(target_words & set(re.findall(r"[a-z]+", str(title).lower())))

    df_scored = df.assign(_match=df["title"].apply(score))
    best = df_scored.sort_values("_match", ascending=False).iloc[0]
    return best.to_dict() if int(best["_match"]) > 0 else None


def _onet_summary(row: Optional[Dict]) -> str:
    """Render an O*NET row as a compact prompt-friendly summary."""
    if not row:
        return "(No O*NET match for this role; ground the response in widely-accepted industry expectations for the title instead.)"
    return (
        f"Title: {row.get('title')}\n"
        f"Top skills: {row.get('top_skills')}\n"
        f"Day in life: {row.get('day_in_life')}\n"
        f"Salary band: ${int(row.get('salary_low', 0)):,} – ${int(row.get('salary_high', 0)):,}\n"
        f"Projected growth: {row.get('growth_pct')}%"
    )


# ---------------------------------------------------------------------------
# Skill gap + plan
# ---------------------------------------------------------------------------

_PLAN_PROMPT = """You are a senior career coach building a tailored upskilling plan.

CANDIDATE PROFILE (parsed from their resume):
{resume_json}

TARGET ROLE: {target_role}

INTERESTS: {interests}

INDUSTRY REFERENCE (from O*NET / BLS):
{onet_summary}

Produce a single JSON object — no prose, no markdown. Schema:

{{
  "skill_gap": {{
    "strengths": [str],                  // candidate skills that already match the target role
    "transferable": [str],               // skills that partially apply (rephrase how they transfer)
    "gaps": [str],                       // missing skills the role explicitly requires
    "blockers": [str],                   // hard prerequisites (degrees, certs, years) the candidate is missing
    "readiness_score": number            // 0-100, honest estimate of how close the candidate is today
  }},
  "roadmap": {{
    "entry_level":   {{ "title": str, "duration": str, "salary_range": str, "skills_to_acquire": [str], "responsibilities": [str], "milestones": [str] }},
    "mid_level":     {{ "title": str, "duration": str, "salary_range": str, "skills_to_acquire": [str], "responsibilities": [str], "milestones": [str] }},
    "senior_level":  {{ "title": str, "duration": str, "salary_range": str, "skills_to_acquire": [str], "responsibilities": [str], "milestones": [str] }}
  }},
  "ninety_day_plan": [                    // weekly cadence for the first 90 days
    {{ "week": "1-2", "focus": str, "actions": [str], "deliverable": str }},
    {{ "week": "3-4", "focus": str, "actions": [str], "deliverable": str }},
    {{ "week": "5-6", "focus": str, "actions": [str], "deliverable": str }},
    {{ "week": "7-8", "focus": str, "actions": [str], "deliverable": str }},
    {{ "week": "9-12", "focus": str, "actions": [str], "deliverable": str }}
  ],
  "projects_to_build": [                  // concrete, portfolio-grade projects tailored to candidate's existing experience
    {{ "title": str, "why": str, "stack": [str], "scope": str, "stretch_goal": str }}
  ],
  "resources": [                          // books / courses / docs — names only, no URLs
    {{ "title": str, "type": "book"|"course"|"doc"|"paper", "why": str }}
  ],
  "interview_prep": {{
    "core_topics": [str],
    "behavioral_themes": [str],           // pull from candidate's actual experience to anchor STAR stories
    "system_design_targets": [str]
  }},
  "market_insights": {{
    "salary_range": str,
    "growth_outlook": str,
    "hot_skills": [str]
  }}
}}

Rules:
- Tailor every section to the candidate's actual resume — reference their stack, projects, and experience explicitly when relevant.
- Use the O*NET salary band as the source of truth for "market_insights.salary_range".
- Keep "gaps" honest: if the candidate is already strong, say so (small gap list is fine).
- "projects_to_build" must be 2-3 items, each something the candidate could realistically ship in 2-6 weeks.
- No filler text. No emojis. No "Conclusion" sections."""


async def build_career_plan(
    parsed_resume: Dict,
    target_role: str,
    interests: List[str],
) -> Dict:
    """Run skill-gap + roadmap + 90-day plan in a single LLM call."""
    onet_row = _find_onet_row(target_role)

    prompt = _PLAN_PROMPT.format(
        resume_json=json.dumps(parsed_resume, ensure_ascii=False)[:8000],
        target_role=target_role or "(unspecified)",
        interests=", ".join(interests) if interests else "(none specified)",
        onet_summary=_onet_summary(onet_row),
    )

    raw = await call_groq([{"role": "user", "content": prompt}])
    plan = _parse_json_safely(raw) or {}

    # Stitch O*NET-grounded numbers back in even if the model elided them
    if onet_row and isinstance(plan.get("market_insights"), dict):
        mi = plan["market_insights"]
        if not mi.get("salary_range"):
            mi["salary_range"] = (
                f"${int(onet_row.get('salary_low', 0)):,} – ${int(onet_row.get('salary_high', 0)):,}"
            )
        if not mi.get("growth_outlook"):
            mi["growth_outlook"] = f"{onet_row.get('growth_pct', 0)}% projected growth"

    return {
        "target_role": target_role,
        "interests": interests,
        "onet_match": {
            "title": onet_row.get("title") if onet_row else None,
            "soc_code": onet_row.get("soc_code") if onet_row else None,
            "salary_low": onet_row.get("salary_low") if onet_row else None,
            "salary_high": onet_row.get("salary_high") if onet_row else None,
            "growth_pct": onet_row.get("growth_pct") if onet_row else None,
        },
        "plan": plan,
    }


async def upgrade_from_pdf(
    file_path: Path,
    target_role: str,
    interests: List[str],
) -> Dict:
    """One-shot helper: parse resume + build plan."""
    parsed = await parse_resume(file_path)
    plan = await build_career_plan(parsed, target_role, interests)
    return {"resume": parsed, **plan}
