"""Synchronous API wrapper for browser_use."""

import asyncio
from typing import Any

from browser_use.agent.service import Agent as AsyncAgent
from browser_use.llm.base import BaseChatModel


class Agent:
	"""Synchronous wrapper for the async Agent."""
	
	def __init__(self, task: str, llm: BaseChatModel, **kwargs: Any):
		self.async_agent = AsyncAgent(task=task, llm=llm, **kwargs)
	
	def run(self) -> Any:
		"""Run the agent synchronously."""
		return asyncio.run(self.async_agent.run())
	
	def __getattr__(self, name: str) -> Any:
		"""Delegate attribute access to the async agent."""
		return getattr(self.async_agent, name)