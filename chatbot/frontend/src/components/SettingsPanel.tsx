import { FormEvent, useEffect, useState } from "react";
import {
  BOT_ICON_OPTIONS,
  ChatbotSettings,
  DEFAULT_BOT_ICON,
  DEFAULT_BOT_NAME,
  DEFAULT_SETTINGS,
} from "../types";
import "../styles/App.css";

interface SettingsPanelProps {
  settings: ChatbotSettings;
  saved: boolean;
  onSave: (settings: ChatbotSettings) => void;
  onReset: () => void;
}

export function SettingsPanel({ settings, saved, onSave, onReset }: SettingsPanelProps) {
  const [draft, setDraft] = useState(settings);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSave(draft);
  };

  const handleReset = () => {
    onReset();
    setDraft(DEFAULT_SETTINGS);
  };

  const botName = draft.botName.trim() || DEFAULT_BOT_NAME;

  return (
    <div className="builder-card">
      <h2>تنظیم چت‌بات</h2>
      <p className="subtitle">
        این گزینه‌ها با هر پیامی که{" "}
        <strong>{botName}</strong> به{" "}
        <code>/chat</code> می‌فرستد همراه است. اگر فیلدی را خالی
        بگذارید، مقدار پیش‌فرض سرور استفاده می‌شود.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>آیکون ربات</label>
          <div className="icon-picker" role="radiogroup" aria-label="انتخاب آیکون ربات">
            {BOT_ICON_OPTIONS.map((option) => (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={draft.botIcon === option.emoji}
                aria-label={option.label}
                className={`icon-option${draft.botIcon === option.emoji ? " selected" : ""}`}
                onClick={() => setDraft({ ...draft, botIcon: option.emoji })}
              >
                <span className="icon-option-emoji">{option.emoji}</span>
                <span className="icon-option-label">{option.label}</span>
              </button>
            ))}
          </div>
          <p className="field-hint">
            در آیکون شناور و بالای پنجره گفتگو نمایش داده می‌شود. پیش‌فرض:{" "}
            {DEFAULT_BOT_ICON}
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="botName">نام ربات</label>
          <input
            id="botName"
            type="text"
            value={draft.botName}
            onChange={(e) => setDraft({ ...draft, botName: e.target.value })}
            placeholder={DEFAULT_BOT_NAME}
          />
          <p className="field-hint">در بالای پنجره گفتگو نمایش داده می‌شود.</p>
        </div>

        <div className="form-group">
          <label htmlFor="systemPrompt">دستور راهنما</label>
          <textarea
            id="systemPrompt"
            value={draft.systemPrompt}
            onChange={(e) => setDraft({ ...draft, systemPrompt: e.target.value })}
            placeholder="شخصیت و نحوه صحبت ربات با بچه‌ها. به‌صورت system_prompt ارسال می‌شود."
          />
          <p className="field-hint">
            شخصیت و نحوه صحبت ربات. به‌صورت <code>system_prompt</code> ارسال
            می‌شود.
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="maxTokens">حداکثر طول پاسخ</label>
          <input
            id="maxTokens"
            type="number"
            min={1}
            max={4096}
            value={draft.maxTokens}
            onChange={(e) => setDraft({ ...draft, maxTokens: e.target.value })}
            placeholder="خالی = پیش‌فرض سرور"
          />
          <p className="field-hint">
            حداکثر طول پاسخ ربات. به‌صورت <code>max_tokens</code> ارسال می‌شود.
          </p>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary">
            ذخیره تنظیمات
          </button>
          <button type="button" className="btn-secondary" onClick={handleReset}>
            بازنشانی
          </button>
          {saved && <span className="saved-badge">✓ ذخیره شد</span>}
        </div>
      </form>

      <p className="app-footer-note">
        {botName} تنظیمات جدید را از پیام بعدی اعمال می‌کند — نیازی به بارگذاری
        مجدد نیست. تنظیمات در مرورگر شما ذخیره می‌شوند.
      </p>
    </div>
  );
}
