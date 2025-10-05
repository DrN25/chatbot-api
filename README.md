# Chatbot FastAPI

API REST para chatbot con recomendación de artículos científicos usando LLM.

## Instalación

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env`
2. Configura tu `OPENROUTER_API_KEY` en `.env`

## Ejecutar

```powershell
# Desarrollo (con auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Documentación

- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Endpoints

### POST /chat
Interactuar con el chatbot.

**Request:**
```json
{
  "user_input": "Necesito artículos sobre inteligencia artificial",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "action": "search_articles",
  "message": "Realizando búsqueda...",
  "keywords": ["artificial intelligence", "machine learning", "AI"],
  "data": ["artificial intelligence", "machine learning", "AI"]
}
```

## Acciones disponibles

- `search_articles` - Búsqueda de artículos (devuelve keywords)
- `recommend_themes` - Sugerencia de temas relacionados
- `explain` - Explicación de conceptos técnicos
- `summarize` - Resumen de textos
- `generate_metrics` - Generación de métricas (no implementado)
- `chat` - Respuesta conversacional genérica
