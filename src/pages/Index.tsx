/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useRef } from "react";
import Icon from "@/components/ui/icon";

const MOCK_PROJECT = {
  name: "ecommerce_backend",
  path: "/projects/ecommerce_backend",
  totalFiles: 47,
  pyFiles: 31,
  testFiles: 6,
  analyzedFiles: 25,
  lastScan: "2026-04-10 14:32:07",
};

const STATS = {
  totalLines: 8_412,
  codeLines: 6_089,
  commentLines: 984,
  blankLines: 1_339,
  avgLinesPerFile: 244,
  maxLinesFile: "services/order_processor.py",
  maxLines: 892,
};

const COMPLEXITY = [
  { name: "order_processor.py", cc: 42, grade: "D" },
  { name: "payment_gateway.py", cc: 31, grade: "C" },
  { name: "user_auth.py", cc: 18, grade: "B" },
  { name: "product_catalog.py", cc: 12, grade: "A" },
  { name: "cart_manager.py", cc: 9, grade: "A" },
  { name: "notification.py", cc: 7, grade: "A" },
];

const CLASSES = [
  {
    name: "OrderProcessor",
    file: "services/order_processor.py",
    parents: ["BaseService"],
    methods: 14,
    properties: 8,
    children: ["ExpressOrderProcessor", "B2BOrderProcessor"],
  },
  {
    name: "PaymentGateway",
    file: "services/payment_gateway.py",
    parents: ["ABC"],
    methods: 9,
    properties: 5,
    children: ["StripeGateway", "YooKassaGateway"],
  },
  {
    name: "UserAuth",
    file: "auth/user_auth.py",
    parents: ["BaseAuth"],
    methods: 7,
    properties: 4,
    children: [],
  },
  {
    name: "ProductCatalog",
    file: "catalog/product_catalog.py",
    parents: [],
    methods: 11,
    properties: 6,
    children: ["DigitalCatalog"],
  },
  {
    name: "CartManager",
    file: "cart/cart_manager.py",
    parents: ["SessionMixin"],
    methods: 8,
    properties: 3,
    children: [],
  },
];

const FUNCTIONS = [
  { name: "process_order()", file: "order_processor.py", lines: 87, params: 4, async: true, returns: "OrderResult" },
  { name: "validate_payment()", file: "payment_gateway.py", lines: 52, params: 3, async: true, returns: "bool" },
  { name: "authenticate_user()", file: "user_auth.py", lines: 41, params: 2, async: false, returns: "Token" },
  { name: "apply_discount()", file: "cart_manager.py", lines: 34, params: 3, async: false, returns: "Decimal" },
  { name: "send_notification()", file: "notification.py", lines: 28, params: 4, async: true, returns: "None" },
  { name: "get_products()", file: "product_catalog.py", lines: 24, params: 2, async: false, returns: "List[Product]" },
  { name: "create_invoice()", file: "order_processor.py", lines: 61, params: 3, async: true, returns: "Invoice" },
  { name: "refresh_token()", file: "user_auth.py", lines: 19, params: 1, async: false, returns: "Token" },
];

const DEPENDENCIES = {
  stdlib: ["os", "sys", "json", "typing", "datetime", "pathlib", "logging", "abc", "decimal", "uuid"],
  thirdparty: [
    { name: "fastapi", version: "0.104.1", usedIn: 12 },
    { name: "sqlalchemy", version: "2.0.23", usedIn: 18 },
    { name: "pydantic", version: "2.5.0", usedIn: 21 },
    { name: "stripe", version: "7.8.0", usedIn: 3 },
    { name: "redis", version: "5.0.1", usedIn: 6 },
    { name: "celery", version: "5.3.4", usedIn: 4 },
    { name: "boto3", version: "1.34.0", usedIn: 2 },
    { name: "pytest", version: "7.4.3", usedIn: 6 },
  ],
  internal: ["services", "models", "auth", "cart", "catalog", "notifications", "utils"],
};

