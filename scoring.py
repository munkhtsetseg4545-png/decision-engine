from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Question:
    key: str
    text: str
    category: str
    weight: float
    hard_fail_threshold: int | None = None
    red_flag_threshold: int | None = None


QUESTIONS: List[Question] = [
    Question(key="business_vs_market", text="1. Би market timing (зах зээл таах) биш, business analysis (бизнес шинжилгээ) хийж байна уу?", category="Thinking", weight=1.2, red_flag_threshold=4),
    Question(key="anchoring", text="2. Би худалдаж авсан үнэдээ уягдаагүй байна уу? (Anchoring bias — анхны үнэд хэт баригдах алдаа)", category="Temperament", weight=1.0, red_flag_threshold=4),
    Question(key="growth_assumption", text="3. Миний growth assumption (өсөлтийн төсөөлөл) бодитой, хэт өөдрөг биш үү?", category="Valuation", weight=1.2, red_flag_threshold=4),
    Question(key="leverage_and_concentration", text="4. Leverage (хөшүүрэг) болон hidden leverage (далд хөшүүрэг: хэт төвлөрөл) байхгүй юу?", category="Risk", weight=1.4, hard_fail_threshold=2, red_flag_threshold=4),
    Question(key="big_picture", text="5. Би detail (нарийн зүйл)-д живээгүй, big picture (том дүр зураг)-ээ алдаагүй юу?", category="Thinking", weight=1.0, red_flag_threshold=4),
    Question(key="complexity", text="6. Би яагаад авч/барьж байгаагаа энгийнээр тайлбарлаж чадах уу?", category="Thinking", weight=1.1, red_flag_threshold=4),
    Question(key="self_limiting", text="7. Би өөрийн зуршил, айдсаасаа болж сайн боломжийг өөрөө хааж байна уу?", category="Opportunity", weight=0.8, red_flag_threshold=3),
    Question(key="fresh_start", text="8. Хэрэв өнөөдөр 0-ээс эхэлсэн бол би энэ хувьцааг одоо авах байсан уу? (Fresh start test)", category="Decision", weight=1.5, hard_fail_threshold=2, red_flag_threshold=4),
    Question(key="ego", text="9. Энэ decision миний ego (өөрийгөө зөв гэж батлах хүсэл)-г хамгаалаагүй юу?", category="Temperament", weight=1.2, red_flag_threshold=4),
    Question(key="survival", text="10. Хэрэв энэ хөрөнгө оруулалт буруу болбол, би санхүүгийн болон сэтгэлзүйн хувьд дааж, үргэлжлүүлэн тоглож чадах уу?", category="Risk", weight=1.6, hard_fail_threshold=3, red_flag_threshold=4),
]

RED_FLAG_LABELS: Dict[str, str] = {
    "business_vs_market":         "Market-driven decision (зах зээл таасан шийдвэр)",
    "anchoring":                  "Anchoring bias (худалдаж авсан үнэд уягдсан)",
    "growth_assumption":          "Over-optimistic growth assumption",
    "leverage_and_concentration": "Leverage / hidden leverage risk",
    "big_picture":                "Detail trap (нарийн зүйлд гацсан)",
    "complexity":                 "Complexity illusion",
    "self_limiting":              "Self-limiting bias",
    "fresh_start":                "Fresh-start failure (conviction сул)",
    "ego":                        "Ego-driven decision",
    "survival":                   "Survival risk (даах чадвар сул)",
}


def weighted_score(scores: Dict[str, int]) -> float:
    total = sum(scores[q.key] * q.weight for q in QUESTIONS)
    max_total = sum(10 * q.weight for q in QUESTIONS)
    return round((total / max_total) * 100, 1)


def collect_red_flags(scores: Dict[str, int]) -> List[str]:
    return [RED_FLAG_LABELS[q.key] for q in QUESTIONS
            if q.red_flag_threshold is not None and scores[q.key] <= q.red_flag_threshold]


def collect_hard_fails(scores: Dict[str, int]) -> List[str]:
    return [q.key for q in QUESTIONS
            if q.hard_fail_threshold is not None and scores[q.key] <= q.hard_fail_threshold]


def category_breakdown(scores: Dict[str, int]) -> Dict[str, float]:
    grouped: Dict[str, List[int]] = {}
    for q in QUESTIONS:
        grouped.setdefault(q.category, []).append(scores[q.key])
    return {cat: round(sum(v) / len(v) * 10, 1) for cat, v in grouped.items()}


def decision_logic(scores, total_score, red_flags, hard_fails) -> Tuple[str, str]:
    if "survival" in hard_fails:
        return "AUTO NO-GO", "Survival failed: хамгийн муу хувилбарт даах чадвар хангалтгүй."
    if "fresh_start" in hard_fails:
        return "AUTO NO-GO", "Fresh start failed: өнөөдөр шинээр авахгүй бол thesis сул."
    if "leverage_and_concentration" in hard_fails:
        return "AUTO NO-GO", "Leverage / concentration failed: данс устгах эрсдэл өндөр."
    if scores["ego"] <= 4 and scores["fresh_start"] <= 4:
        return "EXIT / NO-GO", "Ego + fresh start хоёул сул: өөрийгөө хуурах эрсдэл өндөр."
    if total_score >= 85 and len(red_flags) <= 1:
        return "STRONG BUY / ADD", "Өндөр чанартай decision. Bias бага, risk хянагдсан."
    if total_score >= 70 and len(red_flags) <= 3:
        return "SMALL POSITION / WATCHLIST", "Санаа боломжийн. Sizing-аа болгоомжтой хий."
    if total_score >= 55:
        return "HOLD / NEED MORE WORK", "Илүү судалгаа, эсрэг кейс, downside analysis хэрэгтэй."
    return "NO-GO", "Decision quality хангалтгүй. Алдаа гаргах магадлал өндөр."


def action_guide(decision: str) -> str:
    return {
        "STRONG BUY / ADD": "Normal position авч болно. Thesis бэлэн бол add хийж болно. Review interval тогтоо.",
        "SMALL POSITION / WATCHLIST": "Starter position эсвэл watchlist. Position size бага байлга. Red flag цэвэрлэсний дараа нэмж болно.",
        "HOLD / NEED MORE WORK": "Одоо том decision бүү гарга. Bear case, valuation, management risk ахин шалга. Дараа нь дахин score хий.",
    }.get(decision, "Capital commit хийхгүй. Existing position байвал бууруулах / гарах хувилбар бод. Thesis-ээ шинээр барь.")


def score_answers(answers: Dict[str, int]) -> Dict:
    scores = {q.key: int(answers.get(q.key, 5)) for q in QUESTIONS}
    total = weighted_score(scores)
    red_flags = collect_red_flags(scores)
    hard_fails = collect_hard_fails(scores)
    decision, interpretation = decision_logic(scores, total, red_flags, hard_fails)
    return {
        "score": total,
        "decision": decision,
        "interpretation": interpretation,
        "action": action_guide(decision),
        "red_flags": red_flags,
        "hard_fails": hard_fails,
        "category_breakdown": category_breakdown(scores),
        "normalized_scores": scores,
    }