import uuid
from flask import Flask, render_template, request, jsonify
from scoring import score_answers, QUESTIONS
from deep_work import PHASES, generate_thesis
from decision import calculate_decision
from analytics import build_analytics
from database import (init_db, init_trade_log, save_session, get_all_sessions,
                      get_ticker_sessions, save_deep_work, get_deep_work_sessions,
                      get_db, save_settings, get_settings, save_trade, update_trade,
                      get_all_trades, get_trade, delete_trade, get_trade_analytics)

app = Flask(__name__)

with app.app_context():
    init_db()
    init_trade_log()


def phases_to_dict():
    return [{"key": p.key, "title": p.title, "duration_min": p.duration_min,
             "questions": p.questions} for p in PHASES]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/demo")
def demo():
    return render_template("demo.html")


@app.route("/api/demo")
def api_demo():
    ticker = request.args.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker оруулна уу"})
    try:
        from demo import run_demo
        from decision import calculate_decision
        result = run_demo(ticker)
        if "error" in result:
            return jsonify(result)
        settings = get_settings()
        dec = calculate_decision(
            result["score"]["score"],
            settings["capital"],
            settings["max_position"]
        )
        result["decision"] = dec
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/deep-work")
def deep_work():
    return render_template("deep_work.html", phases=phases_to_dict())


@app.route("/api/deep-work/save", methods=["POST"])
def save_deep_work_route():
    data = request.get_json()
    ticker = data.get("ticker", "").strip()
    answers = data.get("answers", {})
    elapsed_sec = int(data.get("elapsed_sec", 0))
    if not ticker:
        return jsonify({"error": "Ticker оруулна уу"}), 400
    thesis = generate_thesis(ticker, answers)
    save_deep_work(ticker, answers, thesis, elapsed_sec)
    return jsonify({"thesis": thesis})


@app.route("/scoring")
def scoring():
    return render_template("scoring.html", questions=QUESTIONS)


@app.route("/score", methods=["POST"])
def score():
    data = request.get_json()
    answers = data.get("answers", {})
    ticker = data.get("ticker", "").strip()
    elapsed_sec = int(data.get("elapsed_sec", 0))
    if not ticker:
        return jsonify({"error": "Ticker оруулна уу"}), 400
    result = score_answers(answers)
    save_session(ticker, result, answers, elapsed_sec)
    return jsonify(result)


@app.route("/decision")
def decision():
    ticker = request.args.get("ticker", "")
    score = request.args.get("score", 0, type=float)
    settings = get_settings()
    result = None
    if score > 0:
        result = calculate_decision(score, settings["capital"], settings["max_position"])
    return render_template("decision.html", ticker=ticker, score=score,
                           result=result, settings=settings)


@app.route("/trade-log")
def trade_log():
    trades = get_all_trades()
    analytics = get_trade_analytics()
    return render_template("trade_log.html", trades=trades, analytics=analytics)


@app.route("/analytics")
def analytics():
    trades = get_all_trades()
    closed = [t for t in trades if t["status"] == "closed"]
    if not closed:
        return render_template("analytics.html", data=None)
    data = build_analytics(closed)
    return render_template("analytics.html", data=data)


@app.route("/api/trade", methods=["POST"])
def add_trade():
    data = request.get_json()
    data["id"] = str(uuid.uuid4())[:8]
    save_trade(data)
    return jsonify({"ok": True, "id": data["id"]})


@app.route("/api/trade/<trade_id>", methods=["PUT"])
def edit_trade(trade_id):
    data = request.get_json()
    update_trade(trade_id, data)
    return jsonify({"ok": True})


@app.route("/api/trade/<trade_id>", methods=["DELETE"])
def remove_trade(trade_id):
    delete_trade(trade_id)
    return jsonify({"ok": True})


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        save_settings({
            "name": request.form.get("name", ""),
            "capital": request.form.get("capital", 0),
            "max_position": request.form.get("max_position", 10),
            "risk_tolerance": request.form.get("risk_tolerance", "moderate"),
        })
        return jsonify({"ok": True})
    return render_template("settings.html", settings=get_settings())


@app.route("/history")
def history():
    ticker = request.args.get("ticker", "").strip().upper()
    scoring_sessions = get_ticker_sessions(ticker) if ticker else get_all_sessions()
    dw_sessions = get_deep_work_sessions(ticker)
    return render_template("history.html", scoring_sessions=scoring_sessions,
                           dw_sessions=dw_sessions, ticker=ticker)


@app.route("/delete/scoring/<int:session_id>", methods=["POST"])
def delete_scoring(session_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM scoring_sessions WHERE id=%s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/delete/deepwork/<int:session_id>", methods=["POST"])
def delete_deepwork(session_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM deep_work_sessions WHERE id=%s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/demo")
def demo():
    return "Demo горим түр зогсоосон байна.", 503
