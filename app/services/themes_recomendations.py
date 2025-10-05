from app.services.llm_consult import Consult
from typing import List

class ThemesRecommender:
    """
    Recomendador de temas relacionados usando LLM.
    """
    def __init__(self, api_key: str):
        self.llm_consult = Consult(api_key)

    async def recommend(self, text: str) -> List[str]:
        """
        Sugiere temas relacionados basándose en el texto de entrada.
        
        Args:
            text: Descripción del tema de interés del usuario
            
        Returns:
            Lista de temas relacionados sugeridos
        """
        system_prompt = (
            "Eres un asistente que sugiere temas de investigación relacionados.\n"
            "Dado un tema o área de interés, sugiere 5 temas relacionados específicos "
            "que podrían ser de interés para investigación científica.\n"
            "Responde con los temas separados por comas, en inglés.\n"
            "Ejemplo de salida: deep learning applications, convolutional neural networks, "
            "transfer learning, computer vision, image classification"
        )
        
        response = await self.llm_consult.consult(system_prompt, text)
        content = response['choices'][0]['message']['content'].strip()
        
        # Parsear respuesta
        themes = [t.strip() for t in content.split(',')]
        return themes[:5]  # Limitar a 5
