"""
Billing Agent - Handles billing issues, refunds, and payment problems.
"""

from typing import Dict, Any

from src.agents.base import BaseAgent
from src.agents.prompts.billing import BILLING_AGENT_PROMPT
from src.llm.client import get_llm_client
from src.observability.decorators import trace_agent
from src.tools.registry import get_tool_registry
from src.tools.database import DatabaseQueryInput
from src.tools.payment import RefundInput
from src.tools.email import EmailInput


class BillingAgent(BaseAgent):
    """
    Billing agent that handles payment and refund issues.
    """

    def __init__(self):
        super().__init__(name="billing")
        self.llm_client = get_llm_client()
        self.tool_registry = get_tool_registry()

    @trace_agent("billing")
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle billing issue.

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

        # Get payment history
        tool_calls = []
        payment_history = None

        db_tool = self.tool_registry.get("database_query")
        if db_tool and customer_id:
            result = await db_tool.execute(
                DatabaseQueryInput(
                    query_type="payment_history",
                    customer_id=customer_id,
                    limit=5,
                )
            )
            if result.success:
                payment_history = result.result
                tool_calls.append({
                    "tool": "database_query",
                    "input": {"query_type": "payment_history", "customer_id": customer_id},
                    "output": payment_history,
                })

        # Build context for LLM
        context = f"""Ticket: {subject}
Description: {body}

Customer ID: {customer_id}
Tier: {customer_context.get('tier', 'unknown')}

Payment History (last 5):
{self._format_payment_history(payment_history) if payment_history else 'Not available'}

Analyze this billing issue and provide a solution. If you need to process a refund, indicate that clearly in your response."""

        # Get LLM response
        response = await self.llm_client.generate(
            system=BILLING_AGENT_PROMPT,
            user_message=context,
            agent_name="billing",
        )

        resolution_text = response.content

        # Check if LLM explicitly signals to process a refund
        if "ACTION: PROCESS_REFUND" in resolution_text and payment_history and payment_history.get("payments"):
            # Process refund for the most recent payment
            recent_payment = payment_history["payments"][0]

            payment_tool = self.tool_registry.get("payment_gateway")
            if payment_tool:
                refund_result = await payment_tool.execute(
                    RefundInput(
                        payment_id=recent_payment["payment_id"],
                        customer_id=customer_id,
                        amount=recent_payment["amount"],
                        reason=f"Issue: {subject[:100]}",
                    )
                )

                if refund_result.success and refund_result.result.get("success"):
                    tool_calls.append({
                        "tool": "payment_gateway",
                        "input": {"payment_id": recent_payment["payment_id"], "amount": recent_payment["amount"]},
                        "output": refund_result.result,
                    })

        # Send confirmation email
        email_tool = self.tool_registry.get("email_sender")
        if email_tool:
            customer_email = customer_context.get("email", "customer@example.com")
            email_result = await email_tool.execute(
                EmailInput(
                    to=customer_email,
                    subject=f"Re: {subject}",
                    body=resolution_text[:500],  # Truncate for email
                )
            )

            if email_result.success:
                tool_calls.append({
                    "tool": "email_sender",
                    "input": {"to": customer_email, "subject": f"Re: {subject}"},
                    "output": email_result.result,
                })

        # Log decision
        self.log_decision(
            decision="Billing issue resolved",
            reasoning="Investigated payment history and provided solution",
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
            "agent_name": "billing_agent",
            "timestamp": state.get("timestamp"),
            "action": "resolve",
            "reasoning": "Processed billing issue with payment tools",
            "tool_calls": tool_calls,
            "result": "Issue resolved",
        })

        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        if "token_usage" not in state["metadata"]:
            state["metadata"]["token_usage"] = {}

        state["metadata"]["token_usage"]["billing"] = {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
        }

        return state

    def _format_payment_history(self, payment_history: Dict[str, Any]) -> str:
        """Format payment history for LLM context."""
        if not payment_history or not payment_history.get("payments"):
            return "No payment history found"

        lines = []
        for payment in payment_history["payments"]:
            lines.append(
                f"- {payment['date']}: ${payment['amount']:.2f} ({payment['status']}) - {payment['description']}"
            )
        return "\n".join(lines)
