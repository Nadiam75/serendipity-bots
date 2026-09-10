import json
import re
from typing import Any

from app.contracts import get_question_type
from app.prompts import GENERATE_EXERCISES_SYSTEM_PROMPT
from app.schemas import (
    GenerateExercisesRequest,
    GenerateExercisesResponse,
    GeneratedExercise,
    GeneratedMcqOption,
    McqExercise,
    QuestionTypeId,
    StoryPage,
    StoryPageMeta,
)


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
        raise ValueError("generation JSON must be an object")
    return data


def _parse_options(raw_options: list[Any]) -> list[GeneratedMcqOption]:
    options: list[GeneratedMcqOption] = []
    for opt in raw_options:
        if not isinstance(opt, dict):
            continue
        opt_id = str(opt.get("id") or "").strip()
        if not opt_id:
            continue
        options.append(
            GeneratedMcqOption(
                id=opt_id,
                label=str(opt.get("label")).strip() if opt.get("label") else None,
                alt=str(opt.get("alt")).strip() if opt.get("alt") else None,
                image_path=str(opt.get("image_path")).strip() if opt.get("image_path") else None,
            )
        )
    return options


def _default_question_type_id(body: GenerateExercisesRequest) -> QuestionTypeId:
    if body.question_type_id:
        return body.question_type_id
    if body.question_mode == "divergent":
        return "open_question"
    if body.max_selections == 1 or (body.min_selections == 1 and body.max_selections == 1):
        return "mcq_single"
    return "mcq_multi"


def _parse_story_page(item: dict[str, Any], *, fallback_text: str, body: GenerateExercisesRequest) -> StoryPage:
    raw_page = item.get("story_page")
    if isinstance(raw_page, dict):
        meta_raw = raw_page.get("meta") or {}
        qt = get_question_type(str(item.get("question_type_id") or body.question_type_id or ""))
        layout = meta_raw.get("layout") or (qt or {}).get("layout") or (
            "question" if body.question_mode == "divergent" else "multiple_choice"
        )
        question_mode = meta_raw.get("question_mode") or body.question_mode or "convergent"
        return StoryPage(
            type="exercise",
            title=str(raw_page.get("title") or body.story_title or "سؤال"),
            text=str(raw_page.get("text") or fallback_text),
            image_path=raw_page.get("image_path") or body.story_image_path,
            meta=StoryPageMeta(
                layout=layout,  # type: ignore[arg-type]
                question_mode=question_mode,  # type: ignore[arg-type]
                min_selections=meta_raw.get("min_selections", body.min_selections),
                max_selections=meta_raw.get("max_selections", body.max_selections),
                answer_count=meta_raw.get("answer_count", body.answer_count),
                max_words_per_answer=meta_raw.get("max_words_per_answer", body.max_words_per_answer),
                max_characters_per_answer=meta_raw.get(
                    "max_characters_per_answer", body.max_characters_per_answer
                ),
                answer_placeholders=meta_raw.get("answer_placeholders", body.answer_placeholders),
            ),
        )

    qt = get_question_type(body.question_type_id)
    layout = (qt or {}).get("layout") or (
        "question" if body.question_mode == "divergent" else "multiple_choice"
    )
    return StoryPage(
        type="exercise",
        title=body.story_title or "سؤال",
        text=fallback_text,
        image_path=body.story_image_path,
        meta=StoryPageMeta(
            layout=layout,  # type: ignore[arg-type]
            question_mode=body.question_mode or "convergent",  # type: ignore[arg-type]
            min_selections=body.min_selections,
            max_selections=body.max_selections,
            answer_count=body.answer_count,
            max_words_per_answer=body.max_words_per_answer,
            max_characters_per_answer=body.max_characters_per_answer,
            answer_placeholders=body.answer_placeholders,
        ),
    )


