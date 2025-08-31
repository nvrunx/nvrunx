"""Token usage tracking."""

from pydantic import BaseModel


class UsageSummary(BaseModel):
	"""Summary of token usage."""
	
	total_tokens: int = 0
	prompt_tokens: int = 0
	completion_tokens: int = 0