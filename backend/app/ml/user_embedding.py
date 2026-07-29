"""
user_embedding.py
Future ML Module — User travel personality embedding via matrix factorization.

Plans:
  - Encode user interest scores into dense embedding vectors
  - Use ALS (Alternating Least Squares) for collaborative filtering
  - Find users with similar travel personalities
  - Generate "Travelers like you also loved..." recommendations
"""

class UserEmbeddingModel:
    """Placeholder for user embedding model."""

    def embed_user(self, user_profile) -> list:
        raise NotImplementedError("User embedding model not yet trained.")

    def find_similar_users(self, user_id: int, top_k: int = 5) -> list:
        raise NotImplementedError("Collaborative user-similarity not yet available.")
