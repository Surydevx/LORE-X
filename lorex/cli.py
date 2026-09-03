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

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Database initialized successfully.")
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
