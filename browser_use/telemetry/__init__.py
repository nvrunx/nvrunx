"""Observability and telemetry for nvrunx."""

import logging
import os
from typing import Any, Dict

from pydantic import BaseModel


class TelemetryEvent(BaseModel):
	"""Base telemetry event."""
	
	event_type: str
	timestamp: float
	data: Dict[str, Any] = {}


class ProductTelemetry:
	"""Product telemetry collection."""
	
	def __init__(self):
		self.logger = logging.getLogger(f'{__name__}.ProductTelemetry')
		self.enabled = os.getenv('BROWSER_USE_TELEMETRY', 'true').lower() == 'true'
	
	def capture(self, event: TelemetryEvent) -> None:
		"""Capture a telemetry event."""
		if self.enabled:
			self.logger.debug(f"Telemetry event: {event.event_type}")
	
	def flush(self) -> None:
		"""Flush telemetry data."""
		if self.enabled:
			self.logger.debug("Flushing telemetry data")


class CLITelemetryEvent(TelemetryEvent):
	"""CLI-specific telemetry event."""
	
	event_type: str = "cli_event"
	version: str | None = None
	action: str | None = None
	mode: str | None = None
	model: str | None = None
	model_provider: str | None = None
	duration_seconds: float | None = None
	error_message: str | None = None