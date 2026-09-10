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
        name="زال",
        description="همراه مهربان — کمک در پاسخ تشریحی، جمله‌سازی، و گفتگوی آموزشی",
        instructions=TEACHER_SYSTEM_PROMPT,
    ),
    "story": ChatBot(
        id="story",
        name="زال — داستان",
        description="کمک در درک داستان، احساس شخصیت‌ها، نشانه‌ها، و سؤال‌های مرتبط با متن",
        instructions=STORY_SYSTEM_PROMPT,
    ),
}


def get_chat_bot(bot_id: str) -> ChatBot | None:
    return CHAT_BOTS.get(bot_id)
