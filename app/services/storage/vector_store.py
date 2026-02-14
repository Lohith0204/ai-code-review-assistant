from typing import List, Dict
import numpy as np
from app.core.models import CodeChunk

class VectorStore:
    def __init__(self):
        self.chunks: List[CodeChunk] = []
        self.embeddings: np.ndarray = np.array([])

    def add_documents(self, chunks: List[CodeChunk], embeddings: List[List[float]]):
        self.chunks.extend(chunks)
        new_embeddings = np.array(embeddings)
        
        if self.embeddings.size == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack((self.embeddings, new_embeddings))

    def search(self, query_embedding: List[float], k: int = 5) -> List[CodeChunk]:
        if self.embeddings.size == 0:
            return []
            
        # Cosine similarity
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        # Normalize
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
            
        emb_norms = np.linalg.norm(self.embeddings, axis=1)
        # Avoid division by zero
        emb_norms[emb_norms == 0] = 1e-10
        
        similarities = np.dot(self.embeddings, query_vec.T).flatten() / (emb_norms * query_norm)
        
        # Get top k indices
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        return [self.chunks[i] for i in top_k_indices]
