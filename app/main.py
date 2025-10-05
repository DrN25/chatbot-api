from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from app.services.chatbot_entrance import ChatBot

# --- Función para obtener API key ---
def get_api_key() -> str:
    """Obtiene API key desde env o endpoint remoto"""
    env_key = os.getenv("OPENROUTER_API_KEY")
    
    # Si es una URL, hacer request
    if env_key and env_key.startswith("http"):
        try:
            resp = requests.get(env_key, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("message")
        except:
            pass
    elif env_key:
        return env_key
    
    raise ValueError("OPENROUTER_API_KEY no configurada correctamente")

# Cargar API Key (lazy loading para Vercel)
chatbot = None

def get_chatbot():
    """Lazy loading del chatbot para Vercel serverless"""
    global chatbot
    if chatbot is None:
        try:
            api_key = get_api_key()
            chatbot = ChatBot(api_key=api_key)
        except Exception as e:
            print(f"⚠️  Error inicializando chatbot: {e}")
            raise HTTPException(status_code=503, detail=f"Chatbot initialization failed: {str(e)}")
    return chatbot

# --- Modelos Pydantic ---
class ChatRequest(BaseModel):
    user_input: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    action: str
    message: Optional[str] = None
    keywords: Optional[List[str]] = None
    data: Optional[Any] = None

# --- Configuración FastAPI ---
app = FastAPI(
    title="Chatbot API",
    description="API para chatbot con recomendación de artículos científicos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Chatbot API running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    try:
        bot = get_chatbot()
        return {"status": "healthy", "chatbot_ready": True}
    except:
        return {"status": "unhealthy", "chatbot_ready": False}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Endpoint para interactuar con el chatbot.
    
    Ejemplos:
    - "Necesito artículos sobre IA en medicina"
    - "Explícame qué es CRISPR"
    - "Dame temas relacionados con machine learning"
    """
    try:
        bot = get_chatbot()
    except HTTPException as e:
        raise e
    
    try:
        llm_response = await bot.handle_message(request.user_input)
        
        action = llm_response["action"]
        data = llm_response["data"]
        
        response_model = ChatResponse(action=action)
        
        if action == "search_articles" or action == "recommend_themes":
            response_model.message = "Realizando búsqueda..."
            response_model.keywords = data
        elif action == "chat":
            response_model.message = data
        elif action == "summarize" or action == "explain" or action == "generate_metrics":
            response_model.message = data
        
        return response_model
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

