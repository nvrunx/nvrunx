"""
Example showing how to use different LLM providers.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatOpenAI, ChatAnthropic, ChatGoogle


async def openai_example():
	"""Example using OpenAI GPT."""
	agent = Agent(
		task="Search for Python tutorials on Google",
		llm=ChatOpenAI(model="gpt-4o-mini"),
	)
	return await agent.run()


async def anthropic_example():
	"""Example using Anthropic Claude."""
	agent = Agent(
		task="Search for Python tutorials on Google", 
		llm=ChatAnthropic(model="claude-3-sonnet-20240229"),
	)
	return await agent.run()


async def google_example():
	"""Example using Google Gemini."""
	agent = Agent(
		task="Search for Python tutorials on Google",
		llm=ChatGoogle(model="gemini-pro"),
	)
	return await agent.run()


async def main():
	print("Running with OpenAI...")
	result1 = await openai_example()
	print(f"OpenAI result: {result1}")
	
	print("\nRunning with Anthropic...")
	result2 = await anthropic_example()
	print(f"Anthropic result: {result2}")
	
	print("\nRunning with Google...")
	result3 = await google_example()
	print(f"Google result: {result3}")


if __name__ == "__main__":
	asyncio.run(main())