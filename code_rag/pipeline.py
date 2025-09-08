from code_rag import ingestion,chunking
from code_rag.embedding import Embedder
from code_rag.llm_response import LLMResponder

class CodeRAGPipeline:
    def __init__(self, path=None, repo=None):
        self.repo_path = path
        self.repo_url = repo
        self.files = []
        self.chunks = []
        self.vector_store = None
        self.embedder = Embedder()

    def ingest(self):
        ingestor = ingestion.CodeIngestion(self.repo_path, self.repo_url)
        self.files = ingestor.ingest()

    def chunk(self):
        self.chunks = chunking.chunk_codebase(self.files)

    def embed(self):
        """Create embeddings for the chunks and store in ChromaDB"""
        if not self.chunks:
            raise ValueError("No chunks found. Run chunk() first.")
        self.embedder.create_embeddings(self.chunks)

    def query(self, query_text: str, top_k: int = 10):
        """Query stored embeddings with a user query"""
        return self.embedder.query(query_text, top_k=top_k)
