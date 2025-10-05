# 📖 Guía de uso - Chatbot API

## 🌐 URL Base
```
http://192.168.1.100:8000
```
*(Reemplaza con la IP real del servidor)*

## 📚 Documentación Interactiva
Abre en tu navegador:
```
http://192.168.1.100:8000/docs
```

---

## 🔌 Endpoints Disponibles

### 1. **POST /chat** - Interactuar con el chatbot

**URL:** `POST http://192.168.1.100:8000/chat`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "user_input": "Tu mensaje aquí",
  "user_id": "opcional-id-usuario"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://192.168.1.100:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Necesito artículos sobre inteligencia artificial",
    "user_id": "usuario123"
  }'
```

**Ejemplo con Python (requests):**
```python
import requests

url = "http://192.168.1.100:8000/chat"
data = {
    "user_input": "Explícame qué es machine learning",
    "user_id": "dev_test"
}

response = requests.post(url, json=data)
print(response.json())
```

**Ejemplo con JavaScript (fetch):**
```javascript
const url = "http://192.168.1.100:8000/chat";

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_input: "Dame temas relacionados con deep learning",
    user_id: "frontend_user"
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 📤 Formato de Respuesta

```json
{
  "action": "search_articles",
  "message": "Realizando búsqueda...",
  "keywords": [
    "machine learning",
    "artificial intelligence",
    "deep learning",
    "algorithms",
    "data science"
  ],
  "data": null
}
```

### Tipos de `action`:

| Action | Descripción | Keywords |
|--------|-------------|----------|
| `search_articles` | Búsqueda de artículos científicos | ✅ Devuelve keywords |
| `recommend_themes` | Sugerencia de temas relacionados | ✅ Devuelve temas |
| `explain` | Explicación de conceptos técnicos | ❌ Usa `message` |
| `summarize` | Resumen de textos | ❌ Usa `message` |
| `generate_metrics` | Métricas (no implementado) | ❌ Usa `message` |
| `chat` | Respuesta conversacional genérica | ❌ Usa `message` |

---

## 🧪 Ejemplos de Uso

### 1. Buscar artículos
```json
{
  "user_input": "Necesito papers sobre CRISPR y edición genética"
}
```

**Respuesta esperada:**
```json
{
  "action": "search_articles",
  "keywords": ["CRISPR", "gene editing", "genetic engineering", ...]
}
```

### 2. Temas relacionados
```json
{
  "user_input": "Dame temas relacionados con blockchain"
}
```

**Respuesta esperada:**
```json
{
  "action": "recommend_themes",
  "keywords": ["distributed ledger", "smart contracts", ...]
}
```

### 3. Explicar conceptos
```json
{
  "user_input": "Explícame qué es reinforcement learning"
}
```

**Respuesta esperada:**
```json
{
  "action": "explain",
  "message": "Reinforcement learning es un tipo de aprendizaje automático..."
}
```

---

## 🔧 Health Check

**URL:** `GET http://192.168.1.100:8000/health`

**Respuesta:**
```json
{
  "status": "healthy",
  "chatbot_ready": true
}
```

---

## ❓ Troubleshooting

### Error: "Connection refused"
- Verifica que el servidor esté corriendo
- Verifica que la IP sea correcta
- Verifica que el puerto 8000 esté abierto en el firewall

### Error: 503 "Chatbot no inicializado"
- El servidor está corriendo pero la API key no se cargó
- Contactar al administrador del servidor

### Error: 500 "Internal Server Error"
- Verifica el formato del JSON
- Revisa los logs del servidor
- Contactar al administrador

---

## 📞 Contacto

**Responsable:** [Tu nombre]  
**Repositorio:** https://github.com/RodrigoAlexander7/pmb-clusterign  
**Docs:** http://192.168.1.100:8000/docs
