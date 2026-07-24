from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=32000)


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body. `model` selects the upstream model."""

    model: str | None = Field(
        default=None,
        description="Upstream model id (e.g. deepseek-v4-flash). Falls back to server default if omitted.",
    )
    messages: list[ChatMessage] = Field(..., min_length=1)


class ChatCompletionChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatCompletionChoiceMessage
    finish_reason: str | None = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]


class BotChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=32000)


class BotChatRequest(BaseModel):
    """Chat body for /v1/bots/{bot_id}/chat."""

    message: str = Field(..., min_length=1, max_length=20000)
    history: list[BotChatHistoryMessage] = Field(default_factory=list)
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra instructions merged into the bot system prompt.",
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )


class BotChatResponse(BaseModel):
    bot_id: str
    reply: str
    model: str


class BotInfo(BaseModel):
    id: str
    name: str
    description: str
    chat_url: str | None = None
    assess_url: str | None = None


class AssessSubArea(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    objectives: list[str] = Field(..., min_length=1)


class AssessArea(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    sub_areas: list[AssessSubArea] = Field(..., min_length=1)


class AssessRequest(BaseModel):
    """Assess a child's answer against each objective under each sub-area of each area."""

    areas: list[AssessArea] = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=20000)
    answer: str = Field(..., min_length=1, max_length=20000)
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra instructions for this assessment (appended to the user message).",
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )


class ObjectiveAssessment(BaseModel):
    area: str
    sub_area: str
    objective: str
    status: Literal["met", "partial", "not_met"]
    score: float = Field(..., ge=0.0, le=1.0, description="0.0–1.0 alignment with the objective")
    feedback: str = Field(..., description="Short teacher-facing note in Persian")


class AssessResponse(BaseModel):
    assessments: list[ObjectiveAssessment]
    summary: str = Field(..., description="Overall Persian summary for the teacher")
