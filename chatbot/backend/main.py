import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import run_chat

app = FastAPI(title="چت‌بات کودکانه API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=4096)


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not os.getenv("GAPGPT_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="کلید GAPGPT_API_KEY تنظیم نشده. متغیر را در محیط اجرا export کنید.",
        )

    try:
        reply = run_chat(
            message=req.message,
            history=[m.model_dump() for m in req.history],
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(reply=reply)
