from typing import List
from sentence_transformers import SentenceTransformer
from app.core.models import CodeChunk

class EmbeddingService:
    _model = None

    def __init__(self):
        if EmbeddingService._model is None:
            print("Loading SentenceTransformer model (first time only)...")
            EmbeddingService._model = SentenceTransformer("all-MiniLM-L6-v2")
        self.model = EmbeddingService._model

    def embed_chunks(self, chunks: List[CodeChunk]) -> List[List[float]]:
        texts = [chunk.content for chunk in chunks]
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
