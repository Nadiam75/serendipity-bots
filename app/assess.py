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
    if body.image_description and body.image_description.strip():
        lines.extend(
            [
                "توضیح تصویر:",
                body.image_description.strip(),
                "",
            ]
        )
    lines.extend(
        [
            "سؤال:",
            body.question.strip(),
            "",
        ]
    )
    if body.answer and body.answer.strip():
        lines.extend(["پاسخ کودک:", body.answer.strip(), ""])
    lines.extend(
        [
            f"نوع سؤال (question_mode): {body.question_mode}",
        ]
    )
    if body.question_type_id:
        lines.append(f"شناسه نوع سؤال (question_type_id): {body.question_type_id}")
    if body.assess_mode:
        lines.append(f"حالت ارزیابی (assess_mode): {body.assess_mode}")
    if body.interests:
        lines.append(f"علایق کودک: {', '.join(i.strip() for i in body.interests if i.strip())}")
    if body.question_type:
        lines.append(f"چیدمان (layout): {body.question_type}")
    if body.min_selections is not None:
        lines.append(f"حداقل انتخاب (min_selections): {body.min_selections}")
    if body.max_selections is not None:
        lines.append(f"حداکثر انتخاب (max_selections): {body.max_selections}")
    if body.answer_count is not None:
        lines.append(f"تعداد پاسخ (answer_count): {body.answer_count}")
    if body.max_words_per_answer is not None:
        lines.append(f"حداکثر کلمات (max_words_per_answer): {body.max_words_per_answer}")
    if body.max_characters_per_answer is not None:
        lines.append(f"حداکثر کاراکتر (max_characters_per_answer): {body.max_characters_per_answer}")
    if body.answer_placeholders:
        lines.append(f"placeholderها: {', '.join(body.answer_placeholders)}")
    if body.story_title:
        lines.append(f"عنوان صفحه داستان: {body.story_title}")
    if body.story_image_path:
        lines.append(f"مسیر تصویر صفحه: {body.story_image_path}")
    if body.selected_option_ids:
        lines.append(f"گزینه‌های انتخاب‌شده: {', '.join(body.selected_option_ids)}")
    if body.correct_option_ids:
        lines.append(f"گزینه‌های صحیح: {', '.join(body.correct_option_ids)}")
    if body.options:
        lines.append("گزینه‌های موجود:")
        for opt in body.options:
            label = opt.label or opt.alt or opt.image_path or opt.id
            lines.append(f"  - {opt.id}: {label}")
        lines.append("")
    lines.extend(
        [
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


def _normalize_score_0_5(raw: Any) -> int:
    """Coerce model score to integer 0–5. Legacy 0–1 floats map via *5."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0
    if 0.0 < value < 1.0:
        value = value * 5.0
    return int(max(0, min(5, round(value))))


def score_segment_from_overall(overall_score: int) -> str:
    if overall_score <= 1:
        return "نوآموز"
    if overall_score <= 3:
        return "توانمند"
    return "پیشرو"


def parse_assess_response(
    raw_text: str,
    expected: list[tuple[str, str, str]],
    question_mode: str,
    *,
    question_type_id: str | None = None,
    assess_mode: str | None = None,
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
        score = _normalize_score_0_5(item.get("score", 0))
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

    if assessments:
        overall_score = int(
            max(0, min(5, round(sum(a.score for a in assessments) / len(assessments))))
        )
    else:
        overall_score = 0
    score_segment = score_segment_from_overall(overall_score)

    mode = str(data.get("question_mode") or question_mode).strip().lower()
    if mode not in {"convergent", "divergent"}:
        mode = question_mode

    return AssessResponse(
        question_mode=mode,  # type: ignore[arg-type]
        question_type_id=question_type_id,  # type: ignore[arg-type]
        assess_mode=assess_mode,  # type: ignore[arg-type]
        assessments=assessments,
        overall_score=overall_score,
        score_segment=score_segment,  # type: ignore[arg-type]
        summary=summary,
    )


def assess_request_parts(body: AssessRequest) -> tuple[str, str]:
    """Return (instructions, input) for AvalAI Responses API."""
    return ASSESS_SYSTEM_PROMPT, build_assess_user_prompt(body)
