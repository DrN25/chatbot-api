"""
Article Analyzer Service
Analyzes scientific articles from PMC database using LLM
Handles different levels of analysis based on user intent
"""

import json
import os
from typing import Dict, Any, List, Optional
from app.services.llm_consult import Consult
import asyncio


# Global LLM client (will be initialized when needed)
_llm_client = None


def get_llm_client():
    """Get or create LLM client"""
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        _llm_client = Consult(api_key)
    return _llm_client


def load_article_json(pmc_id: str) -> Optional[Dict[str, Any]]:
    """
    Load article JSON from resources/sections directory
    
    Args:
        pmc_id: PMC identifier (e.g., "PMC2910419")
    
    Returns:
        Dict with article sections or None if not found
    """
    # Remove PMC prefix if user included it
    clean_id = pmc_id.upper().replace("PMC", "")
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "resources",
        "sections",
        f"PMC{clean_id}.json"
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def detect_analysis_type(user_query: str) -> str:
    """
    Detect which type of analysis the user wants (3.1, 3.2, 3.3, or 3.5)
    
    Args:
        user_query: User's question about the article
    
    Returns:
        Analysis type code: "quick_summary", "full_analysis", "methodology", or "free_query"
    """
    query_lower = user_query.lower()
    
    # 3.1 - Quick summary keywords
    quick_keywords = ["resume", "summary", "summarize", "quick", "brief", "overview", "qué trata", "de qué habla"]
    
    # 3.3 - Methodology keywords
    method_keywords = ["method", "metodología", "cómo", "how", "procedure", "técnica", "technique", "resultados", "results"]
    
    # 3.2 - Full analysis keywords
    full_keywords = ["análisis completo", "full analysis", "detalle", "detail", "explain", "explica", "conclusión", "conclusion"]
    
    # Check for quick summary
    if any(keyword in query_lower for keyword in quick_keywords):
        return "quick_summary"
    
    # Check for methodology
    if any(keyword in query_lower for keyword in method_keywords):
        return "methodology"
    
    # Check for full analysis
    if any(keyword in query_lower for keyword in full_keywords):
        return "full_analysis"
    
    # Default: free query (3.5)
    return "free_query"


