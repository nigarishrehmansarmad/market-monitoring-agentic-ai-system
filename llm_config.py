"""
llm_config.py
-------------
Single source of truth for the LLM — Groq API via langchain-groq.

Models available on Groq:
  Fast:    llama-3.1-8b-instant                  — ~150ms/call, good quality
  Best:    llama-3.3-70b-versatile               — ~600ms/call, highest quality
  Llama 4: meta-llama/llama-4-scout-17b-16e-instruct — next-gen, balanced

Caching: responses are cached by prompt hash.
  Redis available → RedisCache (shared, survives restarts)
  Redis down      → SQLiteCache (.llm_cache.db, persists locally)
Cache is set up once at import time. Clear it by flushing Redis or
deleting .llm_cache.db, or set LLM_CACHE=false in .env to disable.

Set LLM_MODEL_ID in .env to override. Requires GROQ_API_KEY in .env.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL_ID       = os.getenv("LLM_MODEL_ID",       "llama-3.3-70b-versatile")
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", 512))
SYSTEM_PROMPT      = "You are a smart city market intelligence assistant. Be concise and analytical."


def _setup_cache() -> None:
    """
    Wire up LangChain's global LLM response cache.
    Tries Redis first (shared across processes), falls back to SQLite (local file).
    Skipped entirely if LLM_CACHE=false in .env.
    """
    if os.getenv("LLM_CACHE", "true").lower() == "false":
        print("[llm_config] LLM cache disabled (LLM_CACHE=false)")
        return

    from langchain.globals import set_llm_cache

    # Try Redis first — already a project dependency
    try:
        import redis as redis_lib
        r = redis_lib.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=False,  # RedisCache needs bytes
        )
        r.ping()
        from langchain_community.cache import RedisCache
        set_llm_cache(RedisCache(r))
        print("[llm_config] LLM cache: Redis")
        return
    except Exception:
        pass

    # SQLite fallback — zero extra infrastructure
    from langchain_community.cache import SQLiteCache
    set_llm_cache(SQLiteCache(database_path=".llm_cache.db"))
    print("[llm_config] LLM cache: SQLite (.llm_cache.db)")


_setup_cache()


@lru_cache(maxsize=1)
def _get_chat_model():
    """Instantiate ChatGroq once and cache it. Raises clearly if API key is missing."""
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Add it to your .env file.\n"
            "Get a free key at https://console.groq.com"
        )
    print(f"[llm_config] ChatGroq ready (model: {LLM_MODEL_ID})")
    return ChatGroq(
        model=LLM_MODEL_ID,
        api_key=api_key,
        max_tokens=LLM_MAX_NEW_TOKENS,
        temperature=0.3,
    )


def get_llm():
    """
    Returns a callable that accepts a prompt string and returns a response string.
    ChatGroq is instantiated once via lru_cache and shared across all agent calls.
    Responses are transparently served from cache on repeated identical prompts.

    Usage:
        llm = get_llm()
        response = llm("Analyze this inventory data: ...")
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    chat = _get_chat_model()

    def invoke(prompt: str) -> str:
        response = chat.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return response.content

    return invoke
