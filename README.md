# Decision Engine — Scoring Module

**Layer 2 of the 90-Minute Investment Decision System**

---

## Систем тухай

Энэ бол **90 минутын 3 давхар investment decision system**-ийн **2-р хэсэг** юм:

| Layer | Хугацаа | Зорилго |
|-------|---------|---------|
| **1 — Deep Work** | 0–60 мин | Business, Moat, Management, Industry судлах |
| **2 — Scoring** ← _энд байна_ | 60–75 мин | 10 асуулт бөглөж оноо гаргах |
| **3 — Decision** | 75–90 мин | Дүрмээр action хийх |

---

## Scoring дүрэм

| Оноо | Шийдвэр |
|------|---------|
| ≥ 85, red flag байхгүй | **STRONG BUY / ADD** |
| 70–84 | **WATCHLIST / SMALL STARTER POSITION** |
| 55–69 | **HOLD / NEED MORE WORK** |
| < 55 эсвэл red flag + < 70 | **NO-GO** |

---

## Асуултууд

| # | Key | Category | Weighted |
|---|-----|----------|---------|
| 1 | business_vs_market | Thinking | 1.0× |
| 2 | anchoring | Temperament | 1.0× |
| 3 | growth_assumption | Thinking | 1.0× |
| 4 | leverage | Risk | **1.2×** |
| 5 | big_picture | Thinking | 1.0× |
| 6 | complexity | Thinking | 1.0× |
| 7 | self_limit | Opportunity | 1.0× |
| 8 | fresh_buy | Temperament | **1.2×** |
| 9 | ego | Temperament | **1.1×** |
| 10 | survive_worst_case | Risk | **1.3×** |

Сөрөг асуулт (reverse=True): raw оноог `10 - raw` болгон normalize хийнэ.

---

## Red Flag дүрэм

Дараах нөхцөл хангагдвал автоматаар red flag гарна:

- `leverage` ≥ 6
- `ego` ≥ 7
- `anchoring` ≥ 7
- `growth_assumption` ≥ 7
- `complexity` ≥ 7
- `fresh_buy` (normalized) ≤ 4
- `survive_worst_case` (normalized) ≤ 4

---

## Локал ажиллуулах

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/decision-engine.git
cd decision-engine

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Run
python app.py
# → http://localhost:5000
```

---

## Render.com deploy

1. GitHub-т push хийнэ
2. [render.com](https://render.com) → **New → Web Service**
3. Repository холбоно
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. **Deploy** дарна

`render.yaml` файл байгаа тул автоматаар тохируулна.

---

## Файлын бүтэц

```
decision-engine/
├── app.py              # Flask entry point
├── scoring.py          # Бүх scoring логик (QUESTIONS, тооцоолол, red flags)
├── requirements.txt    # Flask + gunicorn
├── Procfile            # Render/Heroku start command
├── render.yaml         # Render.com auto-config
├── .gitignore
├── templates/
│   └── index.html      # UI template
└── static/
    ├── css/
    │   └── style.css   # Royal smart загвар
    └── js/
        └── main.js     # Frontend логик
```

---

## Цаашид нэмэх хэсгүүд

- **Layer 1 — Deep Work**: Business, Moat, Management, Industry судалгааны форм
- **Layer 3 — Decision**: Автомат action log, history, portfolio tracker

---

## Багийн хэрэглээ

Render дээр deploy хийсний дараа URL-г багтайгаа хуваалцана.
Нэмэлт authentication шаардлагатай бол environment variable ашиглана.

```
# .env (локал, git-д оруулахгүй)
SECRET_KEY=your_secret_key
```
