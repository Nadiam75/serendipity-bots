from typing import Sequence, TypeVar

T = TypeVar("T")


def trim_history(messages: Sequence[T], *, max_turns: int) -> list[T]:
    """Keep the most recent conversation turns.

    One turn is a user message plus the following assistant reply (two messages).
    Laravel should store full history in DB and send prior turns only (not the
    current user message); this helper caps what reaches the LLM.
    """
    if max_turns <= 0:
        return []
    max_messages = max_turns * 2
    if len(messages) <= max_messages:
        return list(messages)
    return list(messages[-max_messages:])
