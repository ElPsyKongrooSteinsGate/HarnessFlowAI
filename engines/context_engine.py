from typing import List, Dict, Any

class ContextEngine:
    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self.history: List[Dict[str, Any]] = []

    async def assemble_context(
        self,
        task: Any,
        memory: List[str],
        system_prompt: str,
        workflow_knowledge: List[str] | None = None,
        governance_knowledge: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        context = [{"role": "system", "content": system_prompt}]

        if workflow_knowledge:
            context.append({
                "role": "system",
                "content": "Workflow definition knowledge:\n" + "\n".join(workflow_knowledge),
            })

        if governance_knowledge:
            context.append({
                "role": "system",
                "content": "Governance policy knowledge:\n" + "\n".join(governance_knowledge),
            })
        
        # Inject long-term memory context
        if memory:
            context.append({"role": "system", "content": f"Relevant Context:\n" + "\n".join(memory)})

        # Append execution history while enforcing sliding window limits
        pruned_history = self._prune_to_token_limit(self.history, self.max_tokens - 2000)
        context.extend(pruned_history)
        
        return context

    async def add_observation(self, tool_call_id: str, output: str) -> None:
        # Truncate overly long observations to prevent token bloat
        truncated_output = output[:4000] + "\n...[Truncated]" if len(output) > 4000 else output
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": truncated_output
        })

    def _prune_to_token_limit(self, history: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        # Simple FIFO history pruner (production should use exact tokenizer estimation)
        return history[-20:]