import httpx

from app.core.config import Settings, get_settings

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
EMBED_TIMEOUT_SECONDS = 60.0
CHAT_TIMEOUT_SECONDS = 120.0
DEFAULT_CHAT_TEMPERATURE = 0.4


class OpenAiProvider:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key.strip())

    async def embed(self, text: str) -> list[float]:
        if not self.enabled:
            raise RuntimeError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=EMBED_TIMEOUT_SECONDS) as client:
            res = await client.post(
                OPENAI_EMBEDDINGS_URL,
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": self.settings.ai_embedding_model, "input": text},
            )
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]

    async def chat(self, system: str, user_message: str) -> str:
        if not self.enabled:
            raise RuntimeError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT_SECONDS) as client:
            res = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.ai_chat_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": DEFAULT_CHAT_TEMPERATURE,
                },
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()
