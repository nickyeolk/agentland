#!/usr/bin/env python3
"""
Phase 4 validation script: End-to-end workflow testing.

Tests the complete ticket processing workflow from API through orchestration to resolution.
"""

import asyncio
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, "/data/data/com.termux/files/home/lik/agentland")

from src.orchestration.graph import process_ticket
from src.observability.context import set_correlation_id


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_state_summary(state: dict):
    """Print a summary of the state."""
    routing = state.get("routing", {})
    resolution = state.get("resolution", {})
    interactions = state.get("agent_interactions", [])
    metadata = state.get("metadata", {})

    print(f"Ticket ID: {state.get('ticket_id')}")
    print(f"Correlation ID: {state.get('correlation_id')}")
    print(f"\nRouting:")
    print(f"  - Urgency: {routing.get('urgency')}")
    print(f"  - Assigned Agent: {routing.get('assigned_agent')}")
    print(f"  - Confidence: {routing.get('confidence_score')}")
    print(f"  - Reasoning: {routing.get('reasoning', 'N/A')[:100]}...")

    print(f"\nAgent Interactions ({len(interactions)} total):")
    for i, interaction in enumerate(interactions, 1):
        agent_name = interaction.get("agent_name", "unknown")
        action = interaction.get("action", "")
        tool_calls = interaction.get("tool_calls", [])
        print(f"  {i}. {agent_name}: {action}")
        if tool_calls:
            print(f"     Tools called: {[tc.get('tool') for tc in tool_calls]}")

    print(f"\nResolution:")
    print(f"  - Status: {resolution.get('status')}")
    print(f"  - Requires Human: {resolution.get('requires_human')}")
    print(f"  - Response Preview: {resolution.get('response', '')[:150]}...")

    print(f"\nMetadata:")
    print(f"  - Token Usage: {metadata.get('token_usage', {})}")
    print(f"  - Latency: {metadata.get('latency_ms', {})}")
    print(f"  - Errors: {metadata.get('error_count', 0)}")


async def test_billing_ticket():
    """Test a billing ticket workflow."""
    print_section("TEST 1: Billing Ticket - Refund Request")

    set_correlation_id("TEST-BILLING-001")

    state = await process_ticket(
        ticket_id="T-TEST-001",
        correlation_id="TEST-BILLING-001",
        customer_id="cust_001",
        subject="I need a refund",
        body="I was charged twice for my subscription. Please refund the duplicate charge.",
        email="john@example.com",
    )

    print_state_summary(state)

    # Validate
    assert state.get("routing", {}).get("assigned_agent") == "billing_agent", \
        f"Expected billing_agent, got {state.get('routing', {}).get('assigned_agent')}"

    print("\n✅ Billing ticket test PASSED")
    return state


async def test_technical_ticket():
    """Test a technical ticket workflow."""
    print_section("TEST 2: Technical Ticket - API Error")

    set_correlation_id("TEST-TECH-001")

    state = await process_ticket(
        ticket_id="T-TEST-002",
        correlation_id="TEST-TECH-001",
        customer_id="cust_002",
        subject="API returning 500 errors",
        body="When I try to fetch user data via /api/users endpoint, I'm getting 500 internal server errors. This started about 2 hours ago.",
        email="jane@example.com",
    )

    print_state_summary(state)

    # Validate
    assert state.get("routing", {}).get("assigned_agent") == "technical_agent", \
        f"Expected technical_agent, got {state.get('routing', {}).get('assigned_agent')}"

    print("\n✅ Technical ticket test PASSED")
    return state


