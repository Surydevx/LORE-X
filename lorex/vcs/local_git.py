import asyncio
import shlex
import sys
import uuid
from datetime import datetime, timezone
from lorex.db.schema import EngineeringEvent, Experience, Project
from lorex.engine.extraction import ExperienceExtractor
from lorex.db.session import SessionLocal

# Unique separator that won't appear in diffs
_RECORD_SEP = "---LOREX_COMMIT_SEP---"

class GitLogIngester:
    def __init__(self):
        self.extractor = ExperienceExtractor()

    async def ingest_repository(self, repo_path: str, project_id: str, session, limit: int = 10) -> list:
        # Ensure project exists
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            project = Project(id=project_id, name=f"Project {project_id}")
            session.add(project)
            session.commit()

        # Run git log asynchronously — use create_subprocess_exec to prevent shell injection (C4)
        format_str = f"{_RECORD_SEP}%H%nAuthorName: %an%nAuthorEmail: %ae%nDate: %aI%n%n%B"
        process = await asyncio.create_subprocess_exec(
            "git", "-C", repo_path, "log",
            f"-n{limit}",
            f"--format={format_str}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to run git log in {repo_path}: {stderr.decode(errors='replace')}")

        log_output = stdout.decode(errors="replace")
        commits_raw = log_output.split(_RECORD_SEP)
        
        # Idempotency: check existing commit hashes (C3 — use commit_hash, not source_id)
        existing_hashes = {
            row[0] for row in session.query(Experience.commit_hash).filter(
                Experience.commit_hash.isnot(None)
            ).all()
        }
        
        events = []
        skip_keywords = ["lint", "typo", "bump", "format", "merge"]
        
        for c in commits_raw:
            if not c.strip():
                continue
            
            lines = c.split("\n")
            commit_hash = lines[0].strip()
            if not commit_hash or len(commit_hash) < 7:
                continue
            if commit_hash in existing_hashes:
                print(f"Skipping already ingested commit: {commit_hash[:7]}")
                continue
                
            author_name = "Unknown"
            author_email = "Unknown"
            committed_at = None
            
            message_lines = []
            parsing_message = False
            for line in lines[1:]:
                if line.startswith("AuthorName:"):
                    author_name = line.replace("AuthorName:", "").strip()
                elif line.startswith("AuthorEmail:"):
                    author_email = line.replace("AuthorEmail:", "").strip()
                elif line.startswith("Date:"):
                    date_str = line.replace("Date:", "").strip()
                    try:
                        committed_at = datetime.fromisoformat(date_str)
                    except ValueError:
                        committed_at = datetime.now(timezone.utc)
                    parsing_message = True
                elif parsing_message and line.strip():
                    message_lines.append(line.strip())
                    
            message = " ".join(message_lines).lower()
            
            # Heuristic Filtering — only against commit message, not diffstat (H8)
            if len(message) < 30:
                continue
            # Use word boundary matching to avoid false positives (H8)
            if any(f" {keyword} " in f" {message} " for keyword in skip_keywords):
                continue
            
            event = EngineeringEvent(
                id=str(uuid.uuid4()),
                project_id=project_id,
                source_type="git_commit",
                source_id=commit_hash,
                timestamp=datetime.now(timezone.utc),
                author=author_name,
                commit_hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                committed_at=committed_at,
                content="\n".join(message_lines)
            )
            session.add(event)
            events.append(event)
            
        session.commit()
        
        # Concurrency Throttling via Semaphore
        # Use per-thread sessions to avoid thread-safety violations (H6)
        sem = asyncio.Semaphore(5)
        
        async def throttled_extract(evt):
            async with sem:
                def _extract_in_thread():
                    # Create a dedicated session for this thread
                    thread_session = SessionLocal()
                    try:
                        # Re-fetch event in this thread's session to avoid lazy-load issues
                        local_evt = thread_session.query(EngineeringEvent).get(evt.id)
                        if local_evt is None:
                            return None
                        tup = self.extractor.extract_from_event(local_evt)
                        return tup
                    finally:
                        thread_session.close()
                
                tup = await asyncio.to_thread(_extract_in_thread)
                return tup, evt
                
        results = await asyncio.gather(*(throttled_extract(evt) for evt in events))
        
        extracted_experiences = []
        for tup, evt in results:
            if tup is None:
                continue
            exp = self.extractor.persist_experience(tup, project_id, session)
            exp.commit_hash = evt.commit_hash
            exp.author = evt.author_name
            exp.source = f"Commit {evt.commit_hash[:7]} by {evt.author_name} <{evt.author_email}>"
            extracted_experiences.append(exp)
            
        session.commit()
        return extracted_experiences
