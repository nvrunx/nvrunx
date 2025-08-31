"""Agent action models and views."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

from browser_use.tools.registry.views import ActionModel


class ActionResult(BaseModel):
	"""Result of executing an action"""

	# For done action
	is_done: bool | None = False
	success: bool | None = None

	# Error handling - always include in long term memory
	error: str | None = None

	# Files
	attachments: list[str] | None = None  # Files to display in the done message

	# Always include in long term memory
	long_term_memory: str | None = None  # Memory of this action

	# if update_only_read_state is True we add the extracted_content to the agent context only once for the next step
	# if update_only_read_state is False we add the extracted_content to the agent long term memory if no long_term_memory is provided
	extracted_content: str | None = None
	include_extracted_content_only_once: bool = False  # Whether the extracted content should be used to update the read_state

	# Metadata for observability (e.g., click coordinates)
	metadata: dict | None = None

	# Deprecated
	include_in_memory: bool = False  # whether to include in extracted_content inside long_term_memory


class AgentOutput(BaseModel):
	"""Output from the agent including thinking and actions"""
	
	thinking: str | None = None
	evaluation_previous_goal: str | None = None
	memory: str | None = None
	next_goal: str | None = None
	action: list[ActionModel] = Field(
		...,
		description='List of actions to execute',
		json_schema_extra={'min_items': 1},  # Ensure at least one action is provided
	)


class AgentHistory(BaseModel):
	"""History item for agent actions"""

	model_output: AgentOutput | None
	result: list[ActionResult]
	# state: BrowserStateHistory  # Simplified for now


AgentStructuredOutput = TypeVar('AgentStructuredOutput', bound=BaseModel)


class AgentHistoryList(BaseModel, Generic[AgentStructuredOutput]):
	"""List of AgentHistory messages, i.e. the history of the agent's actions and thoughts."""

	history: list[AgentHistory]

	def __len__(self) -> int:
		"""Return the number of history items"""
		return len(self.history)

	def add_item(self, history_item: AgentHistory) -> None:
		"""Add a history item to the list"""
		self.history.append(history_item)