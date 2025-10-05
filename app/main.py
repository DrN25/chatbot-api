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
    data: Optional[Any] = None
    
    class Config:
        # Excluir campos None de la respuesta JSON
        exclude_none = True

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
        
        # llm_response ya tiene la estructura correcta: {"action": "keywords/recommendations", "data": {...}}
        # Simplemente retornar la respuesta tal cual
        action = llm_response["action"]
        data = llm_response["data"]
        
        # Para actions de búsqueda con estructura de datos compleja, pasar data directamente
        if action == "keywords":
            # Verificar si hay artículos
            articles = data.get("articles", []) if isinstance(data, dict) else []
            if not articles:
                message = "No pude encontrar artículos relacionados. Intenta reformular tu búsqueda con otros términos."
            else:
                message = "Me muestro articulos que seguramente sean de tu interes"
            
            return ChatResponse(
                action=action,
                message=message,
                data=data
            )
        
        if action == "recommendations":
            # Verificar si hay clusters
            clusters = data.get("recommended_clusters", []) if isinstance(data, dict) else []
            if not clusters:
                message = "No pude encontrar temas relacionados. Intenta pedirlo de otra manera o usa términos más específicos."
            else:
                message = "Seguramente estos temas sean de tu interes"
            
            return ChatResponse(
                action=action,
                message=message,
                data=data
            )
        
        # Para otros actions (chat, explain, etc), data es texto simple
        return ChatResponse(
            action=action,
            message=data if isinstance(data, str) else None,
            data=data if not isinstance(data, str) else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

