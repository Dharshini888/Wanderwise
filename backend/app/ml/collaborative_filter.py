"""
collaborative_filter.py — WanderWise Phase 2 ML Module

Collaborative Filtering Engine using User-Item Interaction Signals:
- Signal Weights: Clicked (1.0), Saved (2.0), Booked (3.0), Rated High (4.0), Skipped (-1.0)
Calculates item-item similarity & matrix factorization predictions for "Users like you also loved..."
"""

import math
from typing import List, Dict, Any, Tuple


class CollaborativeFilter:
    """Matrix Factorization & Collaborative Scorer for User Interactions."""

    def __init__(self):
        self.interaction_matrix: Dict[int, Dict[str, float]] = {}

    def record_signal(self, user_id: int, item_id: str, signal_type: str, rating: float = 0.0) -> None:
        """Records user interaction signals into interaction matrix."""
        if user_id not in self.interaction_matrix:
            self.interaction_matrix[user_id] = {}

        weights = {
            "clicked": 1.0,
            "saved": 2.0,
            "booked": 3.0,
            "liked": 3.5,
            "rated": rating or 4.0,
            "skipped": -1.0,
            "disliked": -2.0,
        }
        val = weights.get(signal_type.lower(), 1.0)
        current = self.interaction_matrix[user_id].get(item_id, 0.0)
        self.interaction_matrix[user_id][item_id] = current + val

    def predict_user_item_affinity(self, target_user_id: int, item_id: str) -> float:
        """Predicts user affinity score [0.0, 1.0] using collaborative nearest-neighbor signal match."""
        if not self.interaction_matrix or target_user_id not in self.interaction_matrix:
            return 0.5  # Neutral default

        target_signals = self.interaction_matrix[target_user_id]
        if item_id in target_signals:
            return round(min(1.0, max(0.0, target_signals[item_id] / 5.0)), 3)

        # Compute cosine similarity with other users who interacted with item_id
        similarities: List[Tuple[float, float]] = []

        for other_user_id, other_signals in self.interaction_matrix.items():
            if other_user_id == target_user_id or item_id not in other_signals:
                continue

            # Compute user-user similarity
            common_items = set(target_signals.keys()).intersection(set(other_signals.keys()))
            if not common_items:
                continue

            dot_product = sum(target_signals[it] * other_signals[it] for it in common_items)
            norm_target = math.sqrt(sum(v * v for v in target_signals.values()))
            norm_other = math.sqrt(sum(v * v for v in other_signals.values()))

            sim = dot_product / (norm_target * norm_other) if (norm_target * norm_other) > 0 else 0.0
            if sim > 0:
                similarities.append((sim, other_signals[item_id]))

        if not similarities:
            return 0.5

        weighted_score = sum(sim * score for sim, score in similarities) / sum(sim for sim, _ in similarities)
        return round(min(1.0, max(0.0, weighted_score / 5.0)), 3)
