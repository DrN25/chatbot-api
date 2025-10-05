"""
Servicio para recomendar clusters científicos más relevantes por keywords.
Usa mapeo directo: Keywords → Clusters (sin artículos)
"""
import json
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class ClusterRecommender:
    """
    Recomienda clusters científicos basándose en keywords.
    Analiza unigramKeywords.json y bigramKeywords.json para encontrar el mejor match.
    """
    
    def __init__(self):
        """Inicializa el recomendador cargando keywords de clusters"""
        self.resources_dir = Path(__file__).parent / "resources"
        
        # Cargar keywords de clusters
        self.cluster_keywords = self._load_cluster_keywords()
        
        # Crear índice invertido: keyword → [cluster_ids]
        self.keyword_to_clusters = self._build_keyword_index()
        
        total_keywords = sum(len(kws) for kws in self.cluster_keywords.values())
        
        print(f"✅ ClusterRecommender inicializado:")
        print(f"   • {len(self.cluster_keywords)} clusters indexados")
        print(f"   • {total_keywords} keywords totales")
        print(f"   • {len(self.keyword_to_clusters)} keywords únicas")
    
    
    def _load_cluster_keywords(self) -> Dict[str, Set[str]]:
        """
        Carga todas las keywords de cada cluster (unigrams + bigrams).
        Retorna: {cluster_id: {keyword1, keyword2, ...}}
        """
        cluster_kws = defaultdict(set)
        
        # Cargar unigrams
        unigram_file = self.resources_dir / "unigramKeywords.json"
        with open(unigram_file, 'r', encoding='utf-8') as f:
            unigrams = json.load(f)
        
        for cluster_id, keywords in unigrams.items():
            for keyword in keywords:
                cluster_kws[cluster_id].add(keyword.lower().strip())
        
        # Cargar bigrams
        bigram_file = self.resources_dir / "bigramKeywords.json"
        with open(bigram_file, 'r', encoding='utf-8') as f:
            bigrams = json.load(f)
        
        for cluster_id, keywords in bigrams.items():
            for keyword in keywords:
                cluster_kws[cluster_id].add(keyword.lower().strip())
        
        return dict(cluster_kws)
    
    
    def _build_keyword_index(self) -> Dict[str, Set[str]]:
        """
        Construye índice invertido: keyword → {cluster_ids}
        """
        keyword_index = defaultdict(set)
        
        for cluster_id, keywords in self.cluster_keywords.items():
            for keyword in keywords:
                keyword_index[keyword].add(cluster_id)
        
        return dict(keyword_index)
    
    
    def find_best_cluster(
        self, 
        keywords: List[str], 
        top_n: int = 1
    ) -> List[Dict[str, any]]:
        """
        Encuentra el/los cluster(s) más relevante(s) para las keywords dadas.
        
        Args:
            keywords: Lista de keywords científicas (máximo 5 recomendado)
            top_n: Número de clusters a retornar (default: 1)
        
        Returns:
            Lista de diccionarios con:
            {
                "cluster_id": "0",
                "relevance_score": 0.85,
                "matched_keywords": ["keyword1", "keyword2"],
                "total_keywords_in_cluster": 45
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
        
        # Encontrar clusters que contengan las keywords
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
        
        # Calcular scores y preparar resultados
        results = []
        
        for cluster_id, score_info in cluster_scores.items():
            # Score = proporción de keywords input que el cluster contiene
            match_score = score_info["count"] / len(normalized_keywords)
            
            # Total de keywords en el cluster
            total_kws = len(self.cluster_keywords.get(cluster_id, set()))
            
            results.append({
                "cluster_id": cluster_id,
                "relevance_score": round(match_score, 4),
                "matched_keywords": sorted(list(score_info["keywords"])),
                "total_keywords_in_cluster": total_kws
            })
        
        # Ordenar por relevance_score (mayor primero)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:top_n]


# Instancia global (singleton)
_cluster_recommender_instance = None


def get_cluster_recommender() -> ClusterRecommender:
    """
    Obtiene la instancia singleton del recomendador de clusters.
    """
    global _cluster_recommender_instance
    
    if _cluster_recommender_instance is None:
        _cluster_recommender_instance = ClusterRecommender()
    
    return _cluster_recommender_instance


# --- Función principal para usar en el chatbot ---

def recommend_cluster_by_keywords(
    keywords: List[str],
    limit: int = 1
) -> List[Dict[str, any]]:
    """
    API principal para recomendar cluster(s) basándose en keywords.
    
    Args:
        keywords: Lista de keywords científicas (máximo 5)
        limit: Número de clusters a retornar (default: 1)
    
    Returns:
        Lista de clusters ordenados por relevancia
    
    Example:
        >>> keywords = ["microgravity", "bone", "spaceflight"]
        >>> clusters = recommend_cluster_by_keywords(keywords, limit=1)
        >>> print(clusters[0])
        {
            "cluster_id": "23",
            "relevance_score": 1.0,
            "matched_keywords": ["microgravity", "bone", "spaceflight"],
            "total_keywords_in_cluster": 48
        }
    """
    recommender = get_cluster_recommender()
    return recommender.find_best_cluster(keywords, top_n=limit)


# --- Script de prueba ---

if __name__ == "__main__":
    print("🧪 Probando ClusterRecommender\n")
    
    # Test 1: Keywords relacionadas con microgravity
    print("=" * 80)
    print("📋 Test 1: Microgravity & Bone Loss")
    print("=" * 80)
    keywords1 = ["microgravity", "bone", "spaceflight"]
    results1 = recommend_cluster_by_keywords(keywords1, limit=3)
    
    for i, cluster in enumerate(results1, 1):
        print(f"\n{i}. Cluster {cluster['cluster_id']} (score: {cluster['relevance_score']})")
        print(f"   Matched: {', '.join(cluster['matched_keywords'])}")
        print(f"   Total keywords en cluster: {cluster['total_keywords_in_cluster']}")
    
    # Test 2: Keywords de inmunología
    print("\n" + "=" * 80)
    print("📋 Test 2: Immune System")
    print("=" * 80)
    keywords2 = ["immune", "lymphocyte", "cytokine"]
    results2 = recommend_cluster_by_keywords(keywords2, limit=3)
    
    for i, cluster in enumerate(results2, 1):
        print(f"\n{i}. Cluster {cluster['cluster_id']} (score: {cluster['relevance_score']})")
        print(f"   Matched: {', '.join(cluster['matched_keywords'])}")
        print(f"   Total keywords en cluster: {cluster['total_keywords_in_cluster']}")
    
    # Test 3: Keywords de plantas
    print("\n" + "=" * 80)
    print("📋 Test 3: Plant Biology")
    print("=" * 80)
    keywords3 = ["arabidopsis", "root", "gravity"]
    results3 = recommend_cluster_by_keywords(keywords3, limit=3)
    
    for i, cluster in enumerate(results3, 1):
        print(f"\n{i}. Cluster {cluster['cluster_id']} (score: {cluster['relevance_score']})")
        print(f"   Matched: {', '.join(cluster['matched_keywords'])}")
        print(f"   Total keywords en cluster: {cluster['total_keywords_in_cluster']}")
    
    # Test 4: Single keyword
    print("\n" + "=" * 80)
    print("📋 Test 4: Single Keyword - Spaceflight")
    print("=" * 80)
    keywords4 = ["spaceflight"]
    results4 = recommend_cluster_by_keywords(keywords4, limit=5)
    
    for i, cluster in enumerate(results4, 1):
        print(f"\n{i}. Cluster {cluster['cluster_id']} (score: {cluster['relevance_score']})")
        print(f"   Matched: {', '.join(cluster['matched_keywords'])}")
        print(f"   Total keywords en cluster: {cluster['total_keywords_in_cluster']}")
    
    print("\n" + "=" * 80)
    print("✅ Tests completados!")
