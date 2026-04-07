from __future__ import annotations

import os

DEFAULT_GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
DEFAULT_PROMPT_VERSION = "phase3-v1-groq"
