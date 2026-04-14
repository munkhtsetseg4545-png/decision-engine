import os
import json
from datetime import datetime, timezone, timedelta

MN_TZ = timezone(timedelta(hours=8))


def mn_now():
    return datetime.now(MN_TZ).strftime("%Y-%m-%d %H:%M")


def format_elapsed(sec):
    if not sec:
        return ""
    return f"{sec // 60:02d}:{sec % 60:02d}"


def get_db():
    import psycopg2
    import psycopg2.extras
    url = os.environ.get("DATABASE_URL", "")
    conn = psycopg2.connect(url)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scoring_sessions (
            id SERIAL PRIMARY KEY,
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deep_work_sessions (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            created_at TEXT NOT NULL,
            elapsed_sec INTEGER DEFAULT 0,
            answers TEXT NOT NULL,
            thesis TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            name TEXT DEFAULT '',
            capital REAL DEFAULT 0,
            max_position REAL DEFAULT 10,
            risk_tolerance TEXT DEFAULT 'moderate'
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_session(ticker, result, answers, elapsed_sec=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scoring_sessions
        (ticker, created_at, elapsed_sec, total_score, decision, interpretation, red_flags, hard_fails, answers)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        ticker.upper().strip(), mn_now(), elapsed_sec,
        result["score"], result["decision"], result["interpretation"],
        json.dumps(result["red_flags"], ensure_ascii=False),
        json.dumps(result["hard_fails"], ensure_ascii=False),
        json.dumps(answers, ensure_ascii=False),
    ))
    conn.commit()
    cur.close()
    conn.close()


def _parse_scoring(rows):
    sessions = []
    for row in rows:
        s = dict(zip(['id','ticker','created_at','elapsed_sec','total_score','decision',
                      'interpretation','red_flags','hard_fails','answers'], row))
        s["red_flags"] = json.loads(s["red_flags"])
        s["hard_fails"] = json.loads(s["hard_fails"])
        s["answers"] = json.loads(s["answers"])
        s["elapsed_fmt"] = format_elapsed(s.get("elapsed_sec", 0))
        sessions.append(s)
    return sessions


def get_all_sessions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,ticker,created_at,elapsed_sec,total_score,decision,interpretation,red_flags,hard_fails,answers FROM scoring_sessions ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return _parse_scoring(rows)


def get_ticker_sessions(ticker):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,ticker,created_at,elapsed_sec,total_score,decision,interpretation,red_flags,hard_fails,answers FROM scoring_sessions WHERE ticker=%s ORDER BY created_at DESC", (ticker.upper().strip(),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return _parse_scoring(rows)


def save_deep_work(ticker, answers, thesis, elapsed_sec=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO deep_work_sessions (ticker, created_at, elapsed_sec, answers, thesis)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        ticker.upper().strip(), mn_now(), elapsed_sec,
        json.dumps(answers, ensure_ascii=False), thesis,
    ))
    conn.commit()
    cur.close()
    conn.close()


def get_deep_work_sessions(ticker=""):
    conn = get_db()
    cur = conn.cursor()
    if ticker:
        cur.execute("SELECT id,ticker,created_at,elapsed_sec,answers,thesis FROM deep_work_sessions WHERE ticker=%s ORDER BY created_at DESC", (ticker.upper().strip(),))
    else:
        cur.execute("SELECT id,ticker,created_at,elapsed_sec,answers,thesis FROM deep_work_sessions ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    sessions = []
    for row in rows:
        s = dict(zip(['id','ticker','created_at','elapsed_sec','answers','thesis'], row))
        s["answers"] = json.loads(s["answers"])
        s["elapsed_fmt"] = format_elapsed(s.get("elapsed_sec", 0))
        sessions.append(s)
    return sessions


def save_settings(settings: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM settings")
    cur.execute("""
        INSERT INTO settings (id, name, capital, max_position, risk_tolerance)
        VALUES (1, %s, %s, %s, %s)
    """, (
        settings.get("name", ""),
        float(settings.get("capital", 0)),
        float(settings.get("max_position", 10)),
        settings.get("risk_tolerance", "moderate"),
    ))
    conn.commit()
    cur.close()
    conn.close()


def get_settings() -> dict:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,name,capital,max_position,risk_tolerance FROM settings WHERE id=1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return dict(zip(['id','name','capital','max_position','risk_tolerance'], row))
    return {"name": "", "capital": 0, "max_position": 10, "risk_tolerance": "moderate"}


def delete_scoring_session(session_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM scoring_sessions WHERE id=%s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()


def delete_deep_work_session(session_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM deep_work_sessions WHERE id=%s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()
