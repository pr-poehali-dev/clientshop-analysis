export const MOCK_PROJECT = {
  name: "ecommerce_backend",
  path: "/projects/ecommerce_backend",
  totalFiles: 47,
  pyFiles: 31,
  testFiles: 6,
  analyzedFiles: 25,
  lastScan: "2026-04-10 14:32:07",
};

export const STATS = {
  totalLines: 8_412,
  codeLines: 6_089,
  commentLines: 984,
  blankLines: 1_339,
  avgLinesPerFile: 244,
  maxLinesFile: "services/order_processor.py",
  maxLines: 892,
};

export const COMPLEXITY = [
  { name: "order_processor.py", cc: 42, grade: "D" },
  { name: "payment_gateway.py", cc: 31, grade: "C" },
  { name: "user_auth.py", cc: 18, grade: "B" },
  { name: "product_catalog.py", cc: 12, grade: "A" },
  { name: "cart_manager.py", cc: 9, grade: "A" },
  { name: "notification.py", cc: 7, grade: "A" },
];

export const CLASSES = [
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

export const FUNCTIONS = [
  { name: "process_order()", file: "order_processor.py", lines: 87, params: 4, async: true, returns: "OrderResult" },
  { name: "validate_payment()", file: "payment_gateway.py", lines: 52, params: 3, async: true, returns: "bool" },
  { name: "authenticate_user()", file: "user_auth.py", lines: 41, params: 2, async: false, returns: "Token" },
  { name: "apply_discount()", file: "cart_manager.py", lines: 34, params: 3, async: false, returns: "Decimal" },
  { name: "send_notification()", file: "notification.py", lines: 28, params: 4, async: true, returns: "None" },
  { name: "get_products()", file: "product_catalog.py", lines: 24, params: 2, async: false, returns: "List[Product]" },
  { name: "create_invoice()", file: "order_processor.py", lines: 61, params: 3, async: true, returns: "Invoice" },
  { name: "refresh_token()", file: "user_auth.py", lines: 19, params: 1, async: false, returns: "Token" },
];

export const DEPENDENCIES = {
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

export const FILE_TREE = [
  { depth: 0, name: "ecommerce_backend/", type: "dir", lines: null as number | null },
  { depth: 1, name: "services/", type: "dir", lines: null as number | null },
  { depth: 2, name: "order_processor.py", type: "file", lines: 892 },
  { depth: 2, name: "payment_gateway.py", type: "file", lines: 634 },
  { depth: 2, name: "notification.py", type: "file", lines: 287 },
  { depth: 1, name: "auth/", type: "dir", lines: null as number | null },
  { depth: 2, name: "user_auth.py", type: "file", lines: 412 },
  { depth: 2, name: "jwt_handler.py", type: "file", lines: 189 },
  { depth: 1, name: "catalog/", type: "dir", lines: null as number | null },
  { depth: 2, name: "product_catalog.py", type: "file", lines: 356 },
  { depth: 2, name: "search.py", type: "file", lines: 198 },
  { depth: 1, name: "cart/", type: "dir", lines: null as number | null },
  { depth: 2, name: "cart_manager.py", type: "file", lines: 301 },
  { depth: 2, name: "pricing.py", type: "file", lines: 244 },
  { depth: 1, name: "models/", type: "dir", lines: null as number | null },
  { depth: 2, name: "order.py", type: "file", lines: 178 },
  { depth: 2, name: "user.py", type: "file", lines: 143 },
  { depth: 2, name: "product.py", type: "file", lines: 167 },
  { depth: 1, name: "utils/", type: "dir", lines: null as number | null },
  { depth: 2, name: "helpers.py", type: "file", lines: 89 },
  { depth: 2, name: "validators.py", type: "file", lines: 124 },
  { depth: 1, name: "config.py", type: "file", lines: 67 },
  { depth: 1, name: "main.py", type: "file", lines: 52 },
];

export const BUSINESS_FLOWS = [
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

export const TABS = [
  { id: "overview", label: "ОБЗОР", icon: "LayoutDashboard" },
  { id: "stats", label: "СТАТИСТИКА", icon: "BarChart2" },
  { id: "classes", label: "КЛАССЫ", icon: "Layers" },
  { id: "functions", label: "ФУНКЦИИ", icon: "Code2" },
  { id: "deps", label: "ЗАВИСИМОСТИ", icon: "GitBranch" },
  { id: "tree", label: "ДЕРЕВО", icon: "FolderTree" },
  { id: "flows", label: "ПРОЦЕССЫ", icon: "Workflow" },
];

export function getTabText(tabId: string): string {
  const sep = "─".repeat(60);

  if (tabId === "overview") {
    return [
      `PYSCOPE — Обзор проекта: ${MOCK_PROJECT.name}`,
      `Путь: ${MOCK_PROJECT.path}`,
      `Дата сканирования: ${MOCK_PROJECT.lastScan}`,
      sep,
      `Всего строк:    ${STATS.totalLines.toLocaleString()}`,
      `Чистый код:     ${STATS.codeLines.toLocaleString()}`,
      `Комментарии:    ${STATS.commentLines.toLocaleString()}`,
      `Пустые строки:  ${STATS.blankLines.toLocaleString()}`,
      `Файлов .py:     ${MOCK_PROJECT.analyzedFiles} (тесты исключены: ${MOCK_PROJECT.testFiles})`,
      `Классов:        ${CLASSES.length}`,
      sep,
      "Сложность по файлам (CC):",
      ...COMPLEXITY.map((c) => `  ${c.name.padEnd(30)} CC=${c.cc}  [${c.grade}]`),
    ].join("\n");
  }

  if (tabId === "stats") {
    return [
      `PYSCOPE — Статистика: ${MOCK_PROJECT.name}`,
      sep,
      `Всего строк:       ${STATS.totalLines.toLocaleString()}`,
      `Строки кода:       ${STATS.codeLines.toLocaleString()}`,
      `Комментарии:       ${STATS.commentLines.toLocaleString()}`,
      `Пустые строки:     ${STATS.blankLines.toLocaleString()}`,
      `Среднее / файл:    ${STATS.avgLinesPerFile} строк`,
      `Макс. файл:        ${STATS.maxLinesFile} (${STATS.maxLines} строк)`,
      sep,
      "Cyclomatic Complexity:",
      ...COMPLEXITY.map(
        (c) => `  ${c.name.padEnd(30)} CC=${String(c.cc).padStart(3)}  GRADE ${c.grade}`
      ),
      sep,
      "Шкала: [A] 1–10 Простой | [B] 11–20 Умеренный | [C] 21–30 Сложный | [D] 31+ Очень сложный",
    ].join("\n");
  }

  if (tabId === "classes") {
    const lines = [`PYSCOPE — Классы: ${MOCK_PROJECT.name}`, sep];
    CLASSES.forEach((cls) => {
      lines.push(`class ${cls.name}${cls.parents.length ? `(${cls.parents.join(", ")})` : ""}`);
      lines.push(`  Файл:      ${cls.file}`);
      lines.push(`  Методов:   ${cls.methods}`);
      lines.push(`  Атрибутов: ${cls.properties}`);
      if (cls.children.length) {
        lines.push(`  Наследники: ${cls.children.join(", ")}`);
      }
      lines.push("");
    });
    return lines.join("\n");
  }

  if (tabId === "functions") {
    return [
      `PYSCOPE — Функции и методы: ${MOCK_PROJECT.name}`,
      sep,
      ...FUNCTIONS.map(
        (f, i) =>
          `${String(i + 1).padStart(2, "0")}. ${f.async ? "async " : ""}def ${f.name.padEnd(28)} ` +
          `params=${f.params}  lines=${f.lines}  → ${f.returns}  [${f.file}]`
      ),
    ].join("\n");
  }

  if (tabId === "deps") {
    return [
      `PYSCOPE — Зависимости: ${MOCK_PROJECT.name}`,
      sep,
      "Сторонние библиотеки:",
      ...DEPENDENCIES.thirdparty.map(
        (d) => `  ${d.name.padEnd(16)} v${d.version.padEnd(12)} импортов: ${d.usedIn}`
      ),
      sep,
      `Стандартная библиотека: ${DEPENDENCIES.stdlib.join(", ")}`,
      sep,
      `Внутренние модули: ${DEPENDENCIES.internal.join(", ")}`,
    ].join("\n");
  }

  if (tabId === "tree") {
    const lines = [`PYSCOPE — Дерево проекта: ${MOCK_PROJECT.name}`, sep];
    FILE_TREE.forEach((item) => {
      const spaces = "    ".repeat(item.depth);
      const connector =
        item.depth === 0 ? "" : item.depth === 1 ? "├── " : "│   └── ";
      const suffix = item.lines ? `  (${item.lines} стр)` : "";
      lines.push(`${spaces}${connector}${item.name}${suffix}`);
    });
    lines.push(sep);
    lines.push(
      `Файлов .py: ${FILE_TREE.filter((f) => f.type === "file").length}  ` +
        `Директорий: ${FILE_TREE.filter((f) => f.type === "dir").length}`
    );
    return lines.join("\n");
  }

  if (tabId === "flows") {
    const lines = [`PYSCOPE — Бизнес-процессы: ${MOCK_PROJECT.name}`, sep];
    BUSINESS_FLOWS.forEach((flow) => {
      lines.push(`▶ ${flow.name}  (файлы: ${flow.files.join(", ")})`);
      flow.steps.forEach((step, i) => {
        lines.push(`  ${i + 1}. ${step}`);
      });
      lines.push("");
    });
    return lines.join("\n");
  }

  return "";
}