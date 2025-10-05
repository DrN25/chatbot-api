import httpx  # Mejor que requests para llamadas asíncronas
import json

class Consult:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://chatbot-api-two.vercel.app",  # Requerido por OpenRouter
            "X-Title": "Chatbot API"  # Opcional pero recomendado
        }

    async def consult(self, SystemContent: str, UserContent: str):
        data = {
            "model": "google/gemini-2.5-flash-lite-preview-09-2025",
            "messages": [
                {
                    "role": "system",
                    "content": SystemContent
                },
                {
                    "role": "user",
                    "content": UserContent
                }
            ],
        }

        # Usar httpx para llamadas asíncronas, ideal para FastAPI
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, data=json.dumps(data), timeout=60.0)
            response.raise_for_status()
            return response.json()
