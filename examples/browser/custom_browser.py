"""
Example showing how to use custom browser configuration.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatOpenAI, BrowserSession, BrowserProfile


async def main():
	# Create custom browser profile
	profile = BrowserProfile(
		headless=False,  # Run with visible browser
		# user_data_dir="/tmp/my_browser_profile",  # Custom profile directory
		# allowed_domains=["github.com", "google.com"],  # Restrict to specific domains
	)
	
	# Create browser session with custom profile
	browser = BrowserSession(browser_profile=profile)
	
	# Create agent with custom browser
	agent = Agent(
		task="Go to GitHub and find the nvrunx repository",
		llm=ChatOpenAI(model="gpt-4o-mini"),
		browser_session=browser,
	)
	
	result = await agent.run()
	print(f"Result with custom browser: {result}")


if __name__ == "__main__":
	asyncio.run(main())