"""
Technical Agent - Handles technical issues and troubleshooting.
"""

from typing import Dict, Any

from src.agents.base import BaseAgent
from src.agents.prompts.technical import TECHNICAL_AGENT_PROMPT
from src.llm.client import get_llm_client
from src.observability.decorators import trace_agent
from src.tools.registry import get_tool_registry
from src.tools.knowledge_base import KnowledgeBaseInput
from src.tools.email import EmailInput


class TechnicalAgent(BaseAgent):
    """
    Technical agent that handles technical problems and troubleshooting.
    """

    def __init__(self):
        super().__init__(name="technical")
        self.llm_client = get_llm_client()
        self.tool_registry = get_tool_registry()

    @trace_agent("technical")
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle technical issue.

        Args:
            state: Current agent state

        Returns:
            Updated state with resolution
        """
        # Extract information
        ticket_content = state.get("ticket_content", {})
        subject = ticket_content.get("subject", "")
        body = ticket_content.get("body", "")
        customer_context = state.get("customer_context", {})

        # Search knowledge base
        tool_calls = []
        kb_results = None

        kb_tool = self.tool_registry.get("knowledge_base")
        if kb_tool:
            # Extract keywords from subject for KB search
            search_query = subject
            result = await kb_tool.execute(
                KnowledgeBaseInput(
                    query=search_query,
                    category="technical",
                    max_results=3,
                )
            )

            if result.success:
                kb_results = result.result
                tool_calls.append({
                    "tool": "knowledge_base",
                    "input": {"query": search_query, "category": "technical"},
                    "output": kb_results,
                })

        # Build context for LLM
        kb_context = ""
        if kb_results and kb_results.get("results"):
            kb_context = "\n\nRelevant Knowledge Base Articles:\n"
            for article in kb_results["results"]:
                kb_context += f"- [{article['id']}] {article['title']}: {article['content'][:200]}...\n"

        context = f"""Technical Issue: {subject}
Description: {body}

Customer: {customer_context.get('customer_id', 'unknown')}
Tier: {customer_context.get('tier', 'unknown')}
{kb_context}

Provide step-by-step troubleshooting guidance for this technical issue."""

        # Get LLM response
        response = await self.llm_client.generate(
            system=TECHNICAL_AGENT_PROMPT,
            user_message=context,
            agent_name="technical",
        )

        resolution_text = response.content

        # Send detailed guide via email
        email_tool = self.tool_registry.get("email_sender")
        if email_tool:
            customer_email = customer_context.get("email", "customer@example.com")
            email_result = await email_tool.execute(
                EmailInput(
                    to=customer_email,
                    subject=f"Technical Support: {subject}",
                    body=f"Here's the detailed troubleshooting guide:\n\n{resolution_text}",
                )
            )

            if email_result.success:
                tool_calls.append({
                    "tool": "email_sender",
                    "input": {"to": customer_email},
                    "output": email_result.result,
                })

        # Log decision
        self.log_decision(
            decision="Technical issue resolved",
            reasoning="Provided troubleshooting steps based on KB articles",
        )

        # Update state
        state["resolution"] = {
            "status": "resolved",
            "response": resolution_text,
            "requires_human": False,
        }

        if "agent_interactions" not in state:
            state["agent_interactions"] = []

        state["agent_interactions"].append({
            "agent_name": "technical_agent",
            "timestamp": state.get("timestamp"),
            "action": "troubleshoot",
            "reasoning": "Searched KB and provided technical guidance",
            "tool_calls": tool_calls,
            "result": "Troubleshooting guide provided",
        })

        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        if "token_usage" not in state["metadata"]:
            state["metadata"]["token_usage"] = {}

        state["metadata"]["token_usage"]["technical"] = {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
        }

        return state
