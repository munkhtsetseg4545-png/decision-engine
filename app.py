from flask import Flask, render_template, request, jsonify
from scoring import score_answers, QUESTIONS
from database import init_db, save_session, get_all_sessions, get_ticker_sessions

app = Flask(__name__)

with app.app_context():
    init_db()


@app.route("/")
def index():
    return render_template("index.html", questions=QUESTIONS)


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
    if ticker:
        sessions = get_ticker_sessions(ticker)
    else:
        sessions = get_all_sessions()
    return render_template("history.html", sessions=sessions, ticker=ticker)


@app.route("/api/history")
def api_history():
    sessions = get_all_sessions()
    return jsonify(sessions)


if __name__ == "__main__":
    app.run(debug=True)
