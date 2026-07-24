import { useCallback, useEffect, useState } from "react";
import { ChatbotSettings, DEFAULT_SETTINGS, SETTINGS_KEY } from "../types";

function loadSettings(): ChatbotSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function useSettings() {
  const [settings, setSettings] = useState<ChatbotSettings>(loadSettings);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = loadSettings();
    setSettings(stored);
  }, []);

  const save = useCallback((next: ChatbotSettings) => {
    setSettings(next);
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(next));
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  }, []);

  const reset = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem(SETTINGS_KEY);
    setSaved(false);
  }, []);

  return { settings, save, reset, saved };
}
