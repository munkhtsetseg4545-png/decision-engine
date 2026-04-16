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


def init_trade_log():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trade_log (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            setup_type TEXT DEFAULT '',
            thesis TEXT DEFAULT '',
            score REAL DEFAULT 0,
            confidence REAL DEFAULT 0,
            bias_flags TEXT DEFAULT '[]',
            decision TEXT DEFAULT 'buy',
            position_size REAL DEFAULT 0,
            planned_entry REAL DEFAULT 0,
            planned_stop REAL DEFAULT 0,
            planned_target REAL DEFAULT 0,
            planned_dca_count INTEGER DEFAULT 1,
            planned_tp_count INTEGER DEFAULT 1,
            actual_entry REAL DEFAULT 0,
            actual_exit REAL DEFAULT 0,
            pnl REAL DEFAULT 0,
            r_multiple REAL DEFAULT 0,
            rule_followed BOOLEAN DEFAULT TRUE,
            emotion TEXT DEFAULT '',
            status TEXT DEFAULT 'open',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_trade(trade: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trade_log (
            id, ticker, setup_type, thesis, score, confidence, bias_flags,
            decision, position_size, planned_entry, planned_stop, planned_target,
            planned_dca_count, planned_tp_count, actual_entry, actual_exit,
            pnl, r_multiple, rule_followed, emotion, status, notes, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        trade["id"], trade["ticker"], trade.get("setup_type",""),
        trade.get("thesis",""), float(trade.get("score",0)),
        float(trade.get("confidence",0)),
        json.dumps(trade.get("bias_flags",[]), ensure_ascii=False),
        trade.get("decision","buy"), float(trade.get("position_size",0)),
        float(trade.get("planned_entry",0)), float(trade.get("planned_stop",0)),
        float(trade.get("planned_target",0)), int(trade.get("planned_dca_count",1)),
        int(trade.get("planned_tp_count",1)), float(trade.get("actual_entry",0)),
        float(trade.get("actual_exit",0)), float(trade.get("pnl",0)),
        float(trade.get("r_multiple",0)), bool(trade.get("rule_followed",True)),
        trade.get("emotion",""), trade.get("status","open"),
        trade.get("notes",""), mn_now()
    ))
    conn.commit()
    cur.close()
    conn.close()


def update_trade(trade_id: str, data: dict):
    conn = get_db()
    cur = conn.cursor()
    fields = []
    values = []
    allowed = ["actual_entry","actual_exit","pnl","r_multiple","rule_followed",
               "emotion","status","notes","setup_type","thesis","score",
               "confidence","position_size","planned_entry","planned_stop","planned_target"]
    for k in allowed:
        if k in data:
            fields.append(f"{k}=%s")
            values.append(data[k])
    if fields:
        values.append(trade_id)
        cur.execute(f"UPDATE trade_log SET {','.join(fields)} WHERE id=%s", values)
        conn.commit()
    cur.close()
    conn.close()


def get_all_trades():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trade_log ORDER BY created_at DESC")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    trades = []
    for row in rows:
        t = dict(zip(cols, row))
        t["bias_flags"] = json.loads(t["bias_flags"]) if t["bias_flags"] else []
        trades.append(t)
    return trades


def get_trade(trade_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trade_log WHERE id=%s", (trade_id,))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    if row:
        t = dict(zip(cols, row))
        t["bias_flags"] = json.loads(t["bias_flags"]) if t["bias_flags"] else []
        return t
    return None


def delete_trade(trade_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM trade_log WHERE id=%s", (trade_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_trade_analytics():
    trades = [t for t in get_all_trades() if t["status"] == "closed"]
    if not trades:
        return None
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    wr = len(wins) / len(trades)
    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
    expectancy = round((wr * avg_win) - ((1 - wr) * abs(avg_loss)), 2)
    return {
        "total": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "winrate": round(wr * 100, 1),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "expectancy": expectancy,
        "total_pnl": round(sum(t["pnl"] for t in trades), 2),
    }