def _parse_exercise(item: dict[str, Any], *, question_text: str) -> McqExercise | None:
    raw_exercise = item.get("exercise")
    if raw_exercise is None:
        return None
    if not isinstance(raw_exercise, dict):
        return None

    options = _parse_options(raw_exercise.get("options") or [])
    correct_ids = [
        str(x).strip() for x in (raw_exercise.get("correct_option_ids") or []) if str(x).strip()
    ]
    if not options or not correct_ids:
        return None

    return McqExercise(
        type="mcq",
        question=str(raw_exercise.get("question") or question_text),
        options=options,
        correct_option_ids=correct_ids,
        order=int(raw_exercise.get("order") or 1),
        is_required=bool(raw_exercise.get("is_required", True)),
    )


def build_generate_user_prompt(body: GenerateExercisesRequest) -> str:
    lines: list[str] = []
    if body.user_prompt and body.user_prompt.strip():
        lines.extend(
            [
                "دستورالعمل اضافی:",
                body.user_prompt.strip(),
                "",
            ]
        )
    lines.extend(
        [
            f"نوع سؤال (question_mode): {body.question_mode}",
        ]
    )
    if body.question_type_id:
        lines.append(f"شناسه نوع سؤال (question_type_id): {body.question_type_id}")
    if body.min_selections is not None:
        lines.append(f"حداقل انتخاب (min_selections): {body.min_selections}")
    if body.max_selections is not None:
        lines.append(f"حداکثر انتخاب (max_selections): {body.max_selections}")
    if body.answer_count is not None:
        lines.append(f"تعداد پاسخ (answer_count): {body.answer_count}")
    if body.max_words_per_answer is not None:
        lines.append(f"حداکثر کلمات (max_words_per_answer): {body.max_words_per_answer}")
    if body.answer_placeholders:
        lines.append(f"placeholderها: {', '.join(body.answer_placeholders)}")
    lines.extend(
        [
            f"تعداد تمرین مشابه: {body.count}",
            "",
            "سؤال مرجع:",
            body.question.strip(),
            "",
            "پاسخ مرجع:",
            body.answer.strip(),
            "",
        ]
    )
    if body.interests:
        lines.append(f"علایق کودک: {', '.join(i.strip() for i in body.interests if i.strip())}")
        lines.append("")
    lines.append(f"دقیقاً {body.count} تمرین مشابه بساز و فقط JSON بده.")
    return "\n".join(lines)


def parse_generate_response(
    raw_text: str,
    *,
    source_question: str,
    question_mode: str,
    question_type_id: str | None,
    expected_count: int,
    request: GenerateExercisesRequest,
) -> GenerateExercisesResponse:
    data = _extract_json_object(raw_text)
    items = data.get("exercises")
    if not isinstance(items, list) or not items:
        raise ValueError("generation JSON missing exercises[]")

    exercises: list[GeneratedExercise] = []
    for item in items[:expected_count]:
        if not isinstance(item, dict):
            continue

        question_text = ""
        story_page = _parse_story_page(item, fallback_text=source_question, body=request)
        question_text = story_page.text

        raw_type_id = str(item.get("question_type_id") or question_type_id or "").strip()
        if raw_type_id not in {"mcq_single", "mcq_multi", "open_question", "image_mcq"}:
            raw_type_id = _default_question_type_id(request)

        sample_answer = item.get("sample_answer")
        sample = str(sample_answer).strip() if sample_answer else None
        exercise = _parse_exercise(item, question_text=question_text)

        if raw_type_id == "open_question":
            exercise = None
        elif exercise is None and raw_type_id != "open_question":
            continue

        exercises.append(
            GeneratedExercise(
                question_type_id=raw_type_id,  # type: ignore[arg-type]
                story_page=story_page,
                exercise=exercise,
                sample_answer=sample,
            )
        )

    if not exercises:
        raise ValueError("no valid exercises in model response")

    return GenerateExercisesResponse(
        schema_version="1.1",
        source_question=source_question,
        question_type_id=question_type_id,  # type: ignore[arg-type]
        question_mode=question_mode,  # type: ignore[arg-type]
        exercises=exercises,
        model="",
    )


def generate_request_parts(body: GenerateExercisesRequest) -> tuple[str, str]:
    return GENERATE_EXERCISES_SYSTEM_PROMPT, build_generate_user_prompt(body)
