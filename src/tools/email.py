"""
Mock email sending tool.
"""

from typing import Any, Dict
from pydantic import Field
import random

from src.tools.base import BaseTool, ToolInput


class EmailInput(ToolInput):
    """Input for email sending."""

    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    template: str = Field(default="default", description="Email template name")


class EmailTool(BaseTool):
    """Mock email sending tool."""

    def __init__(self):
        super().__init__(
            name="email_sender",
            description="Send emails to customers for confirmations, notifications, and updates",
        )

    async def _execute(self, input_data: EmailInput) -> Dict[str, Any]:
        """
        Send an email (mocked).

        Args:
            input_data: Email parameters

        Returns:
            Send result
        """
        # Simulate success most of the time
        success = random.random() > 0.05  # 95% success rate

        if success:
            message_id = f"MSG-{random.randint(100000, 999999)}"

            # Log email content (in real implementation, this would send)
            self.logger.info(
                "mock_email_sent",
                to=input_data.to,
                subject=input_data.subject,
                body_length=len(input_data.body),
                message_id=message_id,
            )

            return {
                "success": True,
                "message_id": message_id,
                "recipient": input_data.to,
                "subject": input_data.subject,
                "status": "sent",
                "message": f"Email sent successfully to {input_data.to}",
            }
        else:
            return {
                "success": False,
                "recipient": input_data.to,
                "error": "Email service temporarily unavailable",
                "retry_recommended": True,
            }