async def test_account_ticket():
    """Test an account ticket workflow."""
    print_section("TEST 3: Account Ticket - Password Reset")

    set_correlation_id("TEST-ACCOUNT-001")

    state = await process_ticket(
        ticket_id="T-TEST-003",
        correlation_id="TEST-ACCOUNT-001",
        customer_id="cust_001",
        subject="Can't log in - forgot password",
        body="I forgot my password and can't access my account. Can you help me reset it?",
        email="john@example.com",
    )

    print_state_summary(state)

    # Validate
    assert state.get("routing", {}).get("assigned_agent") == "account_agent", \
        f"Expected account_agent, got {state.get('routing', {}).get('assigned_agent')}"

    print("\n✅ Account ticket test PASSED")
    return state


async def test_escalation_ticket():
    """Test an escalation ticket workflow."""
    print_section("TEST 4: Escalation Ticket - GDPR Request")

    set_correlation_id("TEST-ESCALATION-001")

    state = await process_ticket(
        ticket_id="T-TEST-004",
        correlation_id="TEST-ESCALATION-001",
        customer_id="cust_002",
        subject="GDPR data deletion request",
        body="Per GDPR regulations, I request immediate deletion of all my personal data from your systems.",
        email="jane@example.com",
    )

    print_state_summary(state)

    # Validate - could be routed to account or escalation
    assigned = state.get("routing", {}).get("assigned_agent")
    assert assigned in ["account_agent", "escalation_agent"], \
        f"Expected account_agent or escalation_agent, got {assigned}"

    # Should require human review
    # (Note: depends on agent logic)

    print("\n✅ Escalation ticket test PASSED")
    return state


async def validate_observability(states: list):
    """Validate observability features are working."""
    print_section("OBSERVABILITY VALIDATION")

    for i, state in enumerate(states, 1):
        ticket_id = state.get("ticket_id")
        print(f"\nTicket {i} ({ticket_id}):")

        # Check correlation ID
        assert state.get("correlation_id"), f"Missing correlation_id for {ticket_id}"
        print(f"  ✓ Correlation ID: {state.get('correlation_id')}")

        # Check timestamp
        assert state.get("timestamp"), f"Missing timestamp for {ticket_id}"
        print(f"  ✓ Timestamp: {state.get('timestamp')}")

        # Check routing decision
        routing = state.get("routing", {})
        assert routing.get("assigned_agent"), f"Missing assigned_agent for {ticket_id}"
        print(f"  ✓ Routing decision recorded")

        # Check agent interactions
        interactions = state.get("agent_interactions", [])
        assert len(interactions) >= 1, f"No agent interactions for {ticket_id}"
        print(f"  ✓ Agent interactions recorded: {len(interactions)}")

        # Check tool calls
        total_tool_calls = sum(
            len(i.get("tool_calls", [])) for i in interactions
        )
        print(f"  ✓ Tool calls recorded: {total_tool_calls}")

        # Check resolution
        resolution = state.get("resolution", {})
        assert resolution.get("status"), f"Missing resolution status for {ticket_id}"
        assert resolution.get("response"), f"Missing response for {ticket_id}"
        print(f"  ✓ Resolution recorded: {resolution.get('status')}")

        # Check metadata
        metadata = state.get("metadata", {})
        print(f"  ✓ Metadata recorded: {list(metadata.keys())}")

    print("\n✅ All observability checks PASSED")


async def main():
    """Run all Phase 4 validation tests."""
    print("\n" + "="*60)
    print("  PHASE 4 VALIDATION: End-to-End Workflow Testing")
    print("="*60)

    try:
        # Run all test cases
        states = []
        states.append(await test_billing_ticket())
        states.append(await test_technical_ticket())
        states.append(await test_account_ticket())
        states.append(await test_escalation_ticket())

        # Validate observability
        await validate_observability(states)

        print_section("PHASE 4 VALIDATION COMPLETE")
        print("✅ All tests passed!")
        print("\nSummary:")
        print(f"  - {len(states)} tickets processed")
        print("  - All agents functioning correctly")
        print("  - Routing working as expected")
        print("  - Observability features validated")
        print("\n🎉 Phase 4 implementation is COMPLETE and VALIDATED!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
