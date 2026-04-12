from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Phase:
    key: str
    title: str
    duration_min: int
    questions: List[Dict[str, str]]


PHASES: List[Phase] = [
    Phase(
        key="business",
        title="Business — Бизнесийг ойлгох",
        duration_min=20,
        questions=[
            {"key": "what_do", "text": "Энэ компани юу хийдэг вэ? Үндсэн бизнес нь юу вэ?"},
            {"key": "revenue",  "text": "Хэрхэн мөнгө олдог вэ? Орлогын эх үүсвэр нь юу вэ?"},
            {"key": "product",  "text": "Үндсэн бүтээгдэхүүн/үйлчилгээ нь юу вэ?"},
        ],
    ),
    Phase(
        key="moat",
        title="Moat & Management — Давуу тал ба Удирдлага",
        duration_min=20,
        questions=[
            {"key": "moat",       "text": "Өрсөлдөгчдөөс ялгарах competitive advantage (moat) байгаа юу?"},
            {"key": "management", "text": "Удирдлага хүчтэй юу? Shareholder-д ээлтэй юу?"},
            {"key": "growth",     "text": "Өсөлт тогтвортой юу? Ирээдүйд өсөх боломж байна уу?"},
        ],
    ),
    Phase(
        key="risk",
        title="Risk & Valuation — Эрсдэл ба Үнэлгээ",
        duration_min=20,
        questions=[
            {"key": "risks",     "text": "Хамгийн том эрсдэлүүд юу вэ?"},
            {"key": "downside",  "text": "Юу буруу болж болох вэ? Worst case юу вэ?"},
            {"key": "valuation", "text": "Хувьцаа хямд уу, үнэтэй юу? Яагаад?"},
        ],
    ),
]


def generate_thesis(ticker: str, answers: Dict[str, str]) -> str:
    business = answers.get("what_do", "—")
    revenue = answers.get("revenue", "—")
    moat = answers.get("moat", "—")
    management = answers.get("management", "—")
    risks = answers.get("risks", "—")
    valuation = answers.get("valuation", "—")

    quality_signal = "өндөр чанартай" if any(
        w in str(moat).lower() for w in ["байна", "тийм", "хүчтэй", "strong", "yes"]
    ) else "дунд зэргийн"

    return (
        f"INVESTMENT THESIS — {ticker.upper()}\n\n"
        f"1. Бизнес: {business}\n"
        f"2. Орлого: {revenue}\n"
        f"3. Давуу тал: {moat}\n"
        f"4. Удирдлага: {management}\n"
        f"5. Эрсдэл: {risks}\n"
        f"6. Үнэлгээ: {valuation}\n\n"
        f"Дүгнэлт: Энэ бол {quality_signal} бизнес бөгөөд тодорхой эрсдэлтэй."
    )
