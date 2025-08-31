# from code_rag import ingestion, chunking, embeddings, retrieval, llm_response
from code_rag import ingestion

class CodeRAGPipeline:
    def __init__(self, path=None, repo=None, use_faiss=True):
        self.repo_path = path
        self.repo_url = repo
        self.files = []
        self.chunks = []
        self.embeddings = []
        self.vector_store = None
        self.use_faiss = use_faiss

    def ingest(self):
        ingestor = ingestion.CodeIngestion(self.repo_path, self.repo_url)
        self.files = ingestor.ingest()

    # def chunk(self):
    #     self.chunks = chunking.extract_chunks(self.files)

    # def embed(self):
    #     self.embeddings = embeddings.embed_chunks(self.chunks)
    #     if self.use_faiss:
    #         self.vector_store = retrieval.build_faiss_index(self.embeddings, self.chunks)

    # def query(self, query_text, top_k=3):
    #     if self.use_faiss:
    #         top_chunks = retrieval.faiss_retrieve(self.vector_store, query_text, top_k)
    #     else:
    #         top_chunks = retrieval.retrieve_top_k(query_text, self.chunks, self.embeddings, top_k)
    #     return llm_response.generate_answer(query_text, top_chunks)
