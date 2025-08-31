"""
Basic example showing how to use nvrunx with OpenAI's GPT model.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatOpenAI


async def main():
	agent = Agent(
		task="Go to GitHub and find the nvrunx repository, then tell me how many stars it has",
		llm=ChatOpenAI(model="gpt-4o-mini"),
	)
	
	result = await agent.run()
	print(f"Task result: {result}")


if __name__ == "__main__":
	asyncio.run(main())