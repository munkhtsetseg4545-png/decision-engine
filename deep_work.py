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

PHASE_LABELS = {
    "what_do":    "Бизнес юу хийдэг вэ?",
    "revenue":    "Хэрхэн мөнгө олдог вэ?",
    "product":    "Үндсэн бүтээгдэхүүн",
    "moat":       "Competitive advantage",
    "management": "Удирдлага",
    "growth":     "Өсөлт",
    "risks":      "Хамгийн том эрсдэлүүд",
    "downside":   "Worst case",
    "valuation":  "Үнэлгээ",
}


def build_thesis_text(ticker: str, answers: Dict[str, str]) -> str:
    lines = [f"INVESTMENT THESIS — {ticker.upper()}", ""]
    sections = [
        ("BUSINESS", ["what_do", "revenue", "product"]),
        ("MOAT & MANAGEMENT", ["moat", "management", "growth"]),
        ("RISK & VALUATION", ["risks", "downside", "valuation"]),
    ]
    for section_title, keys in sections:
        lines.append(section_title)
        for key in keys:
            label = PHASE_LABELS.get(key, key)
            answer = answers.get(key, "—").strip() or "—"
            lines.append(f"• {label}:")
            lines.append(f"  {answer}")
        lines.append("")
    return "\n".join(lines).strip()


def generate_ai_conclusion(ticker: str, answers: Dict[str, str]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "API key тохируулагдаагүй байна."

    prompt = f"""Та Уоррен Баффет, Чарли Мунгер нарын investment philosophy-г гүнзгий судалсан мэргэжлийн хөрөнгө оруулалтын шинжээч. Доорх хөрөнгө оруулагчийн {ticker} хувьцааны судалгааг уншаад монгол хэлээр дэлгэрэнгүй, мэргэжлийн дүгнэлт бич.

СУДАЛГААНЫ ХАРИУЛТУУД:
Бизнес: {answers.get('what_do', '—')}
Орлого: {answers.get('revenue', '—')}
Бүтээгдэхүүн: {answers.get('product', '—')}
Competitive advantage: {answers.get('moat', '—')}
Удирдлага: {answers.get('management', '—')}
Өсөлт: {answers.get('growth', '—')}
Эрсдэл: {answers.get('risks', '—')}
Worst case: {answers.get('downside', '—')}
Үнэлгээ: {answers.get('valuation', '—')}

Дараах бүтцээр дэлгэрэнгүй дүгнэлт бич. Markdown тэмдэгт (#, **, *) огт бүү ашигла. Зөвхөн энгийн текст бич:

1. БИЗНЕСИЙН ЧАНАР
Бизнесийн загвар, тогтвортой байдал, ойлгомжтой байдлын талаар 3-4 өгүүлбэрээр тайлбарла.

2. ӨРСӨЛДӨХ ДАВУУ ТАЛ
Moat хэр хүчтэй вэ, удаан хугацаанд хадгалагдах уу, удирдлага итгэмжтэй юу — 3-4 өгүүлбэр.

3. ӨСӨЛТИЙН БОЛОМЖ
Ирээдүйн өсөлтийн хүчин зүйлүүд, зах зээлийн байр суурь — 3-4 өгүүлбэр.

4. ЭРСДЭЛИЙН ҮНЭЛГЭЭ
Гол эрсдэлүүд хэр ноцтой вэ, worst case хэр магадлалтай вэ — 3-4 өгүүлбэр.

5. НИЙТ ДҮГНЭЛТ
Энэ хувьцаа цааш судлах үнэ цэнэтэй эсэх, юуг анхаарах хэрэгтэй вэ — 2-3 өгүүлбэр.

Дүгнэлт нь практик, тодорхой, хөрөнгө оруулагчид шууд хэрэгтэй мэдээлэл агуулсан байх ёстой."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"AI дүгнэлт үүсгэхэд алдаа гарлаа: {str(e)}"


def generate_thesis(ticker: str, answers: Dict[str, str]) -> str:
    thesis = build_thesis_text(ticker, answers)
    conclusion = generate_ai_conclusion(ticker, answers)
    return thesis + "\n\nAI ДҮГНЭЛТ\n\n" + conclusion
