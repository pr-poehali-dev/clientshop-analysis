#!/usr/bin/env python3
"""
PyScope DB Schema Extractor
Подключается к базе Firebird и выгружает полную схему таблиц.
Использование: python db_schema.py
               python db_schema.py --out C:\\1\\schema.txt
"""

import sys
import argparse
import traceback
from pathlib import Path
from collections import defaultdict


# --- Цвета -------------------------------------------------------------------

class C:
    GREEN  = "\033[92m"
    AMBER  = "\033[93m"
    CYAN   = "\033[96m"
    RED    = "\033[91m"
    PURPLE = "\033[95m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def g(t):    return f"{C.GREEN}{t}{C.RESET}"
def a(t):    return f"{C.AMBER}{t}{C.RESET}"
def c(t):    return f"{C.CYAN}{t}{C.RESET}"
def r(t):    return f"{C.RED}{t}{C.RESET}"
def p(t):    return f"{C.PURPLE}{t}{C.RESET}"
def dim(t):  return f"{C.DIM}{t}{C.RESET}"
def bold(t): return f"{C.BOLD}{t}{C.RESET}"

SEP = dim("=" * 70)
SEP2 = dim("-" * 70)


# --- Настройки подключения ---------------------------------------------------

DB_PATH  = r"C:\ClientShopDatabase\TASK2.FDB"
DB_USER  = "SYSDBA"
DB_PASS  = "masterkey"
DB_CHARSET = "WIN1251"


# --- Подключение -------------------------------------------------------------

def get_connection(db_path, user, password, charset):
    """Подключается к Firebird. Пробует fdb, затем firebirdsql."""
    try:
        import fdb
        con = fdb.connect(
            dsn=db_path,
            user=user,
            password=password,
            charset=charset,
        )
        print(f"  {g('OK')} Подключение через fdb")
        return con, "fdb"
    except ImportError:
        pass
    except Exception as e:
        print(f"  {r('fdb ошибка:')} {e}")

    try:
        import firebirdsql
        con = firebirdsql.connect(
            host="localhost",
            database=db_path,
            user=user,
            password=password,
            charset=charset,
        )
        print(f"  {g('OK')} Подключение через firebirdsql")
        return con, "firebirdsql"
    except ImportError:
        pass
    except Exception as e:
        print(f"  {r('firebirdsql ошибка:')} {e}")

    return None, None


# --- Запросы к системным таблицам Firebird -----------------------------------

SQL_TABLES = """
    SELECT TRIM(r.RDB$RELATION_NAME)
    FROM RDB$RELATIONS r
    WHERE r.RDB$SYSTEM_FLAG = 0
      AND r.RDB$RELATION_TYPE = 0
    ORDER BY r.RDB$RELATION_NAME
"""

SQL_ALL_OBJECTS = """
    SELECT
        TRIM(r.RDB$RELATION_NAME)  AS obj_name,
        r.RDB$RELATION_TYPE        AS obj_type,
        r.RDB$SYSTEM_FLAG          AS is_system
    FROM RDB$RELATIONS r
    ORDER BY r.RDB$SYSTEM_FLAG, r.RDB$RELATION_TYPE, r.RDB$RELATION_NAME
"""

SQL_ALL_FILES = """
    SELECT TRIM(f.RDB$FILE_NAME), f.RDB$FILE_SEQUENCE
    FROM RDB$FILES f
    ORDER BY f.RDB$FILE_SEQUENCE
"""

SQL_COLUMNS = """
    SELECT
        TRIM(rf.RDB$FIELD_NAME)          AS col_name,
        f.RDB$FIELD_TYPE                 AS field_type,
        f.RDB$FIELD_LENGTH               AS field_length,
        f.RDB$FIELD_PRECISION            AS field_precision,
        f.RDB$FIELD_SCALE                AS field_scale,
        rf.RDB$NULL_FLAG                 AS not_null,
        TRIM(rf.RDB$DEFAULT_SOURCE)      AS default_val,
        TRIM(rf.RDB$DESCRIPTION)         AS descr,
        rf.RDB$FIELD_POSITION            AS fld_pos
    FROM RDB$RELATION_FIELDS rf
    JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE
    WHERE TRIM(rf.RDB$RELATION_NAME) = ?
    ORDER BY rf.RDB$FIELD_POSITION
"""

