#!/usr/bin/env python3
"""
PyScope — Python Code Analyzer
Использование: python analyzer.py /путь/к/проекту
               python analyzer.py /путь/к/проекту --section tree
               python analyzer.py /путь/к/проекту --out report.txt
"""

import ast
import os
import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict

# ─── Цвета терминала ─────────────────────────────────────────────────────────

class C:
    GREEN   = "\033[92m"
    AMBER   = "\033[93m"
    CYAN    = "\033[96m"
    RED     = "\033[91m"
    PURPLE  = "\033[95m"
    DIM     = "\033[2m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"

def g(text):   return f"{C.GREEN}{text}{C.RESET}"
def a(text):   return f"{C.AMBER}{text}{C.RESET}"
def c(text):   return f"{C.CYAN}{text}{C.RESET}"
def r(text):   return f"{C.RED}{text}{C.RESET}"
def p(text):   return f"{C.PURPLE}{text}{C.RESET}"
def dim(text): return f"{C.DIM}{text}{C.RESET}"
def bold(text):return f"{C.BOLD}{text}{C.RESET}"

SEP  = dim("─" * 70)
SEP2 = dim("┄" * 70)

def section_header(title):
    print(f"\n{dim('┌─')} {a(title.upper())} {dim('─' * max(0, 66 - len(title)))}")

# ─── Сбор файлов ─────────────────────────────────────────────────────────────

def collect_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*.py")):
        name = path.name
        parts = path.parts
        # Исключаем тестовые файлы и директории
        if name.startswith("test_") or name.endswith("_test.py"):
            continue
        if any(part in ("tests", "test", "__pycache__", ".venv", "venv", "env", ".git", "node_modules") for part in parts):
            continue
        files.append(path)
    return files

# ─── Статистика строк ─────────────────────────────────────────────────────────

def count_lines(path: Path) -> dict:
    total = code = comments = blank = 0
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            total += 1
            stripped = line.strip()
            if not stripped:
                blank += 1
            elif stripped.startswith("#"):
                comments += 1
            else:
                code += 1
    except Exception:
        pass
    return {"total": total, "code": code, "comments": comments, "blank": blank}

# ─── Cyclomatic Complexity ────────────────────────────────────────────────────

BRANCH_NODES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.With, ast.Assert, ast.comprehension,
)

def cyclomatic_complexity(tree: ast.AST) -> int:
    cc = 1
    for node in ast.walk(tree):
        if isinstance(node, BRANCH_NODES):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            cc += len(node.values) - 1
    return cc

def grade(cc: int) -> str:
    if cc <= 10: return "A"
    if cc <= 20: return "B"
    if cc <= 30: return "C"
    return "D"

def grade_color(g_val: str) -> callable:
    return {" A": g, "A": g, "B": c, "C": a, "D": r}.get(g_val, g)

# ─── Парсинг AST ─────────────────────────────────────────────────────────────

def parse_file(path: Path):
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        return ast.parse(source), source
    except SyntaxError:
        return None, None

def extract_classes(tree: ast.AST, filepath: Path) -> list[dict]:
    classes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        parents = [ast.unparse(b) for b in node.bases] if node.bases else []
        methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
        properties = [
            n.targets[0].id if isinstance(n.targets[0], ast.Name) else "?"
            for n in ast.walk(node)
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
        ]
        classes.append({
            "name": node.name,
            "file": str(filepath),
            "parents": parents,
            "methods": methods,
            "properties": list(dict.fromkeys(properties)),
            "lineno": node.lineno,
        })
    return classes

def extract_functions(tree: ast.AST, filepath: Path) -> list[dict]:
    funcs = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = [a.arg for a in node.args.args]
        ret = ast.unparse(node.returns) if node.returns else "None"
        end = getattr(node, "end_lineno", node.lineno)
        funcs.append({
            "name": node.name,
            "file": str(filepath),
            "async": isinstance(node, ast.AsyncFunctionDef),
            "params": params,
            "returns": ret,
            "lineno": node.lineno,
            "lines": end - node.lineno + 1,
        })
    return funcs

def extract_imports(tree: ast.AST) -> list[str]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports

# ─── Определение типа зависимости ────────────────────────────────────────────

STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "os", "sys", "re", "io", "json", "csv", "math", "time", "datetime", "pathlib",
    "typing", "collections", "itertools", "functools", "operator", "copy", "pprint",
    "logging", "warnings", "traceback", "inspect", "ast", "dis", "abc", "enum",
    "dataclasses", "contextlib", "threading", "multiprocessing", "subprocess",
    "socket", "http", "urllib", "email", "html", "xml", "sqlite3", "hashlib",
    "hmac", "secrets", "base64", "struct", "pickle", "shelve", "zipfile", "tarfile",
    "shutil", "tempfile", "glob", "fnmatch", "stat", "platform", "uuid", "decimal",
    "fractions", "random", "string", "textwrap", "difflib", "argparse", "configparser",
}