const FILE_TREE = [
  { depth: 0, name: "ecommerce_backend/", type: "dir", lines: null },
  { depth: 1, name: "services/", type: "dir", lines: null },
  { depth: 2, name: "order_processor.py", type: "file", lines: 892 },
  { depth: 2, name: "payment_gateway.py", type: "file", lines: 634 },
  { depth: 2, name: "notification.py", type: "file", lines: 287 },
  { depth: 1, name: "auth/", type: "dir", lines: null },
  { depth: 2, name: "user_auth.py", type: "file", lines: 412 },
  { depth: 2, name: "jwt_handler.py", type: "file", lines: 189 },
  { depth: 1, name: "catalog/", type: "dir", lines: null },
  { depth: 2, name: "product_catalog.py", type: "file", lines: 356 },
  { depth: 2, name: "search.py", type: "file", lines: 198 },
  { depth: 1, name: "cart/", type: "dir", lines: null },
  { depth: 2, name: "cart_manager.py", type: "file", lines: 301 },
  { depth: 2, name: "pricing.py", type: "file", lines: 244 },
  { depth: 1, name: "models/", type: "dir", lines: null },
  { depth: 2, name: "order.py", type: "file", lines: 178 },
  { depth: 2, name: "user.py", type: "file", lines: 143 },
  { depth: 2, name: "product.py", type: "file", lines: 167 },
  { depth: 1, name: "utils/", type: "dir", lines: null },
  { depth: 2, name: "helpers.py", type: "file", lines: 89 },
  { depth: 2, name: "validators.py", type: "file", lines: 124 },
  { depth: 1, name: "config.py", type: "file", lines: 67 },
  { depth: 1, name: "main.py", type: "file", lines: 52 },
];

const BUSINESS_FLOWS = [
  {
    id: "order",
    name: "Оформление заказа",
    icon: "ShoppingCart",
    steps: [
      "CartManager.checkout() → валидация корзины",
      "ProductCatalog.check_stock() → резерв товаров",
      "apply_discount() → расчёт скидок",
      "PaymentGateway.charge() → списание средств",
      "OrderProcessor.process_order() → создание заказа",
      "send_notification() → уведомление покупателя",
    ],
    files: ["cart_manager.py", "payment_gateway.py", "order_processor.py"],
  },
  {
    id: "auth",
    name: "Аутентификация пользователя",
    icon: "Shield",
    steps: [
      "authenticate_user() → проверка credentials",
      "JWTHandler.create_token() → генерация токена",
      "UserAuth.set_session() → запись сессии в Redis",
      "refresh_token() → обновление по истечении срока",
    ],
    files: ["user_auth.py", "jwt_handler.py"],
  },
  {
    id: "catalog",
    name: "Управление каталогом",
    icon: "Package",
    steps: [
      "ProductCatalog.get_products() → выборка из БД",
      "search.py → полнотекстовый поиск ElasticSearch",
      "pricing.py → динамическое ценообразование",
      "DigitalCatalog.sync() → синхронизация с 1С",
    ],
    files: ["product_catalog.py", "search.py", "pricing.py"],
  },
];

const TABS = [
  { id: "overview", label: "ОБЗОР", icon: "LayoutDashboard" },
  { id: "stats", label: "СТАТИСТИКА", icon: "BarChart2" },
  { id: "classes", label: "КЛАССЫ", icon: "Layers" },
  { id: "functions", label: "ФУНКЦИИ", icon: "Code2" },
  { id: "deps", label: "ЗАВИСИМОСТИ", icon: "GitBranch" },
  { id: "tree", label: "ДЕРЕВО", icon: "FolderTree" },
  { id: "flows", label: "ПРОЦЕССЫ", icon: "Workflow" },
];

function ProgressBar({ value, max, variant = "green" }: { value: number; max: number; variant?: "green" | "amber" | "cyan" | "purple" }) {
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

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="term-dim text-xs">┌─</span>
      <span className="text-xs font-semibold tracking-[0.2em] term-amber uppercase">{children}</span>
      <span className="flex-1 border-t border-dashed" style={{ borderColor: "var(--term-border)" }} />
    </div>
  );
}

function StatCard({ label, value, sub, accent = "green" }: { label: string; value: string | number; sub?: string; accent?: "green" | "cyan" | "amber" | "purple" | "red" | "dim" }) {
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
      <div className="text-2xl font-bold term-glow" style={{ color: colors[accent] }}>{value}</div>
      <div className="text-xs term-dim mt-0.5">{label}</div>
      {sub && <div className="text-[10px] mt-1 truncate" style={{ color: "var(--term-text-muted)" }}>{sub}</div>}
    </div>
  );
}

