def assess_transaction(transaction):
    score = 0
    reasons = []

    if transaction["new_payee"]:
        score += 20
        reasons.append("New payee")

    if transaction["amount"] >= 10000:
        score += 15
        reasons.append("High-value transfer")

    if "crypto" in transaction["destination_type"].lower():
        score += 15
        reasons.append("Digital-asset-related destination")

    if transaction["recent_transfers"] >= 3:
        score += 15
        reasons.append("Multiple recent transfers")

    purpose = transaction["purpose"].lower()

    if "guaranteed" in purpose:
        score += 15
        reasons.append("Guaranteed-return claim")

    if "online friend" in purpose:
        score += 7
        reasons.append("Online-only relationship")

    if "today" in purpose:
        score += 5
        reasons.append("Payment urgency")

    score = min(score, 100)

    if score >= 75:
        risk_level = "HIGH"
    elif score >= 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "reasons": reasons
    }
