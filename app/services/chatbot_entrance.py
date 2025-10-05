from app.services.llm_consult import Consult
from app.services.nlp_parser import KeywordExtractor
from app.services.themes_recomendations import ThemesRecommender

class ChatBot:
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)
        # Instanciar las otras clases con la clave API, si es necesario
        self.keyword_extractor = KeywordExtractor(api_key)
        self.themes_recommender = ThemesRecommender(api_key)
        
        # Elimina la lógica de historial
        # self._local_history = [] 

    async def _detect_intent(self, user_input: str) -> int:
        system_prompt = (
            "Eres un clasificador de intenciones para un chatbot con 5 funciones:\n"
            "1. Recomendación de artículos (ej: Deseo un artículo sobre microbiología y ADN)\n"
            "2. Recomendación de temas relacionados (ej: Quiero temas relacionados a IA y machine learning)\n"
            "3. Resumen personalizado o resaltar palabras clave/hallazgos\n"
            "4. Explicar conceptos o términos técnicos\n"
            "5. Generar métricas y visualizaciones\n"
            "Intenta clasificar la entrada del usuario en una de estas 5 intenciones o a la mas relacionada.\n"
            "Responde solo con el número correspondiente. Si no entiendes la solicitud, responde con 0."
        )
        response = await self.llm_consult.consult(system_prompt, user_input)
        content = response['choices'][0]['message']['content'].strip()
        try:
            intent_number = int(content)
        except ValueError:
            intent_number = 0
        return intent_number

    async def handle_message(self, user_input: str):
        intent = await self._detect_intent(user_input)

        output = None
        action = "chat" # Acción por defecto
        
        # Aquí se devolverían los datos estructurados, no solo texto
        if intent == 1:
            keywords = await self.keyword_extractor.extract(user_input)
            output = keywords
            action = "search_articles" # Nueva acción para el frontend
            
        elif intent == 2:
            keywords = await self.themes_recommender.recommend(user_input)
            output = keywords
            action = "recommend_themes" # Nueva acción para el frontend

        elif intent == 3:
            # Ejemplo: Resumir un texto (el texto real vendría de otra fuente)
            article_txt_test = "..." # Reemplazar con el texto real
            system_prompt = "..."
            response = await self.llm_consult.consult(system_prompt, article_txt_test)
            output = response['choices'][0]['message']['content'].strip()
            action = "summarize"
            
        elif intent == 4:
            system_prompt = (
                "Eres un asistente experto que explica conceptos, términos técnicos o siglas "
                "de manera clara y concisa."
            )
            response = await self.llm_consult.consult(system_prompt, user_input)
            output = response['choices'][0]['message']['content'].strip()
            action = "explain"
            
        elif intent == 5:
            output = f"Generando métricas y visualizaciones para: {user_input}"
            action = "generate_metrics"
            
        else:
            output = "No entendí tu solicitud, por favor vuelve a escribirla."
            action = "chat"
        
        return {
            "action": action,
            "data": output
        }
