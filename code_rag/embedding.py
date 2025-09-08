# embedding.py
from sentence_transformers import SentenceTransformer
import chromadb
import json


class Embedder:
    def __init__(self, collection_name="code_chunks"):
        # Load Qodo embedding model
        self.model = SentenceTransformer("Qodo/Qodo-Embed-1-1.5B")
        # self.model = SentenceTransformer("google/embeddinggemma-300m",token="")
        # Initialize ChromaDB client
        self.client = chromadb.Client()

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def _sanitize_metadata(self, metadata: dict) -> dict:
        """Ensure metadata values are ChromaDB-compatible (no lists/dicts)."""
        clean_meta = {}
        for k, v in metadata.items():
            if isinstance(v, (list, dict)):
                clean_meta[k] = json.dumps(v)  # Convert to JSON string
            else:
                clean_meta[k] = str(v)
        return clean_meta
 
    def create_embeddings(self, chunks: list[dict]):
        """
        Create embeddings for chunks and store them in ChromaDB.
        Each chunk is a dict with keys: content, metadata.
        """
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True)

        for i, chunk in enumerate(chunks):
            safe_metadata = self._sanitize_metadata(chunk["metadata"])
            self.collection.add(
                ids=[f"chunk_{i}"],
                documents=[chunk["content"]],
                embeddings=[embeddings[i].tolist()],
                metadatas=[safe_metadata]
            )
        print(f"✅ Stored {len(chunks)} chunks in collection '{self.collection.name}'")

    def query(self, query_text: str, top_k: int = 10):
        """Query ChromaDB for similar chunks based on text input."""
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)[0]
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        return results






