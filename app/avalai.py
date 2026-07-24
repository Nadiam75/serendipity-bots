from typing import Any

import httpx

from app.config import settings
from app.prompts import TEACHER_SYSTEM_PROMPT
from app.schemas import ChatMessage


def build_input_items(user_messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Build AvalAI `input` items; ignore client system messages."""
    input_items: list[dict[str, str]] = []
    for m in user_messages:
        if m.role == "system":
            continue
        input_items.append({"role": m.role, "content": m.content})
    return input_items


def build_chat_request(user_messages: list[ChatMessage]) -> tuple[str, list[dict[str, str]]]:
    """Default teacher chat: fixed instructions + input history."""
    return TEACHER_SYSTEM_PROMPT, build_input_items(user_messages)


async def create_response(
    *,
    model: str,
    instructions: str,
    input: str | list[dict[str, str]],
) -> dict[str, Any]:
    """Call AvalAI `/v1/responses`."""
    url = f"{settings.avalai_base_url.rstrip('/')}/responses"
    payload: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": input,
    }
    headers = {
        "Authorization": f"Bearer {settings.avalai_api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def chat_completions(
    *,
    model: str,
    messages: list[ChatMessage],
    instructions: str | None = None,
) -> dict[str, Any]:
    system = instructions or TEACHER_SYSTEM_PROMPT
    return await create_response(
        model=model,
        instructions=system,
        input=build_input_items(messages),
    )


def extract_assistant_text(data: dict[str, Any]) -> tuple[str, str | None]:
    """Return (content, finish_reason) from AvalAI Responses payload."""
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        status = data.get("status")
        return output_text, status if isinstance(status, str) else "stop"

    texts: list[str] = []
    for item in data.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if not isinstance(part, dict):
                continue
            if part.get("type") in ("output_text", "text") and part.get("text") is not None:
                texts.append(str(part["text"]))

    if not texts:
        raise ValueError("upstream returned empty assistant content")
    status = data.get("status")
    return "".join(texts), status if isinstance(status, str) else "stop"
