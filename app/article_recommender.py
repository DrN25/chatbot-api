"""
Servicio para buscar artículos científicos más relevantes por keywords.
Usa mapeo directo: Keywords → Clusters → PMC IDs
"""
import json
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class ArticleRecommender:
    """
    Recomienda artículos científicos basándose en keywords usando mapeo cluster.
    """
    
    def __init__(self):
        """Inicializa el recomendador cargando mappings"""
        self.resources_dir = Path(__file__).parent / "resources"
        
        # Cargar datos
        self.pmc_to_title = self._load_pmc_to_title()
        self.clusters_pmc = self._load_clusters_pmc()
        
        # Crear índice: keyword → [cluster_ids]
        self.keyword_to_clusters = self._build_keyword_index()
        
        total_articles = sum(len(pmcs) for pmcs in self.clusters_pmc.values())
        total_keywords = len(self.keyword_to_clusters)
        
        print(f"✅ ArticleRecommender inicializado:")
        print(f"   • {len(self.clusters_pmc)} clusters indexados")
        print(f"   • {total_articles} artículos totales")
        print(f"   • {total_keywords} keywords únicas")
    
    
    def _load_pmc_to_title(self) -> Dict[str, str]:
        """Carga el mapping de PMC IDs a títulos"""
        file_path = self.resources_dir / "articlesName_PMC.json"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("articles", {})
    
    
    def _load_clusters_pmc(self) -> Dict[str, List[str]]:
        """Carga los clusters con PMC IDs"""
        file_path = self.resources_dir / "clustersPMC.json"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("clusters", {})
    
    
    def _build_keyword_index(self) -> Dict[str, Set[str]]:
        """
        Construye índice invertido: keyword → {cluster_ids}
        Lee unigramKeywords.json y bigramKeywords.json
        """
        keyword_index = defaultdict(set)
        
        # Cargar unigrams
        unigram_file = self.resources_dir / "unigramKeywords.json"
        with open(unigram_file, 'r', encoding='utf-8') as f:
            unigrams = json.load(f)
        
        for cluster_id, keywords in unigrams.items():
            for keyword in keywords:
                keyword_lower = keyword.lower().strip()
                keyword_index[keyword_lower].add(cluster_id)
        
        # Cargar bigrams
        bigram_file = self.resources_dir / "bigramKeywords.json"
        with open(bigram_file, 'r', encoding='utf-8') as f:
            bigrams = json.load(f)
        
        for cluster_id, keywords in bigrams.items():
            for keyword in keywords:
                keyword_lower = keyword.lower().strip()
                keyword_index[keyword_lower].add(cluster_id)
        
        return dict(keyword_index)
    
    
    def find_articles_by_keywords(
        self, 
        keywords: List[str], 
        top_n: int = 5
    ) -> List[Dict[str, any]]:
        """
        Encuentra los artículos más relevantes para las keywords dadas.
        Usa mapeo directo: keywords → clusters → PMC IDs
        
        Args:
            keywords: Lista de keywords (máximo 5 recomendado)
            top_n: Número de artículos a retornar (default: 5)
        
        Returns:
            Lista de diccionarios con:
            {
                "pmc_id": "PMC1234567",
                "title": "Article title...",
                "relevance_score": 0.85,
                "cluster_id": "0",
                "matched_keywords": ["keyword1", "keyword2"]
            }
            Ordenados por relevance_score (mayor a menor)
        """
        if not keywords:
            return []
        
        # Validar máximo 5 keywords
        if len(keywords) > 5:
            print(f"⚠️  Se recomienda máximo 5 keywords. Recibidas: {len(keywords)}")
            keywords = keywords[:5]
        
        # Normalizar keywords
        normalized_keywords = [kw.lower().strip() for kw in keywords]
        
        # Paso 1: Encontrar clusters que contengan las keywords
        cluster_scores = defaultdict(lambda: {"count": 0, "keywords": set()})
        
        for keyword in normalized_keywords:
            # Buscar clusters que contengan esta keyword
            matching_clusters = self.keyword_to_clusters.get(keyword, set())
            
            for cluster_id in matching_clusters:
                cluster_scores[cluster_id]["count"] += 1
                cluster_scores[cluster_id]["keywords"].add(keyword)
        
        if not cluster_scores:
            # No hay clusters con estas keywords
            return []
        
        # Paso 2: Ordenar clusters por número de keywords coincidentes
        sorted_clusters = sorted(
            cluster_scores.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Paso 3: Recolectar artículos de los clusters más relevantes
        all_candidates = []
        seen_pmcs = set()  # Evitar duplicados
        
        for cluster_id, score_info in sorted_clusters:
            # Score del cluster = proporción de keywords que contiene
            cluster_score = score_info["count"] / len(normalized_keywords)
            
            # Obtener PMC IDs del cluster
            pmc_ids = self.clusters_pmc.get(cluster_id, [])
            
            for pmc_id in pmc_ids:
                if pmc_id in seen_pmcs:
                    continue
                
                seen_pmcs.add(pmc_id)
                title = self.pmc_to_title.get(pmc_id, "")
                
                if not title:
                    continue
                
                # Encontrar keywords que aparecen en el título
                matched_in_title = self._find_matched_keywords(title, keywords)
                
                # Score final = cluster_score + bonus si keywords aparecen en título
                title_boost = len(matched_in_title) / len(keywords) if keywords else 0
                final_score = cluster_score * (0.8 + 0.2 * title_boost)
                
                all_candidates.append({
                    "pmc_id": pmc_id,
                    "title": title,
                    "relevance_score": round(final_score, 4),
                    "cluster_id": cluster_id,
                    "matched_keywords": list(score_info["keywords"])
                })
        
        # Paso 4: Ordenar por relevance_score y tomar top_n
        all_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return all_candidates[:top_n]
    
    
    def _find_matched_keywords(self, title: str, keywords: List[str]) -> List[str]:
        """
        Encuentra qué keywords aparecen en el título (case-insensitive).
        """
        title_lower = title.lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in title_lower:
                matched.append(keyword)
        
        return matched


# Instancia global (singleton) para reutilizar la matriz TF-IDF
_recommender_instance = None


def get_recommender() -> ArticleRecommender:
    """
    Obtiene la instancia singleton del recomendador.
    La matriz TF-IDF se crea solo una vez al inicio.
    """
    global _recommender_instance
    
    if _recommender_instance is None:
        _recommender_instance = ArticleRecommender()
    
    return _recommender_instance


# --- Función principal para usar en el chatbot ---

def recommend_articles_by_keywords(
    keywords: List[str],
    limit: int = 5
) -> List[Dict[str, any]]:
    """
    API principal para recomendar artículos basándose en keywords.
    
    Args:
        keywords: Lista de keywords científicas (máximo 5)
        limit: Número de artículos a retornar (default: 5)
    
    Returns:
        Lista de artículos ordenados por relevancia con sus PMC IDs
    
    Example:
        >>> keywords = ["microgravity", "bone loss", "spaceflight"]
        >>> articles = recommend_articles_by_keywords(keywords, limit=5)
        >>> print(articles[0])
        {
            "pmc_id": "PMC3630201",
            "title": "Microgravity induces pelvic bone loss...",
            "relevance_score": 0.8542,
            "cluster_id": "0",
            "matched_keywords": ["microgravity", "bone loss", "spaceflight"]
        }
    """
    recommender = get_recommender()
    return recommender.find_articles_by_keywords(keywords, top_n=limit)


# --- Script de prueba ---

if __name__ == "__main__":
    print("🧪 Probando ArticleRecommender\n")
    
    # Test 1: Keywords relacionadas con microgravity
    print("=" * 80)
    print("📋 Test 1: Microgravity & Bone Loss")
    print("=" * 80)
    keywords1 = ["microgravity", "bone loss", "spaceflight"]
    results1 = recommend_articles_by_keywords(keywords1, limit=5)
    
    for i, article in enumerate(results1, 1):
        print(f"\n{i}. {article['pmc_id']} (score: {article['relevance_score']}, cluster: {article['cluster_id']})")
        print(f"   {article['title'][:80]}...")
        print(f"   Matched: {', '.join(article['matched_keywords'])}")
    
    # Test 2: Keywords de inmunología
    print("\n" + "=" * 80)
    print("📋 Test 2: Immune System & Space")
    print("=" * 80)
    keywords2 = ["immune", "lymphocyte", "space"]
    results2 = recommend_articles_by_keywords(keywords2, limit=5)
    
    for i, article in enumerate(results2, 1):
        print(f"\n{i}. {article['pmc_id']} (score: {article['relevance_score']}, cluster: {article['cluster_id']})")
        print(f"   {article['title'][:80]}...")
        print(f"   Matched: {', '.join(article['matched_keywords'])}")
    
    # Test 3: Keywords de plantas
    print("\n" + "=" * 80)
    print("📋 Test 3: Plant Biology")
    print("=" * 80)
    keywords3 = ["arabidopsis", "root", "gravity"]
    results3 = recommend_articles_by_keywords(keywords3, limit=5)
    
    for i, article in enumerate(results3, 1):
        print(f"\n{i}. {article['pmc_id']} (score: {article['relevance_score']}, cluster: {article['cluster_id']})")
        print(f"   {article['title'][:80]}...")
        print(f"   Matched: {', '.join(article['matched_keywords'])}")
    
    print("\n" + "=" * 80)
    print("✅ Tests completados!")