SQL_PRIMARY_KEYS = """
    SELECT TRIM(iseg.RDB$FIELD_NAME)
    FROM RDB$RELATION_CONSTRAINTS rc
    JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = rc.RDB$INDEX_NAME
    WHERE rc.RDB$CONSTRAINT_TYPE = 'PRIMARY KEY'
      AND TRIM(rc.RDB$RELATION_NAME) = ?
    ORDER BY iseg.RDB$FIELD_POSITION
"""

SQL_FOREIGN_KEYS = """
    SELECT
        TRIM(iseg.RDB$FIELD_NAME)            AS col_name,
        TRIM(rc2.RDB$RELATION_NAME)          AS ref_table,
        TRIM(iseg2.RDB$FIELD_NAME)           AS ref_col
    FROM RDB$RELATION_CONSTRAINTS rc
    JOIN RDB$REF_CONSTRAINTS refc ON refc.RDB$CONSTRAINT_NAME = rc.RDB$CONSTRAINT_NAME
    JOIN RDB$RELATION_CONSTRAINTS rc2 ON rc2.RDB$CONSTRAINT_NAME = refc.RDB$CONST_NAME_UQ
    JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = rc.RDB$INDEX_NAME
    JOIN RDB$INDEX_SEGMENTS iseg2 ON iseg2.RDB$INDEX_NAME = rc2.RDB$INDEX_NAME
      AND iseg2.RDB$FIELD_POSITION = iseg.RDB$FIELD_POSITION
    WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
      AND TRIM(rc.RDB$RELATION_NAME) = ?
"""

SQL_INDEXES = """
    SELECT
        TRIM(i.RDB$INDEX_NAME)       AS idx_name,
        i.RDB$UNIQUE_FLAG            AS is_unique,
        TRIM(iseg.RDB$FIELD_NAME)    AS col_name
    FROM RDB$INDICES i
    JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = i.RDB$INDEX_NAME
    WHERE TRIM(i.RDB$RELATION_NAME) = ?
      AND i.RDB$SYSTEM_FLAG = 0
    ORDER BY i.RDB$INDEX_NAME, iseg.RDB$FIELD_POSITION
"""

SQL_TRIGGERS = """
    SELECT
        TRIM(t.RDB$TRIGGER_NAME)     AS trg_name,
        t.RDB$TRIGGER_TYPE           AS trg_type,
        t.RDB$TRIGGER_INACTIVE       AS inactive
    FROM RDB$TRIGGERS t
    WHERE TRIM(t.RDB$RELATION_NAME) = ?
      AND t.RDB$SYSTEM_FLAG = 0
"""

SQL_VIEWS = """
    SELECT TRIM(r.RDB$RELATION_NAME), TRIM(r.RDB$VIEW_SOURCE)
    FROM RDB$RELATIONS r
    WHERE r.RDB$SYSTEM_FLAG = 0
      AND r.RDB$RELATION_TYPE = 1
    ORDER BY r.RDB$RELATION_NAME
"""

SQL_PROCEDURES = """
    SELECT
        TRIM(p.RDB$PROCEDURE_NAME)   AS proc_name,
        TRIM(p.RDB$PROCEDURE_SOURCE) AS proc_source
    FROM RDB$PROCEDURES p
    WHERE p.RDB$SYSTEM_FLAG = 0
    ORDER BY p.RDB$PROCEDURE_NAME
"""

SQL_ROW_COUNTS = """
    SELECT COUNT(*) FROM {}
"""

# --- Маппинг типов Firebird --------------------------------------------------

FB_TYPES = {
    7:  "SMALLINT",
    8:  "INTEGER",
    9:  "QUAD",
    10: "FLOAT",
    11: "D_FLOAT",
    12: "DATE",
    13: "TIME",
    14: "CHAR",
    16: "BIGINT",
    27: "DOUBLE PRECISION",
    35: "TIMESTAMP",
    37: "VARCHAR",
    40: "CSTRING",
    45: "BLOB_ID",
    261:"BLOB",
}

def fb_type_str(type_code, length, precision, scale):
    name = FB_TYPES.get(type_code, f"TYPE_{type_code}")
    if type_code in (14, 37):
        return f"{name}({length})"
    if type_code == 16 and scale and scale < 0:
        return f"NUMERIC({precision},{abs(scale)})"
    if type_code == 8 and scale and scale < 0:
        return f"NUMERIC({precision},{abs(scale)})"
    return name


