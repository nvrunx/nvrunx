"""
Example of online shopping automation.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatOpenAI


async def main():
	agent = Agent(
		task="""Go to Amazon and search for 'wireless headphones'. 
		Find a highly rated pair under $100 and add them to cart.
		Don't actually complete the purchase.""",
		llm=ChatOpenAI(model="gpt-4o"),
	)
	
	result = await agent.run()
	print(f"Shopping task result: {result}")


if __name__ == "__main__":
	asyncio.run(main())