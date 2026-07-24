import { ChatMessage, ChatbotSettings } from "../types";

interface ChatResponse {
  reply: string;
}

export async function sendMessage(
  message: string,
  history: ChatMessage[],
  settings: ChatbotSettings
): Promise<string> {
  const body: Record<string, unknown> = {
    message,
    history,
  };

  if (settings.systemPrompt.trim()) {
    body.system_prompt = settings.systemPrompt.trim();
  }

  const maxTokens = parseInt(settings.maxTokens, 10);
  if (!Number.isNaN(maxTokens) && maxTokens > 0) {
    body.max_tokens = maxTokens;
  }

  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "درخواست ناموفق بود");
  }

  const data: ChatResponse = await res.json();
  return data.reply;
}
