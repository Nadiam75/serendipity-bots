import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.assess import assess_request_parts, flatten_objectives, parse_assess_response
from app.avalai import chat_completions, create_response, extract_assistant_text
from app.bots import CHAT_BOTS, get_chat_bot
from app.config import settings
from app.schemas import (
    AssessRequest,
    AssessResponse,
    BotChatRequest,
    BotChatResponse,
    BotInfo,
    ChatCompletionChoice,
    ChatCompletionChoiceMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)

app = FastAPI(
    title="Elementary School Chatbot API",
    description=(
        "Named bots under /v1/bots/* for Persian child learning: teacher, story chat, "
        "plus assess. Proxies to AvalAI Responses API."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_api_key() -> None:
    if not settings.avalai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Server misconfiguration: AVALAI_API_KEY is not set.",
        )


def _upstream_http_error(e: httpx.HTTPStatusError) -> HTTPException:
    detail: Any
    try:
        detail = e.response.json()
    except Exception:
        detail = e.response.text
    return HTTPException(status_code=e.response.status_code, detail=detail)


async def _run_chat(
    *,
    messages: list[ChatMessage],
    model: str | None,
    instructions: str | None = None,
) -> ChatCompletionResponse:
    _require_api_key()
    use_model = model or settings.default_model
    try:
        raw = await chat_completions(model=use_model, messages=messages, instructions=instructions)
        text, finish_reason = extract_assistant_text(raw)
    except httpx.HTTPStatusError as e:
        raise _upstream_http_error(e) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    created = int(raw.get("created_at") or raw.get("created") or time.time())
    resp_model = raw.get("model") or use_model
    return ChatCompletionResponse(
        id=str(raw.get("id") or f"chatcmpl-{uuid.uuid4().hex}"),
        created=created,
        model=str(resp_model),
        choices=[
            ChatCompletionChoice(
                message=ChatCompletionChoiceMessage(content=text),
                finish_reason=finish_reason,
            )
        ],
    )


async def _run_assess(body: AssessRequest) -> AssessResponse:
    _require_api_key()
    expected = flatten_objectives(body.areas)
    if not expected:
        raise HTTPException(status_code=422, detail="At least one objective is required.")

    model = body.model or settings.default_model
    instructions, input_text = assess_request_parts(body)
    try:
        raw = await create_response(model=model, instructions=instructions, input=input_text)
        text, _ = extract_assistant_text(raw)
        return parse_assess_response(text, expected)
    except httpx.HTTPStatusError as e:
        raise _upstream_http_error(e) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Assessment parse failed: {e!s}") from e


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/bots", response_model=list[BotInfo])
async def list_bots() -> list[BotInfo]:
    bots = [
        BotInfo(
            id=bot.id,
            name=bot.name,
            description=bot.description,
            chat_url=f"/v1/bots/{bot.id}/chat",
        )
        for bot in CHAT_BOTS.values()
    ]
    bots.append(
        BotInfo(
            id="assess",
            name="ارزیاب پاسخ",
            description="ارزیابی پاسخ کودک نسبت به areas / sub_areas / objectives",
            assess_url="/v1/bots/assess",
        )
    )
    return bots


@app.post("/v1/bots/assess", response_model=AssessResponse)
async def bot_assess(body: AssessRequest) -> AssessResponse:
    return await _run_assess(body)


@app.post("/v1/bots/{bot_id}/chat", response_model=BotChatResponse)
async def bot_chat(bot_id: str, body: BotChatRequest) -> BotChatResponse:
    if bot_id == "assess":
        raise HTTPException(
            status_code=404,
            detail="Use POST /v1/bots/assess for assessment.",
        )
    bot = get_chat_bot(bot_id)
    if bot is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown bot '{bot_id}'. GET /v1/bots for the list.",
        )

    instructions = bot.instructions
    if body.user_prompt and body.user_prompt.strip():
        instructions = f"{instructions}\n\nدستورالعمل اضافی:\n{body.user_prompt.strip()}"

    messages: list[ChatMessage] = [
        ChatMessage(role=m.role, content=m.content) for m in body.history
    ]
    messages.append(ChatMessage(role="user", content=body.message))

    result = await _run_chat(messages=messages, model=body.model, instructions=instructions)
    return BotChatResponse(
        bot_id=bot.id,
        reply=result.choices[0].message.content,
        model=result.model,
    )


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(body: ChatCompletionRequest) -> Any:
    """Legacy OpenAI-shaped chat (teacher persona). Prefer /v1/bots/teacher/chat."""
    return await _run_chat(messages=body.messages, model=body.model)


@app.post("/v1/assess", response_model=AssessResponse)
async def assess_answer(body: AssessRequest) -> AssessResponse:
    """Legacy assess path. Prefer /v1/bots/assess."""
    return await _run_assess(body)