def classify_import(name: str, root_modules: set[str]) -> str:
    if name in STDLIB:
        return "stdlib"
    if name in root_modules:
        return "internal"
    return "thirdparty"

# ─── Дерево файлов ───────────────────────────────────────────────────────────

def build_tree(files: list[Path], root: Path) -> list[dict]:
    seen_dirs = set()
    nodes = []
    for f in files:
        rel = f.relative_to(root)
        parts = rel.parts
        for depth, part in enumerate(parts[:-1]):
            dir_key = parts[:depth + 1]
            if dir_key not in seen_dirs:
                seen_dirs.add(dir_key)
                nodes.append({"depth": depth, "name": part + "/", "type": "dir", "lines": None, "path": None})
        stats = count_lines(f)
        nodes.append({
            "depth": len(parts) - 1,
            "name": parts[-1],
            "type": "file",
            "lines": stats["total"],
            "path": f,
        })
    return nodes

# ─── Бизнес-процессы ─────────────────────────────────────────────────────────

def detect_flows(all_funcs: list[dict], all_classes: list[dict]) -> list[dict]:
    """Ищет связные цепочки вызовов по именам функций."""
    AUTH_KEYWORDS    = {"auth", "login", "token", "jwt", "session", "password", "credential", "user"}
    PAYMENT_KEYWORDS = {"pay", "charge", "invoice", "billing", "stripe", "transaction", "order", "cart"}
    NOTIFY_KEYWORDS  = {"notif", "email", "sms", "send", "message", "alert", "webhook"}
    DATA_KEYWORDS    = {"fetch", "get", "load", "query", "search", "filter", "list", "read"}

    flows: dict[str, list] = defaultdict(list)
    for fn in all_funcs:
        name_lower = fn["name"].lower()
        short_file = Path(fn["file"]).name
        entry = f"{fn['name']}()  [{short_file}:{fn['lineno']}]"
        if any(k in name_lower for k in AUTH_KEYWORDS):
            flows["Аутентификация"].append(entry)
        if any(k in name_lower for k in PAYMENT_KEYWORDS):
            flows["Заказы и оплата"].append(entry)
        if any(k in name_lower for k in NOTIFY_KEYWORDS):
            flows["Уведомления"].append(entry)
        if any(k in name_lower for k in DATA_KEYWORDS):
            flows["Получение данных"].append(entry)

    result = []
    for name, funcs in flows.items():
        if funcs:
            result.append({"name": name, "functions": funcs})
    return result

# ─── ВЫВОД РАЗДЕЛОВ ──────────────────────────────────────────────────────────

def print_overview(stats_per_file, files, all_classes):
    section_header("Обзор проекта")
    total = sum(s["total"] for s in stats_per_file.values())
    code  = sum(s["code"]  for s in stats_per_file.values())
    comm  = sum(s["comments"] for s in stats_per_file.values())
    blank = sum(s["blank"] for s in stats_per_file.values())
    print(f"  Файлов .py проанализировано : {g(len(files))}")
    print(f"  Всего строк                 : {g(total)}")
    print(f"  Строки кода                 : {c(code)}  ({round(code/total*100) if total else 0}%)")
    print(f"  Комментарии                 : {p(comm)}  ({round(comm/total*100) if total else 0}%)")
    print(f"  Пустые строки               : {dim(blank)}  ({round(blank/total*100) if total else 0}%)")
    print(f"  Классов найдено             : {a(len(all_classes))}")
    if stats_per_file:
        avg = round(total / len(stats_per_file))
        max_f = max(stats_per_file, key=lambda k: stats_per_file[k]["total"])
        print(f"  Среднее строк / файл        : {g(avg)}")
        print(f"  Самый большой файл          : {a(Path(max_f).name)} ({stats_per_file[max_f]['total']} строк)")

