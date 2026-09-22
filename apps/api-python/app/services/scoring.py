"""Simple heuristic lead scorer — no AI, no external calls needed."""
from __future__ import annotations


def score_lead(raw: dict) -> dict:
    score = 0
    review_count = raw.get("review_count") or 0
    phone = raw.get("phone", "") or ""
    email = raw.get("email", "") or ""
    website = raw.get("website", "") or ""
    rating_str = str(raw.get("rating", "") or "")
    issues = raw.get("issues_found", []) or []

    # Review count signals active business
    if review_count >= 100: score += 25
    elif review_count >= 30: score += 15
    elif review_count >= 5:  score += 8

    # Contact availability
    if phone: score += 15
    if email: score += 20

    # Issues detected = opportunity (agent found problems to pitch against)
    score += min(len(issues) * 8, 24)

    # Rating signal
    try:
        r = float(rating_str)
        if 3.5 <= r <= 4.5: score += 10   # engaged but not perfect
        elif r > 4.5:        score += 5
    except Exception:
        pass

    # No website = warm website-dev lead
    if not website: score += 12

    # Cap at 100
    score = min(score, 100)

    if score >= 70:   priority = "HIGH"
    elif score >= 45: priority = "MEDIUM"
    else:             priority = "LOW"

    return {
        "score": score,
        "icp_fit_score": min(score + 5, 100),
        "intent_score": min(score - 5, 100),
        "priority": priority,
    }
