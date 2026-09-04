import argparse
import asyncio
from getpass import getpass
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


def main():
    # Load environment variables from the current working directory immediately
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=True)

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
    ingest_parser.add_argument(
        "repo_path",
        default=".",
        nargs="?",
        help="Path to local repository",
    )
    ingest_parser.add_argument("--limit", type=int, default=5, help="Number of commits")
    ingest_parser.add_argument("--project", default="p1", help="Project ID")

    # lorex serve
    serve_parser = subparsers.add_parser("serve", help="Launch the LORE-X web dashboard")
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on",
    )
    
    # lorex log
    log_parser = subparsers.add_parser("log", help="View extraction history in a terminal table")
    log_parser.add_argument("--limit", type=int, default=10, help="Number of recent experiences to show")
    log_parser.add_argument("--project", default="p1", help="Project ID to filter by")

    # lorex graph
    graph_parser = subparsers.add_parser("graph", help="View knowledge relationships as a terminal tree")
    graph_parser.add_argument("--limit", type=int, default=5, help="Number of recent commits to map")
    graph_parser.add_argument("--project", default="p1", help="Project ID to filter by")

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
    elif args.command == "log":
        _handle_log(args)
    elif args.command == "graph":
        _handle_graph(args)


def _handle_init():
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

        api_key = getpass(f"Enter your {key_name} (input hidden): ").strip()
        if api_key:
            env_path = Path.cwd() / ".env"
            
            # Avoid leading blank lines; ensure trailing newline before appending
            needs_newline = False
            if env_path.exists() and env_path.stat().st_size > 0:
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content and not content.endswith("\n"):
                        needs_newline = True

            with open(env_path, "a", encoding="utf-8") as f:
                if needs_newline:
                    f.write("\n")
                f.write(f"{key_name}={api_key}\n")

            # Update current process environment
            os.environ[key_name] = api_key
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"{key_name} saved to .env file.")
        else:
            print("Warning: No API key provided. LORE-X may fail during extraction.")

    # Manage .gitignore entries
    gitignore_path = Path(".gitignore")
    ignores = ["# LORE-X", "lorex.db", ".env"]
    existing_lines = []
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing_lines = [line.strip() for line in f.readlines()]

    missing_ignores = [item for item in ignores if item not in existing_lines]
    if missing_ignores:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            if gitignore_path.stat().st_size > 0 and not existing_lines[-1] == "":
                f.write("\n")
            for item in missing_ignores:
                f.write(f"{item}\n")

    from lorex.db.session import init_db

    init_db()
    print("Database initialized successfully.")

    hook_dir = Path(".git") / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hook_dir / "post-commit"
    hook_content = (
        "#!/bin/sh\n"
        "# Automatically ingest the latest commit into LORE-X\n"
        "lorex ingest . --limit 1 > /dev/null 2>&1 &\n"
    )
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)
    hook_path.chmod(0o755)
    print("Git post-commit hook successfully initialized and made executable.")


def _handle_query(args):
    from lorex.db.session import get_session, init_db
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
            for exp, score in results:
                print(f"- [{exp.status}] {exp.action} (Score: {score:.2f})")
        finally:
            session.close()
    except Exception as e:
        print(f"Error during query: {e}", file=sys.stderr)
        sys.exit(1)


def _handle_ingest(args):
    # Ensure target repository's .env takes precedence if specified
    repo_env = Path(args.repo_path).resolve() / ".env"
    if repo_env.exists():
        load_dotenv(dotenv_path=repo_env, override=True)
    else:
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=True)

    supported_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    if not any(os.getenv(k) for k in supported_keys):
        sys.stderr.write(
            "Warning: No LLM API keys detected. Extraction may fail or fallback to basic parsing.\n"
        )

    from lorex.db.session import get_session, init_db
    from lorex.vcs.local_git import GitLogIngester

    try:
        init_db()
        session = get_session()
        try:
            ingester = GitLogIngester()
            asyncio.run(
                ingester.ingest_repository(
                    args.repo_path, args.project, session, limit=args.limit
                )
            )
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


def _handle_log(args):
    from rich.console import Console
    from rich.table import Table
    from lorex.db.session import get_session, init_db
    from lorex.db.schema import Experience

    console = Console()
    try:
        init_db()
        session = get_session()
        try:
            # Order by created_at if present, otherwise fall back to primary key id
            order_col = getattr(Experience, "created_at", getattr(Experience, "id", None))
            query = session.query(Experience).filter(Experience.project_id == args.project)
            
            if order_col is not None:
                experiences = query.order_by(order_col.desc()).limit(args.limit).all()
            else:
                experiences = query.limit(args.limit).all()

            if not experiences:
                console.print(f"[yellow]No extractions found for project '{args.project}'.[/yellow]")
                return

            table = Table(title=f"LORE-X Extraction History ({args.project})", show_lines=True)
            table.add_column("Commit", style="cyan", no_wrap=True)
            table.add_column("Status", justify="center")
            table.add_column("Problem", style="magenta")
            table.add_column("Action", style="green")

            for exp in experiences:
                status_color = "green" if exp.status == "VERIFIED" else "yellow"
                short_hash = (exp.commit_hash or "unknown")[:7]
                problem_trunc = exp.problem[:60] + "..." if len(exp.problem) > 60 else exp.problem
                action_trunc = exp.action[:60] + "..." if len(exp.action) > 60 else exp.action
                
                table.add_row(
                    short_hash,
                    f"[{status_color}]{exp.status}[/{status_color}]",
                    problem_trunc,
                    action_trunc
                )
            
            console.print(table)
        finally:
            session.close()
    except Exception as e:
        console.print(f"[red]Error fetching logs: {e}[/red]")


def _handle_graph(args):
    from rich.console import Console
    from rich.tree import Tree
    from lorex.db.session import get_session, init_db
    from lorex.db.schema import Experience

    console = Console()
    try:
        init_db()
        session = get_session()
        try:
            order_col = getattr(Experience, "created_at", getattr(Experience, "id", None))
            query = session.query(Experience).filter(Experience.project_id == args.project)
            
            if order_col is not None:
                experiences = query.order_by(order_col.desc()).limit(args.limit).all()
            else:
                experiences = query.limit(args.limit).all()

            if not experiences:
                console.print(f"[yellow]No data available to graph for project '{args.project}'.[/yellow]")
                return

            root = Tree(f"🧠 [bold green]LORE-X Knowledge Graph ({args.project})[/bold green]")

            for exp in experiences:
                short_hash = (exp.commit_hash or "unknown")[:7]
                commit_node = root.add(f"[cyan]Commit {short_hash}[/cyan]")
                problem_node = commit_node.add(f"[red]Problem:[/red] {exp.problem}")
                action_node = problem_node.add(f"[blue]Action:[/blue] {exp.action}")
                
                # Check for context/cause and outcome dynamically
                context_val = getattr(exp, "context", getattr(exp, "cause", None))
                if context_val:
                    action_node.add(f"[yellow]Context/Cause:[/yellow] {context_val}")
                if getattr(exp, "outcome", None):
                    action_node.add(f"[magenta]Outcome:[/magenta] {exp.outcome}")

            console.print(root)
        finally:
            session.close()
    except Exception as e:
        console.print(f"[red]Error generating graph: {e}[/red]")

if __name__ == "__main__":
    main()