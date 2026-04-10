import React from "react";

export function ProgressBar({
  value,
  max,
  variant = "green",
}: {
  value: number;
  max: number;
  variant?: "green" | "amber" | "cyan" | "purple";
}) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const colors: Record<string, string> = {
    green: "bar-fill",
    amber: "bar-fill bar-fill-amber",
    cyan: "bar-fill bar-fill-cyan",
    purple: "bar-fill bar-fill-purple",
  };
  return (
    <div className="w-full rounded-sm h-1.5" style={{ background: "#0a140a" }}>
      <div className={colors[variant]} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="term-dim text-xs">┌─</span>
      <span className="text-xs font-semibold tracking-[0.2em] term-amber uppercase">{children}</span>
      <span className="flex-1 border-t border-dashed" style={{ borderColor: "var(--term-border)" }} />
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  accent = "green",
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "green" | "cyan" | "amber" | "purple" | "red" | "dim";
}) {
  const colors: Record<string, string> = {
    green: "var(--term-green)",
    cyan: "var(--term-cyan)",
    amber: "var(--term-amber)",
    purple: "var(--term-purple)",
    red: "var(--term-red)",
    dim: "var(--term-text-dim)",
  };
  return (
    <div className="term-panel-inner p-3 fade-in-up">
      <div className="text-2xl font-bold term-glow" style={{ color: colors[accent] }}>
        {value}
      </div>
      <div className="text-xs term-dim mt-0.5">{label}</div>
      {sub && (
        <div className="text-[10px] mt-1 truncate" style={{ color: "var(--term-text-muted)" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

export function gradeColor(g: string): string {
  return g === "D"
    ? "var(--term-red)"
    : g === "C"
    ? "var(--term-amber)"
    : g === "B"
    ? "var(--term-cyan)"
    : "var(--term-green)";
}

export function useCopy() {
  const [copied, setCopied] = React.useState(false);

  const copy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return { copied, copy };
}

export function CopyButton({ text }: { text: string }) {
  const { copied, copy } = useCopy();

  return (
    <button
      onClick={() => copy(text)}
      className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-sm font-semibold tracking-wider transition-all"
      style={{
        background: copied ? "rgba(57,255,20,0.12)" : "transparent",
        color: copied ? "var(--term-green)" : "var(--term-text-dim)",
        border: `1px solid ${copied ? "var(--term-green)" : "var(--term-border)"}`,
      }}
    >
      {copied ? (
        <>
          <span>✓</span>
          <span>СКОПИРОВАНО</span>
        </>
      ) : (
        <>
          <span style={{ fontSize: 10 }}>⎘</span>
          <span>КОПИРОВАТЬ</span>
        </>
      )}
    </button>
  );
}