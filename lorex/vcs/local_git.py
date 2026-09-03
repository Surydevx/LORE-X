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
        cmd = f"git -C {repo_path} log -n{limit} --stat -p"
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
        
        events = []
        for c in commits_raw:
            if not c.strip():
                continue
            
            lines = c.split("\n")
            commit_hash = lines[0].strip()
            author = "Unknown"
            
            for line in lines:
                if line.startswith("Author:"):
                    author = line.replace("Author:", "").strip()
                    break
            
            event = EngineeringEvent(
                id=str(uuid.uuid4()),
                project_id=project_id,
                source_type="git_commit",
                source_id=commit_hash,
                timestamp=datetime.now(timezone.utc),
                author=author,
                content="commit " + c
            )
            session.add(event)
            events.append(event)
            
        session.commit()
        
        # Concurrently process extraction via LLMClient
        async def extract_and_persist(evt):
            # simulate async LLM call (if LLMClient was async we'd await it, for now we run it synchronously in thread or assume it is fast)
            # Since LLMClient generation is sync in our code, we will just call it.
            # To be truly async we should use asyncio.to_thread if it's blocking.
            tup = await asyncio.to_thread(self.extractor.extract_from_event, evt)
            # persist_experience requires session. We will do it synchronously inside the loop to avoid SQLite locking issues
            return tup
            
        tuples = await asyncio.gather(*(extract_and_persist(evt) for evt in events))
        
        extracted_experiences = []
        for tup in tuples:
            exp = self.extractor.persist_experience(tup, project_id, session)
            extracted_experiences.append(exp)
            
        return extracted_experiences
