from dataclasses import dataclass
from typing import Dict, List
import os
import anthropic


@dataclass
class Phase:
    key: str
    title: str
    duration_min: int
    questions: List[Dict[str, str]]


PHASES: List[Phase] = [
    Phase(key="business", title="Business — Бизнесийг ойлгох", duration_min=20, questions=[
        {"key": "what_do",  "text": "Энэ компани юу хийдэг вэ? Үндсэн бизнес нь юу вэ?"},
        {"key": "revenue",  "text": "Хэрхэн мөнгө олдог вэ? Орлогын эх үүсвэр нь юу вэ?"},
        {"key": "product",  "text": "Үндсэн бүтээгдэхүүн/үйлчилгээ нь юу вэ?"},
    ]),
    Phase(key="moat", title="Moat & Management — Давуу тал ба Удирдлага", duration_min=20, questions=[
        {"key": "moat",       "text": "Өрсөлдөгчдөөс ялгарах competitive advantage байгаа юу?"},
        {"key": "management", "text": "Удирдлага хүчтэй юу? Shareholder-д ээлтэй юу?"},
        {"key": "growth",     "text": "Өсөлт тогтвортой юу? Ирээдүйд өсөх боломж байна уу?"},
    ]),
    Phase(key="risk", title="Risk & Valuation — Эрсдэл ба Үнэлгээ", duration_min=20, questions=[
        {"key": "risks",     "text": "Хамгийн том эрсдэлүүд юу вэ?"},
        {"key": "downside",  "text": "Юу буруу болж болох вэ? Worst case юу вэ?"},
        {"key": "valuation", "text": "Хувьцаа хямд уу, үнэтэй юу? Яагаад?"},
    ]),
]

PHASE_LABELS = {
    "what_do": "Бизнес", "revenue": "Орлого", "product": "Бүтээгдэхүүн",
    "moat": "Competitive advantage", "management": "Удирдлага", "growth": "Өсөлт",
    "risks": "Эрсдэл", "downside": "Worst case", "valuation": "Үнэлгээ",
}


def build_thesis_text(ticker: str, answers: Dict[str, str]) -> str:
    lines = [f"INVESTMENT THESIS — {ticker.upper()}", ""]
    sections = [
        ("BUSINESS", ["what_do", "revenue", "product"]),
        ("MOAT & MANAGEMENT", ["moat", "management", "growth"]),
        ("RISK & VALUATION", ["risks", "downside", "valuation"]),
    ]
    for title, keys in sections:
        lines.append(title)
        for i, key in enumerate(keys, 1):
            ans = answers.get(key, "").strip() or "—"
            lines.append(f"{i}. {PHASE_LABELS[key]}")
            lines.append(f"   {ans}")
        lines.append("")
    return "\n".join(lines).strip()


def generate_ai_conclusion(ticker: str, answers: Dict[str, str]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "API key тохируулагдаагүй."

    a = answers
    prompt = f"""Та {ticker} хувьцааны судалгааг уншиж байна. Монгол хэрэглэгчид зориулан энгийн, шууд үгээр дүгнэлт бич. Академик эсвэл хэт томоохон үг бүү хэрэглэ. Найздаа ярихтай адил тодорхой бич.

Markdown (#, *, **) огт бүү ашигла. Зөвхөн энгийн текст.

Яг дараах бүтцээр бич:

BUSINESS ДҮГНЭЛТ
[Энэ компани юу хийдэг, мөнгөө яаж олдог талаар 2 энгийн өгүүлбэр]

MOAT & MANAGEMENT ДҮГНЭЛТ
[Өрсөлдөгчдөөс хэр ялгаатай, удирдлага хэр итгэмжтэй талаар 2 энгийн өгүүлбэр]

RISK & VALUATION ДҮГНЭЛТ
[Хамгийн аймаар эрсдэл нь юу, үнэ нь зохистой эсэх талаар 2 энгийн өгүүлбэр]

Судалгааны мэдээлэл:
Бизнес: {a.get('what_do','')}
Орлого: {a.get('revenue','')}
Бүтээгдэхүүн: {a.get('product','')}
Moat: {a.get('moat','')}
Удирдлага: {a.get('management','')}
Өсөлт: {a.get('growth','')}
Эрсдэл: {a.get('risks','')}
Worst case: {a.get('downside','')}
Үнэлгээ: {a.get('valuation','')}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Алдаа: {str(e)}"


def generate_thesis(ticker: str, answers: Dict[str, str]) -> str:
    thesis = build_thesis_text(ticker, answers)
    conclusion = generate_ai_conclusion(ticker, answers)
    return thesis + "\n\nAI ДҮГНЭЛТ\n\n" + conclusion
