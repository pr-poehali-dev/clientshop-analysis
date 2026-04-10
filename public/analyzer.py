#!/usr/bin/env python3
"""
PyScope - Python Code Analyzer
Использование: python analyzer.py /путь/к/проекту
               python analyzer.py /путь/к/проекту --section tree
               python analyzer.py /путь/к/проекту --out report.txt
"""

import ast
import os
import sys
import argparse
import io
import re
import traceback
import contextlib
from pathlib import Path
from collections import defaultdict


# --- Цвета терминала ---------------------------------------------------------

class C:
    GREEN  = "\033[92m"
    AMBER  = "\033[93m"
    CYAN   = "\033[96m"
    RED    = "\033[91m"
    PURPLE = "\033[95m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


def g(text):    return f"{C.GREEN}{text}{C.RESET}"
def a(text):    return f"{C.AMBER}{text}{C.RESET}"
def c(text):    return f"{C.CYAN}{text}{C.RESET}"
def r(text):    return f"{C.RED}{text}{C.RESET}"
def p(text):    return f"{C.PURPLE}{text}{C.RESET}"
def dim(text):  return f"{C.DIM}{text}{C.RESET}"
def bold(text): return f"{C.BOLD}{text}{C.RESET}"


SEP = dim("-" * 70)


def section_header(title):
    pad = max(0, 66 - len(title))
    print(f"\n{dim('+-')} {a(title.upper())} {dim('-' * pad)}")


# --- Сбор файлов -------------------------------------------------------------

SKIP_DIRS = {"tests", "test", "__pycache__", ".venv", "venv", "env", ".git",
             "node_modules", ".idea", ".vs", "bin", "obj", "dist", "build", ".svn",
             "UpdBackups", "updbackups", "Backup", "backup", "backups", "Backups",
             "Archive", "archive", "Old", "old",
             "udf", "UDF", "32", "64", "32n", "64n"}

KNOWN_LANGS = {
    ".py":   "Python",
    ".js":   "JavaScript",
    ".ts":   "TypeScript",
    ".php":  "PHP",
    ".cs":   "C#",
    ".java": "Java",
    ".cpp":  "C++",
    ".c":    "C",
    ".rb":   "Ruby",
    ".go":   "Go",
    ".rs":   "Rust",
    ".kt":   "Kotlin",
    ".swift":"Swift",
    ".html": "HTML",
    ".css":  "CSS",
    ".sql":  "SQL",
    ".sh":   "Shell",
    ".ps1":  "PowerShell",
    ".xml":  "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml":  "YAML",
}


def detect_languages(root):
    """Сканирует папку и возвращает словарь {расширение: количество файлов}."""
    counter = defaultdict(int)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        ext = path.suffix.lower()
        if ext in KNOWN_LANGS:
            counter[ext] += 1
    return dict(sorted(counter.items(), key=lambda x: -x[1]))


def ask_language(root):
    """Показывает найденные языки и просит выбрать один для анализа."""
    langs = detect_languages(root)
    if not langs:
        print(r("  Файлы с исходным кодом не найдены."))
        return None

    print(f"\n  {a('Найдены файлы в папке')} {c(root.name)}:")
    items = list(langs.items())
    for i, (ext, cnt) in enumerate(items, 1):
        lang = KNOWN_LANGS.get(ext, ext)
        bar = g("#" * min(cnt, 25))
        print(f"    {g(str(i))}. {lang:<14} {ext:<6}  {bar}  {dim(str(cnt) + ' файлов')}")

    print(f"\n  {dim('Введите номер языка для анализа:')}")
    raw = input(f"  {g('> ')}").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(items):
        return items[int(raw) - 1][0]
    return items[0][0]


def collect_files(root, ext=".py"):
    files = []
    for path in sorted(root.rglob("*" + ext)):
        name = path.name
        parts = path.parts
        if ext == ".py" and (name.startswith("test_") or name.endswith("_test.py")):
            continue
        if any(part in SKIP_DIRS for part in parts):
            continue
        files.append(path)
    return files


# --- Статистика строк --------------------------------------------------------

def count_lines(path):
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


# --- Cyclomatic Complexity ---------------------------------------------------

BRANCH_NODES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.With, ast.Assert, ast.comprehension,
)


def cyclomatic_complexity(tree):
    cc = 1
    for node in ast.walk(tree):
        if isinstance(node, BRANCH_NODES):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            cc += len(node.values) - 1
    return cc


def grade(cc):
    if cc <= 10: return "A"
    if cc <= 20: return "B"
    if cc <= 30: return "C"
    return "D"


def grade_col(gr):
    return {"A": g, "B": c, "C": a, "D": r}.get(gr, g)


# --- Парсинг AST -------------------------------------------------------------

def parse_file(path):
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        return ast.parse(source), source
    except SyntaxError:
        return None, None


def extract_classes(tree, filepath):
    classes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        parents = [ast.unparse(b) for b in node.bases] if node.bases else []
        methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
        props = []
        for n in ast.walk(node):
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
                props.append(n.targets[0].id)
        classes.append({
            "name": node.name,
            "file": str(filepath),
            "parents": parents,
            "methods": methods,
            "properties": list(dict.fromkeys(props)),
            "lineno": node.lineno,
        })
    return classes


def extract_functions(tree, filepath):
    funcs = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = [arg.arg for arg in node.args.args]
        ret = ast.unparse(node.returns) if node.returns else "None"
        end = getattr(node, "end_lineno", node.lineno)
        funcs.append({
            "name": node.name,
            "file": str(filepath),
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "params": params,
            "returns": ret,
            "lineno": node.lineno,
            "lines": end - node.lineno + 1,
        })
    return funcs


def extract_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


# --- Зависимости -------------------------------------------------------------

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


def classify_import(name, root_modules):
    if name in STDLIB:
        return "stdlib"
    if name in root_modules:
        return "internal"
    return "thirdparty"


# --- Дерево файлов -----------------------------------------------------------

