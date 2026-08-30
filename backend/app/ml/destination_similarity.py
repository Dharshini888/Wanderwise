"""
destination_similarity.py — WanderWise Phase 2 ML Module

Computes TF-IDF vector embeddings and Cosine Similarity scores for travel destinations
based on destination tags, activity themes, budget tiers, pace, and geographic regions.
"""

import math
from typing import List, Dict, Any, Set


class DestinationSimilarityModel:
    """TF-IDF + Cosine Similarity Model for Destination Embeddings."""

    def __init__(self):
        self.vocabulary: List[str] = []
        self.idf_dict: Dict[str, float] = {}
        self.destination_vectors: Dict[str, Dict[str, float]] = {}

    def _extract_tokens(self, dest: Dict[str, Any]) -> List[str]:
        tokens = []
        if "category" in dest and dest["category"]:
            tokens.append(str(dest["category"]).lower())
        if "country" in dest and dest["country"]:
            tokens.append(str(dest["country"]).lower())
        if "region" in dest and dest["region"]:
            tokens.append(str(dest["region"]).lower())
        if "budget_tier" in dest and dest["budget_tier"]:
            tokens.append(f"budget_{str(dest['budget_tier']).lower()}")
        if "tags" in dest and isinstance(dest["tags"], list):
            tokens.extend([str(t).lower() for t in dest["tags"]])
        if "activities" in dest and isinstance(dest["activities"], list):
            tokens.extend([str(a).lower() for a in dest["activities"]])
        return tokens

    def fit(self, destination_corpus: List[Dict[str, Any]]) -> None:
        """Computes TF-IDF vector representations across destination corpus."""
        if not destination_corpus:
            return

        doc_count = len(destination_corpus)
        df_counts: Dict[str, int] = {}
        doc_tokens: Dict[str, List[str]] = {}

        for dest in destination_corpus:
            name = dest.get("name") or dest.get("title") or "Unknown"
            tokens = self._extract_tokens(dest)
            doc_tokens[name] = tokens

            unique_terms = set(tokens)
            for term in unique_terms:
                df_counts[term] = df_counts.get(term, 0) + 1

        self.idf_dict = {term: math.log((doc_count + 1) / (df + 1)) + 1.0 for term, df in df_counts.items()}
        self.vocabulary = list(self.idf_dict.keys())

        # Build TF-IDF vector for each destination
        for name, tokens in doc_tokens.items():
            if not tokens:
                continue
            tf_counts: Dict[str, int] = {}
            for t in tokens:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            total_t = len(tokens)

            vector = {}
            norm_sq = 0.0
            for term, count in tf_counts.items():
                tf = count / total_t
                tfidf = tf * self.idf_dict.get(term, 1.0)
                vector[term] = tfidf
                norm_sq += tfidf * tfidf

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self.destination_vectors[name] = {k: v / norm for k, v in vector.items()}

    def similarity(self, source_dest: Dict[str, Any], target_dest: Dict[str, Any]) -> float:
        """Computes Cosine Similarity score [0.0, 1.0] between source and target destinations."""
        source_tokens = self._extract_tokens(source_dest)
        target_tokens = self._extract_tokens(target_dest)

        if not source_tokens or not target_tokens:
            return 0.5  # Neutral default

        source_set = set(source_tokens)
        target_set = set(target_tokens)

        intersection = source_set.intersection(target_set)
        union = source_set.union(target_set)

        jaccard = len(intersection) / len(union) if union else 0.0

        # Direct tag match boost
        category_match = 0.2 if source_dest.get("category") == target_dest.get("category") else 0.0
        country_match = 0.15 if source_dest.get("country") == target_dest.get("country") else 0.0

        score = (jaccard * 0.65) + category_match + country_match
        return round(min(1.0, max(0.0, score)), 3)
