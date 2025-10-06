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
            "You are an intent classifier for a chatbot with 4 functions:\n\n"
            
            "1. Article recommendation - User wants to FIND/RECOMMEND ARTICLES by topic\n"
            "   KEYWORDS: 'article', 'articles', 'paper', 'papers', 'publication', 'study', 'research'\n"
            "   Examples: 'I want articles on DNA', 'Show me papers about AI', 'Recommend articles about CRISPR', 'Find studies on cancer'\n"
            "   Pattern: [verb: want/show/find/recommend/search] + [ARTICLES/PAPERS/STUDIES] + [about/on] + [topic]\n\n"
            
            "2. Topic/Theme recommendation - User wants RELATED TOPICS/THEMES/CLUSTERS (NO mention of articles)\n"
            "   KEYWORDS: 'topic', 'topics', 'theme', 'themes', 'cluster', 'related areas', 'similar fields'\n"
            "   Examples: 'Topics related to machine learning', 'Similar themes to neuroscience', 'What themes are related to genomics?'\n"
            "   Pattern: [verb: show/recommend/what] + [TOPICS/THEMES/CLUSTERS] + [related to/about] + [subject]\n\n"
            
            "3. Article analysis - User asks about a SPECIFIC article (PMC number OR article title)\n"
            "   CRITICAL: If you see 'PMC' + numbers → ALWAYS intent 3\n"
            "   ALSO: If user mentions analyzing/summarizing a SPECIFIC article by its title → intent 3\n"
            "   Examples: 'Summarize PMC2910419', 'Analyze the otolith development article', 'What methodology did the biofilm formation study use?'\n"
            "   Keywords: summarize/analyze/explain + (PMC OR specific article title), methodology + article, results + article\n\n"
            
            "4. General academic questions - User asks about scientific concepts, explanations, definitions (NOT specific articles)\n"
            "   Examples: 'What is CRISPR?', 'Explain neural networks', 'What is biofilm?', 'How does DNA replication work?'\n\n"
            
            "PRIORITY RULES (in order):\n"
            "1. PMC + numbers → ALWAYS return 3\n"
            "2. Words 'article/articles/paper/papers/study/studies/publication/research' in request → return 1\n"
            "3. Words 'topic/topics/theme/themes/cluster/clusters' (NO article words) → return 2\n"
            "4. 'Summarize/analyze [specific article title]' → return 3\n"
            "5. 'What is [general concept]' or 'How does [process] work?' → return 4\n"
            "6. If unclear → return 0\n\n"
            
            "CRITICAL: If user says 'articles' or 'papers' or 'studies' → ALWAYS prioritize intent 1 over intent 2\n"
            "Only choose intent 2 if they explicitly ask for 'topics' or 'themes' WITHOUT mentioning articles/papers\n\n"
            
            "Respond ONLY with the number (0-4). No explanation."
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
            # General academic questions - free query to LLM
            system_prompt = (
                "You are an expert scientific assistant specialized in biology, biomedicine, and related fields.\n\n"
                "CRITICAL: ALWAYS respond in English, regardless of the input language.\n\n"
                "INSTRUCTIONS:\n"
                "1. Answer the user's question clearly and concisely\n"
                "2. Use accessible scientific language\n"
                "3. Be brief but informative (2-4 sentences for definitions, 4-6 for explanations)\n"
                "4. Use PLAIN TEXT ONLY - NO LaTeX formatting (no $, \\text{}, \\gamma, etc.)\n"
                "5. If you don't know, say so honestly\n"
                "6. Focus on biological and biomedical sciences\n\n"
                "Provide a direct, helpful answer in English."
            )
            response = await self.llm_consult.consult(system_prompt, user_input)
            output = response['choices'][0]['message']['content'].strip()
            action = "others"
            
        else:
            output = "I didn't understand your request. Please try rephrasing it."
            action = "chat"
        
        return {
            "action": action,
            "data": output
        }