def build_tree(files, root):
    seen_dirs = set()
    nodes = []
    for f in files:
        rel = f.relative_to(root)
        parts = rel.parts
        for depth, part in enumerate(parts[:-1]):
            dir_key = parts[:depth + 1]
            if dir_key not in seen_dirs:
                seen_dirs.add(dir_key)
                nodes.append({"depth": depth, "name": part + "/", "type": "dir", "lines": None})
        st = count_lines(f)
        nodes.append({"depth": len(parts) - 1, "name": parts[-1], "type": "file", "lines": st["total"]})
    return nodes


# --- Бизнес-процессы ---------------------------------------------------------

def detect_flows(all_funcs):
    AUTH    = {"auth", "login", "token", "jwt", "session", "password", "credential", "user"}
    PAYMENT = {"pay", "charge", "invoice", "billing", "stripe", "transaction", "order", "cart"}
    NOTIFY  = {"notif", "email", "sms", "send", "message", "alert", "webhook"}
    DATA    = {"fetch", "get", "load", "query", "search", "filter", "list", "read"}

    buckets = defaultdict(list)
    for fn in all_funcs:
        nl = fn["name"].lower()
        entry = fn["name"] + "()  [" + Path(fn["file"]).name + ":" + str(fn["lineno"]) + "]"
        if any(k in nl for k in AUTH):    buckets["Аутентификация"].append(entry)
        if any(k in nl for k in PAYMENT): buckets["Заказы и оплата"].append(entry)
        if any(k in nl for k in NOTIFY):  buckets["Уведомления"].append(entry)
        if any(k in nl for k in DATA):    buckets["Получение данных"].append(entry)

    return [{"name": name, "functions": fns} for name, fns in buckets.items() if fns]


# --- Вывод разделов ----------------------------------------------------------

def print_overview(stats_per_file, files, all_classes):
    section_header("Обзор проекта")
    total = sum(s["total"]    for s in stats_per_file.values())
    code  = sum(s["code"]     for s in stats_per_file.values())
    comm  = sum(s["comments"] for s in stats_per_file.values())
    blank = sum(s["blank"]    for s in stats_per_file.values())
    print(f"  Файлов .py проанализировано : {g(str(len(files)))}")
    print(f"  Всего строк                 : {g(str(total))}")
    pct_code  = round(code  / total * 100) if total else 0
    pct_comm  = round(comm  / total * 100) if total else 0
    pct_blank = round(blank / total * 100) if total else 0
    print(f"  Строки кода                 : {c(str(code))}  ({pct_code}%)")
    print(f"  Комментарии                 : {p(str(comm))}  ({pct_comm}%)")
    print(f"  Пустые строки               : {dim(str(blank))}  ({pct_blank}%)")
    print(f"  Классов найдено             : {a(str(len(all_classes)))}")
    if stats_per_file:
        avg   = round(total / len(stats_per_file))
        max_f = max(stats_per_file, key=lambda k: stats_per_file[k]["total"])
        print(f"  Среднее строк / файл        : {g(str(avg))}")
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
    print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*4}  {'-'*6}")
    for name, total, code, cc, gr in rows:
        col = grade_col(gr)
        print(f"  {g(name):<44} {total:>6} {code:>6} {col(str(cc).rjust(4))}  {col('[' + gr + ']')}")
    print(f"\n  {g('[A] 1-10 Простой')}  {c('[B] 11-20 Умеренный')}  {a('[C] 21-30 Сложный')}  {r('[D] 31+ Очень сложный')}")


def print_classes(all_classes):
    section_header(f"Классы и иерархия ({len(all_classes)})")
    for cls in all_classes:
        parents = "(" + ", ".join(cls["parents"]) + ")" if cls["parents"] else ""
        print(f"\n  {a('class')} {g(cls['name'])}{dim(parents)}")
        print(f"    {dim('Файл:      ')}{c(Path(cls['file']).name)}:{cls['lineno']}")
        print(f"    {dim('Методов:   ')}{a(str(len(cls['methods'])))}  {dim('|  Атрибутов: ')}{p(str(len(cls['properties'])))}")
        if cls["methods"]:
            preview = ", ".join(m + "()" for m in cls["methods"][:6])
            extra = len(cls["methods"]) - 6
            suffix = "  (+ ещё " + str(extra) + ")" if extra > 0 else ""
            print(f"    {dim('Методы:    ')}{g(preview)}{dim(suffix)}")


def print_functions(all_funcs):
    section_header(f"Функции и методы ({len(all_funcs)})")
    sorted_funcs = sorted(all_funcs, key=lambda f: f["lines"], reverse=True)
    print(f"  {'N':>3}  {'Функция':<32} {'async':>5}  {'Args':>4}  {'Строк':>5}  {'Тип':>12}  Файл")
    print(f"  {'-'*3}  {'-'*32} {'-'*5}  {'-'*4}  {'-'*5}  {'-'*12}  {'-'*20}")
    for i, fn in enumerate(sorted_funcs, 1):
        async_mark = p("async") if fn["is_async"] else dim("     ")
        ret = fn["returns"][:12] if fn["returns"] else "None"
        short_file = Path(fn["file"]).name
        print(
            f"  {dim(str(i).rjust(3))}  {a('def ')}{g(fn['name']):<36}"
            f" {async_mark}  {c(str(len(fn['params'])).rjust(4))}  "
            f"{a(str(fn['lines']).rjust(5))}  {p(ret.rjust(12))}  {dim(short_file)}"
        )


def print_deps(all_imports, root_modules):
    section_header("Зависимости и модули")
    counter = defaultdict(lambda: {"count": 0, "kind": "thirdparty"})
    for imp in all_imports:
        kind = classify_import(imp, root_modules)
        counter[imp]["count"] += 1
        counter[imp]["kind"] = kind

    third   = [(n, v["count"]) for n, v in counter.items() if v["kind"] == "thirdparty"]
    stdlib  = [(n, v["count"]) for n, v in counter.items() if v["kind"] == "stdlib"]
    intern  = [(n, v["count"]) for n, v in counter.items() if v["kind"] == "internal"]

    print(f"\n  {a('Сторонние библиотеки')} ({len(third)}):")
    for name, cnt in sorted(third, key=lambda x: -x[1]):
        bar = g("#" * min(cnt, 30))
        print(f"    {c(name):<20} {bar}  {dim(str(cnt))}")

    print(f"\n  {a('Стандартная библиотека')} ({len(stdlib)}):")
    print("    " + "  ".join(g(n) for n, _ in sorted(stdlib)))

    if intern:
        print(f"\n  {a('Внутренние модули')} ({len(intern)}):")
        print("    " + "  ".join(c(n) for n, _ in sorted(intern)))


