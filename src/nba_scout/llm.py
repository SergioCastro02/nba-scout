"""Chat model factory.

Both providers return a LangChain `BaseChatModel`, so every graph node is written
against one interface. `bedrock` is the deployed path; `anthropic` is dev.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from .config import get_settings


@lru_cache
def get_chat_model() -> BaseChatModel:
    s = get_settings()

    if s.llm_provider == "bedrock":
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(
            model=s.bedrock_model,
            region_name=s.aws_region,
            temperature=s.llm_temperature,
            max_tokens=s.llm_max_tokens,
        )

    if s.llm_provider == "google":
        import logging

        from langchain_google_genai import ChatGoogleGenerativeAI

        # LangChain drives tool calls itself; silence the SDK's AFC recommendation notice.
        logging.getLogger("google_genai.models").setLevel(logging.ERROR)

        return ChatGoogleGenerativeAI(
            model=s.google_model,
            api_key=s.google_api_key,
            temperature=s.llm_temperature,
            max_tokens=s.llm_max_tokens,
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=s.anthropic_model,
        api_key=s.anthropic_api_key,
        temperature=s.llm_temperature,
        max_tokens=s.llm_max_tokens,
    )
