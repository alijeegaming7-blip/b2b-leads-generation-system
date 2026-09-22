"""Conversation Intelligence — parse reply intent/sentiment/urgency."""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from typing import Optional
from app.services.ai import provider as ai

logger = logging.getLogger(__name__)


@dataclass
class ConversationAnalysis:
    intent: str        # interested | not_interested | question | meeting_request | unsubscribe | unknown
    sentiment: str     # positive | negative | neutral
    urgency: str       # high | medium | low
    summary: str
    recommended_action: str
    ai_enriched: bool


_INTENT_PATTERNS = {
    "unsubscribe":      [r"unsubscribe", r"remove me", r"stop emailing", r"opt.?out", r"don.t contact"],
    "not_interested":   [r"not interested", r"no thank", r"don.t need", r"already have", r"we.re good"],
    "meeting_request":  [r"let.s (chat|talk|meet|schedule|call)", r"book a (call|meeting)", r"schedule", r"calendar", r"when (are you|can we)"],
    "question":         [r"\?", r"how much", r"what (is|are)", r"tell me more", r"can you explain", r"more info"],
    "interested":       [r"interested", r"sounds good", r"i.d like", r"please send", r"yes", r"tell me more"],
}

_SENTIMENT_POSITIVE = re.compile(r"great|good|sounds|yes|love|interested|thank|appreciate|perfect|excellent", re.I)
_SENTIMENT_NEGATIVE = re.compile(r"no|not|never|stop|remove|unsubscribe|don.t|hate|waste|spam", re.I)


def _heuristic(reply: str) -> ConversationAnalysis:
    reply_l = reply.lower()

    # Intent
    intent = "unknown"
    for name, patterns in _INTENT_PATTERNS.items():
        if any(re.search(p, reply_l) for p in patterns):
            intent = name
            break

    # Sentiment
    pos = len(_SENTIMENT_POSITIVE.findall(reply))
    neg = len(_SENTIMENT_NEGATIVE.findall(reply))
    sentiment = "positive" if pos > neg else "negative" if neg > pos else "neutral"

    # Urgency
    urgency = "high" if intent == "meeting_request" else "medium" if intent in ("interested", "question") else "low"

    # Action
    actions = {
        "interested":     "Reply promptly — express enthusiasm and propose next step.",
        "not_interested": "Mark as lost. Consider re-engaging in 3 months.",
        "question":       "Answer their question and include a soft call-to-action.",
        "meeting_request":"Book the meeting immediately. Send calendar link.",
        "unsubscribe":    "Remove from outreach list immediately and confirm.",
        "unknown":        "Read reply carefully and respond with relevant information.",
    }

    return ConversationAnalysis(
        intent=intent, sentiment=sentiment, urgency=urgency,
        summary=f"Reply detected as {intent} with {sentiment} sentiment.",
        recommended_action=actions.get(intent, "Review and respond appropriately."),
        ai_enriched=False,
    )


async def analyse(reply_content: str, lead_name: str = "") -> ConversationAnalysis:
    heuristic = _heuristic(reply_content)
    if not ai.AI_AVAILABLE:
        return heuristic

    try:
        result = await ai.complete_json(
            [
                {"role": "system", "content": "You are a B2B sales conversation analyst. Classify this reply and recommend next action. Return JSON only."},
                {"role": "user", "content": f"""Lead: {lead_name}
Reply: {reply_content[:1000]}

Return JSON:
{{"intent":"interested|not_interested|question|meeting_request|unsubscribe|unknown","sentiment":"positive|negative|neutral","urgency":"high|medium|low","summary":"one sentence summary","recommendedAction":"specific next action for sales rep"}}"""},
            ],
            temperature=0.2, max_tokens=300,
            fallback_fn=lambda: {
                "intent": heuristic.intent,
                "sentiment": heuristic.sentiment,
                "urgency": heuristic.urgency,
                "summary": heuristic.summary,
                "recommendedAction": heuristic.recommended_action,
            },
        )
        if result:
            return ConversationAnalysis(
                intent=result.get("intent", heuristic.intent),
                sentiment=result.get("sentiment", heuristic.sentiment),
                urgency=result.get("urgency", heuristic.urgency),
                summary=result.get("summary", heuristic.summary),
                recommended_action=result.get("recommendedAction", heuristic.recommended_action),
                ai_enriched=True,
            )
    except Exception as exc:
        logger.warning(f"AI conversation analysis failed: {exc}")

    return heuristic
