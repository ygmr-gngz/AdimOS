_STATUS_SCORES = {
    "new": 10,
    "contacted": 30,
    "qualified": 70,
    "lost": 0,
}


def score_lead(lead: dict) -> dict:
    score = _STATUS_SCORES.get(lead.get("status", "new"), 10)
    reasons = []

    if lead.get("phone"):
        score += 10
        reasons.append("Telefon mevcut")
    if lead.get("email"):
        score += 10
        reasons.append("E-posta mevcut")

    return {"lead_id": lead["id"], "score": min(score, 100), "reasons": reasons}
