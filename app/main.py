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
from app.contracts import load_contracts
from app.fun_fact import fun_fact_request_parts, parse_fun_fact_response
from app.generate import generate_request_parts, parse_generate_response
from app.history import trim_history
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
    ContractExerciseExample,
    ContractsResponse,
    FunFactRequest,
    FunFactResponse,
    GenerateExercisesRequest,
    GenerateExercisesResponse,
)

app = FastAPI(
    title="Elementary School Chatbot API",
    description=(
        "Named bots under /v1/bots/* for Persian child learning: teacher, story chat, "
        "plus assess. Proxies to AvalAI Chat Completions API."
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
    max_output_tokens: int | None = None,
) -> ChatCompletionResponse:
    _require_api_key()
    use_model = model or settings.default_model
    try:
        raw = await chat_completions(
            model=use_model,
            messages=messages,
            instructions=instructions,
            max_output_tokens=max_output_tokens,
        )
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
        raw = await create_response(
            model=model,
            instructions=instructions,
            input=input_text,
            max_output_tokens=body.max_output_tokens,
        )
        text, _ = extract_assistant_text(raw)
        return parse_assess_response(
            text,
            expected,
            body.question_mode or "divergent",
            question_type_id=body.question_type_id,
            assess_mode=body.assess_mode,
        )
    except httpx.HTTPStatusError as e:
        raise _upstream_http_error(e) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Assessment parse failed: {e!s}") from e


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/contracts", response_model=ContractsResponse)
async def get_contracts() -> ContractsResponse:
    """Serve contracts.json (question modes, types, and examples)."""
    data = load_contracts()
    examples = [ContractExerciseExample.model_validate(ex) for ex in data.get("examples", [])]
    return ContractsResponse(
        schema_version=data["schema_version"],
        question_modes=data["question_modes"],
        question_types=data["question_types"],
        examples=examples,
    )


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
            description="ارزیابی پاسخ کودک (همگرا/واگرا) نسبت به objectives",
            assess_url="/v1/bots/assess",
        )
    )
    bots.append(
        BotInfo(
            id="generate",
            name="تولید تمرین",
            description="ساخت سؤال‌های مشابه از سؤال و پاسخ مرجع",
            generate_url="/v1/bots/generate-exercises",
        )
    )
    bots.append(
        BotInfo(
            id="fun-fact",
            name="حقیقت جالب",
            description="ساخت یک حقیقت جالب و ساده بر اساس علایق کودک",
            fun_fact_url="/v1/bots/fun-fact",
        )
    )
    return bots


@app.post("/v1/bots/assess", response_model=AssessResponse)
async def bot_assess(body: AssessRequest) -> AssessResponse:
    return await _run_assess(body)


async def _run_generate(body: GenerateExercisesRequest) -> GenerateExercisesResponse:
    _require_api_key()
    model = body.model or settings.default_model
    max_tokens = body.max_output_tokens or min(settings.max_output_tokens * 3, 4096)
    instructions, input_text = generate_request_parts(body)
    try:
        raw = await create_response(
            model=model,
            instructions=instructions,
            input=input_text,
            max_output_tokens=max_tokens,
        )
        text, _ = extract_assistant_text(raw)
        result = parse_generate_response(
            text,
            source_question=body.question,
            question_mode=body.question_mode or "divergent",
            question_type_id=body.question_type_id,
            expected_count=body.count,
            request=body,
        )
        return result.model_copy(update={"model": str(raw.get("model") or model)})
    except httpx.HTTPStatusError as e:
        raise _upstream_http_error(e) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Exercise generation failed: {e!s}") from e


@app.post("/v1/bots/generate-exercises", response_model=GenerateExercisesResponse)
async def generate_exercises(body: GenerateExercisesRequest) -> GenerateExercisesResponse:
    return await _run_generate(body)


async def _run_fun_fact(body: FunFactRequest) -> FunFactResponse:
    _require_api_key()
    interests = [i.strip() for i in body.interests if i.strip()]
    if not interests:
        raise HTTPException(status_code=422, detail="At least one non-empty interest is required.")

    model = body.model or settings.default_model
    instructions, input_text = fun_fact_request_parts(body)
    try:
        raw = await create_response(
            model=model,
            instructions=instructions,
            input=input_text,
            max_output_tokens=body.max_output_tokens,
        )
        text, _ = extract_assistant_text(raw)
        result = parse_fun_fact_response(text, interests=interests)
        return result.model_copy(update={"model": str(raw.get("model") or model)})
    except httpx.HTTPStatusError as e:
        raise _upstream_http_error(e) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Fun fact generation failed: {e!s}") from e


@app.post("/v1/bots/fun-fact", response_model=FunFactResponse)
async def bot_fun_fact(body: FunFactRequest) -> FunFactResponse:
    return await _run_fun_fact(body)


@app.post("/v1/bots/{bot_id}/chat", response_model=BotChatResponse)
async def bot_chat(bot_id: str, body: BotChatRequest) -> BotChatResponse:
    if bot_id == "assess":
        raise HTTPException(
            status_code=404,
            detail="Use POST /v1/bots/assess for assessment.",
        )
    if bot_id == "generate":
        raise HTTPException(
            status_code=404,
            detail="Use POST /v1/bots/generate-exercises for exercise generation.",
        )
    if bot_id == "fun-fact":
        raise HTTPException(
            status_code=404,
            detail="Use POST /v1/bots/fun-fact for fun fact generation.",
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
    if body.image_description and body.image_description.strip():
        instructions = f"{instructions}\n\nتوضیح تصویر:\n{body.image_description.strip()}"

    trimmed = trim_history(body.history, max_turns=settings.max_history_turns)
    history_turns_used = (len(trimmed) + 1) // 2

    messages: list[ChatMessage] = [
        ChatMessage(role=m.role, content=m.content) for m in trimmed
    ]
    messages.append(ChatMessage(role="user", content=body.message))

    result = await _run_chat(
        messages=messages,
        model=body.model,
        instructions=instructions,
        max_output_tokens=body.max_output_tokens,
    )
    return BotChatResponse(
        bot_id=bot.id,
        reply=result.choices[0].message.content,
        model=result.model,
        history_turns_used=history_turns_used,
    )


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(body: ChatCompletionRequest) -> Any:
    """Legacy OpenAI-shaped chat (teacher persona). Prefer /v1/bots/teacher/chat."""
    return await _run_chat(messages=body.messages, model=body.model)


@app.post("/v1/assess", response_model=AssessResponse)
async def assess_answer(body: AssessRequest) -> AssessResponse:
    """Legacy assess path. Prefer /v1/bots/assess."""
    return await _run_assess(body)


@app.post("/v1/fun-fact", response_model=FunFactResponse)
async def fun_fact(body: FunFactRequest) -> FunFactResponse:
    """Legacy fun-fact path. Prefer /v1/bots/fun-fact."""
    return await _run_fun_fact(body)
