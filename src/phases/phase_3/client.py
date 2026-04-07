from __future__ import annotations

import os

from groq import Groq

from src.phases.phase_3.config import DEFAULT_GROQ_MODEL


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        resolved_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError("GROQ_API_KEY is missing in environment/.env")
        self._client = Groq(api_key=resolved_key)
        self.model = model or DEFAULT_GROQ_MODEL

    def complete_json(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You produce valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    def connectivity_smoke_test(self) -> bool:
        prompt = 'Return JSON exactly as {"ok": true}'
        output = self.complete_json(prompt)
        return '"ok"' in output.lower()
