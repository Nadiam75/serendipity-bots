import os
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

DEFAULT_SYSTEM_PROMPT = """تو زال هستی، یک دوست مهربان برای بچه‌های ایرانی.
همیشه به زبان فارسی ساده و گرم صحبت کن.
جمله‌هایت کوتاه و قابل فهم باشد و از کلمات سخت استفاده نکن.
با بچه‌ها صبور، تشویق‌کننده و شوخ‌طبع باش.
گاهی از ایموجی‌های مناسب استفاده کن 🌸
اگر سوالی نامناسب، ترسناک یا خطرناک بود، با مهربانی بگو بهتر است با مامان، بابا یا یک بزرگسال مطمئن صحبت کند.
هرگز اطلاعات شخصی مثل آدرس خانه یا شماره تلفن نخواه."""


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_chat_graph(system_prompt: str, max_tokens: int | None = None):
    model_kwargs: dict = {
        "model": os.getenv("DEFAULT_MODEL", "gpt-5-mini"),
        "temperature": 0.8,
        "api_key": os.getenv("GAPGPT_API_KEY"),
        "base_url": os.getenv("DEFAULT_BASE_URL", "https://api.gapgpt.app/v1"),
    }
    if max_tokens is not None:
        model_kwargs["max_tokens"] = max_tokens

    llm = ChatOpenAI(**model_kwargs)

    def call_model(state: ChatState) -> dict:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(ChatState)
    graph.add_node("agent", call_model)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)
    return graph.compile()


def run_chat(
    message: str,
    history: list[dict],
    system_prompt: str | None = None,
    max_tokens: int | None = None,
) -> str:
    prompt = system_prompt.strip() if system_prompt and system_prompt.strip() else DEFAULT_SYSTEM_PROMPT
    graph = build_chat_graph(prompt, max_tokens)

    messages: list[BaseMessage] = [SystemMessage(content=prompt)]
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))
    result = graph.invoke({"messages": messages})
    last = result["messages"][-1]
    return last.content if isinstance(last, AIMessage) else str(last)