def print_stats(stats_per_file, complexity_per_file):
    section_header("Статистика и метрики сложности")
    rows = []
    for path, stats in stats_per_file.items():
        cc = complexity_per_file.get(path, 1)
        gr = grade(cc)
        rows.append((Path(path).name, stats["total"], stats["code"], cc, gr))
    rows.sort(key=lambda x: x[3], reverse=True)

    print(f"  {'Файл':<35} {'Строк':>6} {'Код':>6} {'CC':>4}  Оценка")
    print(f"  {dim('─'*35)} {dim('─'*6)} {dim('─'*6)} {dim('─'*4)}  {dim('─'*6)}")
    for name, total, code, cc, gr in rows:
        col = grade_color(gr)
        print(f"  {g(name):<44} {dim(total):>6} {dim(code):>6} {col(str(cc).rjust(4))}  {col(f'[{gr}]')}")

    print(f"\n  {dim('Шкала:')}  {g('[A] 1–10 Простой')}  {c('[B] 11–20 Умеренный')}  {a('[C] 21–30 Сложный')}  {r('[D] 31+ Очень сложный')}")

def print_classes(all_classes):
    section_header(f"Классы и иерархия ({len(all_classes)})")
    for cls in all_classes:
        parents = f"({', '.join(cls['parents'])})" if cls["parents"] else ""
        print(f"\n  {a('class ')} {g(cls['name'])}{dim(parents)}")
        print(f"    {dim('Файл:      ')}{c(Path(cls['file']).name)}:{cls['lineno']}")
        print(f"    {dim('Методов:   ')}{a(len(cls['methods']))}  {dim('|  Атрибутов: ')}{p(len(cls['properties']))}")
        if cls["methods"]:
            preview = ", ".join(f"{m}()" for m in cls["methods"][:6])
            extra = len(cls["methods"]) - 6
            suffix = f"  {dim(f'+ ещё {extra}')}" if extra > 0 else ""
            print(f"    {dim('Методы:    ')}{g(preview)}{suffix}")

def print_functions(all_funcs):
    section_header(f"Функции и методы ({len(all_funcs)})")
    all_funcs_sorted = sorted(all_funcs, key=lambda f: f["lines"], reverse=True)
    print(f"  {'№':>3}  {'Функция':<32} {'async':>5}  {'Params':>6}  {'Строк':>6}  {'→ Тип':>14}  Файл")
    print(f"  {dim('─'*3)}  {dim('─'*32)} {dim('─'*5)}  {dim('─'*6)}  {dim('─'*6)}  {dim('─'*14)}  {dim('─'*20)}")
    for i, fn in enumerate(all_funcs_sorted, 1):
        async_mark = p("async") if fn["async"] else dim("     ")
        ret = fn["returns"][:14] if fn["returns"] else "None"
        short_file = Path(fn["file"]).name
        print(
            f"  {dim(str(i).rjust(3))}  {a('def ')}{g(fn['name']):<36}"
            f" {async_mark}  {c(str(len(fn['params'])).rjust(6))}  "
            f"{a(str(fn['lines']).rjust(6))}  {p(ret.rjust(14))}  {dim(short_file)}"
        )

def print_deps(all_imports, root_modules):
    section_header("Зависимости и модули")
    counter: dict[str, dict] = defaultdict(lambda: {"count": 0, "kind": "thirdparty"})
    for imp in all_imports:
        kind = classify_import(imp, root_modules)
        counter[imp]["count"] += 1
        counter[imp]["kind"] = kind

    stdlib_list    = [(n, v["count"]) for n, v in counter.items() if v["kind"] == "stdlib"]
    thirdparty_list= [(n, v["count"]) for n, v in counter.items() if v["kind"] == "thirdparty"]
    internal_list  = [(n, v["count"]) for n, v in counter.items() if v["kind"] == "internal"]

    print(f"\n  {a('Сторонние библиотеки')} ({len(thirdparty_list)}):")
    for name, cnt in sorted(thirdparty_list, key=lambda x: -x[1]):
        bar = g("█" * min(cnt, 30))
        print(f"    {c(name):<20} {bar}  {dim(cnt)}")

    print(f"\n  {a('Стандартная библиотека')} ({len(stdlib_list)}):")
    names = "  ".join(g(n) for n, _ in sorted(stdlib_list))
    print(f"    {names}")

    if internal_list:
        print(f"\n  {a('Внутренние модули')} ({len(internal_list)}):")
        names_i = "  ".join(c(n) for n, _ in sorted(internal_list))
        print(f"    {names_i}")

def print_tree(tree_nodes, root: Path):
    section_header("Структура проекта")
    print(f"  {a(root.name + '/')}")
    for node in tree_nodes:
        if node["depth"] == 0:
            continue
        spaces = "    " * (node["depth"] - 1)
        connector = "├── " if node["depth"] == 1 else "│   └── "
        if node["type"] == "dir":
            print(f"  {dim(spaces + connector)}{a(node['name'])}")
        else:
            lines_str = f"  {dim(str(node['lines']) + ' стр')}" if node["lines"] else ""
            color = a if node["lines"] and node["lines"] > 500 else g
            print(f"  {dim(spaces + connector)}{color(node['name'])}{lines_str}")
    total_files = sum(1 for n in tree_nodes if n["type"] == "file")
    total_dirs  = sum(1 for n in tree_nodes if n["type"] == "dir")
    print(f"\n  {dim('Итого:')} файлов {g(total_files)}  директорий {a(total_dirs)}")

