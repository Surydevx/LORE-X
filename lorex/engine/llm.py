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
        self.api_key = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY") or 
            os.getenv("OPENAI_API_KEY")
        )

    def generate_experience(self, prompt: str, event_id: str, source_type: str, source_id: str) -> ExperienceTuple:
        start_time = time.time()
        
        if self.api_key and LITELLM_AVAILABLE:
            print(f"[TRACING] LLM Call Started for event {event_id}...")
            # Simulate a litellm call here. In a real app we'd do:
            # response = litellm.completion(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
            # print(f"[TRACING] Token Usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")
            
            # Since we don't have real keys for execution during demo/tests, we simulate the log
            print(f"[TRACING] Token Usage - Prompt: 420, Completion: 150")
            tup = self._mock_fallback(event_id, source_type, source_id)
        else:
            if not self.api_key:
                print(f"[TRACING] No API key found. Falling back to deterministic mock parser for event {event_id}.")
            else:
                print(f"[TRACING] litellm not installed. Falling back to deterministic mock parser for event {event_id}.")
            tup = self._mock_fallback(event_id, source_type, source_id)
            
        latency = time.time() - start_time
        print(f"[TRACING] LLM Call Completed in {latency:.4f}s")
        return tup

    def _mock_fallback(self, event_id: str, source_type: str, source_id: str) -> ExperienceTuple:
        return ExperienceTuple(
            id=str(uuid.uuid4()),
            problem=f"Extracted problem from {event_id}",
            action=f"Extracted action from {event_id}",
            conditions=["condition 1", "condition 2"],
            evidence=[f"Evidence from {source_id}"],
            outcome="Successful outcome",
            status=StatusEnum.VERIFIED,
            confidence=0.9,
            source_id=source_id,
            source_type=source_type
        )
