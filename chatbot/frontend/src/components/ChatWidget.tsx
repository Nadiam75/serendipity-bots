import { FormEvent, useEffect, useRef, useState } from "react";
import { sendMessage } from "../api/chat";
import {
  ChatMessage,
  ChatbotSettings,
  DEFAULT_BOT_ICON,
  DEFAULT_BOT_NAME,
} from "../types";
import "../styles/ChatWidget.css";

interface ChatWidgetProps {
  settings: ChatbotSettings;
}

export function ChatWidget({ settings }: ChatWidgetProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const botName = settings.botName.trim() || DEFAULT_BOT_NAME;
  const botIcon = settings.botIcon || DEFAULT_BOT_ICON;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    const userMsg: ChatMessage = { role: "user", content: text };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setLoading(true);

    try {
      const reply = await sendMessage(text, messages, settings);
      setMessages([...nextHistory, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "مشکلی پیش آمد");
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel" role="dialog" aria-label={`گفتگو با ${botName}`}>
          <div className="chat-panel-header">
            <div className="chat-panel-header-left">
              <div className="chat-panel-avatar" aria-hidden="true">
                {botIcon}
              </div>
              <div>
                <div className="chat-panel-title">{botName}</div>
                <div className="chat-panel-subtitle">دوست کوچولوی تو</div>
              </div>
            </div>
            <div className="chat-panel-actions">
              <button
                type="button"
                aria-label="بستن گفتگو"
                onClick={() => setOpen(false)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && !loading ? (
              <div className="chat-empty">
                <span className="chat-empty-icon">{botIcon}</span>
                <p>
                  سلام! من <strong>{botName}</strong> هستم.<br />
                  امروز چطور می‌تونم کمکت کنم؟
                </p>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={`chat-bubble ${msg.role}`}>
                  {msg.content}
                </div>
              ))
            )}
            {loading && <div className="chat-bubble typing">دارم فکر می‌کنم…</div>}
            <div ref={messagesEndRef} />
          </div>

          {error && <div className="chat-error">{error}</div>}

          <form className="chat-input-area" onSubmit={handleSend}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="پیامت را بنویس…"
              rows={1}
              disabled={loading}
              dir="rtl"
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
              aria-label="ارسال پیام"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        className="chat-fab"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "بستن گفتگو" : "باز کردن گفتگو"}
        aria-expanded={open}
      >
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <span className="chat-fab-icon" aria-hidden="true">
            {botIcon}
          </span>
        )}
        {!open && <span className="chat-fab-badge" aria-hidden="true" />}
      </button>
    </div>
  );
}
