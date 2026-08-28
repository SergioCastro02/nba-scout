"""Small helpers shared by graph nodes."""

from __future__ import annotations

from typing import Any


def message_text(response: Any) -> str:
    """Extract plain text from a LangChain message across content shapes."""
    text = getattr(response, "text", None)
    if isinstance(text, str):  # langchain-core 1.x property (may be a callable str subclass)
        return str(text)
    if callable(text):  # older API where .text was a plain method
        return text()
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)
