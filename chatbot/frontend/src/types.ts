export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatbotSettings {
  botName: string;
  botIcon: string;
  systemPrompt: string;
  maxTokens: string;
}

export const DEFAULT_BOT_NAME = "زال";
export const DEFAULT_BOT_ICON = "🧸";

export const BOT_ICON_OPTIONS = [
  { id: "bear", emoji: "🧸", label: "خرس" },
  { id: "flower", emoji: "🌸", label: "گل" },
  { id: "butterfly", emoji: "🦋", label: "پروانه" },
  { id: "cat", emoji: "🐱", label: "گربه" },
  { id: "rabbit", emoji: "🐰", label: "خرگوش" },
  { id: "unicorn", emoji: "🦄", label: "تک‌شاخ" },
  { id: "star", emoji: "⭐", label: "ستاره" },
  { id: "rocket", emoji: "🚀", label: "موشک" },
  { id: "robot", emoji: "🤖", label: "ربات" },
  { id: "book", emoji: "📚", label: "کتاب" },
  { id: "heart", emoji: "💜", label: "قلب" },
  { id: "sun", emoji: "🌞", label: "خورشید" },
] as const;

export const DEFAULT_SYSTEM_PROMPT = `تو زال هستی، یک دوست مهربان برای بچه‌های ایرانی.
همیشه به زبان فارسی ساده و گرم صحبت کن.
جمله‌هایت کوتاه و قابل فهم باشد و از کلمات سخت استفاده نکن.
با بچه‌ها صبور، تشویق‌کننده و شوخ‌طبع باش.
گاهی از ایموجی‌های مناسب استفاده کن 🌸
اگر سوالی نامناسب، ترسناک یا خطرناک بود، با مهربانی بگو بهتر است با مامان، بابا یا یک بزرگسال مطمئن صحبت کند.
هرگز اطلاعات شخصی مثل آدرس خانه یا شماره تلفن نخواه.`;

export const DEFAULT_SETTINGS: ChatbotSettings = {
  botName: DEFAULT_BOT_NAME,
  botIcon: DEFAULT_BOT_ICON,
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  maxTokens: "300",
};

export const SETTINGS_KEY = "chatbot-builder-settings-fa";
