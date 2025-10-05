from app.services.llm_consult import Consult
from typing import List

class KeywordExtractor:
    """
    Extractor de palabras clave técnicas en inglés usando LLM.
    """
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)

    async def extract(self, text: str) -> List[str]:
        """
        Extrae hasta 5 palabras clave técnicas en inglés del texto.
        
        Args:
            text: Texto de entrada (puede estar en cualquier idioma)
            
        Returns:
            Lista de keywords en inglés (máximo 5)
        """
        system_prompt = (
            "Eres un extractor de palabras clave técnicas.\n"
            "Extrae hasta 5 palabras clave técnicas en INGLÉS del texto que te proporcionen.\n"
            "Las palabras deben ser términos técnicos relevantes para búsqueda científica.\n"
            "Responde SOLO con las palabras separadas por comas, sin numeración ni explicaciones.\n"
            "Ejemplo: artificial intelligence, machine learning, neural networks"
        )
        
        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        # Parsear respuesta
        keywords = [k.strip() for k in content.split(',')]
        return keywords[:5]  # Limitar a 5
