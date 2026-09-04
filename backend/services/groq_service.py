import logging
from fastapi import HTTPException
from groq import Groq, GroqError

from config import settings

logger = logging.getLogger("ai-devops-assistant")

groq_client = Groq(api_key=settings.groq_api_key or "missing")


def ask_groq(system_prompt: str, user_prompt: str) -> str:
    try:
        completion = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except GroqError as e:
        raise HTTPException(502, f"AI provider error: {e}")

    return completion.choices[0].message.content or ""


def check_model_available():
    """Best-effort startup check: confirm the configured GROQ_MODEL is one
    this API key can actually use. Logs a loud warning instead of failing
    request-by-request the way the previous code did — a deprecated or
    inaccessible model used to only surface as a 502 on the user's first
    Chat/Log Analyzer/CI-CD/Dockerfile request."""
    if not settings.groq_api_key:
        return

    try:
        available = {m.id for m in groq_client.models.list().data}
    except Exception as e:
        logger.warning("Could not verify GROQ_MODEL availability at startup: %s", e)
        return

    if settings.groq_model not in available:
        logger.warning(
            "GROQ_MODEL=%s is not available to this Groq API key. "
            "AI-backed endpoints will fail until this is fixed. "
            "Models available to this key: %s",
            settings.groq_model,
            ", ".join(sorted(available)) or "(none)",
        )
