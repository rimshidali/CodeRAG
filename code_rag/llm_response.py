# llm_response.py
from transformers import pipeline
from code_rag.embedding import Embedder


class LLMResponder:
    def __init__(self, model_name="microsoft/phi-2", collection_name="code_chunks"):
        # Load a lightweight local model for text generation
        self.generator = pipeline(
            "text-generation",
            model=model_name,
            device_map="auto",   # uses GPU if available, else CPU
            torch_dtype="auto"
        )
        self.embedder = Embedder(collection_name=collection_name)

    def build_prompt(self, query: str, retrieved_chunks: dict) -> str:
        """Combine query + retrieved chunks into a single system prompt."""
        context_texts = []
        for doc, meta in zip(retrieved_chunks["documents"][0], retrieved_chunks["metadatas"][0]):
            context_texts.append(f"File: {meta.get('file')} | Language: {meta.get('language')}\n{doc}")

        context_str = "\n\n".join(context_texts)

        prompt = f"""
You are a coding assistant helping to answer questions about a codebase.

Context from the codebase:
{context_str}

User Question:
{query}

Answer clearly and reference the code when necessary.
"""
        return prompt.strip()

    def answer(self, query: str, top_k: int = 5) -> str:
        """Retrieve context and generate LLM answer."""
        retrieved = self.embedder.query(query, top_k=top_k)
        prompt = self.build_prompt(query, retrieved)

        # Run local inference with the small model
        response = self.generator(
            prompt,
            max_new_tokens=300,
            temperature=0.3,
            do_sample=True
        )
        return response[0]["generated_text"]


# if __name__ == "__main__":
#     llm = LLMResponder()
#     query = "Explain the role of config.py in this codebase."
#     answer = llm.answer(query)
#     print("🤖 LLM Answer:\n", answer)
