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

def collect_files(root):
    files = []
    for path in sorted(root.rglob("*.py")):
        name = path.name
        parts = path.parts
        if name.startswith("test_") or name.endswith("_test.py"):
            continue
        skip_dirs = {"tests", "test", "__pycache__", ".venv", "venv", "env", ".git", "node_modules"}
        if any(part in skip_dirs for part in parts):
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


# --- Main --------------------------------------------------------------------

SECTIONS = ["overview", "stats", "classes", "functions", "deps", "tree", "flows"]


def main():
    parser = argparse.ArgumentParser(description="PyScope - анализатор Python-проектов")
    parser.add_argument("path", help="Путь к папке проекта")
    parser.add_argument("--section", "-s", choices=SECTIONS + ["all"], default="all")
    parser.add_argument("--out", "-o", help="Сохранить отчёт в файл .txt")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        print(r("Ошибка: папка не найдена - " + str(root)))
        sys.exit(1)

    print(f"\n{SEP}")
    print(f"  {bold(g('PYSCOPE'))}  {dim('Python Code Analyzer v1.0.0')}")
    print(f"  {dim('Проект:')} {c(root.name)}  {dim('Путь:')} {dim(str(root))}")
    print(SEP)

    files = collect_files(root)
    if not files:
        print(r("  Файлы .py не найдены (или все отфильтрованы как тестовые)."))
        sys.exit(0)

    root_modules = {f.stem for f in root.iterdir() if f.is_dir() or f.suffix == ".py"}
    print(f"  {dim('Найдено .py файлов:')} {g(str(len(files)))}  {dim('(тест-файлы исключены)')}")

    stats_per_file = {}
    complexity_per_file = {}
    all_classes = []
    all_funcs = []
    all_imports = []

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
    flows = detect_flows(all_funcs)
    active = SECTIONS if args.section == "all" else [args.section]

    captured = {}
    for sec in active:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if sec == "overview":    print_overview(stats_per_file, files, all_classes)
            elif sec == "stats":     print_stats(stats_per_file, complexity_per_file)
            elif sec == "classes":   print_classes(all_classes)
            elif sec == "functions": print_functions(all_funcs)
            elif sec == "deps":      print_deps(all_imports, root_modules)
            elif sec == "tree":      print_tree(tree_nodes, root)
            elif sec == "flows":     print_flows(flows)
        output = buf.getvalue()
        captured[sec] = output
        print(output, end="")

    print(f"\n{SEP}\n")

    if args.out:
        export_report(args.out, captured)
        print()

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
