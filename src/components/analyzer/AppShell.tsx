/* eslint-disable @typescript-eslint/no-explicit-any */
import Icon from "@/components/ui/icon";
import { MOCK_PROJECT, TABS, getTabText } from "./data";
import { CopyButton } from "./ui";

interface AppShellProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  scanning: boolean;
  scanProgress: number;
  scanDone: boolean;
  onStartScan: () => void;
  children: React.ReactNode;
}

export default function AppShell({
  activeTab,
  setActiveTab,
  scanning,
  scanProgress,
  scanDone,
  onStartScan,
  children,
}: AppShellProps) {
  return (
    <div
      className="min-h-screen scan-line"
      style={{ background: "var(--term-bg)", fontFamily: "'JetBrains Mono', monospace" }}
    >
      {/* Header */}
      <header
        className="px-6 py-3 flex items-center justify-between sticky top-0 z-20 border-b"
        style={{ background: "var(--term-surface)", borderColor: "var(--term-border)" }}
      >
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full" style={{ background: "var(--term-red)" }} />
            <div className="w-3 h-3 rounded-full" style={{ background: "var(--term-amber)" }} />
            <div className="w-3 h-3 rounded-full" style={{ background: "var(--term-green)" }} />
          </div>
          <div className="flex items-center gap-2">
            <span
              className="font-bold text-sm tracking-widest term-glow"
              style={{ color: "var(--term-green)" }}
            >
              PYSCOPE
            </span>
            <span className="term-dim text-xs">v1.0.0</span>
            <span className="term-dim text-xs hidden sm:inline">─ Python Code Analyzer</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="term-dim text-xs hidden lg:block">{MOCK_PROJECT.path}</span>
          {scanDone && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-sm"
              style={{
                background: "var(--term-green-muted)",
                color: "var(--term-green)",
                border: "1px solid var(--term-border)",
              }}
            >
              ✓ АНАЛИЗ ЗАВЕРШЁН
            </span>
          )}
          <button
            onClick={onStartScan}
            disabled={scanning}
            className="text-xs px-3 py-1.5 rounded-sm font-semibold tracking-wider transition-all"
            style={{
              background: scanning ? "var(--term-green-muted)" : "var(--term-green)",
              color: scanning ? "var(--term-green)" : "#030c03",
              border: "1px solid var(--term-green)",
            }}
          >
            {scanning ? `СКАНИРОВАНИЕ ${scanProgress}%` : "▶ ЗАПУСТИТЬ"}
          </button>
        </div>
      </header>

      {/* Scan progress bar */}
      {scanning && (
        <div className="h-0.5 w-full" style={{ background: "var(--term-green-muted)" }}>
          <div
            className="h-full transition-all duration-100"
            style={{
              width: `${scanProgress}%`,
              background: "var(--term-green)",
              boxShadow: "0 0 8px var(--term-green)",
            }}
          />
        </div>
      )}

      {/* Info bar */}
      <div
        className="px-6 py-2 flex gap-6 text-[11px] border-b overflow-x-auto"
        style={{ background: "var(--term-surface)", borderColor: "var(--term-border)" }}
      >
        <span className="term-dim whitespace-nowrap">
          проект: <span style={{ color: "var(--term-cyan)" }}>{MOCK_PROJECT.name}</span>
        </span>
        <span className="term-dim whitespace-nowrap">
          .py файлов:{" "}
          <span style={{ color: "var(--term-green)" }}>{MOCK_PROJECT.analyzedFiles}</span>
          <span style={{ color: "var(--term-text-dim)" }}>/{MOCK_PROJECT.pyFiles}</span>
        </span>
        <span className="term-dim whitespace-nowrap">
          тесты исключены:{" "}
          <span style={{ color: "var(--term-amber)" }}>{MOCK_PROJECT.testFiles}</span>
        </span>
        <span className="term-dim whitespace-nowrap hidden md:inline">
          сканирование:{" "}
          <span style={{ color: "var(--term-green)" }}>{MOCK_PROJECT.lastScan}</span>
        </span>
        <span className="ml-auto term-dim whitespace-nowrap">
          фильтр: <span style={{ color: "var(--term-green)" }}>*.py</span>
          <span style={{ color: "var(--term-text-dim)" }}> | exclude: test_*.py</span>
        </span>
      </div>

      {/* Tabs */}
      <div
        className="flex overflow-x-auto border-b items-center"
        style={{ background: "var(--term-surface)", borderColor: "var(--term-border)" }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-semibold tracking-[0.12em] whitespace-nowrap transition-all ${
              activeTab === tab.id ? "tab-active" : "tab-inactive"
            }`}
          >
            <Icon name={tab.icon as any} size={11} />
            {tab.label}
          </button>
        ))}
        <div className="ml-auto px-3 shrink-0">
          <CopyButton text={getTabText(activeTab)} />
        </div>
      </div>

      {/* Content */}
      <div className="p-6 max-w-7xl mx-auto">{children}</div>

      {/* Footer */}
      <footer
        className="px-6 py-3 border-t text-[11px] term-dim flex items-center justify-between mt-8"
        style={{ borderColor: "var(--term-border)" }}
      >
        <span>PyScope — Python Code Analyzer v1.0.0</span>
        <span className="flex items-center gap-1.5">
          <span
            className="w-1.5 h-1.5 rounded-full inline-block blink"
            style={{ background: "var(--term-green)" }}
          />
          ГОТОВ
        </span>
      </footer>
    </div>
  );
}