from flask import Flask, render_template, request, jsonify
from scoring import score_answers, QUESTIONS
from deep_work import PHASES, generate_thesis
from decision import calculate_decision
from database import (init_db, save_session, get_all_sessions, get_ticker_sessions,
                      save_deep_work, get_deep_work_sessions, get_db,
                      save_settings, get_settings)

app = Flask(__name__)

with app.app_context():
    init_db()


def phases_to_dict():
    return [{"key": p.key, "title": p.title, "duration_min": p.duration_min, "questions": p.questions}
            for p in PHASES]


@app.route("/")
def index():
    return render_template("index.html")


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
    conn.execute("DELETE FROM scoring_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/delete/deepwork/<int:session_id>", methods=["POST"])
def delete_deepwork(session_id):
    conn = get_db()
    conn.execute("DELETE FROM deep_work_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
