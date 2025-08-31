"""Action model for browser automation."""

from typing import Any
from pydantic import BaseModel


class ActionModel(BaseModel):
	"""Base model for browser actions."""
	
	action_type: str
	parameters: dict[str, Any] = {}
	
	def get_index(self) -> int | None:
		"""Get index for DOM element interaction."""
		return self.parameters.get('index')