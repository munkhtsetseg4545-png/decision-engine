from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TradeRecord:
    ticker: str
    score: Optional[float]
    pnl: float
    r_multiple: float
    rule_followed: bool
    status: str = "closed"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeRecord":
        return cls(
            ticker=str(data.get("ticker", "")).upper(),
            score=_to_float_or_none(data.get("score")),
            pnl=_to_float(data.get("pnl")),
            r_multiple=_to_float(data.get("r_multiple")),
            rule_followed=_to_bool(data.get("rule_followed", True)),
            status=str(data.get("status", "closed")).lower(),
        )


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_float_or_none(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _closed_trades(trades: List[TradeRecord]) -> List[TradeRecord]:
    return [t for t in trades if t.status == "closed"]


def _wins(trades: List[TradeRecord]) -> List[TradeRecord]:
    return [t for t in trades if t.pnl > 0]


def _losses(trades: List[TradeRecord]) -> List[TradeRecord]:
    return [t for t in trades if t.pnl < 0]


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def calculate_summary(trades: List[TradeRecord]) -> Dict[str, float]:
    closed = _closed_trades(trades)
    wins = _wins(closed)
    losses = _losses(closed)

    total_trades = len(closed)
    win_count = len(wins)
    loss_count = len(losses)

    win_rate_decimal = (win_count / total_trades) if total_trades else 0.0
    loss_rate_decimal = (loss_count / total_trades) if total_trades else 0.0

    avg_win = _avg([t.pnl for t in wins])
    avg_loss = _avg([t.pnl for t in losses])
    avg_r = _avg([t.r_multiple for t in closed])
    total_pnl = sum(t.pnl for t in closed)

    expectancy = (win_rate_decimal * avg_win) - (loss_rate_decimal * abs(avg_loss))

    return {
        "total_trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "win_rate": round(win_rate_decimal * 100, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_r": round(avg_r, 4),
        "total_pnl": round(total_pnl, 2),
        "expectancy": round(expectancy, 2),
        "max_win": round(max([t.pnl for t in wins], default=0.0), 2),
        "max_loss": round(min([t.pnl for t in losses], default=0.0), 2),
    }


def _score_bucket_name(score: Optional[float]) -> str:
    if score is None:
        return "unknown"
    if score >= 90:
        return "90+"
    if score >= 80:
        return "80–89"
    if score >= 70:
        return "70–79"
    return "<70"


def analyze_by_score(trades: List[TradeRecord]) -> Dict[str, Dict[str, float]]:
    closed = _closed_trades(trades)
    buckets: Dict[str, List[TradeRecord]] = {
        "90+": [], "80–89": [], "70–79": [], "<70": [], "unknown": [],
    }
    for trade in closed:
        buckets[_score_bucket_name(trade.score)].append(trade)

    result: Dict[str, Dict[str, float]] = {}
    for bucket_name, bucket_trades in buckets.items():
        if not bucket_trades:
            continue
        wins = _wins(bucket_trades)
        result[bucket_name] = {
            "count": len(bucket_trades),
            "win_rate": round(len(wins) / len(bucket_trades) * 100, 1),
            "avg_pnl": round(_avg([t.pnl for t in bucket_trades]), 2),
            "avg_r": round(_avg([t.r_multiple for t in bucket_trades]), 4),
        }
    return result


def analyze_rule_break(trades: List[TradeRecord]) -> Dict[str, float]:
    closed = _closed_trades(trades)
    followed = [t for t in closed if t.rule_followed]
    broken = [t for t in closed if not t.rule_followed]

    return {
        "followed_count": len(followed),
        "broken_count": len(broken),
        "followed_avg_pnl": round(_avg([t.pnl for t in followed]), 2),
        "broken_avg_pnl": round(_avg([t.pnl for t in broken]), 2),
        "followed_avg_r": round(_avg([t.r_multiple for t in followed]), 4),
        "broken_avg_r": round(_avg([t.r_multiple for t in broken]), 4),
    }


def build_analytics(trade_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    trades = [TradeRecord.from_dict(t) for t in trade_dicts]
    return {
        "summary": calculate_summary(trades),
        "score_analysis": analyze_by_score(trades),
        "rule_break": analyze_rule_break(trades),
    }
