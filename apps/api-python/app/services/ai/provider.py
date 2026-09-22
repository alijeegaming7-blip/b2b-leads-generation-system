"""
AI Provider — LiteLLM wrapper.
Priority: Grok (xAI) → OpenAI → Local (Ollama/LM Studio) → deterministic fallback.
Never raises to callers — always returns a value or falls back gracefully.
"""
from __future__ import annotations
import json
import logging
import time
from typing import Any, Callable, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Resolve active provider at import time ─────────────────────────────────
_MODEL: str = ""
_KWARGS: dict = {}


def _build() -> tuple[str, dict]:
    if settings.GROK_API_KEY:
        return "xai/grok-beta", {"api_key": settings.GROK_API_KEY}
    if settings.OPENAI_API_KEY:
        kw: dict = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            kw["api_base"] = settings.OPENAI_BASE_URL
        return f"openai/{settings.OPENAI_MODEL}", kw
    if settings.LOCAL_AI_BASE_URL:
        return f"openai/{settings.LOCAL_AI_MODEL}", {
            "api_key": "local",
            "api_base": settings.LOCAL_AI_BASE_URL,
        }
    return "", {}


_MODEL, _KWARGS = _build()
AI_AVAILABLE: bool = bool(_MODEL)

if AI_AVAILABLE:
    logger.info(f"AI provider ready: {_MODEL}")
else:
    logger.warning(
        "No AI provider configured — set GROK_API_KEY, OPENAI_API_KEY, or LOCAL_AI_BASE_URL. "
        "All AI calls will use deterministic fallbacks."
    )


# ── Core completion function ───────────────────────────────────────────────

async def complete(
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 2000,
    json_mode: bool = False,
    fallback_fn: Optional[Callable[[], str]] = None,
) -> str:
    """Call AI and return text. On any error returns fallback or empty string."""
    if not AI_AVAILABLE:
        return fallback_fn() if fallback_fn else ""

    try:
        import litellm  # deferred so startup never fails if litellm has issues
        litellm.suppress_debug_info = True

        kwargs: dict = dict(_KWARGS)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await litellm.acompletion(
            model=_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error(f"AI completion failed ({_MODEL}): {exc}")
        return fallback_fn() if fallback_fn else ""


async def complete_json(
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 2000,
    fallback_fn: Optional[Callable[[], Any]] = None,
) -> Any:
    """Complete and parse JSON. Returns parsed dict/list or fallback or None."""

    def _fallback_str() -> str:
        if fallback_fn:
            fb = fallback_fn()
            return json.dumps(fb) if not isinstance(fb, str) else fb
        return "{}"

    raw = await complete(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=True,
        fallback_fn=_fallback_str,
    )

    # Strip markdown code fences if model adds them
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse AI JSON — using fallback")
        return fallback_fn() if fallback_fn else None


async def ping() -> dict:
    """Health-check the configured provider."""
    if not AI_AVAILABLE:
        return {"ok": False, "provider": "none", "model": "none"}
    t0 = time.monotonic()
    try:
        import litellm
        litellm.suppress_debug_info = True
        await litellm.acompletion(
            model=_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            **_KWARGS,
        )
        return {
            "ok": True,
            "provider": _MODEL.split("/")[0],
            "model": _MODEL,
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }
    except Exception as exc:
        return {"ok": False, "provider": _MODEL.split("/")[0], "model": _MODEL, "error": str(exc)}
