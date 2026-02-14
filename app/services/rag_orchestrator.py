from app.services.ingestion.file_loader import FileIngestionService
from app.services.chunking.code_chunker import ChunkingService
from app.services.embeddings.embedder import EmbeddingService
from app.services.storage.vector_store import VectorStore
from app.services.reviewer.code_reviewer import ReviewService
from app.core.models import ReviewResult

class RAGOrchestrator:
    """Orchestrates the RAG pipeline for code review."""
    
    def __init__(self):
        self.ingest_service = FileIngestionService()
        self.chunk_service = ChunkingService()
        self.embed_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.review_service = ReviewService()

    def run_review(self, directory_path: str, query: str = "Identify bugs and security risks") -> ReviewResult:
        files = self.ingest_service.load_directory(directory_path)
        chunks = self.chunk_service.chunk_files(files)
        embeddings = self.embed_service.embed_chunks(chunks)
        self.vector_store.add_documents(chunks, embeddings)
        
        query_embedding = self.embed_service.model.encode([query])[0]
        relevant_chunks = self.vector_store.search(query_embedding, k=5)
        
        context = "\n\n".join(
            [f"File: {c.file_path} (Lines {c.start_line}-{c.end_line})\n{c.content}" for c in relevant_chunks]
        )
        
        return self.review_service.review_code(context)
