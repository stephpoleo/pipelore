import re

import ollama

from pipelore.constants import SAFETY_MODEL
from pipelore.config import INJECTION_MAX_LENGTH

_INJECTION_RE = re.compile(
    r"olvida.{0,30}(anterior|instrucciones)"
    r"|ignora.{0,30}(anterior|instrucciones)"
    r"|script.{0,40}(elimine|borre|delete|destruya|drop)"
    r"|(elimine|borre|delete|destruya).{0,30}registros"
    r"|ignore.{0,20}instructions"
    r"|forget.{0,20}(previous|instructions)",
    re.IGNORECASE,
)


def is_safe(question: str) -> dict:
    """
    Clasifica si una pregunta es segura usando un enfoque híbrido de 3 capas.

    Check 1: longitud — rechaza inputs excesivamente largos sin gastar LLM.
    Check 2: regex — detecta prompt injection y código destructivo.
    Check 3: llama-guard3 — clasifica contenido dañino (sexual, odio, armas, etc.).

    Returns:
        {"safe": bool, "reason": str | None}
        reason: None | "prompt_too_long" | "injection_pattern" | "content_policy"
    """
    if len(question) > INJECTION_MAX_LENGTH:
        return {"safe": False, "reason": "prompt_too_long"}

    if _INJECTION_RE.search(question):
        return {"safe": False, "reason": "injection_pattern"}

    response = ollama.chat(
        model=SAFETY_MODEL,
        messages=[{"role": "user", "content": question}],
        options={"temperature": 0.0, "num_predict": 20},
    )
    label = response["message"]["content"].strip().lower()
    if label.startswith("unsafe"):
        return {"safe": False, "reason": "content_policy"}
    return {"safe": True, "reason": None}
