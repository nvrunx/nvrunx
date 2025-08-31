"""System prompts for agent."""

from typing import Any


class SystemPrompt:
	"""System prompt management."""
	
	def __init__(self, **kwargs: Any):
		pass
	
	def get_prompt(self) -> str:
		"""Get the system prompt."""
		return "You are a helpful AI assistant that can control web browsers."