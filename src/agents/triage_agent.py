"""
Triage Agent - Routes incoming tickets to appropriate specialist agents.
"""

import re
from typing import Dict, Any

from src.agents.base import BaseAgent
from src.agents.prompts.triage import TRIAGE_AGENT_PROMPT
from src.llm.client import get_llm_client
from src.observability.decorators import trace_agent
from src.tools.registry import get_tool_registry


class TriageAgent(BaseAgent):
    """
    Triage agent that analyzes tickets and routes to specialists.
    """

    def __init__(self):
        super().__init__(name="triage")
        self.llm_client = get_llm_client()
        self.tool_registry = get_tool_registry()

    @trace_agent("triage")
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze ticket and determine routing.

        Args:
            state: Current agent state with ticket information

        Returns:
            Updated state with routing decision
        """
        # Extract ticket information
        ticket_content = state.get("ticket_content", {})
        subject = ticket_content.get("subject", "")
        body = ticket_content.get("body", "")
        customer_context = state.get("customer_context", {})

        # Optionally get customer info from database
        customer_id = customer_context.get("customer_id", "")
        if customer_id:
            db_tool = self.tool_registry.get("database_query")
            if db_tool:
                from src.tools.database import DatabaseQueryInput
                result = await db_tool.execute(
                    DatabaseQueryInput(
                        query_type="customer_info",
                        customer_id=customer_id,
                    )
                )
                if result.success and result.result.get("found"):
                    customer_context["tier"] = result.result["customer"]["tier"]
                    customer_context["account_status"] = result.result["customer"]["account_status"]

        # Build user message with context
        user_message = f"""Customer Ticket:
Subject: {subject}
Body: {body}

Customer Context:
- Customer ID: {customer_id}
- Tier: {customer_context.get('tier', 'unknown')}
- Account Status: {customer_context.get('account_status', 'unknown')}

Analyze this ticket and provide your routing decision."""

        # Get LLM decision
        response = await self.llm_client.generate(
            system=TRIAGE_AGENT_PROMPT,
            user_message=user_message,
            agent_name="triage",
        )

        # Parse response
        routing_decision = self._parse_routing_response(response.content)

        # Log decision
        self.log_decision(
            decision=f"Route to {routing_decision['assigned_agent']}",
            reasoning=routing_decision.get("reasoning"),
            confidence=routing_decision.get("confidence_score"),
            urgency=routing_decision.get("urgency"),
        )

        # Update state
        state["routing"] = routing_decision
        if "agent_interactions" not in state:
            state["agent_interactions"] = []

        state["agent_interactions"].append({
            "agent_name": "triage_agent",
            "timestamp": state.get("timestamp"),
            "action": "route",
            "reasoning": routing_decision.get("reasoning"),
            "tool_calls": [],
            "result": f"Routed to {routing_decision['assigned_agent']}",
        })

        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        if "token_usage" not in state["metadata"]:
            state["metadata"]["token_usage"] = {}

        state["metadata"]["token_usage"]["triage"] = {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
        }

        return state

    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract routing decision.

        Args:
            response: Raw LLM response

        Returns:
            Parsed routing decision
        """
        # Initialize default values
        routing = {
            "assigned_agent": "escalation_agent",
            "urgency": "medium",
            "confidence_score": 0.5,
            "reasoning": "Could not parse routing decision",
        }

        # Parse using regex
        route_match = re.search(r"ROUTE:\s*(\w+)", response, re.IGNORECASE)
        urgency_match = re.search(r"URGENCY:\s*(\w+)", response, re.IGNORECASE)
        confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", response, re.IGNORECASE)
        reasoning_match = re.search(r"REASONING:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)

        if route_match:
            routing["assigned_agent"] = route_match.group(1).strip()

        if urgency_match:
            routing["urgency"] = urgency_match.group(1).strip().lower()

        if confidence_match:
            try:
                routing["confidence_score"] = float(confidence_match.group(1).strip())
            except ValueError:
                pass

        if reasoning_match:
            routing["reasoning"] = reasoning_match.group(1).strip()

        return routing
