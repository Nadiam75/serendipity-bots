import json
import re
from typing import Any

from app.prompts import FUN_FACT_SYSTEM_PROMPT
from app.schemas import FunFactRequest, FunFactResponse


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
        raise ValueError("fun fact JSON must be an object")
    return data


def build_fun_fact_user_prompt(body: FunFactRequest) -> str:
    cleaned = [i.strip() for i in body.interests if i.strip()]
    lines: list[str] = []
    if body.user_prompt and body.user_prompt.strip():
        lines.extend(
            [
                "دستورالعمل اضافی:",
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
            "علایق کودک:",
            ", ".join(cleaned),
            "",
            "یک حقیقت جالب، کوتاه، و مناسب سن بساز که به یکی از این علایق مرتبط باشد.",
            "فقط JSON بده.",
        ]
    )
    return "\n".join(lines)


def parse_fun_fact_response(
    raw_text: str,
    *,
    interests: list[str],
) -> FunFactResponse:
    data = _extract_json_object(raw_text)
    fact = str(data.get("fact") or "").strip()
    if not fact:
        raise ValueError("fun fact JSON missing fact")

    related = str(data.get("related_interest") or "").strip()
    if not related:
        related = interests[0]

    return FunFactResponse(
        fact=fact,
        related_interest=related,
        interests=interests,
        model="",
    )


def fun_fact_request_parts(body: FunFactRequest) -> tuple[str, str]:
    return FUN_FACT_SYSTEM_PROMPT, build_fun_fact_user_prompt(body)
