"""Load and resolve question metadata from contracts.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTRACTS_PATH = Path(__file__).resolve().parent.parent / "contracts.json"


@lru_cache
def load_contracts() -> dict[str, Any]:
    with CONTRACTS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def question_types_by_id() -> dict[str, dict[str, Any]]:
    return {qt["id"]: qt for qt in load_contracts().get("question_types", [])}


def get_question_type(question_type_id: str | None) -> dict[str, Any] | None:
    if not question_type_id:
        return None
    return question_types_by_id().get(question_type_id)


def recommended_bot(question_type_id: str | None) -> str | None:
    qt = get_question_type(question_type_id)
    if qt is None:
        return None
    return str(qt.get("recommended_bot") or "")
