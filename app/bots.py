"""Named chatbot personas exposed under /v1/bots/..."""

from dataclasses import dataclass

from app.prompts import (
    STORY_SYSTEM_PROMPT,
    TEACHER_SYSTEM_PROMPT,
)


@dataclass(frozen=True)
class ChatBot:
    id: str
    name: str
    description: str
    instructions: str


CHAT_BOTS: dict[str, ChatBot] = {
    "teacher": ChatBot(
        id="teacher",
        name="معلم مهربان",
        description="گفتگوی عمومی معلم‌مانند با کودک ۷ تا ۱۰ سال",
        instructions=TEACHER_SYSTEM_PROMPT,
    ),
    "story": ChatBot(
        id="story",
        name="همراه داستان و معنا",
        description="تمرکز روی گوش دادن، پیام اصلی، و دریافت معنا از متن/تصویر",
        instructions=STORY_SYSTEM_PROMPT,
    ),
}


def get_chat_bot(bot_id: str) -> ChatBot | None:
    return CHAT_BOTS.get(bot_id)