def build_article_payload(article_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """
    Build optimized article payload based on analysis type
    Avoids sending massive REFERENCIAS array
    
    Args:
        article_data: Complete article JSON
        analysis_type: Type of analysis requested
    
    Returns:
        Optimized payload with only necessary sections
    """
    payload = {}
    
    if analysis_type == "quick_summary":
        # 3.1 - TITLE + ABSTRACT (~1.5K tokens)
        payload["TITLE"] = article_data.get("TITLE", [])
        payload["ABSTRACT"] = article_data.get("ABSTRACT", [])
    
    elif analysis_type == "full_analysis":
        # 3.2 - TITLE + ABSTRACT + INTRO + CONCL + first 5 references (~5K tokens)
        payload["TITLE"] = article_data.get("TITLE", [])
        payload["ABSTRACT"] = article_data.get("ABSTRACT", [])
        payload["INTRO"] = article_data.get("INTRO", [])
        payload["CONCL"] = article_data.get("CONCL", [])
        
        # Only titles from REF (not full REFERENCIAS)
        ref_titles = article_data.get("REF", [])
        payload["REFERENCE_TITLES"] = ref_titles[:5] if ref_titles else []
    
    elif analysis_type == "methodology":
        # 3.3 - TITLE + ABSTRACT + METHODS + RESULTS (~7K tokens)
        payload["TITLE"] = article_data.get("TITLE", [])
        payload["ABSTRACT"] = article_data.get("ABSTRACT", [])
        payload["METHODS"] = article_data.get("METHODS", [])
        payload["RESULTS"] = article_data.get("RESULTS", [])
    
    else:  # free_query
        # 3.5 - Everything EXCEPT full REFERENCIAS array (~15K tokens)
        # Send only REF (titles) instead of REFERENCIAS (full details)
        for key in article_data.keys():
            if key == "REFERENCIAS":
                # Skip the massive REFERENCIAS array completely
                continue
            elif key == "REF":
                # Include REF titles (much smaller)
                payload["REFERENCE_TITLES"] = article_data.get("REF", [])
            else:
                payload[key] = article_data.get(key, [])
    
    return payload


async def analyze_article(user_query: str, pmc_id: str) -> Dict[str, Any]:
    """
    Main function to analyze an article based on user query
    
    Args:
        user_query: User's question about the article
        pmc_id: PMC article identifier
    
    Returns:
        Dict with action, analysis result, and optional error
    """
    # Load article data
    article_data = load_article_json(pmc_id)
    
    if article_data is None:
        return {
            "action": "llm_analysis",
            "error": f"Article {pmc_id} not found in database",
            "data": None
        }
    
    # Detect analysis type
    analysis_type = detect_analysis_type(user_query)
    
    # Build optimized payload (NO massive REFERENCIAS)
    article_payload = build_article_payload(article_data, analysis_type)
    
    # Create analysis prompt
    system_prompt = """You are a scientific research assistant in a chatbot interface.

CRITICAL INSTRUCTIONS:
1. Answer the user's question based ONLY on the article data provided below
2. Be EXTREMELY CONCISE - this is a chatbot with limited display space
3. Keep responses SHORT:
   - Summaries: 2-3 sentences maximum
   - Methodology: 3-4 sentences maximum
   - Detailed questions: 4-6 sentences maximum
4. Use clear, accessible scientific language
5. Focus ONLY on KEY findings - no filler text
6. If the data doesn't contain the answer, say so briefly
7. DO NOT add disclaimers, apologies, or meta-commentary

RESPONSE FORMAT (MUST BE VALID JSON):
{
    "analysis": "Your concise answer here (2-6 sentences max)",
    "key_points": ["key point 1", "key point 2", "key point 3"]
}

EXAMPLE GOOD RESPONSES:

For "Summarize the article":
{
    "analysis": "This study examines X in Y population. The researchers found A and B using method C. Results showed significant D with implications for E.",
    "key_points": ["Main finding 1", "Main finding 2", "Main methodology"]
}

For "What methodology was used?":
{
    "analysis": "The study used a randomized controlled trial with N participants. Data was collected via X and analyzed using Y statistical methods. Primary outcome was Z.",
    "key_points": ["Study design", "Sample size and population", "Analysis methods"]
}

Remember: BE BRIEF. Users want quick, clear answers, not academic essays."""
    
    user_content = f"""USER QUESTION: {user_query}

ARTICLE DATA:
{json.dumps(article_payload, indent=2, ensure_ascii=False)}"""
    
    # Call LLM
    try:
        llm_client = get_llm_client()
        llm_response_json = await llm_client.consult(system_prompt, user_content)
        
        # Extract content from OpenRouter response
        llm_response = llm_response_json['choices'][0]['message']['content'].strip()
        
        # Parse LLM response
        try:
            parsed_response = json.loads(llm_response)
            
            return {
                "action": "llm_analysis",
                "data": {
                    "pmc_id": pmc_id,
                    "analysis_type": analysis_type,
                    "analysis": parsed_response.get("analysis", ""),
                    "key_points": parsed_response.get("key_points", [])
                }
            }
        
        except json.JSONDecodeError:
            # If LLM didn't return valid JSON, wrap the response
            return {
                "action": "llm_analysis",
                "data": {
                    "pmc_id": pmc_id,
                    "analysis_type": analysis_type,
                    "analysis": llm_response,
                    "key_points": []
                }
            }
    
    except Exception as e:
        return {
            "action": "llm_analysis",
            "error": f"Error analyzing article: {str(e)}",
            "data": None
        }


def extract_pmc_id_from_query(user_query: str) -> Optional[str]:
    """
    Extract PMC ID from user query
    
    Args:
        user_query: User's input text
    
    Returns:
        PMC ID string or None if not found
    """
    import re
    
    # Look for patterns like "PMC2910419" or "2910419"
    pmc_pattern = r'PMC\d+|\b\d{7,8}\b'
    matches = re.findall(pmc_pattern, user_query, re.IGNORECASE)
    
    if matches:
        return matches[0]  # Return first match
    
    return None
