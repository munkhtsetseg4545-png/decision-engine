import os
from typing import Dict, Any


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        pe = info.get("trailingPE") or info.get("forwardPE") or 0
        market_cap = info.get("marketCap") or 0
        profit_margin = info.get("profitMargins") or 0
        sector = info.get("sector") or "Unknown"
        industry = info.get("industry") or "Unknown"
        name = info.get("longName") or ticker
        beta = info.get("beta") or 1.0
        debt_equity = info.get("debtToEquity") or 0
        roe = info.get("returnOnEquity") or 0
        rev_growth = info.get("revenueGrowth") or 0
        summary = info.get("longBusinessSummary") or ""
        return {
            "ticker": ticker.upper(), "name": name,
            "price": round(float(price), 2),
            "pe": round(float(pe), 2) if pe else None,
            "market_cap": market_cap,
            "profit_margin": round(float(profit_margin) * 100, 2) if profit_margin else None,
            "sector": sector, "industry": industry,
            "beta": round(float(beta), 2),
            "debt_equity": round(float(debt_equity), 2) if debt_equity else None,
            "roe": round(float(roe) * 100, 2) if roe else None,
            "rev_growth": round(float(rev_growth) * 100, 2) if rev_growth else None,
            "summary": summary[:400] if summary else "",
            "error": None,
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)}


def format_market_cap(mc: int) -> str:
    if not mc: return "N/A"
    if mc >= 1_000_000_000_000: return f"${mc/1_000_000_000_000:.1f}T"
    if mc >= 1_000_000_000: return f"${mc/1_000_000_000:.1f}B"
    return f"${mc/1_000_000:.0f}M"


def generate_demo_thesis(ticker: str, d: Dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_thesis(ticker, d)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Та мэргэжлийн хөрөнгө оруулалтын шинжээч. {d['name']} ({ticker}) хувьцааны бодит мэдээлэлд үндэслэн монголоор investment thesis бич.

Мэдээлэл:
- Үнэ: ${d['price']} | P/E: {d['pe'] or 'N/A'} | Market cap: {format_market_cap(d['market_cap'])}
- Sector: {d['sector']} / {d['industry']}
- Profit margin: {d['profit_margin'] or 'N/A'}% | ROE: {d['roe'] or 'N/A'}% | Rev growth: {d['rev_growth'] or 'N/A'}%
- Beta: {d['beta']} | D/E: {d['debt_equity'] or 'N/A'}
- Бизнес: {d['summary'][:300] if d['summary'] else 'N/A'}

Markdown бүү ашигла. Дараах бүтцээр бич:

BUSINESS
1. Бизнес юу хийдэг вэ?: [2 өгүүлбэр]
2. Хэрхэн мөнгө олдог вэ?: [орлогын эх үүсвэр]
3. Үндсэн бүтээгдэхүүн: [гол product]

MOAT & MANAGEMENT
1. Competitive advantage: [давуу тал]
2. Удирдлага: [ROE-д тулгуурлан]
3. Өсөлт: [rev growth-д тулгуурлан]

RISK & VALUATION
1. Хамгийн том эрсдэлүүд: [beta, debt-д тулгуурлан]
2. Worst case: [хамгийн муу хувилбар]
3. Үнэлгээ: [P/E-д тулгуурлан]

AI ДҮГНЭЛТ

BUSINESS ДҮГНЭЛТ
[2 өгүүлбэр]

MOAT & MANAGEMENT ДҮГНЭЛТ
[2 өгүүлбэр]

RISK & VALUATION ДҮГНЭЛТ
[2 өгүүлбэр]"""
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception:
        return _fallback_thesis(ticker, d)


def _fallback_thesis(ticker: str, d: Dict) -> str:
    return f"""INVESTMENT THESIS — {ticker}

BUSINESS
1. Бизнес юу хийдэг вэ?: {d.get('name', ticker)} — {d.get('sector', 'N/A')} салбар.
2. Хэрхэн мөнгө олдог вэ?: {d.get('industry', 'N/A')} чиглэл.
3. Үндсэн бүтээгдэхүүн: {d.get('summary', '')[:100]}

MOAT & MANAGEMENT
1. Competitive advantage: ROE {d.get('roe', 'N/A')}%
2. Удирдлага: Profit margin {d.get('profit_margin', 'N/A')}%
3. Өсөлт: Revenue growth {d.get('rev_growth', 'N/A')}%

RISK & VALUATION
1. Хамгийн том эрсдэлүүд: Beta {d.get('beta', 'N/A')}
2. Worst case: Зах зээлийн нөхцөл муудах
3. Үнэлгээ: P/E {d.get('pe', 'N/A')}"""


def generate_demo_score(d: Dict) -> Dict:
    scores = {}
    pe = d.get("pe")
    scores["valuation"] = 9 if pe and pe < 15 else (7 if pe and pe < 25 else (5 if pe and pe < 40 else 3))
    roe = d.get("roe")
    scores["quality"] = 9 if roe and roe > 20 else (7 if roe and roe > 10 else 5)
    growth = d.get("rev_growth")
    scores["growth"] = 9 if growth and growth > 20 else (7 if growth and growth > 10 else (5 if growth and growth > 0 else 3))
    beta = d.get("beta") or 1.0
    scores["risk"] = 9 if beta < 0.8 else (7 if beta < 1.2 else (5 if beta < 1.5 else 3))
    margin = d.get("profit_margin")
    scores["margin"] = 9 if margin and margin > 20 else (7 if margin and margin > 10 else 5)
    total = round(sum(scores.values()) / len(scores) * 10, 1)
    return {"total_score": total, "breakdown": scores}


def run_demo(ticker: str) -> Dict:
    stock_data = fetch_stock_data(ticker)
    if stock_data.get("error"):
        return {"error": f"{ticker} мэдээлэл татахад алдаа: {stock_data['error']}"}
    thesis = generate_demo_thesis(ticker, stock_data)
    score_result = generate_demo_score(stock_data)
    return {
        "ticker": ticker.upper(),
        "stock_data": stock_data,
        "thesis": thesis,
        "score": score_result,
    }
