import asyncio
import uuid
from datetime import datetime, timezone
from lorex.db.schema import EngineeringEvent, Project
from lorex.engine.extraction import ExperienceExtractor

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

        # Run git log asynchronously
        cmd = f'git -C {repo_path} log -n{limit} --format="commit %H%nAuthorName: %an%nAuthorEmail: %ae%nDate: %aI%n%n%B" --stat -p'
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to run git log in {repo_path}: {stderr.decode()}")

        log_output = stdout.decode()
        commits_raw = log_output.split("commit ")
        
        from lorex.db.schema import Experience
        existing_hashes = {record.source_id for record in session.query(Experience.source_id).all()}
        
        events = []
        skip_keywords = ["lint", "typo", "bump", "docs", "format", "ignore", "merge"]
        
        for c in commits_raw:
            if not c.strip():
                continue
            
            lines = c.split("\n")
            commit_hash = lines[0].strip()
            if commit_hash in existing_hashes:
                print(f"Skipping already ingested commit: {commit_hash[:7]}")
                continue
                
            author_name = "Unknown"
            author_email = "Unknown"
            committed_at = None
            
            message_lines = []
            parsing_message = False
            for line in lines:
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
                elif parsing_message and line.strip() and not line.startswith("diff "):
                    message_lines.append(line.strip())
                elif line.startswith("diff "):
                    break
                    
            message = " ".join(message_lines).lower()
            
            # Heuristic Filtering
            if len(message) < 30:
                continue
            if any(keyword in message for keyword in skip_keywords):
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
                content="commit " + c
            )
            session.add(event)
            events.append(event)
            
        session.commit()
        
        # Concurrency Throttling via Semaphore
        sem = asyncio.Semaphore(5)
        
        async def throttled_extract(evt):
            async with sem:
                tup = await asyncio.to_thread(self.extractor.extract_from_event, evt)
                return tup, evt
                
        results = await asyncio.gather(*(throttled_extract(evt) for evt in events))
        
        extracted_experiences = []
        for tup, evt in results:
            exp = self.extractor.persist_experience(tup, project_id, session)
            exp.commit_hash = evt.commit_hash
            exp.author = evt.author_name
            exp.source = f"Commit {evt.commit_hash[:7]} by {evt.author_name} <{evt.author_email}>"
            extracted_experiences.append(exp)
            
        session.commit()
        return extracted_experiences
