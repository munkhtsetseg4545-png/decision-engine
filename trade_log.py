from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# ── Data Model ────────────────────────────────────────────────

@dataclass
class Trade:
    ticker: str
    setup_type: str
    thesis: str

    # Layer 2
    score: float = 0.0
    confidence: float = 0.0
    bias_flags: list = field(default_factory=list)

    # Layer 3 — plan
    decision: str = "buy"
    position_size: float = 0.0
    planned_entry: float = 0.0
    planned_stop: float = 0.0
    planned_target: float = 0.0
    planned_dca_count: int = 1
    planned_tp_count: int = 1

    # Layer 4 — result
    actual_entry: float = 0.0
    actual_exit: float = 0.0
    pnl: float = 0.0
    r_multiple: float = 0.0
    rule_followed: bool = True
    emotion: str = ""
    status: str = "open"
    notes: str = ""

    # Auto fields
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


# ── Trade Log ─────────────────────────────────────────────────

class TradeLog:
    def __init__(self):
        self._trades: dict[str, Trade] = {}

    def add_trade(self, trade: Trade) -> Trade:
        self._trades[trade.id] = trade
        return trade

    def update_trade_result(self, trade_id: str, result_data: dict) -> Optional[Trade]:
        trade = self._trades.get(trade_id)
        if not trade:
            return None
        for key, val in result_data.items():
            if hasattr(trade, key):
                setattr(trade, key, val)
        if trade.planned_stop and trade.actual_entry and trade.actual_exit:
            risk = abs(trade.actual_entry - trade.planned_stop)
            if risk > 0:
                trade.r_multiple = round((trade.actual_exit - trade.actual_entry) / risk, 2)
        return trade

    def get_all_trades(self) -> list[Trade]:
        return list(self._trades.values())

    def get_closed_trades(self) -> list[Trade]:
        return [t for t in self._trades.values() if t.status == "closed"]

    # ── Analytics ─────────────────────────────────────────────

    def calculate_winrate(self) -> float:
        closed = self.get_closed_trades()
        if not closed:
            return 0.0
        wins = sum(1 for t in closed if t.pnl > 0)
        return round(wins / len(closed), 4)

    def calculate_avg_win(self) -> float:
        wins = [t.pnl for t in self.get_closed_trades() if t.pnl > 0]
        return round(sum(wins) / len(wins), 2) if wins else 0.0

    def calculate_avg_loss(self) -> float:
        losses = [t.pnl for t in self.get_closed_trades() if t.pnl < 0]
        return round(sum(losses) / len(losses), 2) if losses else 0.0

    def calculate_expectancy(self) -> float:
        wr = self.calculate_winrate()
        avg_win = self.calculate_avg_win()
        avg_loss = self.calculate_avg_loss()
        return round((wr * avg_win) - ((1 - wr) * abs(avg_loss)), 2)

    def analyze_by_score(self) -> dict:
        bands = {"90+": [], "80-89": [], "70-79": [], "<70": []}
        for t in self.get_closed_trades():
            if t.score >= 90:
                bands["90+"].append(t)
            elif t.score >= 80:
                bands["80-89"].append(t)
            elif t.score >= 70:
                bands["70-79"].append(t)
            else:
                bands["<70"].append(t)
        return {band: _band_stats(trades) for band, trades in bands.items()}

    def analyze_by_setup(self) -> dict:
        setups: dict[str, list] = {}
        for t in self.get_closed_trades():
            setups.setdefault(t.setup_type, []).append(t)
        result = {}
        for setup, trades in setups.items():
            stats = _band_stats(trades)
            wr = stats["winrate"]
            avg_win = _avg([t.pnl for t in trades if t.pnl > 0])
            avg_loss = _avg([t.pnl for t in trades if t.pnl < 0])
            stats["expectancy"] = round((wr * avg_win) - ((1 - wr) * abs(avg_loss)), 2)
            result[setup] = stats
        return result

    def analyze_rule_break(self) -> dict:
        closed = self.get_closed_trades()
        followed = [t.pnl for t in closed if t.rule_followed]
        broken = [t.pnl for t in closed if not t.rule_followed]
        return {
            "followed_count": len(followed),
            "followed_avg_pnl": _avg(followed),
            "broken_count": len(broken),
            "broken_avg_pnl": _avg(broken),
        }

    # ── Storage ───────────────────────────────────────────────

    def save_to_file(self, path: str = "trades.json") -> None:
        data = {tid: asdict(t) for tid, t in self._trades.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str = "trades.json") -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._trades = {tid: Trade(**td) for tid, td in data.items()}
        except FileNotFoundError:
            self._trades = {}

    def summary(self) -> dict:
        closed = self.get_closed_trades()
        return {
            "total": len(self._trades),
            "open": len(self._trades) - len(closed),
            "closed": len(closed),
            "winrate": f"{self.calculate_winrate() * 100:.1f}%",
            "avg_win": self.calculate_avg_win(),
            "avg_loss": self.calculate_avg_loss(),
            "expectancy": self.calculate_expectancy(),
        }


