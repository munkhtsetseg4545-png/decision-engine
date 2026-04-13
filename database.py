import sqlite3
import os
import json
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "scoring_history.db")
MN_TZ = timezone(timedelta(hours=8))


def mn_now():
    return datetime.now(MN_TZ).strftime("%Y-%m-%d %H:%M")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scoring_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            created_at TEXT NOT NULL,
            elapsed_sec INTEGER DEFAULT 0,
            total_score REAL NOT NULL,
            decision TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            red_flags TEXT NOT NULL,
            hard_fails TEXT NOT NULL,
            answers TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deep_work_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            created_at TEXT NOT NULL,
            elapsed_sec INTEGER DEFAULT 0,
            answers TEXT NOT NULL,
            thesis TEXT NOT NULL
        )
    """)
    # Add elapsed_sec column if missing (existing DBs)
    try:
        conn.execute("ALTER TABLE scoring_sessions ADD COLUMN elapsed_sec INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE deep_work_sessions ADD COLUMN elapsed_sec INTEGER DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()


def format_elapsed(sec):
    if not sec:
        return ""
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


def save_session(ticker, result, answers, elapsed_sec=0):
    conn = get_db()
    conn.execute("""
        INSERT INTO scoring_sessions
        (ticker, created_at, elapsed_sec, total_score, decision, interpretation, red_flags, hard_fails, answers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticker.upper().strip(),
        mn_now(),
        elapsed_sec,
        result["score"],
        result["decision"],
        result["interpretation"],
        json.dumps(result["red_flags"], ensure_ascii=False),
        json.dumps(result["hard_fails"], ensure_ascii=False),
        json.dumps(answers, ensure_ascii=False),
    ))
    conn.commit()
    conn.close()


def get_all_sessions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM scoring_sessions ORDER BY created_at DESC").fetchall()
    conn.close()
    return _parse_scoring(rows)


def get_ticker_sessions(ticker):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM scoring_sessions WHERE ticker=? ORDER BY created_at DESC",
        (ticker.upper().strip(),)
    ).fetchall()
    conn.close()
    return _parse_scoring(rows)


def _parse_scoring(rows):
    sessions = []
    for row in rows:
        s = dict(row)
        s["red_flags"] = json.loads(s["red_flags"])
        s["hard_fails"] = json.loads(s["hard_fails"])
        s["answers"] = json.loads(s["answers"])
        s["elapsed_fmt"] = format_elapsed(s.get("elapsed_sec", 0))
        sessions.append(s)
    return sessions


def save_deep_work(ticker, answers, thesis, elapsed_sec=0):
    conn = get_db()
    conn.execute("""
        INSERT INTO deep_work_sessions (ticker, created_at, elapsed_sec, answers, thesis)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ticker.upper().strip(),
        mn_now(),
        elapsed_sec,
        json.dumps(answers, ensure_ascii=False),
        thesis,
    ))
    conn.commit()
    conn.close()


def get_deep_work_sessions(ticker=""):
    conn = get_db()
    if ticker:
        rows = conn.execute(
            "SELECT * FROM deep_work_sessions WHERE ticker=? ORDER BY created_at DESC",
            (ticker.upper().strip(),)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM deep_work_sessions ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    sessions = []
    for row in rows:
        s = dict(row)
        s["answers"] = json.loads(s["answers"])
        s["elapsed_fmt"] = format_elapsed(s.get("elapsed_sec", 0))
        sessions.append(s)
    return sessions
