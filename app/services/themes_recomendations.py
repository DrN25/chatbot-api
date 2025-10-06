from app.services.llm_consult import Consult
from app.cluster_recommender import recommend_cluster_by_keywords
from typing import List, Dict
import json
import os

class ThemesRecommender:
    """
    Recomendador de clusters relacionados usando keywords extraídas del input.
    Extrae keywords del input y encuentra el cluster más relevante.
    Retorna información del cluster con mejor match.
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

    async def recommend(self, text: str) -> Dict[str, any]:
        """
        Extrae keywords del input y recomienda los clusters más relacionados.
        
        Retorna: {
            "action": "recommendations", 
            "data": {
                "input_keywords": ["keyword1", "keyword2", ...],
                "recommended_clusters": [
                    {
                        "cluster_id": "23",
                        "relevance_score": 0.85,
                        "matched_keywords": [...],
                        "total_keywords_in_cluster": 45
                    },
                    ...
                ]
            }
        }
        """
        # Paso 1: Extraer keywords del input usando LLM
        vocab_str = ", ".join(sorted(self.vocabulary))
        
        system_prompt = f"""Extract scientific keywords from user input using ONLY this vocabulary:
{vocab_str}

TASK:
1. First, identify the SCIENTIFIC CONCEPT in the user's language (Spanish/English/any)
2. Translate the concept to its SCIENTIFIC ENGLISH EQUIVALENT (not literal translation)
3. Match to vocabulary (exact match, case-insensitive)
4. Return comma-separated keywords (max 5)

- Use scientific terminology, not literal word-by-word translation

RULES:
- Identify ALL relevant scientific concepts, don't skip any
- Translate to scientific English before matching
- Return format: word1, word2, word3 (NO brackets, quotes, or JSON)
- If no matches: return empty

EXAMPLES:
Input: "adn y metabolismo" → Output: dna, metabolism
Input: "temas sobre adn" → Output: dna
Input: "spaceflight y metabolismo" → Output: spaceflight, metabolism
Input: "coronavirus, immunogenicity y cardiomyocytes" → Output: coronavirus, immunogenicity, cardiomyocytes
Input: "células y proteínas" → Output: cell, protein
Input: "hello" → Output: (empty)"""

        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        if not content:
            return {
                "action": "recommendations",
                "data": {
                    "input_keywords": [],
                    "recommended_clusters": []
                }
            }
        
        # Parsear respuesta
        if content.startswith('[') and content.endswith(']'):
            try:
                raw_keywords = [k.strip().lower() for k in json.loads(content)]
            except:
                raw_keywords = [k.strip().lower() for k in content.split(',')]
        else:
            raw_keywords = [k.strip().lower() for k in content.split(',')]
        
        # Validar contra vocabulario
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
        
        input_keywords = validated[:5]
        
        # Paso 2: Buscar TOP 5 clusters más relevantes usando las keywords extraídas
        recommended_clusters = []
        
        if input_keywords:
            clusters = recommend_cluster_by_keywords(input_keywords, limit=5)
            recommended_clusters = clusters  # Ya viene como lista ordenada
        
        return {
            "action": "recommendations",
            "data": {
                "input_keywords": input_keywords,
                "recommended_clusters": recommended_clusters
            }
        }

