from flask import Flask, render_template, request, jsonify
from scoring import score_answers, QUESTIONS

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", questions=QUESTIONS)


@app.route("/score", methods=["POST"])
def score():
    data = request.get_json()
    answers = data.get("answers", {})
    result = score_answers(answers)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
