"""
Example of job search automation.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatOpenAI


async def main():
	agent = Agent(
		task="""Go to LinkedIn and search for 'Machine Learning Engineer' jobs in San Francisco.
		Look at the first 3 job postings and save the company names, job titles, 
		and key requirements to a text file called 'ml_jobs.txt'.""",
		llm=ChatOpenAI(model="gpt-4o"),
	)
	
	result = await agent.run()
	print(f"Job search result: {result}")


if __name__ == "__main__":
	asyncio.run(main())