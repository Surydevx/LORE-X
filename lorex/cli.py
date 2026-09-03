import argparse
import sys
from lorex.db.session import init_db, get_session
from lorex.engine.retrieval import HybridRetrievalEngine
from lorex.vcs.local_git import GitLogIngester

def main():
    parser = argparse.ArgumentParser(prog="lorex", description="LORE-X CLI")
    subparsers = parser.add_subparsers(dest="command")

    # lorex init
    subparsers.add_parser("init", help="Initialize the database schema")

    # lorex query "..."
    query_parser = subparsers.add_parser("query", help="Query engineering experiences")
    query_parser.add_argument("text", type=str, help="Problem query string")
    query_parser.add_argument("--project", default="p1", help="Project ID")

    # lorex ingest <path>
    ingest_parser = subparsers.add_parser("ingest", help="Ingest local git commit logs")
    ingest_parser.add_argument("repo_path", default=".", nargs="?", help="Path to local repository")
    ingest_parser.add_argument("--limit", type=int, default=5, help="Number of commits")

    # lorex serve
    serve_parser = subparsers.add_parser("serve", help="Launch the LORE-X web dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Database initialized successfully.")
        
        import os
        if os.path.exists(".git"):
            hook_path = os.path.join(".git", "hooks", "post-commit")
            hook_content = """#!/bin/sh\n# Automatically ingest the latest commit into LORE-X\nuv run lorex ingest . --limit 1 > /dev/null 2>&1 &\n"""
            with open(hook_path, "w") as f:
                f.write(hook_content)
            os.chmod(hook_path, 0o755)
            print("Git post-commit hook successfully initialized and made executable.")
    elif args.command == "query":
        init_db()
        session = get_session()
        # Note: HybridRetrievalEngine signature in previous code was HybridRetrievalEngine(alpha, beta, gamma, delta).
        # And retrieve(query, session, top_k). The user prompt uses engine.retrieve(args.project, args.text, top_k=3)
        # We'll use the user provided code exactly for the CLI or adapt to match our current API.
        engine = HybridRetrievalEngine()
        # Our previous implementation of retrieve was retrieve(query: str, session, top_k: int = 5)
        # So I'll modify the engine call slightly to not crash since args.text is the query
        results = engine.retrieve(args.text, session, top_k=3)
        print(f"\nResults for '{args.text}':")
        for res in results:
            exp, score = res
            print(f"- [{exp.status}] {exp.action} (Score: {score:.2f})")
    elif args.command == "ingest":
        import asyncio
        init_db()
        session = get_session()
        ingester = GitLogIngester()
        asyncio.run(ingester.ingest_repository(args.repo_path, "p1", session, limit=args.limit))
        print(f"Ingested commits from {args.repo_path}")
    elif args.command == "serve":
        import uvicorn
        print(f"Starting LORE-X Dashboard on port {args.port}...")
        uvicorn.run("lorex.api.app:app", host="127.0.0.1", port=args.port, reload=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
