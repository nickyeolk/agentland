"""
LLM client wrapper with observability and retry logic.

Note: This is a mock implementation since the Anthropic SDK requires
compilation in Termux. For production, replace with real Anthropic client.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.settings import settings
from src.llm.retry import retry_on_llm_error
from src.llm.token_counter import estimate_tokens, TokenUsageTracker
from src.observability.logger import get_logger
from src.observability.tracer import trace_span, add_span_attributes
from src.observability.metrics import record_llm_usage
from src.utils.errors import LLMError

logger = get_logger(__name__)


class LLMResponse:
    """LLM response wrapper."""

    def __init__(
        self,
        content: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        stop_reason: str = "end_turn",
    ):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.model = model
        self.stop_reason = stop_reason

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "model": self.model,
            "stop_reason": self.stop_reason,
        }


class MockAnthropicClient:
    """
    Mock Anthropic client for development/testing.

    This simulates the Anthropic API with realistic responses.
    In production, replace with real anthropic.Anthropic() client.
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        logger.info("mock_llm_initialized", model=model)

    async def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Generate a response (mocked).

        Args:
            system: System prompt
            messages: Conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLM response
        """
        # Simulate API call delay
        await asyncio.sleep(0.1)

        # Get last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break

        # Generate mock response based on content
        mock_response = self._generate_mock_response(user_message, system)

        # Estimate tokens
        prompt_text = system + " " + " ".join([m["content"] for m in messages])
        prompt_tokens = estimate_tokens(prompt_text)
        completion_tokens = estimate_tokens(mock_response)

        logger.info(
            "mock_llm_generated",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return LLMResponse(
            content=mock_response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self.model,
        )

    def _generate_mock_response(self, user_message: str, system: str) -> str:
        """Generate a mock response based on context."""
        user_lower = user_message.lower()

        # Triage agent responses
        if "triage" in system.lower():
            if any(word in user_lower for word in ["charge", "billing", "refund", "payment"]):
                return "ROUTE: billing_agent | URGENCY: medium | CONFIDENCE: 0.92 | REASONING: Customer mentions billing-related terms"
            elif any(word in user_lower for word in ["bug", "error", "crash", "not working"]):
                return "ROUTE: technical_agent | URGENCY: high | CONFIDENCE: 0.88 | REASONING: Technical issue reported"
            elif any(word in user_lower for word in ["password", "account", "login", "profile"]):
                return "ROUTE: account_agent | URGENCY: medium | CONFIDENCE: 0.85 | REASONING: Account management issue"
            else:
                return "ROUTE: escalation_agent | URGENCY: low | CONFIDENCE: 0.60 | REASONING: Unclear category"

        # Billing agent responses
        elif "billing" in system.lower():
            return "I understand you're experiencing a billing issue. Let me check your payment history and help resolve this for you. I'll process a refund for any duplicate charges."

        # Technical agent responses
        elif "technical" in system.lower():
            return "I've identified the technical issue you're experiencing. Let me walk you through the troubleshooting steps to resolve this problem."

        # Account agent responses
        elif "account" in system.lower():
            return "I can help you with your account management request. I'll update your account settings and send you a confirmation email."

        # Default response
        return "Thank you for contacting support. I'll help you with your request right away."


class LLMClient:
    """
    LLM client with observability and retry logic.

    Wraps the Anthropic API (or mock) with automatic tracing,
    logging, metrics, and retry on transient failures.
    """

    def __init__(self):
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.timeout = settings.llm_timeout_seconds

        # Initialize tracker
        self.usage_tracker = TokenUsageTracker()

        # Initialize client (mock or real)
        if settings.use_mock_llm:
            self.client = MockAnthropicClient(
                api_key=settings.anthropic_api_key,
                model=self.model,
            )
            logger.info("llm_client_initialized", mode="mock", model=self.model)
        else:
            # In production with real Anthropic SDK:
            # from anthropic import Anthropic
            # self.client = Anthropic(api_key=settings.anthropic_api_key)
            # For now, use mock
            self.client = MockAnthropicClient(
                api_key=settings.anthropic_api_key,
                model=self.model,
            )
            logger.warning(
                "llm_client_using_mock",
                reason="Anthropic SDK not available",
                model=self.model,
            )

    @retry_on_llm_error
    async def generate(
        self,
        system: str,
        user_message: str,
        agent_name: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            system: System prompt
            user_message: User message
            agent_name: Optional agent name for metrics
            **kwargs: Additional arguments

        Returns:
            LLM response

        Raises:
            LLMError: On API errors
        """
        with trace_span(
            "llm.generate",
            {"llm.model": self.model, "agent": agent_name or "unknown"},
        ):
            try:
                logger.info(
                    "llm_request_started",
                    model=self.model,
                    agent=agent_name,
                    system_length=len(system),
                    message_length=len(user_message),
                )

                # Build messages
                messages = [{"role": "user", "content": user_message}]

                # Call LLM
                response = await self.client.generate(
                    system=system,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )

                # Track usage
                usage = self.usage_tracker.track(
                    response.prompt_tokens,
                    response.completion_tokens,
                    self.model,
                )

                # Record metrics
                record_llm_usage(
                    model=self.model,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    agent=agent_name,
                )

                # Add to span
                add_span_attributes(
                    llm_response_length=len(response.content),
                    llm_prompt_tokens=response.prompt_tokens,
                    llm_completion_tokens=response.completion_tokens,
                    llm_cost=usage["cost"],
                )

                logger.info(
                    "llm_request_completed",
                    model=self.model,
                    agent=agent_name,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    cost=usage["cost"],
                )

                return response

            except Exception as e:
                logger.error(
                    "llm_request_failed",
                    model=self.model,
                    agent=agent_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise LLMError(f"LLM generation failed: {str(e)}") from e

    def get_usage_summary(self) -> Dict[str, float]:
        """
        Get summary of token usage and costs.

        Returns:
            Usage summary dictionary
        """
        return self.usage_tracker.get_summary()

    def reset_usage(self) -> None:
        """Reset usage tracking."""
        self.usage_tracker.reset()


# Global client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get the global LLM client instance.

    Returns:
        LLM client
    """
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
