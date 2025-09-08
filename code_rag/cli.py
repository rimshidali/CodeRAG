# import argparse
# from code_rag.pipeline import CodeRAGPipeline

# def main():
#     parser = argparse.ArgumentParser(description="CodeRAG: RAG for Codebases")
#     parser.add_argument("--path", help="Local repo path")
#     parser.add_argument("--repo", help="GitHub repo URL")
#     # parser.add_argument("--query", required=True, help="Your question about the codebase")
#     args = parser.parse_args()

#     pipeline = CodeRAGPipeline(path=args.path, repo=args.repo)
#     pipeline.ingest()
#     # print("\nIngested files:\n", pipeline.files)
#     pipeline.chunk()
#     # print("\nFiles chunk creates successfully\n", pipeline.chunks[0])
#     pipeline.embed()
#     # answer = pipeline.query(args.query)
    # print("\nAnswer:\n", answer)

import argparse
from code_rag.pipeline import CodeRAGPipeline

def main():
    parser = argparse.ArgumentParser(description="CodeRAG: RAG for Codebases")
    parser.add_argument("--path", help="Local repo path")
    parser.add_argument("--repo", help="GitHub repo URL")
    parser.add_argument("--query", required=True, help="Your question about the codebase")
    args = parser.parse_args()

    pipeline = CodeRAGPipeline(path=args.path, repo=args.repo)

    print("📂 Ingesting files...")
    pipeline.ingest()
    print(f"✅ Ingested {len(pipeline.files)} files")

    print("\n✂️ Chunking files...")
    pipeline.chunk()
    print(f"✅ Created {len(pipeline.chunks)} chunks")

    print("\n🔢 Creating embeddings...")
    pipeline.embed()

    print("\n🔎 Querying...")
    results = pipeline.query(args.query, top_k=10)

    print("\n📌 Query Results:")
    for i, doc in enumerate(results["documents"][0], start=1):
        print(f"\nResult {i}:")
        print(doc)

    answer = pipeline.answer(args.query)
    print("🤖 Answer:\n", answer)




if __name__ == "__main__":
    main()