# ── Helpers ───────────────────────────────────────────────────

def _avg(values: list) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _band_stats(trades: list) -> dict:
    if not trades:
        return {"count": 0, "winrate": 0.0, "avg_pnl": 0.0, "avg_r": 0.0}
    wins = [t for t in trades if t.pnl > 0]
    return {
        "count": len(trades),
        "winrate": round(len(wins) / len(trades), 4),
        "avg_pnl": _avg([t.pnl for t in trades]),
        "avg_r": _avg([t.r_multiple for t in trades]),
    }


# ── Sample Usage ──────────────────────────────────────────────

if __name__ == "__main__":
    log = TradeLog()

    # Trade 1 — Layer 1-3 мэдээлэл
    t1 = Trade(
        ticker="AAPL",
        setup_type="breakout",
        thesis="Strong moat, cheap valuation, AI growth",
        score=87.5,
        confidence=0.8,
        bias_flags=[],
        decision="buy",
        position_size=1000.0,
        planned_entry=175.0,
        planned_stop=168.0,
        planned_target=190.0,
    )
    log.add_trade(t1)

    # Trade 2
    t2 = Trade(
        ticker="AMD",
        setup_type="dca",
        thesis="Data center growth, undervalued vs NVDA",
        score=72.0,
        confidence=0.6,
        bias_flags=["anchoring"],
        decision="buy",
        position_size=500.0,
        planned_entry=120.0,
        planned_stop=110.0,
        planned_target=140.0,
    )
    log.add_trade(t2)

    # Layer 4 — үр дүн нэмэх
    log.update_trade_result(t1.id, {
        "actual_entry": 175.5,
        "actual_exit": 189.0,
        "pnl": 77.0,
        "rule_followed": True,
        "emotion": "calm",
        "status": "closed",
    })

    log.update_trade_result(t2.id, {
        "actual_entry": 121.0,
        "actual_exit": 112.0,
        "pnl": -45.0,
        "rule_followed": False,
        "emotion": "fear",
        "status": "closed",
    })

    # Analytics
    print("=" * 50)
    print("TRADE LOG SUMMARY")
    print("=" * 50)
    for k, v in log.summary().items():
        print(f"{k:15}: {v}")

    print("\nSCORE ANALYSIS")
    print("=" * 50)
    for band, stats in log.analyze_by_score().items():
        if stats["count"] > 0:
            print(f"{band}: {stats}")

    print("\nSETUP ANALYSIS")
    print("=" * 50)
    for setup, stats in log.analyze_by_setup().items():
        print(f"{setup}: {stats}")

    print("\nRULE BREAK ANALYSIS")
    print("=" * 50)
    print(log.analyze_rule_break())

    # JSON-д хадгалах
    log.save_to_file("trades.json")
    print("\nHadgalagdsan: trades.json")
