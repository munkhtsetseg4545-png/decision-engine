from flask import Flask, render_template, request, jsonify
from scoring import score_answers, QUESTIONS
from deep_work import PHASES, generate_thesis
from database import init_db, save_session, get_all_sessions, get_ticker_sessions, save_deep_work, get_deep_work_sessions

app = Flask(__name__)

with app.app_context():
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/deep-work")
def deep_work():
    return render_template("deep_work.html", phases=PHASES)


@app.route("/api/deep-work/save", methods=["POST"])
def save_deep_work_route():
    data = request.get_json()
    ticker = data.get("ticker", "").strip()
    answers = data.get("answers", {})
    if not ticker:
        return jsonify({"error": "Ticker оруулна уу"}), 400
    thesis = generate_thesis(ticker, answers)
    save_deep_work(ticker, answers, thesis)
    return jsonify({"thesis": thesis})


@app.route("/scoring")
def scoring():
    return render_template("scoring.html", questions=QUESTIONS)


@app.route("/score", methods=["POST"])
def score():
    data = request.get_json()
    answers = data.get("answers", {})
    ticker = data.get("ticker", "").strip()
    if not ticker:
        return jsonify({"error": "Ticker оруулна уу"}), 400
    result = score_answers(answers)
    save_session(ticker, result, answers)
    return jsonify(result)


@app.route("/history")
def history():
    ticker = request.args.get("ticker", "").strip().upper()
    scoring_sessions = get_ticker_sessions(ticker) if ticker else get_all_sessions()
    dw_sessions = get_deep_work_sessions(ticker)
    return render_template("history.html", scoring_sessions=scoring_sessions, dw_sessions=dw_sessions, ticker=ticker)


if __name__ == "__main__":
    app.run(debug=True)
