def get_position_size(score: float, max_position: float) -> float:
    if score >= 85:
        pct = 10.0
    elif score >= 75:
        pct = 7.0
    elif score >= 65:
        pct = 5.0
    elif score >= 55:
        pct = 3.0
    else:
        pct = 0.0
    return min(pct, max_position)


def get_action(score: float) -> str:
    if score >= 85:
        return "BUY"
    elif score >= 70:
        return "SMALL POSITION"
    else:
        return "NO ACTION"


def get_execution(score: float, position_value: float, capital: float) -> str:
    action = get_action(score)

    if action == "NO ACTION":
        return "Энэ хувьцааг авахгүй. Score хэт бага."

    if capital == 0:
        if score >= 85:
            return "BUY — Capital тохируулаагүй байна. Settings-д capital оруулна уу."
        return "SMALL POSITION — Capital тохируулаагүй байна. Settings-д capital оруулна уу."

    if position_value > 5000:
        return "DCA — 3-5 удаа хуваан авах"
    elif position_value > 1000:
        return "2 алхмаар авах"
    else:
        return "Нэг удаа авах"


def calculate_decision(score: float, capital: float, max_position: float) -> dict:
    size_pct = get_position_size(score, max_position)
    position_value = capital * (size_pct / 100)
    action = get_action(score)
    execution = get_execution(score, position_value, capital)

    risk_ok = size_pct <= max_position
    risk_status = "OK" if risk_ok else f"Position хэт том — max {max_position}%"

    warnings = []
    if capital == 0:
        warnings.append("⚠ Capital тохируулаагүй — Settings-д оруулна уу")

    return {
        "action": action,
        "size_pct": round(size_pct, 1),
        "position_value": round(position_value, 2),
        "execution": execution,
        "risk_status": risk_status,
        "risk_ok": risk_ok,
        "warnings": warnings,
    }
