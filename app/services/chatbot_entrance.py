from app.services.llm_consult import Consult
from app.services.nlp_parser import KeywordExtractor
from app.services.themes_recomendations import ThemesRecommender
from app.services.article_analyzer import analyze_article, extract_pmc_id_from_query, find_article_by_name

class ChatBot:
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)
        # Instanciar las otras clases con la clave API, si es necesario
        self.keyword_extractor = KeywordExtractor(api_key)
        self.themes_recommender = ThemesRecommender(api_key)

    async def _detect_intent(self, user_input: str) -> int:
        system_prompt = (
            "You are an intent classifier for a chatbot with 5 functions:\n\n"
            
            "1. Article recommendation - User wants to FIND articles by topic\n"
            "   Examples: 'I want articles on DNA', 'Show me papers about AI'\n\n"
            
            "2. Topic recommendation - User wants RELATED THEMES/CLUSTERS\n"
            "   Examples: 'Topics related to machine learning', 'Similar themes to neuroscience'\n\n"
            
            "3. Article analysis - User asks about a SPECIFIC article (PMC number OR article title)\n"
            "   CRITICAL: If you see 'PMC' + numbers → ALWAYS intent 3\n"
            "   ALSO: If user mentions analyzing/summarizing a SPECIFIC article by its title → intent 3\n"
            "   Examples: 'Summarize PMC2910419', 'Analyze the otolith development article', 'What methodology did the biofilm formation study use?'\n"
            "   Keywords: summarize/analyze/explain + (PMC OR specific article title), methodology + article, results + article\n\n"
            
            "4. Explain concepts - User asks about GENERAL scientific concepts (NOT a specific article)\n"
            "   Examples: 'What is CRISPR?', 'Explain neural networks', 'What is biofilm?'\n\n"
            
            "5. Metrics/visualizations - User wants stats or graphs\n"
            "   Examples: 'Show me statistics', 'Generate a chart'\n\n"
            
            "RULES:\n"
            "- PMC + numbers → ALWAYS return 3\n"
            "- 'Summarize/analyze [specific article title]' → return 3\n"
            "- 'What is [general concept]' → return 4\n"
            "- If asking for articles by topic (no specific article) → return 1\n"
            "- If asking for related topics/themes → return 2\n"
            "- If unclear → return 0\n\n"
            
            "Respond ONLY with the number (0-5). No explanation."
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
            result = await self.keyword_extractor.extract(user_input)
            # result ya tiene la estructura completa: {"action": "keywords", "data": {"keywords": [...], "articles": [...]}}
            return result  # Retornar directamente sin re-envolver
            
        elif intent == 2:
            result = await self.themes_recommender.recommend(user_input)
            # result ya tiene la estructura completa: {"action": "recommendations", "data": [...]}
            return result  # Retornar directamente sin re-envolver

        elif intent == 3:
            # Article analysis - Try to find PMC ID or article by name
            # Step 1: Try to extract direct PMC ID from query
            pmc_id = extract_pmc_id_from_query(user_input)
            
            # Step 2: If no direct PMC found, try to find article by name using LLM
            if pmc_id is None:
                print(f"[INFO] No direct PMC found. Attempting to find article by name...")
                pmc_id = await find_article_by_name(user_input, self.llm_consult)
                
                if pmc_id:
                    print(f"[SUCCESS] Found article by name: {pmc_id}")
                else:
                    print(f"[ERROR] Could not find article by name")
                    return {
                        "action": "llm_analysis",
                        "data": {
                            "error": "Please provide a PMC article ID (e.g., PMC2910419) or mention the article title more clearly"
                        }
                    }
            
            # Step 3: Analyze article with the found PMC ID
            result = await analyze_article(user_input, pmc_id, self.llm_consult)
            return result  # Return directly without re-wrapping
            
        elif intent == 4:
            system_prompt = (
                "You are an expert assistant that explains concepts, technical terms, or acronyms "
                "in a clear and concise manner."
            )
            response = await self.llm_consult.consult(system_prompt, user_input)
            output = response['choices'][0]['message']['content'].strip()
            action = "explain"
            
        elif intent == 5:
            output = f"Generating metrics and visualizations for: {user_input}"
            action = "generate_metrics"
            
        else:
            output = "I didn't understand your request. Please try rephrasing it."
            action = "chat"
        
        return {
            "action": action,
            "data": output
        }