# --- Вывод схемы -------------------------------------------------------------

def print_table_schema(cur, table_name, pks, fks_map, show_counts=True, con=None):
    """Выводит схему одной таблицы."""
    print(f"\n  {a('TABLE')} {g(table_name)}")

    # Количество строк
    if show_counts and con:
        try:
            cur2 = con.cursor()
            cur2.execute(f"SELECT COUNT(*) FROM {table_name}")
            cnt = cur2.fetchone()[0]
            print(f"  {dim('Строк в таблице: ')}{c(str(cnt))}")
        except Exception:
            pass

    # Колонки
    cur.execute(SQL_COLUMNS, (table_name,))
    rows = cur.fetchall()
    if not rows:
        print(f"  {dim('(нет колонок)')}")
        return

    print(f"\n  {'Поле':<28} {'Тип':<22} {'NULL':>5}  {'По умолчанию':<18}  Описание")
    print(f"  {'-'*28} {'-'*22} {'-'*5}  {'-'*18}  {'-'*20}")

    for row in rows:
        col_name, ftype, flen, fprec, fscale, not_null, default, desc, pos = row
        type_str  = fb_type_str(ftype, flen or 0, fprec or 0, fscale or 0)
        null_str  = dim("NOT NULL") if not_null else g("NULL   ")
        def_str   = (default or "").replace("DEFAULT ", "")[:18]
        desc_str  = (desc or "")[:20]
        is_pk     = col_name in pks
        is_fk     = col_name in fks_map
        pk_mark   = f" {a('PK')}" if is_pk else "   "
        fk_mark   = f" {p('FK→' + fks_map[col_name][0])}" if is_fk else ""
        col_disp  = g(col_name) if is_pk else (p(col_name) if is_fk else col_name)
        print(f"  {col_disp:<37}{pk_mark} {type_str:<22} {null_str}  {dim(def_str):<18}  {dim(desc_str)}{fk_mark}")

    # Индексы
    cur.execute(SQL_INDEXES, (table_name,))
    idx_rows = cur.fetchall()
    if idx_rows:
        idx_map = defaultdict(list)
        idx_unique = {}
        for iname, unique, col in idx_rows:
            idx_map[iname].append(col)
            idx_unique[iname] = unique
        print(f"\n  {dim('Индексы:')}")
        for iname, cols in idx_map.items():
            umark = a("UNIQUE ") if idx_unique.get(iname) else dim("       ")
            print(f"    {umark} {c(iname):<35} {', '.join(cols)}")

    # Триггеры
    cur.execute(SQL_TRIGGERS, (table_name,))
    trg_rows = cur.fetchall()
    if trg_rows:
        active = [t[0] for t in trg_rows if not t[2]]
        if active:
            print(f"\n  {dim('Триггеры: ')}{p(', '.join(active))}")


