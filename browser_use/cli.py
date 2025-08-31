"""Simple CLI interface for nvrunx."""

import asyncio
import sys
from pathlib import Path

try:
	import click
except ImportError:
	print('⚠️ CLI addon is not installed. Please install it with: `pip install "nvrunx[cli]"` and try again.')
	sys.exit(1)

from browser_use import Agent, ChatOpenAI
from browser_use.config import CONFIG
from browser_use.telemetry import ProductTelemetry, CLITelemetryEvent


@click.command()
@click.option('--version', is_flag=True, help='Print version and exit')
@click.option('--model', type=str, default='gpt-4.1-mini', help='Model to use')
@click.option('--prompt', type=str, help='Run a single task')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(version: bool, model: str, prompt: str | None, debug: bool):
	"""nvrunx - AI Browser Automation
	
	Interactive AI agent that can control your browser.
	"""
	
	if version:
		print("nvrunx v0.7.0")
		sys.exit(0)
	
	if prompt:
		# Run single task mode
		asyncio.run(run_single_task(prompt, model))
	else:
		# Run interactive mode  
		asyncio.run(run_interactive_mode(model))


async def run_single_task(task: str, model: str):
	"""Run a single task and exit."""
	print(f"🤖 Running task: {task}")
	print(f"🧠 Using model: {model}")
	
	# Check for API key
	if not CONFIG.OPENAI_API_KEY:
		print("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
		sys.exit(1)
	
	try:
		agent = Agent(
			task=task,
			llm=ChatOpenAI(model=model),
		)
		
		result = await agent.run()
		print(f"✅ Task completed: {result}")
		
	except Exception as e:
		print(f"❌ Error: {e}")
		sys.exit(1)


async def run_interactive_mode(model: str):
	"""Run interactive CLI mode."""
	print("🤖 nvrunx Interactive Mode")
	print("Type 'quit' or 'exit' to quit")
	print("=" * 50)
	
	if not CONFIG.OPENAI_API_KEY:
		print("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
		sys.exit(1)
	
	try:
		while True:
			task = input("\n🔍 What would you like me to do? ")
			
			if task.lower() in ['quit', 'exit', 'q']:
				print("👋 Goodbye!")
				break
			
			if not task.strip():
				continue
			
			print(f"🤖 Working on: {task}")
			
			try:
				agent = Agent(
					task=task,
					llm=ChatOpenAI(model=model),
				)
				
				result = await agent.run()
				print(f"✅ Completed: {result}")
				
			except Exception as e:
				print(f"❌ Error: {e}")
				
	except KeyboardInterrupt:
		print("\n👋 Goodbye!")
	except Exception as e:
		print(f"❌ Error: {e}")


if __name__ == '__main__':
	main()