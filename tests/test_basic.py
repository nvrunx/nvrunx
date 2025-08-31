"""Basic tests for nvrunx."""

import pytest
from browser_use import Agent, ChatOpenAI


def test_imports():
	"""Test that basic imports work."""
	from browser_use import Agent, ChatOpenAI, ChatAnthropic, ChatGoogle
	assert Agent is not None
	assert ChatOpenAI is not None
	assert ChatAnthropic is not None
	assert ChatGoogle is not None


def test_agent_creation():
	"""Test that we can create an agent."""
	agent = Agent(
		task="Test task",
		llm=ChatOpenAI(model="gpt-4o-mini"),
	)
	assert agent.task == "Test task"
	assert agent.llm.model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_agent_run():
	"""Test that agent run method works."""
	agent = Agent(
		task="Test task",
		llm=ChatOpenAI(model="gpt-4o-mini"),
	)
	result = await agent.run()
	assert result is not None