export default function Index() {
  const [activeTab, setActiveTab] = useState("overview");
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanDone, setScanDone] = useState(true);
  const [expandedClass, setExpandedClass] = useState<string | null>(null);
  const [expandedFlow, setExpandedFlow] = useState<string | null>("order");
  const [filterText, setFilterText] = useState("");
  const scanRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startScan = () => {
    if (scanning) return;
    setScanDone(false);
    setScanning(true);
    setScanProgress(0);
    let p = 0;
    scanRef.current = setInterval(() => {
      p += Math.random() * 7 + 2;
      if (p >= 100) {
        p = 100;
        clearInterval(scanRef.current!);
        setScanning(false);
        setScanDone(true);
      }
      setScanProgress(Math.round(p));
    }, 80);
  };

  useEffect(() => () => { if (scanRef.current) clearInterval(scanRef.current); }, []);

  const filteredFunctions = FUNCTIONS.filter(
    (f) =>
      f.name.toLowerCase().includes(filterText.toLowerCase()) ||
      f.file.toLowerCase().includes(filterText.toLowerCase())
  );

  const gradeColor = (g: string) =>
    g === "D" ? "var(--term-red)" : g === "C" ? "var(--term-amber)" : g === "B" ? "var(--term-cyan)" : "var(--term-green)";

  return (
    <div className="min-h-screen scan-line" style={{ background: "var(--term-bg)", fontFamily: "'JetBrains Mono', monospace" }}>

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
            <span className="font-bold text-sm tracking-widest term-glow" style={{ color: "var(--term-green)" }}>
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
              style={{ background: "var(--term-green-muted)", color: "var(--term-green)", border: "1px solid var(--term-border)" }}
            >
              ✓ АНАЛИЗ ЗАВЕРШЁН
            </span>
          )}
          <button
            onClick={startScan}
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
            style={{ width: `${scanProgress}%`, background: "var(--term-green)", boxShadow: "0 0 8px var(--term-green)" }}
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
          .py файлов: <span style={{ color: "var(--term-green)" }}>{MOCK_PROJECT.analyzedFiles}</span>
          <span style={{ color: "var(--term-text-dim)" }}>/{MOCK_PROJECT.pyFiles}</span>
        </span>
        <span className="term-dim whitespace-nowrap">
          тесты исключены: <span style={{ color: "var(--term-amber)" }}>{MOCK_PROJECT.testFiles}</span>
        </span>
        <span className="term-dim whitespace-nowrap hidden md:inline">
          сканирование: <span style={{ color: "var(--term-green)" }}>{MOCK_PROJECT.lastScan}</span>
        </span>
        <span className="ml-auto term-dim whitespace-nowrap">
          фильтр: <span style={{ color: "var(--term-green)" }}>*.py</span>
          <span style={{ color: "var(--term-text-dim)" }}> | exclude: test_*.py</span>
        </span>
      </div>

      {/* Tabs */}
      <div
        className="flex overflow-x-auto border-b"
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
      </div>

      {/* Content */}
      <div className="p-6 max-w-7xl mx-auto">

        {/* ── ОБЗОР ── */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard label="всего строк кода" value={STATS.totalLines.toLocaleString()} />
              <StatCard label="чистый код" value={STATS.codeLines.toLocaleString()} accent="cyan" />
              <StatCard label="файлов .py" value={MOCK_PROJECT.analyzedFiles} sub="тесты исключены" accent="purple" />
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
                        <span style={{ color: gradeColor(c.grade) }}>CC:{c.cc} [{c.grade}]</span>
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
                    <div className="text-2xl font-bold term-glow" style={{ color: item.color }}>{item.pct}%</div>
                    <div className="text-xs term-dim mt-1">{item.label}</div>
                    <div className="text-xs mt-0.5" style={{ color: item.color }}>{item.value.toLocaleString()} строк</div>
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
                      <span style={{ color: "var(--term-green)" }} className="font-medium">{c.name}</span>
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
                      <span className="term-dim ml-1">{item.r} — {item.desc}</span>
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
                      <span className="font-semibold" style={{ color: "var(--term-amber)" }}>class </span>
                      <span className="font-bold" style={{ color: "var(--term-green)" }}>{cls.name}</span>
                      {cls.parents.length > 0 && (
                        <span className="term-dim text-sm">({cls.parents.join(", ")})</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-4 text-xs term-dim shrink-0 ml-4">
                    <span><span style={{ color: "var(--term-amber)" }}>{cls.methods}</span> методов</span>
                    <span><span style={{ color: "var(--term-purple)" }}>{cls.properties}</span> атрибутов</span>
                  </div>
                </div>
                {expandedClass === cls.name && (
                  <div className="px-4 pb-4 space-y-3 border-t" style={{ borderColor: "var(--term-border)" }}>
                    <div className="pt-3 text-xs">
                      <span className="term-dim">📁 </span>
                      <span style={{ color: "var(--term-green)" }}>{cls.file}</span>
                    </div>
                    {cls.children.length > 0 && (
                      <div className="text-xs">
                        <span className="term-dim">Наследники: </span>
                        {cls.children.map((ch, ci) => (
                          <span key={ci} style={{ color: "var(--term-cyan)" }} className="mr-2">{ch}</span>
                        ))}
                      </div>
                    )}
                    <div className="term-panel-inner p-3 text-[11px]">
                      <div className="term-dim mb-2">Граф наследования:</div>
                      {cls.parents.length > 0 && (
                        <div className="mb-1">
                          {cls.parents.map((p) => (
                            <span key={p} style={{ color: "var(--term-text-dim)" }}>{p}</span>
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
            <div
              className="term-panel-inner flex items-center gap-2 px-3 py-2"
            >
              <Icon name="Search" size={12} />
              <input
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                placeholder="фильтр по имени или файлу..."
                className="bg-transparent text-xs outline-none flex-1"
                style={{ color: "var(--term-green)", caretColor: "var(--term-green)" }}
              />
              {filterText && (
                <button onClick={() => setFilterText("")} className="term-dim text-xs hover:opacity-70 transition-opacity">✕</button>
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
                        {fn.async && <span style={{ color: "var(--term-purple)" }}>async </span>}
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
                        <span style={{ color: "var(--term-cyan)" }} className="font-medium">{d.name}</span>
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
            <div className="text-[13px] space-y-0.5" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {FILE_TREE.map((item, i) => {
                const spaces = "    ".repeat(item.depth);
                const connector =
                  item.depth === 0 ? "" :
                  item.depth === 1 ? "├── " : "│   └── ";
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between fade-in-up px-2 py-0.5 rounded-sm transition-colors"
                    style={{ animationDelay: `${i * 0.025}s` }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--term-surface2)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <span>
                      <span className="term-dim">{spaces}{connector}</span>
                      {item.type === "dir" ? (
                        <span style={{ color: "var(--term-amber)" }}>{item.name}</span>
                      ) : (
                        <span style={{ color: "var(--term-green)" }}>{item.name}</span>
                      )}
                    </span>
                    {item.lines && (
                      <span className="text-[11px] ml-4 shrink-0">
                        <span style={{ color: item.lines > 500 ? "var(--term-amber)" : "var(--term-text-dim)" }}>
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
                файлов .py: <span style={{ color: "var(--term-green)" }}>
                  {FILE_TREE.filter((f) => f.type === "file").length}
                </span>
              </span>
              <span>
                директорий: <span style={{ color: "var(--term-amber)" }}>
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
                  onClick={() => setExpandedFlow(expandedFlow === flow.id ? null : flow.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="term-dim text-xs">{expandedFlow === flow.id ? "▼" : "▶"}</span>
                    <Icon name={flow.icon as any} size={14} style={{ color: "var(--term-cyan)" }} />
                    <span className="font-semibold text-sm" style={{ color: "var(--term-cyan)" }}>{flow.name}</span>
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
                  <div className="px-4 pb-4 border-t" style={{ borderColor: "var(--term-border)" }}>
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
                                {pi > 0 && <span style={{ color: "var(--term-amber)" }}> → </span>}
                                <span style={{ color: pi === 0 ? "var(--term-green)" : "var(--term-text-dim)" }}>
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
      </div>

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