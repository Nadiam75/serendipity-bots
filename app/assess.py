import json
import re
from typing import Any

from app.prompts import ASSESS_SYSTEM_PROMPT
from app.schemas import AssessArea, AssessRequest, AssessResponse, ObjectiveAssessment


def flatten_objectives(areas: list[AssessArea]) -> list[tuple[str, str, str]]:
    """Return (area, sub_area, objective) triples in input order."""
    triples: list[tuple[str, str, str]] = []
    for area in areas:
        for sub in area.sub_areas:
            for objective in sub.objectives:
                text = objective.strip()
                if text:
                    triples.append((area.name, sub.name, text))
    return triples


def build_assess_user_prompt(body: AssessRequest) -> str:
    lines: list[str] = []
    if body.user_prompt and body.user_prompt.strip():
        lines.extend(
            [
                "دستورالعمل اضافی از سمت درخواست‌کننده:",
                body.user_prompt.strip(),
                "",
            ]
        )
    lines.extend(
        [
            "سؤال:",
            body.question.strip(),
            "",
            "پاسخ کودک:",
            body.answer.strip(),
            "",
            "چارچوب ارزیابی (areas → sub_areas → objectives):",
        ]
    )
    for area in body.areas:
        lines.append(f"- حوزه: {area.name}")
        for sub in area.sub_areas:
            lines.append(f"  - زیر‌حوزه: {sub.name}")
            for objective in sub.objectives:
                lines.append(f"    - هدف: {objective.strip()}")
    lines.append("")
    lines.append("پاسخ کودک را نسبت به هر هدف ارزیابی کن و فقط JSON بده.")
    return "\n".join(lines)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("model did not return JSON") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("assessment JSON must be an object")
    return data


def parse_assess_response(
    raw_text: str,
    expected: list[tuple[str, str, str]],
) -> AssessResponse:
    data = _extract_json_object(raw_text)
    items = data.get("assessments")
    if not isinstance(items, list) or not items:
        raise ValueError("assessment JSON missing assessments[]")

    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = (
            str(item.get("area", "")).strip(),
            str(item.get("sub_area", "")).strip(),
            str(item.get("objective", "")).strip(),
        )
        by_key[key] = item
        ordered.append(item)

    assessments: list[ObjectiveAssessment] = []
    for i, (area, sub_area, objective) in enumerate(expected):
        item = by_key.get((area, sub_area, objective))
        if item is None and i < len(ordered):
            item = ordered[i]
        if item is None:
            raise ValueError(f"missing assessment for objective: {objective}")

        status = str(item.get("status", "partial")).strip().lower()
        if status not in {"met", "partial", "not_met"}:
            status = "partial"
        try:
            score = float(item.get("score", 0.5))
        except (TypeError, ValueError):
            score = 0.5
        score = max(0.0, min(1.0, score))
        feedback = str(item.get("feedback") or "").strip() or "ارزیابی کامل نشد."

        assessments.append(
            ObjectiveAssessment(
                area=area,
                sub_area=sub_area,
                objective=objective,
                status=status,  # type: ignore[arg-type]
                score=score,
                feedback=feedback,
            )
        )

    summary = str(data.get("summary") or "").strip() or "ارزیابی انجام شد."
    return AssessResponse(assessments=assessments, summary=summary)


def assess_request_parts(body: AssessRequest) -> tuple[str, str]:
    """Return (instructions, input) for AvalAI Responses API."""
    return ASSESS_SYSTEM_PROMPT, build_assess_user_prompt(body)
