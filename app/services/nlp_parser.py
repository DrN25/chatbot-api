from app.services.llm_consult import Consult
from typing import List

class KeywordExtractor:
    """
    Extractor de palabras clave técnicas en inglés usando LLM.
    """
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)

    async def extract(self, text: str) -> List[str]:
        system_prompt = ("""You are an assistant that extracts only scientific and technical keywords from academic or technical texts.
                        Consider that the output will be used for searching similarities on academic papers.
                        Automatically correct spelling mistakes or variants of scientific terms.
                        The text can be in English or any other language.
                        Independently of the input language, the output keywords must be in English always.
                        Ignore generic or common words (such as 'research', 'articles', 'information').
                        First, identify the keywords. After that, convert all terms to their equivalent technical English, not literal translations.
                        If the text does not contain scientific or technical information, return an empty list.
                        Return exactly a Python list with a maximum of 5 keywords, in lowercase, without accents or punctuation.
                        Do not analyze the question, do not add explanations, just extract the keywords."""
                    )
        
        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        # Parsear respuesta
        keywords = [k.strip() for k in content.split(',')]
        return keywords[:5]  # Limitar a 5
