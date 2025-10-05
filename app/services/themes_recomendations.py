from app.services.llm_consult import Consult
from typing import List

class ThemesRecommender:
    """
    Recomendador de temas relacionados usando LLM.
    """
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)

    async def recommend(self, text: str) -> List[str]:
        system_prompt = ("""You are an assistant that gives recommendations of scientific and technical keywords based on one or more input keywords.
                        The output will be used for searching similarities on academic papers and needs to be in English.
                        The output keywords must be diferent from the input keywords.
                        Independently of the input language, the output keywords must be in English always.
                        Automatically correct spelling mistakes or variants of scientific terms.
                        If the input is empty, return an empty list.
                        Return exactly a Python list with a maximum of 5 keywords, in lowercase, without accents or punctuation.
                        Do not analyze the question, do not add explanations, just extract the keywords."""
                    )
        
        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        # Parsear respuesta
        themes = [t.strip() for t in content.split(',')]
        return themes[:5]  # Limitar a 5
