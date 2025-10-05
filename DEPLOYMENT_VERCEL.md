# 🚀 Desplegar Chatbot API en Vercel

## 📋 Requisitos previos
- Cuenta en [Vercel](https://vercel.com) (gratis)
- Cuenta en [GitHub](https://github.com) (gratis)
- Git instalado

---

## 🔧 Paso 1: Subir código a GitHub

```powershell
# En la carpeta del proyecto
cd D:\PROYECTOS\BACKEND\Rodrigo\apis\chatbot_fastApi

# Inicializar Git (si no está inicializado)
git init

# Crear .gitignore si no existe
@"
__pycache__/
*.py[cod]
.env
.venv
venv/
*.log
"@ | Out-File -FilePath .gitignore -Encoding utf8

# Agregar archivos
git add .
git commit -m "Initial commit: FastAPI Chatbot"

# Crear repositorio en GitHub (hazlo desde github.com)
# Luego conectar:
git remote add origin https://github.com/TU_USUARIO/chatbot-api.git
git branch -M main
git push -u origin main
```

---

## 🌐 Paso 2: Desplegar en Vercel

### Opción A: Desde la Web (Recomendado)

1. Ve a https://vercel.com/new
2. **Import Git Repository**
3. Selecciona tu repositorio `chatbot-api`
4. **Framework Preset:** Other
5. **Root Directory:** `./` (raíz)
6. **Build Command:** (dejar vacío)
7. **Output Directory:** (dejar vacío)
8. **Install Command:** `pip install -r requirements.txt`

#### Configurar Variables de Entorno:
En la sección **Environment Variables**, agrega:

```
OPENROUTER_API_KEY = sk-or-v1-tu-api-key-aqui
```

9. Click **Deploy**

### Opción B: Desde CLI

```powershell
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Desplegar
vercel

# Seguir las instrucciones:
# - Set up and deploy? Y
# - Which scope? (tu cuenta)
# - Link to existing project? N
# - What's your project's name? chatbot-api
# - In which directory is your code located? ./
```

Agregar variables de entorno:
```powershell
vercel env add OPENROUTER_API_KEY
# Pegar tu API key cuando te lo pida
```

Redesplegar con las env vars:
```powershell
vercel --prod
```

---

## 🧪 Paso 3: Probar el despliegue

Tu API estará en:
```
https://chatbot-api-tu-usuario.vercel.app
```

Pruebas:
```powershell
# Health check
curl https://chatbot-api-tu-usuario.vercel.app/health

# Chat
curl -X POST https://chatbot-api-tu-usuario.vercel.app/chat `
  -H "Content-Type: application/json" `
  -d '{\"user_input\": \"Necesito artículos sobre IA\"}'
```

---

## ⚙️ Configuración Avanzada

### Aumentar timeout (Plan Pro)
Edita `vercel.json`:
```json
{
  "version": 2,
  "functions": {
    "app/main.py": {
      "maxDuration": 60
    }
  }
}
```

### Configurar dominio personalizado
1. En el dashboard de Vercel
2. **Settings → Domains**
3. Agregar tu dominio

---

## 🔄 Actualizaciones Automáticas

Cada vez que hagas `git push`, Vercel desplegará automáticamente:

```powershell
# Hacer cambios en el código
git add .
git commit -m "Actualización: mejoras en el chatbot"
git push

# Vercel detecta el push y despliega automáticamente
```

---

## ⚠️ Limitaciones de Vercel (Plan Gratuito)

| Recurso | Límite |
|---------|--------|
| **Timeout** | 10 segundos |
| **Bandwidth** | 100 GB/mes |
| **Invocations** | 100,000/mes |
| **Build Time** | 6 horas/mes |
| **Serverless Size** | 50 MB |

### ¿Tu chatbot supera el timeout?
Si las respuestas del LLM tardan >10s:

**Solución 1:** Actualizar a Vercel Pro ($20/mes)
- Timeout de 60 segundos
- 1 TB bandwidth

**Solución 2:** Usar modelo LLM más rápido
```python
# En llm_consult.py, cambiar a modelo más rápido:
"model": "meta-llama/llama-3.1-8b-instruct:free"  # Más rápido que Gemini
```

**Solución 3:** Implementar cache agresivo
- Guardar respuestas frecuentes en KV storage
- Usar Redis/Upstash para cache

---

## 📊 Monitoreo

Ver logs en tiempo real:
```powershell
vercel logs chatbot-api --follow
```

Dashboard: https://vercel.com/dashboard

---

## 🔐 Seguridad

### Proteger con API Key (opcional)

Edita `app/main.py`:
```python
from fastapi import Header, HTTPException

@app.post("/chat")
async def chat_with_bot(
    request: ChatRequest,
    x_api_key: str = Header(...)
):
    # Verificar API key
    if x_api_key != os.getenv("CLIENT_API_KEY"):
        raise HTTPException(401, "Invalid API Key")
    
    # ... resto del código
```

Agrega variable de entorno en Vercel:
```
CLIENT_API_KEY = tu-secret-key-para-clientes
```

Tus compañeros deben enviar:
```bash
curl -X POST https://tu-api.vercel.app/chat \
  -H "X-API-Key: tu-secret-key-para-clientes" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "..."}'
```

---

## 🆘 Troubleshooting

### Error: "Build failed"
- Verifica que `requirements.txt` esté correcto
- Asegúrate de que `vercel.json` esté bien formateado

### Error: "Function timeout"
- Usa un modelo LLM más rápido
- Implementa cache
- Actualiza a Vercel Pro

### Error: "Module not found"
- Verifica que todas las dependencias estén en `requirements.txt`
- Asegúrate de que los paths sean relativos

---

## 🔗 URLs Útiles

- **Dashboard:** https://vercel.com/dashboard
- **Docs:** https://vercel.com/docs
- **CLI Docs:** https://vercel.com/docs/cli
- **Pricing:** https://vercel.com/pricing
