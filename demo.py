import os
import yfinance as yf
import anthropic


def fetch_stock_data(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        pe = info.get("trailingPE") or info.get("forwardPE") or 0
        market_cap = info.get("marketCap") or 0
        revenue = info.get("totalRevenue") or 0
        profit_margin = info.get("profitMargins") or 0
        debt_equity = info.get("debtToEquity") or 0
        roe = info.get("returnOnEquity") or 0
        sector = info.get("sector") or ""
        industry = info.get("industry") or ""
        name = info.get("longName") or ticker
        summary = info.get("longBusinessSummary") or ""
        beta = info.get("beta") or 0
        week_52_high = info.get("fiftyTwoWeekHigh") or 0
        week_52_low = info.get("fiftyTwoWeekLow") or 0
        analyst_target = info.get("targetMeanPrice") or 0
        recommendation = info.get("recommendationKey") or ""
        dividend_yield = info.get("dividendYield") or 0

        def fmt_b(v):
            if v >= 1e12:
                return f"${v/1e12:.1f}T"
            if v >= 1e9:
                return f"${v/1e9:.1f}B"
            if v >= 1e6:
                return f"${v/1e6:.1f}M"
            return f"${v:,.0f}"

        return {
            "ticker": ticker.upper(),
            "name": name,
            "sector": sector,
            "industry": industry,
            "price": round(price, 2),
            "pe": round(pe, 1) if pe else "N/A",
            "market_cap": fmt_b(market_cap) if market_cap else "N/A",
            "revenue": fmt_b(revenue) if revenue else "N/A",
            "profit_margin": f"{profit_margin*100:.1f}%" if profit_margin else "N/A",
            "debt_equity": round(debt_equity, 1) if debt_equity else "N/A",
            "roe": f"{roe*100:.1f}%" if roe else "N/A",
            "beta": round(beta, 2) if beta else "N/A",
            "week_52_high": round(week_52_high, 2),
            "week_52_low": round(week_52_low, 2),
            "analyst_target": round(analyst_target, 2) if analyst_target else "N/A",
            "recommendation": recommendation,
            "dividend_yield": f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A",
            "summary": summary[:500] if summary else "",
            "upside": round((analyst_target / price - 1) * 100, 1) if analyst_target and price else "N/A",
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker.upper()}


def generate_demo_thesis(data: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or "error" in data:
        return {
            "what_do": data.get("summary", ""),
            "revenue": f"Revenue: {data.get('revenue','N/A')}, Profit margin: {data.get('profit_margin','N/A')}",
            "product": f"{data.get('sector','')} — {data.get('industry','')}",
            "moat": "N/A",
            "management": f"ROE: {data.get('roe','N/A')}, Debt/Equity: {data.get('debt_equity','N/A')}",
            "growth": f"Analyst target: ${data.get('analyst_target','N/A')}, Upside: {data.get('upside','N/A')}%",
            "risks": f"Beta: {data.get('beta','N/A')}, P/E: {data.get('pe','N/A')}",
            "downside": f"52W Low: ${data.get('week_52_low','N/A')}",
            "valuation": f"P/E: {data.get('pe','N/A')}, Market cap: {data.get('market_cap','N/A')}",
        }

    prompt = f"""Та {data['ticker']} ({data['name']}) хувьцааны бодит өгөгдлийг уншиж байна.

Өгөгдөл:
- Үнэ: ${data['price']}
- P/E: {data['pe']}
- Market cap: {data['market_cap']}
- Revenue: {data['revenue']}
- Profit margin: {data['profit_margin']}
- ROE: {data['roe']}
- Debt/Equity: {data['debt_equity']}
- Beta: {data['beta']}
- 52W High/Low: ${data['week_52_high']} / ${data['week_52_low']}
- Analyst target: ${data['analyst_target']} (upside: {data['upside']}%)
- Sector: {data['sector']} — {data['industry']}
- Тайлбар: {data['summary'][:300]}

Монголоор товч хариулт өг. Markdown бүү ашигла. Яг дараах формат:

what_do: [компани юу хийдэг 1-2 өгүүлбэр]
revenue: [мөнгө яаж олдог, margin]
product: [үндсэн бүтээгдэхүүн]
moat: [competitive advantage байгаа эсэх]
management: [ROE, debt байдал]
growth: [өсөлтийн боломж, analyst target]
risks: [гол эрсдэлүүд]
downside: [worst case]
valuation: [үнэ хямд уу үнэтэй юу]"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text
        answers = {}
        for line in text.strip().split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                if key in ["what_do","revenue","product","moat","management","growth","risks","downside","valuation"]:
                    answers[key] = val.strip()
        # fallback
        for k in ["what_do","revenue","product","moat","management","growth","risks","downside","valuation"]:
            if k not in answers:
                answers[k] = "—"
        return answers
    except Exception as e:
        return {"what_do": f"Алдаа: {str(e)}"}


def generate_demo_score(data: dict) -> dict:
    from scoring import score_answers, QUESTIONS

    pe = data.get("pe", 0)
    profit_margin = data.get("profit_margin", "0%")
    roe = data.get("roe", "0%")
    beta = data.get("beta", 1)
    upside = data.get("upside", 0)

    def pct(s):
        try:
            return float(str(s).replace("%","").strip())
        except:
            return 0.0

    pm = pct(profit_margin)
    roe_v = pct(roe)
    up = upside if isinstance(upside, (int, float)) else 0
    pe_v = pe if isinstance(pe, (int, float)) else 20
    beta_v = beta if isinstance(beta, (int, float)) else 1

    answers = {
        "business_vs_market": 8,
        "anchoring": 7,
        "growth_assumption": 7 if up > 10 else 5,
        "leverage_and_concentration": 8 if pe_v < 30 else 5,
        "big_picture": 8,
        "complexity": 7,
        "self_limiting": 6,
        "fresh_start": 8 if up > 15 else 6,
        "ego": 8,
        "survival": 8 if beta_v < 1.5 else 5,
    }

    return score_answers(answers), answers


def run_demo(ticker: str) -> dict:
    data = fetch_stock_data(ticker)
    if "error" in data:
        return {"error": data["error"]}

    answers = generate_demo_thesis(data)
    score_result, score_answers_raw = generate_demo_score(data)

    return {
        "stock_data": data,
        "answers": answers,
        "score": score_result,
        "score_answers": score_answers_raw,
    }
