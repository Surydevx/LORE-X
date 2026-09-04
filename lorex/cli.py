import argparse
import sys
import os

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
    ingest_parser.add_argument("--project", default="p1", help="Project ID")

    # lorex serve
    serve_parser = subparsers.add_parser("serve", help="Launch the LORE-X web dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        _handle_init()
    elif args.command == "query":
        _handle_query(args)
    elif args.command == "ingest":
        _handle_ingest(args)
    elif args.command == "serve":
        _handle_serve(args)

def _handle_init():
    from getpass import getpass
    
    if not os.path.exists(".git"):
        print("Error: Not a git repository. Please run 'git init' first.")
        sys.exit(1)
        
    supported_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    if not any(os.getenv(k) for k in supported_keys):
        print("No LLM API keys detected in the environment.")
        print("Supported providers:")
        print("1. Gemini")
        print("2. OpenAI")
        print("3. Anthropic")
        choice = input("Select your provider (1/2/3) [default: 1]: ").strip()
        
        key_name = "GEMINI_API_KEY"
        if choice == "2":
            key_name = "OPENAI_API_KEY"
        elif choice == "3":
            key_name = "ANTHROPIC_API_KEY"
            
        api_key = getpass(f"Enter your {key_name} (input hidden): ")
        if api_key.strip():
            with open(".env", "a") as f:
                f.write(f"\n{key_name}={api_key.strip()}\n")
            # Reload into os.environ so subsequent operations see it (M7)
            os.environ[key_name] = api_key.strip()
            print(f"{key_name} saved to .env file.")
        else:
            print("Warning: No API key provided. LORE-X may fail during extraction.")
            
    gitignore_path = ".gitignore"
    ignores = ["\n# LORE-X\n", "lorex.db\n", ".env\n"]
    existing_ignores = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_ignores = f.readlines()
    
    with open(gitignore_path, "a") as f:
        for item in ignores:
            if item.strip() and not any(item.strip() in line for line in existing_ignores):
                f.write(item)
    
    from lorex.db.session import init_db
    init_db()
    print("Database initialized successfully.")
    
    hook_dir = os.path.join(".git", "hooks")
    os.makedirs(hook_dir, exist_ok=True)
    hook_path = os.path.join(hook_dir, "post-commit")
    hook_content = "#!/bin/sh\n# Automatically ingest the latest commit into LORE-X\nlorex ingest . --limit 1 > /dev/null 2>&1 &\n"
    with open(hook_path, "w") as f:
        f.write(hook_content)
    os.chmod(hook_path, 0o755)
    print("Git post-commit hook successfully initialized and made executable.")

def _handle_query(args):
    from lorex.db.session import init_db, get_session
    from lorex.engine.retrieval import HybridRetrievalEngine
    
    try:
        init_db()
        session = get_session()
        try:
            engine = HybridRetrievalEngine()
            results = engine.retrieve(args.text, session, top_k=3)
            print(f"\nResults for '{args.text}':")
            if not results:
                print("  No experiences found.")
            for res in results:
                exp, score = res
                print(f"- [{exp.status}] {exp.action} (Score: {score:.2f})")
        finally:
            session.close()
    except Exception as e:
        print(f"Error during query: {e}", file=sys.stderr)
        sys.exit(1)

def _handle_ingest(args):
    if not any(os.getenv(k) for k in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]):
        sys.stderr.write("Warning: No LLM API keys detected. Extraction may fail or fallback to basic parsing.\n")
    
    import asyncio
    from lorex.db.session import init_db, get_session
    from lorex.vcs.local_git import GitLogIngester
    
    try:
        init_db()
        session = get_session()
        try:
            ingester = GitLogIngester()
            asyncio.run(ingester.ingest_repository(args.repo_path, args.project, session, limit=args.limit))
            print(f"Ingested commits from {args.repo_path}")
        finally:
            session.close()
    except RuntimeError as e:
        print(f"Error during ingestion: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during ingestion: {e}", file=sys.stderr)
        sys.exit(1)

def _handle_serve(args):
    try:
        import uvicorn
        from lorex.api.app import app
        print(f"Starting LORE-X Dashboard on port {args.port}...")
        uvicorn.run(app, host="127.0.0.1", port=args.port, reload=False)
    except OSError as e:
        print(f"Error: Could not start server: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
