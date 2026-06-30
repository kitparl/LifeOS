import httpx

from app.core.config import Settings, get_settings


class OpenAiProvider:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key.strip())

    async def embed(self, text: str) -> list[float]:
        if not self.enabled:
            raise RuntimeError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": self.settings.ai_embedding_model, "input": text},
            )
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]

    async def chat(self, system: str, user_message: str) -> str:
        if not self.enabled:
            raise RuntimeError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.ai_chat_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.4,
                },
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()
