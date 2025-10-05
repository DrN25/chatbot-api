from app.services.llm_consult import Consult
from app.services.nlp_parser import KeywordExtractor
from app.services.themes_recomendations import ThemesRecommender

class ChatBot:
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)
        # Instanciar las otras clases con la clave API, si es necesario
        self.keyword_extractor = KeywordExtractor(api_key)
        self.themes_recommender = ThemesRecommender(api_key)

    async def _detect_intent(self, user_input: str) -> int:
        system_prompt = (
            "You are an intent classifier for a chatbot with 5 functions:\n"
            "1. Article recommendation (e.g., I want an article on microbiology and DNA)\n"
            "2. Related topic recommendation (e.g., I want topics related to AI and machine learning)\n"
            "3. Personalized summary or highlight keywords/findings\n"
            "4. Explain technical concepts or terms\n"
            "5. Generate metrics and visualizations\n"
            "Try to classify the user input into one of these 5 intents or the most related one.\n"
            "Respond only with the corresponding number. If you don't understand the prompt, respond with 0."
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
