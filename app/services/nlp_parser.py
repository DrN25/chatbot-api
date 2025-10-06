from app.services.llm_consult import Consult
from app.article_recommender import recommend_articles_by_keywords
from typing import List, Dict
import json
import os

class KeywordExtractor:
    """
    Extrae keywords científicas usando vocabulario restringido completo (961 términos).
    Solo devuelve keywords que existan en keywords.json
    El LLM tiene acceso a TODAS las keywords (no hay limitación).
    """
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)
        self.vocabulary = self._load_vocabulary()
        self.vocabulary_lower = {v.lower() for v in self.vocabulary}
    
    def _load_vocabulary(self) -> set:
        """Carga vocabulario desde keywords.json"""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'resources')
        keywords_path = os.path.join(base_path, 'keywords.json')
        
        with open(keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data['keywords']) if isinstance(data, dict) else set(data)

    async def extract(self, text: str) -> Dict[str, any]:
        """
        Extrae máximo 5 keywords del texto usuario y busca artículos relacionados.
        Retorna: {
            "action": "keywords",
            "data": {
                "keywords": [...],
                "articles": [{"pmc_id": "PMC123", "cluster_id": "0", "title": "...", "relevance_score": 0.85}, ...]
            }
        }
        """
        # Usar TODO el vocabulario (961 keywords) en el prompt
        vocab_str = ", ".join(sorted(self.vocabulary))
        
        system_prompt = f"""Extract scientific keywords from user input using ONLY this vocabulary:
{vocab_str}

TASK:
1. Identify ALL scientific concepts in the input (translate to English if needed)
2. Match each concept to vocabulary (exact match, case-insensitive)
3. Return comma-separated keywords (max 5)

RULES:
- Extract ALL relevant concepts, don't skip any
- Return format: word1, word2, word3 (NO brackets, quotes, or JSON)
- If no matches, first try to find related keywords from the vocabulary. If still no close matches, return empty

EXAMPLES:
Input: "spaceflight y metabolismo" → Output: spaceflight, metabolism
Input: "coronavirus, immunogenicity y cardiomyocytes" → Output: coronavirus, immunogenicity, cardiomyocytes
Input: "hello" → Output: (empty)"""

        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        if not content:
            return {
                "action": "keywords",
                "data": {
                    "keywords": [],
                    "articles": []
                }
            }
        
        # Parsear respuesta (manejar CSV o JSON)
        if content.startswith('[') and content.endswith(']'):
            try:
                raw_keywords = [k.strip().lower() for k in json.loads(content)]
            except:
                raw_keywords = [k.strip().lower() for k in content.split(',')]
        else:
            raw_keywords = [k.strip().lower() for k in content.split(',')]
        
        # Validar contra vocabulario y eliminar duplicados
        validated = []
        seen = set()
        
        for keyword in raw_keywords:
            if keyword in seen:
                continue
            
            # Match exacto
            if keyword in self.vocabulary_lower:
                validated.append(keyword)
                seen.add(keyword)
            # Match parcial (substring)
            else:
                matches = [v for v in self.vocabulary_lower if keyword in v or v in keyword]
                if matches and matches[0] not in seen:
                    validated.append(matches[0])
                    seen.add(matches[0])
        
        # Limitar a máximo 5 keywords
        final_keywords = validated[:5]
        
        # Buscar artículos recomendados basados en las keywords
        recommended_articles = []
        if final_keywords:
            articles = recommend_articles_by_keywords(final_keywords, limit=5)
            recommended_articles = [
                {
                    "pmc_id": article["pmc_id"],
                    "cluster_id": article["cluster_id"],
                    "title": article["title"],
                    "relevance_score": article["relevance_score"]
                }
                for article in articles
            ]
        
        return {
            "action": "keywords",
            "data": {
                "keywords": final_keywords,
                "articles": recommended_articles
            }
        }
