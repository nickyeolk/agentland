"""
Account Agent - Handles account management and security.
"""

from typing import Dict, Any

from src.agents.base import BaseAgent
from src.agents.prompts.account import ACCOUNT_AGENT_PROMPT
from src.llm.client import get_llm_client
from src.observability.decorators import trace_agent
from src.tools.registry import get_tool_registry
from src.tools.database import DatabaseQueryInput
from src.tools.email import EmailInput


class AccountAgent(BaseAgent):
    """
    Account agent that handles account management and security issues.
    """

    def __init__(self):
        super().__init__(name="account")
        self.llm_client = get_llm_client()
        self.tool_registry = get_tool_registry()

    @trace_agent("account")
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle account issue.

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
        customer_id = customer_context.get("customer_id", "")

        # Get customer info from database
        tool_calls = []
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
                    "input": {"query_type": "customer_info", "customer_id": customer_id},
                    "output": customer_info,
                })

        # Build context for LLM
        account_context = ""
        if customer_info and customer_info.get("customer"):
            cust = customer_info["customer"]
            account_context = f"""
Account Information:
- Name: {cust.get('name', 'N/A')}
- Email: {cust.get('email', 'N/A')}
- Status: {cust.get('account_status', 'N/A')}
- Tier: {cust.get('tier', 'N/A')}
- Joined: {cust.get('joined_date', 'N/A')}
"""

        context = f"""Account Issue: {subject}
Description: {body}

Customer ID: {customer_id}
{account_context}

Help this customer with their account-related issue. For security-sensitive actions like password resets, indicate that you're sending them via email."""

        # Get LLM response
        response = await self.llm_client.generate(
            system=ACCOUNT_AGENT_PROMPT,
            user_message=context,
            agent_name="account",
        )

        resolution_text = response.content

        # Send email for account actions
        email_tool = self.tool_registry.get("email_sender")
        if email_tool:
            customer_email = customer_context.get("email") or (
                customer_info.get("customer", {}).get("email") if customer_info else "customer@example.com"
            )

            # Determine email type based on issue
            email_subject = f"Account Update: {subject}"
            if "password" in subject.lower() or "password" in body.lower():
                email_subject = "Password Reset Link"

            email_result = await email_tool.execute(
                EmailInput(
                    to=customer_email,
                    subject=email_subject,
                    body=resolution_text[:500],
                )
            )

            if email_result.success:
                tool_calls.append({
                    "tool": "email_sender",
                    "input": {"to": customer_email, "subject": email_subject},
                    "output": email_result.result,
                })

        # Log decision
        self.log_decision(
            decision="Account issue resolved",
            reasoning="Verified account details and provided solution",
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
            "agent_name": "account_agent",
            "timestamp": state.get("timestamp"),
            "action": "account_management",
            "reasoning": "Handled account issue with database lookup",
            "tool_calls": tool_calls,
            "result": "Account issue resolved",
        })

        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        if "token_usage" not in state["metadata"]:
            state["metadata"]["token_usage"] = {}

        state["metadata"]["token_usage"]["account"] = {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
        }

        return state
