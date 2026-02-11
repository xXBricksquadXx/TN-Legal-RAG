import os
from sentence_transformers import CrossEncoder

# MISSION: Precision alignment of target to barrel
# Model is optimized for legal/factual relevance
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

class LegalReRanker:
    def __init__(self):
        print(">>> INITIALIZING RE-RANKER: Cross-Encoder online.")
        self.model = CrossEncoder(RERANK_MODEL)

    def sort_results(self, query: str, documents: List[str], metadatas: List[dict]):
        """
        Takes ChromaDB outputs and sorts them by actual logical relevance.
        """
        if not documents:
            return [], []

        # Pair the query with each document for the cross-encoder to score
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)

        # Zip, sort by score (descending), and unpack
        scored_results = sorted(zip(scores, documents, metadatas), key=lambda x: x[0], reverse=True)
        
        print(f">>> RE-RANK COMPLETE: Top match score: {scored_results[0][0]:.4f}")
        
        # Return sorted docs and metadata
        return [res[1] for res in scored_results], [res[2] for res in scored_results]