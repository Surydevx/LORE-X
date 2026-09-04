import os
import re
import sys
import uuid
import json
import time
from lorex.core.models import ExperienceTuple, StatusEnum

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from LLM JSON responses."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

class LLMClient:
    def __init__(self):
        # 1. Manually load .env into os.environ if it exists in the current directory
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Strip whitespace and surrounding quotes (single or double)
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip(' "\'')

        # 2. Now check the environment for keys — consistent priority order
        self.api_key = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY")
        )

    def generate_experience(self, prompt: str, event_id: str, source_type: str, source_id: str) -> ExperienceTuple:
        start_time = time.time()
        
        if not self.api_key or not LITELLM_AVAILABLE:
            raise ValueError("No API key or litellm not available")
            
        print(f"[TRACING] LLM Call Started for event {event_id}...", file=sys.stderr)
        
        # Model routing — consistent with __init__ priority order
        model_name = "gemini/gemini-3.6-flash"
        completion_kwargs = {}
        
        if os.getenv("GEMINI_API_KEY"):
            model_name = "gemini/gemini-3.6-flash"
            completion_kwargs["response_format"] = {"type": "json_object"}
        elif os.getenv("OPENAI_API_KEY"):
            model_name = "gpt-4o-mini"
            completion_kwargs["response_format"] = {"type": "json_object"}
        elif os.getenv("ANTHROPIC_API_KEY"):
            model_name = "claude-3-haiku-20240307"
            # Anthropic does NOT support response_format — omit it
            
        sys_prompt = """You are an architectural memory extractor. Extract the engineering decision into JSON matching this schema:
{
    "problem": "The issue",
    "action": "The decision made",
    "conditions": ["condition1", "condition2"],
    "outcome": "The result",
    "status": "VERIFIED"
}
Status must be one of: VERIFIED, PARTIALLY_VERIFIED, CONDITIONALLY_VALID, SUPERSEDED, FAILED.
Return ONLY valid JSON. No markdown fences, no explanation."""

        try:
            response = litellm.completion(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                timeout=30,
                **completion_kwargs
            )
        except Exception as e:
            raise ValueError(f"LiteLLM API call failed: {str(e)}") from e
        
        if hasattr(response, 'usage') and response.usage:
            print(f"[TRACING] Token Usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}", file=sys.stderr)
        
        # Safe content extraction
        if not response.choices:
            raise ValueError("LLM returned empty choices")
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")
            
        # Strip markdown fences if present
        content = _strip_markdown_fences(content)
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {content[:200]}") from e
        
        if not isinstance(data, dict):
            raise ValueError(f"LLM returned non-object JSON: {type(data)}")
        
        latency = time.time() - start_time
        print(f"[TRACING] LLM Call Completed in {latency:.4f}s", file=sys.stderr)
        
        # Safe status parsing
        raw_status = data.get("status", "VERIFIED")
        try:
            status = StatusEnum(raw_status.upper() if isinstance(raw_status, str) else "VERIFIED")
        except ValueError:
            status = StatusEnum.VERIFIED
        
        # Safe conditions parsing
        conditions = data.get("conditions", [])
        if isinstance(conditions, str):
            conditions = [conditions]
        elif not isinstance(conditions, list):
            conditions = []
        
        return ExperienceTuple(
            id=str(uuid.uuid4()),
            problem=data.get("problem", "Unknown problem"),
            action=data.get("action", "Unknown action"),
            conditions=conditions,
            evidence=[f"Extracted from {source_id}"],
            outcome=data.get("outcome", "Unknown outcome"),
            status=status,
            confidence=0.9,
            source_id=source_id,
            source_type=source_type
        )
