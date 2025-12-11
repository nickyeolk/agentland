"""
Escalation Agent - Handles complex issues and determines human escalation.
"""

from typing import Dict, Any

from src.agents.base import BaseAgent
from src.agents.prompts.escalation import ESCALATION_AGENT_PROMPT
from src.llm.client import get_llm_client
from src.observability.decorators import trace_agent
from src.tools.registry import get_tool_registry
from src.tools.database import DatabaseQueryInput
from src.tools.knowledge_base import KnowledgeBaseInput


class EscalationAgent(BaseAgent):
    """
    Escalation agent that handles complex issues requiring advanced resolution.
    """

    def __init__(self):
        super().__init__(name="escalation")
        self.llm_client = get_llm_client()
        self.tool_registry = get_tool_registry()

    @trace_agent("escalation")
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle escalated issue.

        Args:
            state: Current agent state

        Returns:
            Updated state with resolution or escalation to human
        """
        # Extract information
        ticket_content = state.get("ticket_content", {})
        subject = ticket_content.get("subject", "")
        body = ticket_content.get("body", "")
        customer_context = state.get("customer_context", {})
        customer_id = customer_context.get("customer_id", "")

        # Gather comprehensive context
        tool_calls = []

        # Get customer info
        customer_info = None
        db_tool = self.tool_registry.get("database_query")
        if db_tool and customer_id:
            result = await db_tool.execute(
                DatabaseQueryInput(
                    query_type="customer_info",
                    customer_id=customer_id,
                )
            )
            if result.success:
                customer_info = result.result
                tool_calls.append({
                    "tool": "database_query",
                    "input": {"query_type": "customer_info"},
                    "output": customer_info,
                })

            # Get ticket history
            history_result = await db_tool.execute(
                DatabaseQueryInput(
                    query_type="ticket_history",
                    customer_id=customer_id,
                    limit=10,
                )
            )
            if history_result.success:
                tool_calls.append({
                    "tool": "database_query",
                    "input": {"query_type": "ticket_history"},
                    "output": history_result.result,
                })

        # Search knowledge base for any relevant info
        kb_tool = self.tool_registry.get("knowledge_base")
        if kb_tool:
            result = await kb_tool.execute(
                KnowledgeBaseInput(
                    query=subject,
                    category="all",
                    max_results=5,
                )
            )
            if result.success:
                tool_calls.append({
                    "tool": "knowledge_base",
                    "input": {"query": subject},
                    "output": result.result,
                })

        # Build comprehensive context
        context = f"""Complex/Escalated Issue: {subject}
Description: {body}

Customer Information:
- Customer ID: {customer_id}
- Tier: {customer_context.get('tier', 'unknown')}
- Account Status: {customer_info.get('customer', {}).get('account_status', 'unknown') if customer_info else 'unknown'}

Previous Interactions: {len(state.get('agent_interactions', []))} prior agent(s) worked on this

Routing History:
{self._format_routing_history(state)}

Analyze this complex issue thoroughly. Determine if you can resolve it or if it requires human escalation. If escalating to human, clearly state why."""

        # Get LLM response
        response = await self.llm_client.generate(
            system=ESCALATION_AGENT_PROMPT,
            user_message=context,
            agent_name="escalation",
        )

        resolution_text = response.content

        # Determine if human escalation is needed
        requires_human = self._check_human_escalation_needed(resolution_text)

        # Log decision
        self.log_decision(
            decision="Escalated to human" if requires_human else "Resolved complex issue",
            reasoning=resolution_text[:200],
            confidence=0.7 if requires_human else 0.8,
        )

        # Update state
        state["resolution"] = {
            "status": "escalated" if requires_human else "resolved",
            "response": resolution_text,
            "requires_human": requires_human,
        }

        if "agent_interactions" not in state:
            state["agent_interactions"] = []

        state["agent_interactions"].append({
            "agent_name": "escalation_agent",
            "timestamp": state.get("timestamp"),
            "action": "escalate" if requires_human else "resolve_complex",
            "reasoning": "Comprehensive analysis of complex issue",
            "tool_calls": tool_calls,
            "result": "Escalated to human" if requires_human else "Complex issue resolved",
        })

        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        if "token_usage" not in state["metadata"]:
            state["metadata"]["token_usage"] = {}

        state["metadata"]["token_usage"]["escalation"] = {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
        }

        return state

    def _format_routing_history(self, state: Dict[str, Any]) -> str:
        """Format routing history for context."""
        interactions = state.get("agent_interactions", [])
        if not interactions:
            return "No previous routing"

        history = []
        for interaction in interactions:
            history.append(f"- {interaction['agent_name']}: {interaction.get('action', 'N/A')}")
        return "\n".join(history)

    def _check_human_escalation_needed(self, response: str) -> bool:
        """
        Determine if human escalation is needed based on response.

        Args:
            response: LLM response text

        Returns:
            True if human escalation is needed
        """
        # Keywords indicating human escalation
        escalation_keywords = [
            "escalat",
            "human",
            "manual review",
            "legal",
            "compliance",
            "policy exception",
            "beyond my capability",
            "specialized expertise",
        ]

        response_lower = response.lower()
        return any(keyword in response_lower for keyword in escalation_keywords)