def run_schema(con, out_file=None):
    """Основная логика выгрузки схемы."""
    import io, re

    cur = con.cursor()

    # --- Диагностика: все объекты без фильтров ---
    print(f"\n{'=' * 70}")
    print(f"  {a('ДИАГНОСТИКА — ВСЕ ОБЪЕКТЫ БАЗЫ (включая системные)')}")
    print(f"{'=' * 70}")

    TYPE_NAMES = {0: "ТАБЛИЦА", 1: "VIEW", 2: "EXTERNAL", 3: "VIRTUAL", 4: "GLOBAL_TMP", 5: "LOCAL_TMP"}
    try:
        cur.execute(SQL_ALL_OBJECTS)
        all_objs = cur.fetchall()
        user_tables   = [(n, t) for n, t, s in all_objs if s == 0 and t == 0]
        user_views    = [(n, t) for n, t, s in all_objs if s == 0 and t == 1]
        system_tables = [(n, t) for n, t, s in all_objs if s != 0]
        print(f"  {g('Пользовательских таблиц:')} {len(user_tables)}")
        print(f"  {c('Представлений (Views):  ')} {len(user_views)}")
        print(f"  {dim('Системных объектов:     ')} {len(system_tables)}")
        print(f"\n  {a('Все пользовательские таблицы:')}")
        for name, ttype in sorted(user_tables):
            print(f"    {g(name)}")
        if user_views:
            print(f"\n  {a('Все представления (Views):')}")
            for name, _ in sorted(user_views):
                print(f"    {c(name)}")
    except Exception as e:
        print(f"  {r('Ошибка диагностики:')} {e}")

    # --- Подключённые файлы базы ---
    try:
        cur.execute(SQL_ALL_FILES)
        files = cur.fetchall()
        if files:
            print(f"\n  {a('Подключённые файлы базы:')}")
            for fname, fseq in files:
                print(f"    [{fseq}] {c(fname)}")
    except Exception:
        pass

    # Список таблиц
    cur.execute(SQL_TABLES)
    tables = [row[0] for row in cur.fetchall()]

    print(f"\n{SEP}")
    print(f"  {bold(g('СХЕМА БАЗЫ ДАННЫХ'))}  {dim('Firebird / ClientShop')}")
    print(f"  {dim('Таблиц найдено:')} {g(str(len(tables)))}")
    print(SEP)

    # Сводная таблица
    print(f"\n{'=' * 70}")
    print(f"  {a('ВСЕ ТАБЛИЦЫ — СВОДКА')}")
    print(f"{'=' * 70}")
    print(f"  {'Таблица':<40} {'Тип':>8}")
    print(f"  {'-'*40} {'-'*8}")
    for tbl in tables:
        kind = "DIR" if tbl.upper().startswith("DIR_") else "DOC" if tbl.upper().startswith("DOC_") else "OTHER"
        col = c if kind == "DIR" else g if kind == "DOC" else dim
        print(f"  {col(tbl):<49} {dim(kind)}")

    # Схема каждой таблицы
    captured = {}
    for tbl in tables:
        buf = io.StringIO()

        # PK
        try:
            cur.execute(SQL_PRIMARY_KEYS, (tbl,))
            pks = {row[0] for row in cur.fetchall()}
        except Exception:
            pks = set()

        # FK
        try:
            cur.execute(SQL_FOREIGN_KEYS, (tbl,))
            fks_map = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
        except Exception:
            fks_map = {}

        import contextlib
        with contextlib.redirect_stdout(buf):
            print_table_schema(cur, tbl, pks, fks_map, show_counts=True, con=con)

        output = buf.getvalue()
        captured[tbl] = output
        print(output, end="")

    # Представления (Views)
    cur.execute(SQL_VIEWS)
    views = cur.fetchall()
    if views:
        print(f"\n{'=' * 70}")
        print(f"  {a('ПРЕДСТАВЛЕНИЯ (VIEWS)')}  {dim(str(len(views)) + ' шт.')}")
        print(f"{'=' * 70}")
        for vname, vsource in views:
            print(f"\n  {c('VIEW')} {g(vname)}")
            if vsource:
                for line in (vsource or "")[:500].splitlines()[:10]:
                    print(f"    {dim(line)}")

    # Хранимые процедуры
    cur.execute(SQL_PROCEDURES)
    procs = cur.fetchall()
    if procs:
        print(f"\n{'=' * 70}")
        print(f"  {a('ХРАНИМЫЕ ПРОЦЕДУРЫ')}  {dim(str(len(procs)) + ' шт.')}")
        print(f"{'=' * 70}")
        for pname, psource in procs:
            print(f"\n  {p('PROC')} {g(pname)}")
            if psource:
                for line in (psource or "")[:300].splitlines()[:8]:
                    print(f"    {dim(line)}")

    # Сохранение
    if out_file:
        base = out_file if out_file.endswith(".txt") else out_file + ".txt"
        ansi = re.compile(r"\033\[[0-9;]*m")
        lines = ["=" * 70, "  CLIENTSHOP — СХЕМА БАЗЫ ДАННЫХ FIREBIRD", "=" * 70, ""]
        lines.append(f"  Таблиц: {len(tables)}")
        lines.append(f"  Файл БД: {DB_PATH}")
        lines.append("")
        lines.append("  ВСЕ ТАБЛИЦЫ:")
        for tbl in tables:
            lines.append(f"    {tbl}")
        lines.append("")
        for tbl, content in captured.items():
            lines.append("=" * 70)
            lines.append(f"  {tbl}")
            lines.append("=" * 70)
            lines.extend(ansi.sub("", content).splitlines())
            lines.append("")
        with open(base, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n  {g('OK')} Схема сохранена: {c(base)}")


# --- Форма ввода -------------------------------------------------------------

def ask(label, default=None, can_skip=False):
    print(f"\n  {a(label)}")
    if default:
        print(f"  {dim('Сохранено: ')}{c(default)}  {dim('(Enter чтобы использовать)')}")
    if can_skip:
        print(f"  {dim('Введите 0 чтобы пропустить')}")
    raw = input(f"  {g('> ')}").strip().strip('"').strip("'")
    if raw == "" and default is not None:
        return default
    if raw == "0" and can_skip:
        return None
    return raw if raw else default


def interactive_form():
    print(f"\n{'=' * 70}")
    print(f"  {bold(g('PYSCOPE DB SCHEMA'))}  {dim('Firebird Schema Extractor v1.0')}")
    print(f"{'=' * 70}")
    print(f"  {dim('Подключается к базе ClientShop и выгружает полную схему таблиц.')}")
    print(f"{'=' * 70}")

    db_path = ask("Путь к файлу базы данных (.FDB):", default=DB_PATH)
    user    = ask("Пользователь:", default=DB_USER)
    passwd  = ask("Пароль:", default=DB_PASS)
    charset = ask("Кодировка (WIN1251 для русского):", default=DB_CHARSET)
    out     = ask("Сохранить схему в файл .txt:", default=r"C:\1\schema", can_skip=True)

    return db_path, user, passwd, charset, out


# --- Main --------------------------------------------------------------------

def check_driver():
    """Проверяет наличие драйвера и даёт инструкцию по установке."""
    try:
        import fdb
        return True
    except ImportError:
        pass
    try:
        import firebirdsql
        return True
    except ImportError:
        pass

    print(f"\n  {r('Драйвер Firebird не установлен.')}")
    print(f"\n  Установите один из двух вариантов:")
    print(f"\n  {a('Вариант 1')} — fdb (рекомендуется):")
    print(f"    {c('pip install fdb')}")
    print(f"\n  {a('Вариант 2')} — firebirdsql:")
    print(f"    {c('pip install firebirdsql')}")
    print(f"\n  {dim('После установки запустите скрипт снова.')}")
    return False


def main():
    if not check_driver():
        input(f"\n  {dim('Нажмите Enter для выхода...')}")
        return

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Firebird Schema Extractor")
        parser.add_argument("--db",      default=DB_PATH,    help="Путь к .FDB файлу")
        parser.add_argument("--user",    default=DB_USER,    help="Пользователь")
        parser.add_argument("--pass",    default=DB_PASS,    dest="password")
        parser.add_argument("--charset", default=DB_CHARSET)
        parser.add_argument("--out",     default=None,       help="Файл для сохранения")
        args = parser.parse_args()
        db_path, user, passwd, charset, out = args.db, args.user, args.password, args.charset, args.out
    else:
        db_path, user, passwd, charset, out = interactive_form()

    print(f"\n{SEP}")
    print(f"  {dim('Подключаюсь к:')} {c(db_path)}")
    print(f"  {dim('Пользователь:  ')} {c(user)}")
    print(SEP)

    if not Path(db_path).exists():
        print(r(f"\n  Файл базы не найден: {db_path}"))
        print(dim("  Проверьте путь и попробуйте снова."))
        input(f"\n  {dim('Нажмите Enter для выхода...')}")
        return

    con, driver = get_connection(db_path, user, passwd, charset)
    if con is None:
        print(r("\n  Не удалось подключиться к базе данных."))
        print(dim("  Убедитесь что Firebird Server запущен и путь к файлу верный."))
        input(f"\n  {dim('Нажмите Enter для выхода...')}")
        return

    try:
        run_schema(con, out)
    finally:
        con.close()

    print(f"\n{SEP}")
    print(f"  {g('Готово!')} Схема базы данных выгружена.")
    print(SEP)
    input(f"\n  {dim('Нажмите Enter для выхода...')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n" + "-" * 70)
        print(f"  ОШИБКА: {e}")
        print("-" * 70)
        traceback.print_exc()
        input("\n  Нажмите Enter для выхода...")