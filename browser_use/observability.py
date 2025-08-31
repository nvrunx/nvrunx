"""Observability features for monitoring and debugging."""

import logging
import time
from typing import Any, Callable, Dict

from pydantic import BaseModel


class ObservabilityEvent(BaseModel):
	"""Base observability event."""
	
	event_type: str
	timestamp: float = None
	source: str | None = None
	data: Dict[str, Any] = {}
	
	def __init__(self, **kwargs):
		if 'timestamp' not in kwargs:
			kwargs['timestamp'] = time.time()
		super().__init__(**kwargs)


class ObservabilityManager:
	"""Manager for observability events and metrics."""
	
	def __init__(self):
		self.logger = logging.getLogger(f'{__name__}.ObservabilityManager')
		self.callbacks: list[Callable[[ObservabilityEvent], None]] = []
	
	def add_callback(self, callback: Callable[[ObservabilityEvent], None]) -> None:
		"""Add callback for observability events."""
		self.callbacks.append(callback)
	
	def emit_event(self, event: ObservabilityEvent) -> None:
		"""Emit an observability event."""
		self.logger.debug(f"Observability event: {event.event_type}")
		for callback in self.callbacks:
			try:
				callback(event)
			except Exception as e:
				self.logger.error(f"Error in observability callback: {e}")


# Global observability manager
observability = ObservabilityManager()