def print_tree(tree_nodes, root):
    section_header("Структура проекта")
    print(f"  {a(root.name + '/')}")
    for node in tree_nodes:
        if node["depth"] == 0:
            continue
        spaces    = "    " * (node["depth"] - 1)
        connector = "+-- " if node["depth"] == 1 else "|   +-- "
        if node["type"] == "dir":
            print(f"  {dim(spaces + connector)}{a(node['name'])}")
        else:
            lines_str = "  " + dim(str(node["lines"]) + " стр") if node["lines"] else ""
            col = a if node["lines"] and node["lines"] > 500 else g
            print(f"  {dim(spaces + connector)}{col(node['name'])}{lines_str}")
    total_files = sum(1 for n in tree_nodes if n["type"] == "file")
    total_dirs  = sum(1 for n in tree_nodes if n["type"] == "dir")
    print(f"\n  {dim('Итого:')} файлов {g(str(total_files))}  директорий {a(str(total_dirs))}")


def print_flows(flows):
    section_header("Бизнес-процессы и потоки данных")
    if not flows:
        print(f"  {dim('Явных бизнес-процессов не обнаружено.')}")
        return
    for flow in flows:
        cnt = str(len(flow["functions"]))
        print(f"\n  {c('>')} {bold(flow['name'])}  {dim('(' + cnt + ' функций)')}")
        for i, fn in enumerate(flow["functions"], 1):
            print(f"    {dim(str(i) + '.')}  {g(fn)}")


# --- Экспорт -----------------------------------------------------------------

def export_report(path, sections):
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    lines = ["=" * 70, "  PYSCOPE - Python Code Analyzer Report", "=" * 70]
    for name, content in sections.items():
        lines.append("")
        lines.append("-" * 70)
        lines.append("  " + name.upper())
        lines.append("-" * 70)
        lines.extend(ansi_escape.sub("", content).splitlines())
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  {g('OK')} Отчёт сохранён: {c(path)}")


# --- Пользовательская форма --------------------------------------------------

SECTIONS = ["overview", "stats", "classes", "functions", "deps", "tree", "flows"]

SECTION_NAMES = {
    "overview":  "Обзор проекта",
    "stats":     "Статистика и сложность",
    "classes":   "Классы и иерархия",
    "functions": "Функции и методы",
    "deps":      "Зависимости",
    "tree":      "Дерево файлов",
    "flows":     "Бизнес-процессы",
}


# --- Сохранённые папки (заполняются автоматически после первого запуска) ------

DEFAULT_FOLDERS = [
    r"C:\ClientShop2site",
    r"C:\ClientShop2x",
    r"C:\ClientShopDatabase",
    r"C:\ClientShopDocuments",
]

DEFAULT_OUT = r"C:\1\report"


def ask_folder(label, index, default=None):
    """Запрашивает путь к папке. Enter = использовать сохранённый."""
    while True:
        print(f"\n  {a(label)}")
        if default:
            print(f"  {dim('Сохранено: ')}{c(default)}  {dim('(Enter чтобы использовать)')}")
        else:
            print(f"  {dim('Пример: C:\\Users\\Имя\\МойПроект  или  оставьте пустым чтобы пропустить')}")
        raw = input(f"  {g('> ')}").strip().strip('"').strip("'")
        if raw == "" and default:
            path = Path(default).resolve()
            if path.exists() and path.is_dir():
                print(f"  {g('OK')} Используется: {c(str(path))}")
                return path
            else:
                print(f"  {r('Сохранённая папка не найдена:')} {default}")
                print(f"  {dim('Введите новый путь:')}")
                continue
        if raw == "" and not default:
            return None
        path = Path(raw).resolve()
        if path.exists() and path.is_dir():
            print(f"  {g('OK')} Папка найдена: {c(str(path))}")
            return path
        else:
            print(f"  {r('Папка не найдена, попробуйте ещё раз.')}")


def ask_sections():
    """Выбор разделов анализа."""
    print(f"\n  {a('Какие разделы анализировать?')}")
    for i, sec in enumerate(SECTIONS, 1):
        print(f"    {g(str(i))}. {SECTION_NAMES[sec]}")
    print(f"    {g('0')}. Все разделы (по умолчанию)")
    print(f"\n  {dim('Введите номера через запятую, например: 1,3,5  или 0 для всех')}")
    raw = input(f"  {g('> ')}").strip()
    if raw == "" or raw == "0":
        return SECTIONS
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(SECTIONS):
                selected.append(SECTIONS[idx])
    return selected if selected else SECTIONS


def ask_export():
    """Спрашивает куда сохранить отчёт."""
    print(f"\n  {a('Сохранить отчёт в файл .txt?')}")
    print(f"  {dim('Сохранено: ')}{c(DEFAULT_OUT)}  {dim('(Enter чтобы использовать, или введите новый путь)')}")
    print(f"  {dim('Введите 0 чтобы не сохранять')}")
    raw = input(f"  {g('> ')}").strip().strip('"').strip("'")
    if raw == "0":
        return None
    if raw == "":
        return DEFAULT_OUT
    return raw


