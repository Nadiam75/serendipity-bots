import { SettingsPanel } from "./components/SettingsPanel";
import { ChatWidget } from "./components/ChatWidget";
import { useSettings } from "./hooks/useSettings";
import "./styles/App.css";

export default function App() {
  const { settings, save, reset, saved } = useSettings();

  return (
    <div className="app">
      <header className="app-header">
        <h1>چت‌بات کودکانه</h1>
      </header>

      <main className="app-main">
        <SettingsPanel
          settings={settings}
          saved={saved}
          onSave={save}
          onReset={reset}
        />
      </main>

      <ChatWidget settings={settings} />
    </div>
  );
}
