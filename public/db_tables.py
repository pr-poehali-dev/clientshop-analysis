#!/usr/bin/env python3
"""
PyScope — Полный список таблиц Firebird
Пробует все доступные способы подключения.
"""

import sys
import traceback

DB_PATH = r"C:\ClientShopDatabase\TASK2.FDB"
DB_USER = "SYSDBA"
DB_PASS = "masterkey"

def sep(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print("="*60)

SQL_TABLES_ALL = """
    SELECT TRIM(r.RDB$RELATION_NAME), r.RDB$RELATION_TYPE, r.RDB$SYSTEM_FLAG
    FROM RDB$RELATIONS r
    ORDER BY r.RDB$SYSTEM_FLAG, r.RDB$RELATION_TYPE, r.RDB$RELATION_NAME
"""

SQL_COUNT = "SELECT COUNT(*) FROM {}"


def print_tables(cur):
    cur.execute(SQL_TABLES_ALL)
    rows = cur.fetchall()

    user_tables = [(n.strip(), t, s) for n, t, s in rows if s == 0 and t == 0]
    user_views  = [(n.strip(), t, s) for n, t, s in rows if s == 0 and t == 1]
    sys_tables  = [(n.strip(), t, s) for n, t, s in rows if s != 0]

    print(f"\n  Пользовательских таблиц : {len(user_tables)}")
    print(f"  Представлений (Views)   : {len(user_views)}")
    print(f"  Системных объектов      : {len(sys_tables)}")

    print(f"\n  {'№':>3}  {'Таблица':<45} {'Строк':>8}")
    print(f"  {'-'*3}  {'-'*45} {'-'*8}")

    for i, (name, _, _) in enumerate(user_tables, 1):
        try:
            cur.execute(SQL_COUNT.format(name))
            cnt = cur.fetchone()[0]
        except Exception:
            cnt = "?"
        marker = "  " if cnt == 0 or cnt == "?" else ">>"
        print(f"  {str(i):>3}  {marker} {name:<43} {str(cnt):>8}")

    if user_views:
        print(f"\n  Представления:")
        for name, _, _ in user_views:
            print(f"       {name}")

    return user_tables


def try_firebirdsql():
    sep("СПОСОБ 1: firebirdsql")
    try:
        import firebirdsql
        print("  Подключаюсь...")
        con = firebirdsql.connect(
            host="localhost",
            database=DB_PATH,
            user=DB_USER,
            password=DB_PASS,
            charset="WIN1251",
        )
        print("  OK подключено через firebirdsql")
        cur = con.cursor()
        tables = print_tables(cur)
        con.close()
        return len(tables)
    except ImportError:
        print("  firebirdsql не установлен")
        return 0
    except Exception as e:
        print(f"  Ошибка: {e}")
        return 0


def try_fdb():
    sep("СПОСОБ 2: fdb")
    try:
        import fdb
        print("  Подключаюсь...")
        con = fdb.connect(dsn=DB_PATH, user=DB_USER, password=DB_PASS, charset="WIN1251")
        print("  OK подключено через fdb")
        cur = con.cursor()
        tables = print_tables(cur)
        con.close()
        return len(tables)
    except ImportError:
        print("  fdb не установлен")
        return 0
    except Exception as e:
        print(f"  Ошибка: {e}")
        return 0


def try_odbc():
    sep("СПОСОБ 3: ODBC (Firebird ODBC Driver)")
    try:
        import pyodbc
        # Пробуем разные строки подключения
        conn_strings = [
            f"DRIVER={{Firebird/InterBase(r) driver}};DBNAME={DB_PATH};UID={DB_USER};PWD={DB_PASS};CHARSET=WIN1251;",
            f"DRIVER={{Firebird}};DATABASE={DB_PATH};UID={DB_USER};PWD={DB_PASS};CHARSET=WIN1251;",
            f"DRIVER={{InterBase}};DATABASE={DB_PATH};UID={DB_USER};PWD={DB_PASS};",
        ]
        for cs in conn_strings:
            try:
                print(f"  Пробую: {cs[:60]}...")
                con = pyodbc.connect(cs)
                print("  OK подключено через ODBC")
                cur = con.cursor()
                tables = print_tables(cur)
                con.close()
                return len(tables)
            except Exception as e:
                print(f"  Не удалось: {e}")
        return 0
    except ImportError:
        print("  pyodbc не установлен. Установить: pip install pyodbc")
        return 0


def try_isql():
    sep("СПОСОБ 4: isql (встроенный инструмент Firebird)")
    import os, subprocess, tempfile

    isql_paths = [
        r"C:\Program Files\Firebird\Firebird_2_5\bin\isql.exe",
        r"C:\Program Files (x86)\Firebird\Firebird_2_5\bin\isql.exe",
        r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
        r"C:\Firebird\bin\isql.exe",
        r"C:\Program Files\Firebird\bin\isql.exe",
    ]

    isql = None
    for path in isql_paths:
        if os.path.exists(path):
            isql = path
            break

    if not isql:
        # Пробуем найти в PATH
        try:
            result = subprocess.run(["where", "isql"], capture_output=True, text=True)
            if result.returncode == 0:
                isql = result.stdout.strip().splitlines()[0]
        except Exception:
            pass

    if not isql:
        print("  isql.exe не найден.")
        print("  Поиск Firebird на компьютере...")
        # Ищем сам Firebird
        for root_dir in [r"C:\Program Files", r"C:\Program Files (x86)", r"C:\\"]:
            try:
                for entry in os.scandir(root_dir):
                    if "firebird" in entry.name.lower() and entry.is_dir():
                        print(f"  Найдена папка Firebird: {entry.path}")
            except Exception:
                pass
        return 0

    print(f"  Найден isql: {isql}")

    # Создаём SQL-скрипт
    sql_script = """
SELECT TRIM(r.RDB$RELATION_NAME) || ' | TYPE=' || r.RDB$RELATION_TYPE || ' | SYS=' || r.RDB$SYSTEM_FLAG
FROM RDB$RELATIONS r
WHERE r.RDB$SYSTEM_FLAG = 0 AND r.RDB$RELATION_TYPE = 0
ORDER BY r.RDB$RELATION_NAME;
QUIT;
"""
    tmp_sql = tempfile.mktemp(suffix=".sql")
    tmp_out = tempfile.mktemp(suffix=".txt")

    with open(tmp_sql, "w") as f:
        f.write(sql_script)

    try:
        cmd = [isql, "-user", DB_USER, "-password", DB_PASS, DB_PATH, "-i", tmp_sql, "-o", tmp_out]
        subprocess.run(cmd, timeout=15)

        with open(tmp_out, "r", errors="ignore") as f:
            content = f.read()

        tables = [line.split("|")[0].strip() for line in content.splitlines() if "|" in line and "TYPE" in line]
        print(f"  Таблиц найдено через isql: {len(tables)}")
        for i, t in enumerate(tables, 1):
            print(f"  {str(i):>3}.  {t}")
        return len(tables)
    except Exception as e:
        print(f"  Ошибка isql: {e}")
        return 0
    finally:
        try:
            os.remove(tmp_sql)
            os.remove(tmp_out)
        except Exception:
            pass


def main():
    sep("PYSCOPE — Полный список таблиц Firebird")
    print(f"  База: {DB_PATH}")
    print(f"  Пользователь: {DB_USER}")

    results = {}
    results["firebirdsql"] = try_firebirdsql()
    results["fdb"]         = try_fdb()
    results["odbc"]        = try_odbc()
    results["isql"]        = try_isql()

    sep("ИТОГ")
    for method, count in results.items():
        status = f"{count} таблиц" if count > 0 else "не удалось"
        print(f"  {method:<20} {status}")

    best = max(results.values())
    if best <= 40:
        print(f"\n  Все методы показывают <= 40 таблиц.")
        print(f"  Вероятно TASK2.FDB действительно содержит только {best} таблиц.")
        print(f"  Основная база может называться иначе.")
        print(f"\n  Проверь содержимое архива Data-Connect.zip в папке:")
        print(f"  C:\\ClientShopDatabase\\")
        print(f"  Там могут быть инструкции по подключению к основной базе.")

    input("\n  Нажмите Enter для выхода...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
