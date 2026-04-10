/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import Icon from "@/components/ui/icon";
import { ProgressBar, SectionHeader, StatCard, gradeColor } from "./ui";
import {
  STATS,
  COMPLEXITY,
  CLASSES,
  FUNCTIONS,
  DEPENDENCIES,
  FILE_TREE,
  BUSINESS_FLOWS,
  MOCK_PROJECT,
} from "./data";

interface TabContentProps {
  activeTab: string;
}

export default function TabContent({ activeTab }: TabContentProps) {
  const [expandedClass, setExpandedClass] = useState<string | null>(null);
  const [expandedFlow, setExpandedFlow] = useState<string | null>("order");
  const [filterText, setFilterText] = useState("");

  const filteredFunctions = FUNCTIONS.filter(
    (f) =>
      f.name.toLowerCase().includes(filterText.toLowerCase()) ||
      f.file.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <>
      {/* ── ОБЗОР ── */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="всего строк кода" value={STATS.totalLines.toLocaleString()} />
            <StatCard label="чистый код" value={STATS.codeLines.toLocaleString()} accent="cyan" />
            <StatCard
              label="файлов .py"
              value={MOCK_PROJECT.analyzedFiles}
              sub="тесты исключены"
              accent="purple"
            />
            <StatCard label="классов найдено" value={CLASSES.length} accent="amber" />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="term-panel p-4">
              <SectionHeader>Сложность по файлам (CC)</SectionHeader>
              <div className="space-y-3">
                {COMPLEXITY.map((c, i) => (
                  <div key={i} className="fade-in-up" style={{ animationDelay: `${i * 0.06}s` }}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: "var(--term-green)" }}>{c.name}</span>
                      <span style={{ color: gradeColor(c.grade) }}>
                        CC:{c.cc} [{c.grade}]
                      </span>
                    </div>
                    <ProgressBar
                      value={c.cc}
                      max={50}
                      variant={c.grade === "D" ? "amber" : c.grade === "C" ? "cyan" : "green"}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="term-panel p-4">
              <SectionHeader>Топ зависимостей</SectionHeader>
              <div className="space-y-3">
                {DEPENDENCIES.thirdparty.slice(0, 6).map((d, i) => (
                  <div key={i} className="fade-in-up" style={{ animationDelay: `${i * 0.06}s` }}>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: "var(--term-cyan)" }}>{d.name}</span>
                      <span className="term-dim">{d.usedIn} импортов</span>
                    </div>
                    <ProgressBar value={d.usedIn} max={25} variant="cyan" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="term-panel p-4">
            <SectionHeader>Состав кодовой базы</SectionHeader>
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                { label: "Исходный код", value: STATS.codeLines, pct: 72, color: "var(--term-green)" },
                { label: "Комментарии", value: STATS.commentLines, pct: 12, color: "var(--term-cyan)" },
                { label: "Пустые строки", value: STATS.blankLines, pct: 16, color: "var(--term-text-dim)" },
              ].map((item, i) => (
                <div key={i} className="term-panel-inner p-3">
                  <div className="text-2xl font-bold term-glow" style={{ color: item.color }}>
                    {item.pct}%
                  </div>
                  <div className="text-xs term-dim mt-1">{item.label}</div>
                  <div className="text-xs mt-0.5" style={{ color: item.color }}>
                    {item.value.toLocaleString()} строк
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── СТАТИСТИКА ── */}
      {activeTab === "stats" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <StatCard label="всего строк" value={STATS.totalLines.toLocaleString()} />
            <StatCard label="строки кода" value={STATS.codeLines.toLocaleString()} accent="cyan" />
            <StatCard label="комментарии" value={STATS.commentLines.toLocaleString()} accent="purple" />
            <StatCard label="пустые строки" value={STATS.blankLines.toLocaleString()} accent="dim" />
            <StatCard label="среднее / файл" value={STATS.avgLinesPerFile} sub="строк" accent="amber" />
            <StatCard label="макс. файл" value={STATS.maxLines} sub={STATS.maxLinesFile} accent="red" />
          </div>

          <div className="term-panel p-4">
            <SectionHeader>Метрики Cyclomatic Complexity</SectionHeader>
            <div className="space-y-4">
              {COMPLEXITY.map((c, i) => (
                <div key={i} className="fade-in-up" style={{ animationDelay: `${i * 0.07}s` }}>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span style={{ color: "var(--term-green)" }} className="font-medium">
                      {c.name}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="term-dim">CC = {c.cc}</span>
                      <span
                        className="px-2 py-0.5 text-[10px] font-bold rounded-sm"
                        style={{
                          background: `${gradeColor(c.grade)}20`,
                          color: gradeColor(c.grade),
                          border: `1px solid ${gradeColor(c.grade)}60`,
                        }}
                      >
                        GRADE {c.grade}
                      </span>
                    </div>
                  </div>
                  <ProgressBar
                    value={c.cc}
                    max={50}
                    variant={c.grade === "D" ? "amber" : c.grade === "C" ? "cyan" : "green"}
                  />
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 term-panel-inner text-[11px] space-y-1">
              <div className="term-dim mb-2">Шкала оценки сложности:</div>
              <div className="flex gap-6 flex-wrap">
                {[
                  { g: "A", r: "1–10", desc: "Простой" },
                  { g: "B", r: "11–20", desc: "Умеренный" },
                  { g: "C", r: "21–30", desc: "Сложный" },
                  { g: "D", r: "31+", desc: "Очень сложный" },
                ].map((item) => (
                  <div key={item.g} style={{ color: gradeColor(item.g) }}>
                    <span className="font-bold">[{item.g}]</span>
                    <span className="term-dim ml-1">
                      {item.r} — {item.desc}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── КЛАССЫ ── */}
      {activeTab === "classes" && (
        <div className="space-y-3">
          <SectionHeader>Иерархия классов ({CLASSES.length})</SectionHeader>
          {CLASSES.map((cls, i) => (
            <div
              key={i}
              className="term-panel fade-in-up cursor-pointer"
              style={{ animationDelay: `${i * 0.06}s` }}
              onClick={() => setExpandedClass(expandedClass === cls.name ? null : cls.name)}
            >
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="term-dim text-xs">{expandedClass === cls.name ? "▼" : "▶"}</span>
                  <div>
                    <span className="font-semibold" style={{ color: "var(--term-amber)" }}>
                      class{" "}
                    </span>
                    <span className="font-bold" style={{ color: "var(--term-green)" }}>
                      {cls.name}
                    </span>
                    {cls.parents.length > 0 && (
                      <span className="term-dim text-sm">({cls.parents.join(", ")})</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-4 text-xs term-dim shrink-0 ml-4">
                  <span>
                    <span style={{ color: "var(--term-amber)" }}>{cls.methods}</span> методов
                  </span>
                  <span>
                    <span style={{ color: "var(--term-purple)" }}>{cls.properties}</span> атрибутов
                  </span>
                </div>
              </div>
              {expandedClass === cls.name && (
                <div
                  className="px-4 pb-4 space-y-3 border-t"
                  style={{ borderColor: "var(--term-border)" }}
                >
                  <div className="pt-3 text-xs">
                    <span className="term-dim">📁 </span>
                    <span style={{ color: "var(--term-green)" }}>{cls.file}</span>
                  </div>
                  {cls.children.length > 0 && (
                    <div className="text-xs">
                      <span className="term-dim">Наследники: </span>
                      {cls.children.map((ch, ci) => (
                        <span key={ci} style={{ color: "var(--term-cyan)" }} className="mr-2">
                          {ch}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="term-panel-inner p-3 text-[11px]">
                    <div className="term-dim mb-2">Граф наследования:</div>
                    {cls.parents.length > 0 && (
                      <div className="mb-1">
                        {cls.parents.map((p) => (
                          <span key={p} style={{ color: "var(--term-text-dim)" }}>
                            {p}
                          </span>
                        ))}
                        <span style={{ color: "var(--term-amber)" }}> → </span>
                        <span style={{ color: "var(--term-green)" }}>{cls.name}</span>
                      </div>
                    )}
                    {cls.children.map((ch, ci) => (
                      <div key={ci}>
                        <span style={{ color: "var(--term-green)" }}>{cls.name}</span>
                        <span style={{ color: "var(--term-amber)" }}> → </span>
                        <span style={{ color: "var(--term-cyan)" }}>{ch}</span>
                      </div>
                    ))}
                    {cls.parents.length === 0 && cls.children.length === 0 && (
                      <span className="term-dim">Корневой класс без наследников</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── ФУНКЦИИ ── */}
      {activeTab === "functions" && (
        <div className="space-y-4">
          <SectionHeader>Функции и методы ({FUNCTIONS.length})</SectionHeader>
          <div className="term-panel-inner flex items-center gap-2 px-3 py-2">
            <Icon name="Search" size={12} />
            <input
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="фильтр по имени или файлу..."
              className="bg-transparent text-xs outline-none flex-1"
              style={{ color: "var(--term-green)", caretColor: "var(--term-green)" }}
            />
            {filterText && (
              <button
                onClick={() => setFilterText("")}
                className="term-dim text-xs hover:opacity-70 transition-opacity"
              >
                ✕
              </button>
            )}
          </div>
          <div className="space-y-2">
            {filteredFunctions.map((fn, i) => (
              <div
                key={i}
                className="term-panel p-3 fade-in-up flex items-center justify-between"
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="term-dim text-xs shrink-0">{String(i + 1).padStart(2, "0")}</span>
                  <div className="min-w-0">
                    <div className="text-sm font-medium">
                      {fn.async && (
                        <span style={{ color: "var(--term-purple)" }}>async </span>
                      )}
                      <span style={{ color: "var(--term-amber)" }}>def </span>
                      <span style={{ color: "var(--term-green)" }}>{fn.name}</span>
                    </div>
                    <div className="text-[10px] term-dim mt-0.5 truncate">{fn.file}</div>
                  </div>
                </div>
                <div className="flex gap-4 text-[11px] shrink-0 ml-4">
                  <span className="term-dim">
                    <span style={{ color: "var(--term-cyan)" }}>{fn.params}</span> param
                  </span>
                  <span className="term-dim">
                    <span style={{ color: "var(--term-amber)" }}>{fn.lines}</span> строк
                  </span>
                  <span className="term-dim hidden md:inline">
                    → <span style={{ color: "var(--term-purple)" }}>{fn.returns}</span>
                  </span>
                </div>
              </div>
            ))}
            {filteredFunctions.length === 0 && (
              <div className="term-panel p-8 text-center term-dim text-sm">
                нет совпадений для «{filterText}»
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── ЗАВИСИМОСТИ ── */}
      {activeTab === "deps" && (
        <div className="space-y-6">
          <div className="term-panel p-4">
            <SectionHeader>Сторонние библиотеки ({DEPENDENCIES.thirdparty.length})</SectionHeader>
            <div className="space-y-3">
              {DEPENDENCIES.thirdparty.map((d, i) => (
                <div key={i} className="fade-in-up" style={{ animationDelay: `${i * 0.06}s` }}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div className="flex items-center gap-2">
                      <span style={{ color: "var(--term-cyan)" }} className="font-medium">
                        {d.name}
                      </span>
                      <span className="term-dim text-[10px]">v{d.version}</span>
                    </div>
                    <span className="term-dim">{d.usedIn} импортов</span>
                  </div>
                  <ProgressBar value={d.usedIn} max={25} variant="cyan" />
                </div>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="term-panel p-4">
              <SectionHeader>Стандартная библиотека Python</SectionHeader>
              <div className="flex flex-wrap gap-2">
                {DEPENDENCIES.stdlib.map((m, i) => (
                  <span
                    key={i}
                    className="text-[11px] px-2 py-0.5 rounded-sm"
                    style={{
                      background: "var(--term-green-muted)",
                      color: "var(--term-green)",
                      border: "1px solid var(--term-border)",
                    }}
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>

            <div className="term-panel p-4">
              <SectionHeader>Внутренние модули</SectionHeader>
              <div className="flex flex-wrap gap-2">
                {DEPENDENCIES.internal.map((m, i) => (
                  <span
                    key={i}
                    className="text-[11px] px-2 py-0.5 rounded-sm"
                    style={{
                      background: "rgba(0,229,255,0.05)",
                      color: "var(--term-cyan)",
                      border: "1px solid rgba(0,229,255,0.2)",
                    }}
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── ДЕРЕВО ── */}
      {activeTab === "tree" && (
        <div className="term-panel p-4">
          <SectionHeader>Структура проекта</SectionHeader>
          <div
            className="text-[13px] space-y-0.5"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            {FILE_TREE.map((item, i) => {
              const spaces = "    ".repeat(item.depth);
              const connector =
                item.depth === 0 ? "" : item.depth === 1 ? "├── " : "│   └── ";
              return (
                <div
                  key={i}
                  className="flex items-center justify-between fade-in-up px-2 py-0.5 rounded-sm transition-colors"
                  style={{ animationDelay: `${i * 0.025}s` }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--term-surface2)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                >
                  <span>
                    <span className="term-dim">
                      {spaces}
                      {connector}
                    </span>
                    {item.type === "dir" ? (
                      <span style={{ color: "var(--term-amber)" }}>{item.name}</span>
                    ) : (
                      <span style={{ color: "var(--term-green)" }}>{item.name}</span>
                    )}
                  </span>
                  {item.lines && (
                    <span className="text-[11px] ml-4 shrink-0">
                      <span
                        style={{
                          color:
                            item.lines > 500 ? "var(--term-amber)" : "var(--term-text-dim)",
                        }}
                      >
                        {item.lines}
                      </span>
                      <span className="term-muted"> стр</span>
                    </span>
                  )}
                </div>
              );
            })}
          </div>
          <div
            className="mt-4 pt-3 border-t text-[11px] term-dim flex gap-6"
            style={{ borderColor: "var(--term-border)" }}
          >
            <span>
              файлов .py:{" "}
              <span style={{ color: "var(--term-green)" }}>
                {FILE_TREE.filter((f) => f.type === "file").length}
              </span>
            </span>
            <span>
              директорий:{" "}
              <span style={{ color: "var(--term-amber)" }}>
                {FILE_TREE.filter((f) => f.type === "dir").length}
              </span>
            </span>
          </div>
        </div>
      )}

      {/* ── ПРОЦЕССЫ ── */}
      {activeTab === "flows" && (
        <div className="space-y-4">
          <SectionHeader>Бизнес-процессы и потоки данных</SectionHeader>
          {BUSINESS_FLOWS.map((flow, i) => (
            <div
              key={flow.id}
              className="term-panel fade-in-up"
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              <button
                className="w-full p-4 flex items-center justify-between text-left"
                onClick={() =>
                  setExpandedFlow(expandedFlow === flow.id ? null : flow.id)
                }
              >
                <div className="flex items-center gap-3">
                  <span className="term-dim text-xs">
                    {expandedFlow === flow.id ? "▼" : "▶"}
                  </span>
                  <Icon
                    name={flow.icon as any}
                    size={14}
                    style={{ color: "var(--term-cyan)" }}
                  />
                  <span
                    className="font-semibold text-sm"
                    style={{ color: "var(--term-cyan)" }}
                  >
                    {flow.name}
                  </span>
                  <span className="text-[11px] term-dim">{flow.steps.length} шагов</span>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {flow.files.map((f, fi) => (
                    <span
                      key={fi}
                      className="text-[10px] px-1.5 py-0.5 rounded-sm hidden md:inline"
                      style={{
                        background: "var(--term-green-muted)",
                        color: "var(--term-green)",
                        border: "1px solid var(--term-border)",
                      }}
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </button>

              {expandedFlow === flow.id && (
                <div
                  className="px-4 pb-4 border-t"
                  style={{ borderColor: "var(--term-border)" }}
                >
                  <div className="pt-3 space-y-2">
                    {flow.steps.map((step, si) => (
                      <div
                        key={si}
                        className="flex items-start gap-3 text-xs fade-in-up"
                        style={{ animationDelay: `${si * 0.05}s` }}
                      >
                        <span
                          className="shrink-0 w-5 h-5 flex items-center justify-center text-[10px] font-bold rounded-sm"
                          style={{
                            background: "var(--term-green-muted)",
                            color: "var(--term-green)",
                            border: "1px solid var(--term-border)",
                          }}
                        >
                          {si + 1}
                        </span>
                        <div className="term-panel-inner px-3 py-1.5 flex-1 leading-relaxed">
                          {step.split(" → ").map((part, pi) => (
                            <span key={pi}>
                              {pi > 0 && (
                                <span style={{ color: "var(--term-amber)" }}> → </span>
                              )}
                              <span
                                style={{
                                  color:
                                    pi === 0
                                      ? "var(--term-green)"
                                      : "var(--term-text-dim)",
                                }}
                              >
                                {part}
                              </span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
