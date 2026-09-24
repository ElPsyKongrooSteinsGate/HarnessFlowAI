import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GatewayResponse(BaseModel):
    text: Optional[str] = None
    tool_calls: List[Any] = []
    is_complete: bool = False
    provider_used: str

class ModelGateway:
    def __init__(self, providers: List[str]):
        self.providers = providers  # Order of preference, e.g., ["claude-3-5-sonnet", "gpt-4o"]

    async def generate_completion(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> GatewayResponse:
        last_exception = None
        
        for provider in self.providers:
            try:
                # Abstract call to concrete provider API
                response = await self._dispatch_call(provider, messages, tools)
                return response
            except Exception as e:
                last_exception = e
                # Fallback to next provider on rate limits, timeouts, or 5xx errors
                continue
                
        raise RuntimeError(f"All Model Gateway providers failed. Last error: {last_exception}")

    async def _dispatch_call(self, provider: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> GatewayResponse:
        # Implementation details for OpenAI/Anthropic/Gemini client invocation
        ...