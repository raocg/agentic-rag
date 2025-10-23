from anthropic import Anthropic
import os
from typing import List, Dict, Any, Optional

class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self._initialized = True

    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return self._initialized

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate a response from Claude"""

        # Build messages
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        # Create message
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else None,
            messages=messages
        )

        # Extract text response
        text_response = ""
        for content_block in response.content:
            if content_block.type == "text":
                text_response += content_block.text

        return {
            "response": text_response,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "model": response.model,
            "stop_reason": response.stop_reason
        }

    async def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate a response with tool use capabilities"""

        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt if system_prompt else None,
            messages=messages,
            tools=tools
        )

        # Parse response
        text_responses = []
        tool_uses = []

        for content_block in response.content:
            if content_block.type == "text":
                text_responses.append(content_block.text)
            elif content_block.type == "tool_use":
                tool_uses.append({
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })

        return {
            "text": "\n".join(text_responses) if text_responses else "",
            "tool_uses": tool_uses,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
