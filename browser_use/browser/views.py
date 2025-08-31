"""Browser-related views and models."""

from typing import Any
from pydantic import BaseModel


class BrowserStateHistory(BaseModel):
	"""Browser state information for history tracking."""
	
	url: str | None = None
	title: str | None = None
	screenshot_path: str | None = None
	interacted_element: list[Any] | None = None
	
	def get_screenshot(self) -> str | None:
		"""Get screenshot as base64 string."""
		return None  # Placeholder
	
	def to_dict(self) -> dict[str, Any]:
		"""Convert to dictionary."""
		return self.model_dump()