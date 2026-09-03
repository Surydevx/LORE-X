import os
import uuid
import json
import time
from lorex.core.models import ExperienceTuple, StatusEnum

try:
    import litellm
    # Configure basic callbacks if needed, litellm supports logging out of the box
    litellm.success_callback = ["console"]
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

class LLMClient:
    def __init__(self):
        # 1. Manually load .env into os.environ if it exists in the current directory
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        os.environ[key] = val

        # 2. Now check the environment for keys
        self.api_key = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY") or 
            os.getenv("OPENAI_API_KEY")
        )

    def generate_experience(self, prompt: str, event_id: str, source_type: str, source_id: str) -> ExperienceTuple:
        start_time = time.time()
        
        if not self.api_key or not LITELLM_AVAILABLE:
            raise ValueError("No API key or litellm not available")
            
        print(f"[TRACING] LLM Call Started for event {event_id}...")
        
        model_name = "gemini/gemini-1.5-flash-latest"
        if os.getenv("OPENAI_API_KEY"):
            model_name = "gpt-4o-mini"
        elif os.getenv("ANTHROPIC_API_KEY"):
            model_name = "claude-3-haiku-20240307"
            
        sys_prompt = """You are an architectural memory extractor. Extract the engineering decision into JSON matching this schema:
{
    "problem": "The issue",
    "action": "The decision made",
    "conditions": ["condition1", "condition2"],
    "outcome": "The result",
    "status": "VERIFIED"
}
Status must be one of: VERIFIED, PARTIALLY_VERIFIED, CONDITIONALLY_VALID, SUPERSEDED, FAILED."""

        response = litellm.completion(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        if hasattr(response, 'usage'):
            print(f"[TRACING] Token Usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")
            
        content = response.choices[0].message.content
        data = json.loads(content)
        
        latency = time.time() - start_time
        print(f"[TRACING] LLM Call Completed in {latency:.4f}s")
        
        return ExperienceTuple(
            id=str(uuid.uuid4()),
            problem=data.get("problem", "Unknown problem"),
            action=data.get("action", "Unknown action"),
            conditions=data.get("conditions", []),
            evidence=[f"Extracted from {source_id}"],
            outcome=data.get("outcome", "Unknown outcome"),
            status=StatusEnum(data.get("status", "VERIFIED")),
            confidence=0.9,
            source_id=source_id,
            source_type=source_type
        )
