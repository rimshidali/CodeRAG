import argparse
from code_rag.pipeline import CodeRAGPipeline

def main():
    parser = argparse.ArgumentParser(description="CodeRAG: RAG for Codebases")
    parser.add_argument("--path", help="Local repo path")
    parser.add_argument("--repo", help="GitHub repo URL")
    # parser.add_argument("--query", required=True, help="Your question about the codebase")
    args = parser.parse_args()

    pipeline = CodeRAGPipeline(path=args.path, repo=args.repo)
    pipeline.ingest()
    print("\nIngested files:\n", pipeline.files)
    # pipeline.chunk()
    # pipeline.embed()
    # answer = pipeline.query(args.query)
    # print("\nAnswer:\n", answer)



if __name__ == "__main__":
    main()