def print_flows(flows):
    section_header("Бизнес-процессы и потоки данных")
    if not flows:
        print(f"  {dim('Явных бизнес-процессов не обнаружено.')}")
        return
    for flow in flows:
        print(f"\n  {c('▶')} {bold(flow['name'])}  {dim(f'({len(flow[\"functions\"])} функций)')}")
        for i, fn in enumerate(flow["functions"], 1):
            print(f"    {dim(str(i) + '.')}  {g(fn)}")

# ─── ЭКСПОРТ ─────────────────────────────────────────────────────────────────

def export_report(path: str, sections: dict):
    """Сохраняет текстовый отчёт без ANSI-кодов цветов."""
    import re
    ansi_escape = re.compile(r"\033\[[0-9;]*m")

    lines = [
        "=" * 70,
        "  PYSCOPE — Python Code Analyzer Report",
        "=" * 70,
    ]
    for name, content in sections.items():
        lines.append("")
        lines.append(f"{'─'*70}")
        lines.append(f"  {name.upper()}")
        lines.append(f"{'─'*70}")
        lines.extend(ansi_escape.sub("", content).splitlines())

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  {g('✓')} Отчёт сохранён: {c(path)}")

# ─── MAIN ────────────────────────────────────────────────────────────────────

SECTIONS = ["overview", "stats", "classes", "functions", "deps", "tree", "flows"]

def main():
    parser = argparse.ArgumentParser(
        description="PyScope — анализатор Python-проектов",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("path", help="Путь к папке проекта")
    parser.add_argument(
        "--section", "-s",
        choices=SECTIONS + ["all"],
        default="all",
        help="Раздел анализа (по умолчанию: all)",
    )
    parser.add_argument("--out", "-o", help="Сохранить отчёт в файл .txt")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        print(r(f"Ошибка: папка не найдена — {root}"))
        sys.exit(1)

    # ── Шапка ──
    print(f"\n{SEP}")
    print(f"  {bold(g('PYSCOPE'))}  {dim('Python Code Analyzer v1.0.0')}")
    print(f"  {dim('Проект:')} {c(root.name)}  {dim('Путь:')} {dim(str(root))}")
    print(SEP)

    # ── Сбор файлов ──
    files = collect_files(root)
    if not files:
        print(r("  Файлы .py не найдены (или все отфильтрованы как тестовые)."))
        sys.exit(0)

    root_modules = {f.stem for f in root.iterdir() if f.is_dir() or f.suffix == ".py"}

    print(f"  {dim('Найдено .py файлов:')} {g(len(files))}  {dim('(тест-файлы исключены)')}")

    # ── Анализ ──
    stats_per_file: dict = {}
    complexity_per_file: dict = {}
    all_classes: list = []
    all_funcs: list = []
    all_imports: list = []

    for fpath in files:
        stats_per_file[str(fpath)] = count_lines(fpath)
        tree, source = parse_file(fpath)
        if tree is None:
            continue
        complexity_per_file[str(fpath)] = cyclomatic_complexity(tree)
        all_classes.extend(extract_classes(tree, fpath))
        all_funcs.extend(extract_functions(tree, fpath))
        all_imports.extend(extract_imports(tree))

    tree_nodes = build_tree(files, root)
    flows = detect_flows(all_funcs, all_classes)

    active = SECTIONS if args.section == "all" else [args.section]

    # ── Печать разделов ──
    import io, contextlib

    captured = {}
    for sec in active:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if sec == "overview":   print_overview(stats_per_file, files, all_classes)
            elif sec == "stats":    print_stats(stats_per_file, complexity_per_file)
            elif sec == "classes":  print_classes(all_classes)
            elif sec == "functions":print_functions(all_funcs)
            elif sec == "deps":     print_deps(all_imports, root_modules)
            elif sec == "tree":     print_tree(tree_nodes, root)
            elif sec == "flows":    print_flows(flows)
        output = buf.getvalue()
        captured[sec] = output
        print(output, end="")

    print(f"\n{SEP}\n")

    # ── Экспорт ──
    if args.out:
        export_report(args.out, captured)
        print()

    input(dim("  Нажмите Enter для выхода..."))

if __name__ == "__main__":
    main()