def interactive_form():
    """Главная форма ввода."""
    print(f"\n{'=' * 70}")
    print(f"  {bold(g('PYSCOPE'))}  {dim('Universal Code Analyzer v2.0')}")
    print(f"{'=' * 70}")
    print(f"  {dim('Анализирует проекты на любом языке. До 4 папок за один запуск.')}")
    print(f"  {dim('Папки сохранены — просто нажимайте Enter для подтверждения.')}")
    print(f"{'=' * 70}")

    folders = []
    labels = [
        "Папка 1:",
        "Папка 2 (Enter чтобы пропустить):",
        "Папка 3 (Enter чтобы пропустить):",
        "Папка 4 (Enter чтобы пропустить):",
    ]
    for i, label in enumerate(labels):
        default = DEFAULT_FOLDERS[i] if i < len(DEFAULT_FOLDERS) else None
        path = ask_folder(label, i + 1, default=default)
        if path is None and i == 0:
            print(r("\n  Нужно указать хотя бы одну папку."))
            return interactive_form()
        if path is None:
            break
        folders.append(path)

    active_sections = ask_sections()
    out_file = ask_export()

    return folders, active_sections, out_file


# --- Main --------------------------------------------------------------------


def collect_all_files(root):
    """Собирает ВСЕ файлы с исходным кодом любого языка."""
    all_files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in KNOWN_LANGS:
            all_files.append(path)
    return all_files


