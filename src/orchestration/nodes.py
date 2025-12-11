"""
Node functions for the agent workflow.

Each node wraps an agent and updates the state.
"""

from typing import Dict, Any
import time

from src.agents.triage_agent import TriageAgent
from src.agents.billing_agent import BillingAgent
from src.agents.technical_agent import TechnicalAgent
from src.agents.account_agent import AccountAgent
from src.agents.escalation_agent import EscalationAgent
from src.observability.logger import get_logger
from src.observability.tracer import trace_span

logger = get_logger(__name__)

# Global agent instances (initialized once)
_triage_agent = None
_billing_agent = None
_technical_agent = None
_account_agent = None
_escalation_agent = None


def get_triage_agent() -> TriageAgent:
    """Get or create triage agent instance."""
    global _triage_agent
    if _triage_agent is None:
        _triage_agent = TriageAgent()
    return _triage_agent


def get_billing_agent() -> BillingAgent:
    """Get or create billing agent instance."""
    global _billing_agent
    if _billing_agent is None:
        _billing_agent = BillingAgent()
    return _billing_agent


def get_technical_agent() -> TechnicalAgent:
    """Get or create technical agent instance."""
    global _technical_agent
    if _technical_agent is None:
        _technical_agent = TechnicalAgent()
    return _technical_agent


def get_account_agent() -> AccountAgent:
    """Get or create account agent instance."""
    global _account_agent
    if _account_agent is None:
        _account_agent = AccountAgent()
    return _account_agent


def get_escalation_agent() -> EscalationAgent:
    """Get or create escalation agent instance."""
    global _escalation_agent
    if _escalation_agent is None:
        _escalation_agent = EscalationAgent()
    return _escalation_agent


async def triage_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triage node - Analyze and route ticket.

    Args:
        state: Current state

    Returns:
        Updated state with routing decision
    """
    with trace_span("node.triage"):
        start_time = time.time()

        logger.info("node_started", node="triage", ticket_id=state.get("ticket_id"))

        agent = get_triage_agent()
        state = await agent.execute(state)

        duration_ms = int((time.time() - start_time) * 1000)
        if "metadata" in state and "latency_ms" in state["metadata"]:
            state["metadata"]["latency_ms"]["triage"] = duration_ms

        logger.info(
            "node_completed",
            node="triage",
            ticket_id=state.get("ticket_id"),
            assigned_agent=state.get("routing", {}).get("assigned_agent"),
            duration_ms=duration_ms,
        )

        return state


async def billing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Billing node - Handle billing issues.

    Args:
        state: Current state

    Returns:
        Updated state with resolution
    """
    with trace_span("node.billing"):
        start_time = time.time()

        logger.info("node_started", node="billing", ticket_id=state.get("ticket_id"))

        agent = get_billing_agent()
        state = await agent.execute(state)

        duration_ms = int((time.time() - start_time) * 1000)
        if "metadata" in state and "latency_ms" in state["metadata"]:
            state["metadata"]["latency_ms"]["billing"] = duration_ms

        logger.info(
            "node_completed",
            node="billing",
            ticket_id=state.get("ticket_id"),
            duration_ms=duration_ms,
        )

        return state


async def technical_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Technical node - Handle technical issues.

    Args:
        state: Current state

    Returns:
        Updated state with resolution
    """
    with trace_span("node.technical"):
        start_time = time.time()

        logger.info("node_started", node="technical", ticket_id=state.get("ticket_id"))

        agent = get_technical_agent()
        state = await agent.execute(state)

        duration_ms = int((time.time() - start_time) * 1000)
        if "metadata" in state and "latency_ms" in state["metadata"]:
            state["metadata"]["latency_ms"]["technical"] = duration_ms

        logger.info(
            "node_completed",
            node="technical",
            ticket_id=state.get("ticket_id"),
            duration_ms=duration_ms,
        )

        return state


async def account_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Account node - Handle account issues.

    Args:
        state: Current state

    Returns:
        Updated state with resolution
    """
    with trace_span("node.account"):
        start_time = time.time()

        logger.info("node_started", node="account", ticket_id=state.get("ticket_id"))

        agent = get_account_agent()
        state = await agent.execute(state)

        duration_ms = int((time.time() - start_time) * 1000)
        if "metadata" in state and "latency_ms" in state["metadata"]:
            state["metadata"]["latency_ms"]["account"] = duration_ms

        logger.info(
            "node_completed",
            node="account",
            ticket_id=state.get("ticket_id"),
            duration_ms=duration_ms,
        )

        return state


async def escalation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Escalation node - Handle escalated issues.

    Args:
        state: Current state

    Returns:
        Updated state with resolution or human escalation
    """
    with trace_span("node.escalation"):
        start_time = time.time()

        logger.info("node_started", node="escalation", ticket_id=state.get("ticket_id"))

        agent = get_escalation_agent()
        state = await agent.execute(state)

        duration_ms = int((time.time() - start_time) * 1000)
        if "metadata" in state and "latency_ms" in state["metadata"]:
            state["metadata"]["latency_ms"]["escalation"] = duration_ms

        logger.info(
            "node_completed",
            node="escalation",
            ticket_id=state.get("ticket_id"),
            requires_human=state.get("resolution", {}).get("requires_human"),
            duration_ms=duration_ms,
        )

        return state
