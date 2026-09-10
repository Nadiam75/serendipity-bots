from typing import Any

import httpx

from app.config import settings
from app.prompts import TEACHER_SYSTEM_PROMPT
from app.schemas import ChatMessage


def build_input_items(user_messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Build chat messages; ignore client system messages (server owns system prompt)."""
    items: list[dict[str, str]] = []
    for m in user_messages:
        if m.role == "system":
            continue
        items.append({"role": m.role, "content": m.content})
    return items


def _build_messages(
    *,
    instructions: str,
    input: str | list[dict[str, str]],
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": instructions}]
    if isinstance(input, str):
        messages.append({"role": "user", "content": input})
    else:
        messages.extend(input)
    return messages


async def create_response(
    *,
    model: str,
    instructions: str,
    input: str | list[dict[str, str]],
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    """Call AvalAI `/v1/chat/completions` (instructions → system message)."""
    url = f"{settings.avalai_base_url.rstrip('/')}/chat/completions"
    token_limit = max_output_tokens if max_output_tokens is not None else settings.max_output_tokens
    payload: dict[str, Any] = {
        "model": model,
        "messages": _build_messages(instructions=instructions, input=input),
        "max_completion_tokens": token_limit,
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
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    system = instructions or TEACHER_SYSTEM_PROMPT
    return await create_response(
        model=model,
        instructions=system,
        input=build_input_items(messages),
        max_output_tokens=max_output_tokens,
    )


def extract_assistant_text(data: dict[str, Any]) -> tuple[str, str | None]:
    """Return (content, finish_reason) from chat/completions or legacy responses payload."""
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        if isinstance(choice, dict):
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    finish = choice.get("finish_reason")
                    return content, finish if isinstance(finish, str) else "stop"

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
