"""Message manager for agent communication."""

from pydantic import BaseModel


class MessageManagerState(BaseModel):
	"""State for the message manager."""
	
	message_count: int = 0
	total_tokens: int = 0