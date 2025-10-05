from app.services.llm_consult import Consult
from typing import List, Dict
import json
import os

class ThemesRecommender:
    """
    Recomendador de temas relacionados usando vocabulario restringido (961 términos).
    Recomienda keywords DIFERENTES a las del input, pero del mismo vocabulario.
    Solo devuelve keywords que existan en keywords.json
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
        Recomienda máximo 5 keywords relacionadas (diferentes al input)
        Retorna: {"action": "recommendations", "data": [...]}
        """
        # Usar TODO el vocabulario (961 keywords) en el prompt
        vocab_str = ", ".join(sorted(self.vocabulary))
        
        system_prompt = f"""Recommend RELATED scientific keywords based on user input using ONLY this vocabulary:
{vocab_str}

TASK:
1. Identify the main concepts in the user's input (translate to English if needed)
2. Find RELATED/SIMILAR keywords from vocabulary (NOT the same as input)
3. Return comma-separated keywords (max 5)

RULES:
- Recommended keywords must be DIFFERENT from input keywords
- Find semantically related terms (e.g., if input is "spaceflight" → recommend "microgravity, astronauts, weightless")
- Return format: word1, word2, word3 (NO brackets, quotes, or JSON)
- If no matches: return empty

EXAMPLES:
Input: "spaceflight" → Output: microgravity, astronauts, weightless, radiation
Input: "coronavirus" → Output: immunogenicity, pathogens, immunity, toxicity
Input: "osteocytes" → Output: bone deterioration, osteogenesis, metabolism, microgravity"""

        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        if not content:
            return []
        
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
        
        return {
            "action": "recommendations",
            "data": validated[:5]
        }
