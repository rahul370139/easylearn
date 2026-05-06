"""Persist resume-driven career upgrade plans per user (JSON on disk).

Production alternative: Supabase table. This keeps Hostinger VPS deploys simple
without new migrations.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

_PLANS_DIR = Path(__file__).resolve().parent / "data" / "career_plans"


def _safe_user_segment(user_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", user_id.strip())[:200]
    return cleaned or "anonymous"


def save_latest_plan(user_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """Write the latest career plan snapshot for ``user_id``."""
    _PLANS_DIR.mkdir(parents=True, exist_ok=True)
    path = _PLANS_DIR / f"{_safe_user_segment(user_id)}.json"
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "plan": plan,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    logger.info("Saved career plan for user segment {}", _safe_user_segment(user_id))
    return payload


def load_latest_plan(user_id: str) -> Optional[Dict[str, Any]]:
    """Return ``{saved_at, user_id, plan}`` or ``None`` if missing."""
    path = _PLANS_DIR / f"{_safe_user_segment(user_id)}.json"
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load career plan for {}: {}", user_id, e)
        return None