def print_universal_overview(root, all_files):
    """Обзор проекта для любого языка."""
    section_header("Обзор проекта")

    # Статистика по языкам
    by_lang = defaultdict(list)
    for f in all_files:
        by_lang[f.suffix.lower()].append(f)

    total_lines = 0
    total_code  = 0
    total_files = len(all_files)

    print(f"  Папка:              {c(str(root))}")
    print(f"  Всего файлов кода:  {g(str(total_files))}")
    print(f"\n  {'Язык':<16} {'Расш.':<8} {'Файлов':>7}  Доля")
    print(f"  {'-'*16} {'-'*8} {'-'*7}  {'-'*20}")

    for ext, files in sorted(by_lang.items(), key=lambda x: -len(x[1])):
        lang = KNOWN_LANGS.get(ext, ext)
        cnt  = len(files)
        pct  = round(cnt / total_files * 100) if total_files else 0
        bar  = g("#" * (pct // 4))
        for f in files:
            st = count_lines(f)
            total_lines += st["total"]
            total_code  += st["code"]
        print(f"  {lang:<16} {ext:<8} {str(cnt):>7}  {bar} {dim(str(pct) + '%')}")

    print(f"\n  Всего строк:        {g(str(total_lines))}")
    if total_lines:
        print(f"  Строки кода (~):    {c(str(total_code))}  ({round(total_code/total_lines*100)}%)")


def print_universal_tree(root, all_files):
    """Дерево файлов для любого языка."""
    section_header("Структура проекта")
    tree_nodes = build_tree(all_files, root)
    print(f"  {a(root.name + '/')}")
    for node in tree_nodes:
        if node["depth"] == 0:
            continue
        spaces    = "    " * (node["depth"] - 1)
        connector = "+-- " if node["depth"] == 1 else "|   +-- "
        if node["type"] == "dir":
            print(f"  {dim(spaces + connector)}{a(node['name'])}")
        else:
            ext = Path(node["name"]).suffix.lower()
            lang = KNOWN_LANGS.get(ext, "")
            lang_str = "  " + dim("[" + lang + "]") if lang else ""
            lines_str = "  " + dim(str(node["lines"]) + " стр") if node["lines"] else ""
            col = a if node["lines"] and node["lines"] > 500 else g
            print(f"  {dim(spaces + connector)}{col(node['name'])}{lang_str}{lines_str}")
    print(f"\n  {dim('Итого:')} {g(str(len(all_files)))} файлов")


def print_universal_stats(root, all_files):
    """Статистика строк для любого языка."""
    section_header("Статистика по файлам")
    rows = []
    for f in all_files:
        st = count_lines(f)
        rows.append((f.relative_to(root), st["total"], st["code"]))
    rows.sort(key=lambda x: -x[1])
    print(f"  {'Файл':<50} {'Строк':>6}  {'Код':>6}")
    print(f"  {'-'*50} {'-'*6}  {'-'*6}")
    for rel, total, code in rows[:40]:
        col = a if total > 500 else g
        print(f"  {col(str(rel)):<59} {total:>6}  {dim(str(code)):>6}")
    if len(rows) > 40:
        print(f"  {dim('... и ещё ' + str(len(rows)-40) + ' файлов')}")


def print_universal_keywords(all_files):
    """Ищет бизнес-ключевые слова — только в коде, не в HTML/лицензиях."""
    section_header("Бизнес-логика — ключевые слова")

    # Расширения где ищем (исключаем HTML, CSS, лицензионные SQL)
    CODE_EXTS = {".ts", ".js", ".py", ".php", ".cs", ".java", ".json", ".xml", ".ps1"}

    BUSINESS = {
        "Авторизация / Пользователи": ["login", "logout", "auth", "password", "register", "token", "session", "permission", "role"],
        "Заказы / Продажи":           ["simplesale", "checksale", "sale", "order", "checkout", "purchase"],
        "Оплата / Долги":             ["payment", "pay", "invoice", "buyerdebt", "charge", "transaction", "refund", "doc_pays"],
        "Товары / Каталог":           ["goods", "product", "catalog", "category", "stock", "dir_goods", "price_", "discount", "art"],
        "Уведомления / SMS":          ["sms", "notify", "notification", "alert", "sendmessage"],
        "База данных / Таблицы":      ["doc_", "dir_", "database", "connectionstring", "fdb", "firebird", "getactivegoods"],
        "Отчёты":                     ["report", "setname", "addcolumn", "createreport", "addrow", "setvalue"],
        "Инвентаризация":             ["invsession", "inventory", "остаток", "остатки", "приход", "расход"],
    }

    # Строки которые пропускаем (лицензии, комментарии, HTML-теги)
    SKIP_PATTERNS = [
        "license", "copyright", "mozilla", "initial developer",
        "contents of this file", "you may not use",
        "<span", "<font", "<meta", "<table", "border-width",
        "border-collapse", "stylesheet", "fbudf_api",
    ]

    found = defaultdict(list)
    for fpath in all_files:
        if fpath.suffix.lower() not in CODE_EXTS:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            for category, keywords in BUSINESS.items():
                for i, line in enumerate(lines, 1):
                    line_low = line.lower().strip()
                    # Пропускаем пустые, комментарии-лицензии и HTML
                    if not line_low or len(line_low) < 5:
                        continue
                    if any(sp in line_low for sp in SKIP_PATTERNS):
                        continue
                    for kw in keywords:
                        if kw in line_low:
                            snippet = line.strip()[:70]
                            entry = f"{fpath.name}:{i}  {snippet}"
                            if entry not in found[category]:
                                found[category].append(entry)
                            break
        except Exception:
            pass

    if not found:
        print(f"  {dim('Ключевых бизнес-слов не найдено.')}")
        return

    for category, hits in found.items():
        print(f"\n  {c('>')} {bold(category)}")
        for h in hits[:6]:
            print(f"    {dim('-')}  {g(h)}")


def print_universal_deps(root, all_files):
    """Анализ зависимостей — таблицы SQL, модули TS/JS, библиотеки PHP/C#."""
    section_header("Зависимости и подключения")

    # Стоп-слова — мусор из комментариев и ключевые слова языков
    STOPWORDS = {
        "as", "the", "this", "from", "that", "with", "for", "and", "not",
        "new", "null", "true", "false", "native", "srand", "void", "int",
        "char", "return", "class", "public", "private", "static", "using",
        "select", "where", "inner", "outer", "left", "right", "join", "on",
        "by", "or", "in", "is", "of", "to", "be", "at", "an", "do", "if",
        "set", "all", "any", "end", "var", "let", "const", "type", "enum",
    }

    # JS/TS: import X from '...'  или  import '...'
    ts_modules   = defaultdict(int)
    # SQL: FROM table, JOIN table, INTO table
    sql_tables   = defaultdict(int)
    # PHP/C#: use / require / #include
    other_deps   = defaultdict(int)

    pat_ts_from  = re.compile(r"""from\s+['"]([^'"]+)['"]""", re.IGNORECASE)
    pat_ts_req   = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.IGNORECASE)
    pat_sql_tbl  = re.compile(r"""(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-zA-Z_]\w*)""", re.IGNORECASE)
    pat_php_use  = re.compile(r"""(?:use|require_once|require|include_once|include)\s+['"]?([A-Za-z_][\w/\\]*)""", re.IGNORECASE)
    pat_cs_using = re.compile(r"""using\s+([A-Za-z_][\w.]*)""")
    pat_include  = re.compile(r"""#include\s+[<"]([^>"]+)[>"]""")

    for fpath in all_files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            ext  = fpath.suffix.lower()

            if ext in (".ts", ".js"):
                for m in pat_ts_from.finditer(text):
                    mod = m.group(1).split("/")[0].lstrip("@")
                    if mod and not mod.startswith(".") and mod not in STOPWORDS:
                        ts_modules[mod] += 1
                for m in pat_ts_req.finditer(text):
                    mod = m.group(1).split("/")[0]
                    if mod and not mod.startswith(".") and mod not in STOPWORDS:
                        ts_modules[mod] += 1
                # TypeScript может содержать SQL-запросы в строках
                for m in pat_sql_tbl.finditer(text):
                    tbl = m.group(1).lower()
                    if len(tbl) > 3 and tbl not in STOPWORDS and not tbl.isdigit():
                        sql_tables[tbl] += 1

            elif ext == ".sql":
                for m in pat_sql_tbl.finditer(text):
                    tbl = m.group(1).lower()
                    if len(tbl) > 3 and tbl not in STOPWORDS and not tbl.isdigit():
                        sql_tables[tbl] += 1

            elif ext == ".php":
                for m in pat_php_use.finditer(text):
                    dep = m.group(1).split("/")[0].split("\\")[0]
                    if dep and dep not in STOPWORDS:
                        other_deps[dep] += 1

            elif ext in (".cs",):
                for m in pat_cs_using.finditer(text):
                    dep = m.group(1).split(".")[0]
                    if dep and dep not in STOPWORDS:
                        other_deps[dep] += 1

            elif ext in (".c", ".cpp", ".h"):
                for m in pat_include.finditer(text):
                    other_deps[m.group(1)] += 1

        except Exception:
            pass

    found_any = False

    if ts_modules:
        found_any = True
        print(f"\n  {a('Модули TypeScript / JavaScript')} ({len(ts_modules)}):")
        print(f"  {'Модуль':<30} {'Упоминаний':>10}  График")
        print(f"  {'-'*30} {'-'*10}  {'-'*25}")
        for dep, cnt in sorted(ts_modules.items(), key=lambda x: -x[1])[:25]:
            bar = g("#" * min(cnt, 25))
            print(f"  {c(dep):<30} {str(cnt):>10}  {bar}")

    if sql_tables:
        found_any = True
        print(f"\n  {a('Таблицы базы данных (SQL)')} ({len(sql_tables)}):")
        print(f"  {'Таблица':<35} {'Упоминаний':>10}  График")
        print(f"  {'-'*35} {'-'*10}  {'-'*20}")
        for tbl, cnt in sorted(sql_tables.items(), key=lambda x: -x[1])[:30]:
            bar = g("#" * min(cnt, 20))
            print(f"  {c(tbl):<35} {str(cnt):>10}  {bar}")

    if other_deps:
        found_any = True
        print(f"\n  {a('Прочие зависимости')} ({len(other_deps)}):")
        for dep, cnt in sorted(other_deps.items(), key=lambda x: -x[1])[:20]:
            print(f"  {c(dep):<30} {dim(str(cnt) + ' упом.')}")

    if not found_any:
        print(f"  {dim('Зависимостей не найдено.')}")


def analyze_folder(root, active_sections, out_file=None):
    """Универсальный анализ папки — любой язык программирования."""
    print(f"\n{'=' * 70}")
    print(f"  {bold(g('АНАЛИЗ:'))} {c(root.name)}")
    print(f"  {dim(str(root))}")
    print(f"{'=' * 70}")

    all_files = collect_all_files(root)
    if not all_files:
        print(r("  Файлы с исходным кодом не найдены."))
        return

    # Python-файлы для глубокого AST-анализа
    py_files = [f for f in all_files if f.suffix.lower() == ".py"]

    stats_per_file     = {}
    complexity_per_file = {}
    all_classes = []
    all_funcs   = []
    all_imports = []

    for fpath in py_files:
        stats_per_file[str(fpath)] = count_lines(fpath)
        tree, source = parse_file(fpath)
        if tree is None:
            continue
        complexity_per_file[str(fpath)] = cyclomatic_complexity(tree)
        all_classes.extend(extract_classes(tree, fpath))
        all_funcs.extend(extract_functions(tree, fpath))
        all_imports.extend(extract_imports(tree))

    # Для не-Python файлов добавляем в статистику
    for fpath in all_files:
        key = str(fpath)
        if key not in stats_per_file:
            stats_per_file[key] = count_lines(fpath)

    root_modules = {f.stem for f in root.iterdir() if f.is_dir() or f.suffix == ".py"}

    captured = {}
    for sec in active_sections:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if sec == "overview":
                print_universal_overview(root, all_files)
            elif sec == "tree":
                print_universal_tree(root, all_files)
            elif sec == "stats":
                print_universal_stats(root, all_files)
            elif sec == "deps":
                print_universal_deps(root, all_files)
            elif sec == "flows":
                # Бизнес-ключевые слова для любого языка
                print_universal_keywords(all_files)
                # Если есть Python — ещё и AST-потоки
                if all_funcs:
                    flows = detect_flows(all_funcs)
                    print_flows(flows)
            elif sec == "classes" and all_classes:
                print_classes(all_classes)
            elif sec == "classes":
                section_header("Классы и иерархия")
                print(f"  {dim('Python-классы не найдены. Проект написан на другом языке.')}")
            elif sec == "functions" and all_funcs:
                print_functions(all_funcs)
            elif sec == "functions":
                section_header("Функции и методы")
                print(f"  {dim('Python-функции не найдены. Проект написан на другом языке.')}")
        output = buf.getvalue()
        captured[sec] = output
        print(output, end="")

    print(f"\n{SEP}\n")

    if out_file:
        # Сохраняем с именем папки
        base = out_file if out_file.endswith(".txt") else out_file + ".txt"
        folder_out = base.replace(".txt", f"_{root.name}.txt")
        export_report(folder_out, captured)


def print_architecture(all_folders_data):
    """Архитектурный анализ — всё необходимое для проектирования веб-приложения."""
    print(f"\n{'=' * 70}")
    print(f"  {bold(g('АРХИТЕКТУРНЫЙ АНАЛИЗ — ОСНОВА ДЛЯ ВЕБ-ПРИЛОЖЕНИЯ'))}")
    print(f"{'=' * 70}")

    # Собираем все таблицы по всем папкам
    all_tables = defaultdict(int)
    all_biz    = defaultdict(list)
    for d in all_folders_data:
        for tbl, cnt in d["sql_tables"].items():
            all_tables[tbl] += cnt
        for cat, hits in d["biz_keywords"].items():
            for h in hits:
                entry = f"[{d['name']}]  {h}"
                if entry not in all_biz[cat]:
                    all_biz[cat].append(entry)

    # ── 1. Модули веб-приложения ─────────────────────────────────────────
    print(f"\n  {a('1. МОДУЛИ ВЕБ-ПРИЛОЖЕНИЯ (предлагаемые страницы/разделы):')}")
    modules = [
        ("Товары и каталог",     ["dir_goods", "dir_goods_scan", "dir_goods_price", "goods"], "Просмотр, поиск, редактирование товаров, цен, штрихкодов"),
        ("Продажи и чеки",       ["doc_sale", "doc_sale_table", "simplesale"], "История продаж, детализация чеков, возвраты"),
        ("Инвентаризация",       ["doc_invsession", "doc_invsession_table", "invsession"], "Сессии инвентаризации, сравнение остатков"),
        ("Закупки и поставщики", ["dir_purchases", "doc_session", "doc_session_table"], "Сессии закупок, поставщики, приход товара"),
        ("Контрагенты / Долги",  ["dir_contragents", "doc_pays", "buyersdebts", "buyerdebt"], "Покупатели, долги, история оплат"),
        ("Отчёты и аналитика",   ["doc_date", "salesreturns", "datedays", "oborot"], "Обороты, средний чек, остатки по периодам"),
        ("Скидки и цены",        ["dir_discounts", "doc_changeprices", "price_", "discount"], "Управление скидками, переоценка"),
        ("Склад / Остатки",      ["exist", "doc_balance", "doc_return", "остаток"], "Текущие остатки, движение товара"),
        ("Настройки",            ["database", "connectionstring", "config", "fdb"], "Подключение к БД, конфигурация"),
        ("EDO / ЕГАИС",          ["sbis", "egais", "edo", "xml"], "Электронный документооборот, алкоголь"),
    ]

    for name, keywords, desc in modules:
        found = any(k in all_tables or any(k in h.lower() for hits in all_biz.values() for h in hits) for k in keywords)
        status = g("✓ найдено в коде") if found else dim("~ возможно нужен")
        print(f"\n  {c(name)}")
        print(f"    {dim('Описание:  ')}{desc}")
        print(f"    {dim('Статус:    ')}{status}")
        related = [tbl for tbl in all_tables if any(k in tbl for k in keywords)]
        if related:
            print(f"    {dim('Таблицы:   ')}{g(', '.join(related[:6]))}")

    # ── 2. Схема базы данных ─────────────────────────────────────────────
    print(f"\n\n  {a('2. СХЕМА БАЗЫ ДАННЫХ FIREBIRD (из анализа кода):')}")
    groups = {
        "Справочники (DIR_*)":  [(t, c_) for t, c_ in all_tables.items() if t.startswith("dir_")],
        "Документы (DOC_*)":    [(t, c_) for t, c_ in all_tables.items() if t.startswith("doc_")],
        "Прочие таблицы":       [(t, c_) for t, c_ in all_tables.items() if not t.startswith("dir_") and not t.startswith("doc_")],
    }
    for group_name, items in groups.items():
        if not items:
            continue
        print(f"\n  {c(group_name)}:")
        for tbl, cnt in sorted(items, key=lambda x: -x[1]):
            bar = g("#" * min(cnt, 15))
            print(f"    {g(tbl):<40} {bar}  {dim(str(cnt) + ' упом.')}")

    # ── 3. API-эндпоинты ─────────────────────────────────────────────────
    print(f"\n\n  {a('3. ПРЕДЛАГАЕМЫЕ API-ЭНДПОИНТЫ для веб-приложения:')}")
    endpoints = [
        ("GET",    "/api/goods",                  "Список товаров с ценами и остатками"),
        ("GET",    "/api/goods/:id",               "Карточка товара"),
        ("GET",    "/api/goods/search?q=",         "Поиск по названию / штрихкоду"),
        ("GET",    "/api/sales",                   "История продаж за период"),
        ("GET",    "/api/sales/:id",               "Детализация чека"),
        ("GET",    "/api/inventory/sessions",      "Список сессий инвентаризации"),
        ("GET",    "/api/inventory/:id/compare",   "Сравнение сессии с остатками"),
        ("GET",    "/api/purchases/sessions",      "Сессии закупок"),
        ("GET",    "/api/contragents",             "Покупатели и контрагенты"),
        ("GET",    "/api/contragents/:id/debt",    "Долги покупателя"),
        ("GET",    "/api/reports/turnover",        "Отчёт: оборот магазина"),
        ("GET",    "/api/reports/avg-check",       "Отчёт: средний чек"),
        ("GET",    "/api/reports/stock",           "Отчёт: остатки товаров"),
        ("GET",    "/api/discounts",               "Список скидок"),
        ("GET",    "/api/config",                  "Конфигурация подключения"),
    ]
    print(f"  {'Метод':<6} {'Маршрут':<40} Описание")
    print(f"  {'-'*6} {'-'*40} {'-'*25}")
    for method, route, desc in endpoints:
        col = g if method == "GET" else a
        print(f"  {col(method):<15} {c(route):<49} {dim(desc)}")

    # ── 4. Стек технологий ───────────────────────────────────────────────
    print(f"\n\n  {a('4. РЕКОМЕНДУЕМЫЙ СТЕК ВЕБ-ПРИЛОЖЕНИЯ:')}")
    stack = [
        ("База данных",   "Firebird (существующая)  →  читаем напрямую через API"),
        ("Backend API",   "Python (FastAPI)  —  подключение к Firebird через fdb / firebirdsql"),
        ("Frontend",      "React + TypeScript  —  уже знакомый формат (.ts файлы в проекте)"),
        ("Авторизация",   "JWT-токены  —  пользователь/пароль из ClientShop_Program_Config.json"),
        ("Отчёты",        "Переносим существующие .ts запросы в API-эндпоинты"),
        ("Развёртывание", "poehali.dev  —  хостинг фронтенда + облачные функции для API"),
    ]
    for layer, desc in stack:
        print(f"\n  {c(layer + ':')}")
        print(f"    {g(desc)}")

    # ── 5. Следующие шаги ────────────────────────────────────────────────
    print(f"\n\n  {a('5. СЛЕДУЮЩИЕ ШАГИ:')}")
    steps = [
        "Открыть файл ClientShop_Program_Config.json — там строка подключения к Firebird",
        "Подключиться к базе TASK2.FDB и выгрузить полную схему таблиц (CREATE TABLE)",
        "Определить приоритетные модули веб-приложения (начать с Товаров и Продаж)",
        "Создать Python backend с подключением к Firebird",
        "Построить React-интерфейс — аналог существующих TypeScript-отчётов",
    ]
    for i, step in enumerate(steps, 1):
        print(f"  {g(str(i) + '.')} {step}")

    print(f"\n{'=' * 70}\n")


def print_summary(all_folders_data):
    """Сводка по всем папкам — таблицы БД, бизнес-процессы, статистика."""
    print(f"\n{'=' * 70}")
    print(f"  {bold(g('СВОДКА ПО ВСЕМ ПАПКАМ'))}")
    print(f"{'=' * 70}")

    total_files = sum(d["file_count"] for d in all_folders_data)
    total_lines = sum(d["total_lines"] for d in all_folders_data)

    # --- Общая статистика ---
    print(f"\n  {a('Общая статистика:')}")
    print(f"  {'Папка':<30} {'Файлов':>7}  {'Строк':>8}  Языки")
    print(f"  {'-'*30} {'-'*7}  {'-'*8}  {'-'*25}")
    for d in all_folders_data:
        langs = ", ".join(d["langs"][:4])
        fc = str(d["file_count"]) if d["file_count"] else dim("нет кода")
        print(f"  {c(d['name']):<39} {fc:>7}  {dim(str(d['total_lines'])):>8}  {dim(langs)}")
    print(f"  {dim('-'*70)}")
    print(f"  {'ИТОГО':<30} {g(str(total_files)):>7}  {g(str(total_lines)):>8}")

    # --- Все таблицы БД ---
    all_tables = defaultdict(int)
    for d in all_folders_data:
        for tbl, cnt in d["sql_tables"].items():
            all_tables[tbl] += cnt

    if all_tables:
        print(f"\n  {a('Таблицы базы данных — все папки')} ({len(all_tables)}):")
        print(f"  {'Таблица':<35} {'Упоминаний':>10}  График")
        print(f"  {'-'*35} {'-'*10}  {'-'*20}")
        for tbl, cnt in sorted(all_tables.items(), key=lambda x: -x[1])[:35]:
            bar = g("#" * min(cnt, 20))
            print(f"  {c(tbl):<35} {str(cnt):>10}  {bar}")

    # --- Все бизнес-процессы ---
    all_biz = defaultdict(list)
    for d in all_folders_data:
        for category, hits in d["biz_keywords"].items():
            for h in hits:
                entry = f"[{d['name']}]  {h}"
                if entry not in all_biz[category]:
                    all_biz[category].append(entry)

    if all_biz:
        print(f"\n  {a('Бизнес-логика — сводка по всем папкам:')}")
        for category, hits in all_biz.items():
            print(f"\n  {c('>')} {bold(category)}")
            for h in hits[:4]:
                print(f"    {dim('-')}  {g(h)}")

    print(f"\n{'=' * 70}\n")


def collect_folder_data(root):
    """Собирает данные папки для сводки без вывода."""
    all_files = collect_all_files(root)
    if not all_files:
        return {"name": root.name, "file_count": 0, "total_lines": 0,
                "langs": [], "sql_tables": {}, "biz_keywords": {}}

    # Языки
    by_ext = defaultdict(int)
    total_lines = 0
    for f in all_files:
        by_ext[f.suffix.lower()] += 1
        total_lines += count_lines(f)["total"]
    langs = [KNOWN_LANGS.get(e, e) for e, _ in sorted(by_ext.items(), key=lambda x: -x[1])]

    # Таблицы SQL
    pat_sql = re.compile(r"""(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-zA-Z_]\w*)""", re.IGNORECASE)
    STOPWORDS = {"as","the","this","from","that","with","for","and","not","new","null",
                 "true","false","native","void","int","char","return","class","public",
                 "select","where","inner","outer","left","right","join","on","by","or",
                 "in","is","of","to","be","at","an","do","if","set","all","end","var"}
    sql_tables = defaultdict(int)
    for fpath in all_files:
        if fpath.suffix.lower() in (".ts", ".js", ".sql", ".json", ".xml", ".ps1"):
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                for m in pat_sql.finditer(text):
                    tbl = m.group(1).lower()
                    if len(tbl) > 3 and tbl not in STOPWORDS and not tbl.isdigit():
                        sql_tables[tbl] += 1
            except Exception:
                pass

    # Бизнес-ключевые слова
    CODE_EXTS = {".ts", ".js", ".py", ".php", ".cs", ".json", ".xml", ".ps1"}
    BUSINESS = {
        "Авторизация":    ["login", "auth", "password", "token", "session"],
        "Заказы/Продажи": ["simplesale", "sale", "order", "doc_sale"],
        "Оплата/Долги":   ["payment", "pay", "buyerdebt", "doc_pays", "invoice"],
        "Товары/Каталог": ["goods", "dir_goods", "product", "catalog", "price_"],
        "Отчёты":         ["setname", "addcolumn", "createreport", "report"],
        "Инвентаризация": ["invsession", "inventory", "doc_invsession"],
    }
    SKIP = ["license", "copyright", "<span", "<font", "<meta", "fbudf_api",
            "contents of this file", "you may not use"]
    biz_keywords = defaultdict(list)
    for fpath in all_files:
        if fpath.suffix.lower() not in CODE_EXTS:
            continue
        try:
            lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, line in enumerate(lines, 1):
                ll = line.lower().strip()
                if not ll or len(ll) < 5 or any(s in ll for s in SKIP):
                    continue
                for cat, kws in BUSINESS.items():
                    for kw in kws:
                        if kw in ll:
                            entry = f"{fpath.name}:{i}  {line.strip()[:60]}"
                            if entry not in biz_keywords[cat]:
                                biz_keywords[cat].append(entry)
                            break
        except Exception:
            pass

    return {
        "name": root.name,
        "file_count": len(all_files),
        "total_lines": total_lines,
        "langs": langs,
        "sql_tables": dict(sql_tables),
        "biz_keywords": dict(biz_keywords),
    }


def main():
    # Если путь передан аргументом — старый режим (для опытных)
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="PyScope - анализатор Python-проектов")
        parser.add_argument("path", help="Путь к папке проекта")
        parser.add_argument("--section", "-s", choices=SECTIONS + ["all"], default="all")
        parser.add_argument("--out", "-o", help="Сохранить отчёт в файл .txt")
        args = parser.parse_args()
        root = Path(args.path).resolve()
        if not root.exists() or not root.is_dir():
            print(r("Ошибка: папка не найдена - " + str(root)))
            sys.exit(1)
        active = SECTIONS if args.section == "all" else [args.section]
        analyze_folder(root, active, args.out)
        input("  Нажмите Enter для выхода...")
        return

    # Интерактивная форма
    folders, active_sections, out_file = interactive_form()

    # Анализ каждой папки
    all_folders_data = []
    for folder in folders:
        analyze_folder(folder, active_sections, out_file)
        all_folders_data.append(collect_folder_data(folder))

    # Сводка по всем папкам
    if len(folders) > 1:
        print_summary(all_folders_data)
        if out_file:
            base = out_file if out_file.endswith(".txt") else out_file + ".txt"
            summary_path = base.replace(".txt", "_SUMMARY.txt")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                print_summary(all_folders_data)
            ansi_escape = re.compile(r"\033\[[0-9;]*m")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(ansi_escape.sub("", buf.getvalue()))
            print(f"  {g('OK')} Сводка сохранена: {c(summary_path)}")

    # Архитектурный анализ
    print_architecture(all_folders_data)
    if out_file:
        base = out_file if out_file.endswith(".txt") else out_file + ".txt"
        arch_path = base.replace(".txt", "_ARCHITECTURE.txt")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_architecture(all_folders_data)
        ansi_escape = re.compile(r"\033\[[0-9;]*m")
        with open(arch_path, "w", encoding="utf-8") as f:
            f.write(ansi_escape.sub("", buf.getvalue()))
        print(f"  {g('OK')} Архитектура сохранена: {c(arch_path)}")

    print(f"\n  {g('Анализ завершён.')} Обработано папок: {g(str(len(folders)))}")
    input("  Нажмите Enter для выхода...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n" + "-" * 70)
        print("  ОШИБКА: " + str(e))
        print("-" * 70)
        traceback.print_exc()
        input("\n  Нажмите Enter для выхода...")