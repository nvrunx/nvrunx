"""Enhanced CLI interface for nvrunx with textual UI support."""

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
from browser_use.utils import get_browser_use_version


@click.command()
@click.option('--version', is_flag=True, help='Print version and exit')
@click.option('--model', type=str, default='gpt-4o-mini', help='Model to use')
@click.option('--prompt', type=str, help='Run a single task')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--ui', type=click.Choice(['basic', 'textual']), default='basic', help='UI interface to use')
@click.option('--browser', is_flag=True, help='Enable browser automation features')
@click.option('--gif', is_flag=True, help='Enable GIF recording during browser automation')
def main(version: bool, model: str, prompt: str | None, debug: bool, ui: str, browser: bool, gif: bool):
	"""nvrunx - AI Browser Automation
	
	Interactive AI agent that can control your browser with advanced features.
	"""
	
	if version:
		print("nvrunx v0.7.0")
		sys.exit(0)
	
	if ui == 'textual':
		# Run textual UI
		asyncio.run(run_textual_interface())
	elif prompt:
		# Run single task mode
		asyncio.run(run_single_task(prompt, model, browser, gif))
	else:
		# Run interactive mode  
		asyncio.run(run_interactive_mode(model, browser, gif))


async def run_textual_interface():
	"""Run the rich textual interface."""
	try:
		from browser_use.cli_textual import run_textual_cli
		success = await run_textual_cli()
		if not success:
			print("⚠️ Falling back to basic CLI")
			await run_interactive_mode('gpt-4o-mini', False, False)
	except ImportError:
		print('⚠️ Textual UI not available. Install with: `pip install "nvrunx[cli]"`')
		print("⚠️ Falling back to basic CLI")
		await run_interactive_mode('gpt-4o-mini', False, False)


async def run_single_task(task: str, model: str, browser: bool = False, gif: bool = False):
	"""Run a single task and exit."""
	print(f"🤖 Running task: {task}")
	print(f"🧠 Using model: {model}")
	
	if browser:
		print("🌐 Browser automation enabled")
	if gif:
		print("🎬 GIF recording enabled")
	
	# Check for API key
	if not CONFIG.OPENAI_API_KEY:
		print("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
		sys.exit(1)
	
	try:
		# Create agent with options
		agent_options = {
			'task': task,
			'llm': ChatOpenAI(model=model),
		}
		
		if browser:
			# Enable browser features
			from browser_use.browser import BrowserSession
			session = BrowserSession(headless=False)
			agent_options['browser_session'] = session
			
		if gif:
			# Enable GIF recording
			agent_options['gif_recording'] = True
		
		agent = Agent(**agent_options)
		
		result = await agent.run()
		print(f"✅ Task completed: {result}")
		
		if gif and browser:
			print("🎬 GIF recording saved (if supported)")
		
	except Exception as e:
		print(f"❌ Error: {e}")
		sys.exit(1)


async def run_interactive_mode(model: str, browser: bool = False, gif: bool = False):
	"""Run enhanced interactive CLI mode."""
	print("🤖 nvrunx Interactive Mode")
	print("=" * 50)
	print("Features:")
	print("  • AI-powered browser automation")
	print("  • Multiple LLM providers")
	print("  • DOM extraction and manipulation")
	print(f"  • Browser automation: {'✅' if browser else '❌'}")
	print(f"  • GIF recording: {'✅' if gif else '❌'}")
	print()
	print("Commands:")
	print("  • Type your request normally")
	print("  • 'switch <model>' - Switch AI model")
	print("  • 'browser on/off' - Toggle browser features")
	print("  • 'gif on/off' - Toggle GIF recording")
	print("  • 'models' - List available models")
	print("  • 'help' - Show this help")
	print("  • 'quit' or 'exit' - Exit")
	print("=" * 50)
	
	if not CONFIG.OPENAI_API_KEY:
		print("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
		sys.exit(1)
	
	current_model = model
	browser_enabled = browser
	gif_enabled = gif
	
	try:
		while True:
			task = input(f"\n🔍 [{current_model}] What would you like me to do? ")
			
			if task.lower() in ['quit', 'exit', 'q']:
				print("👋 Goodbye!")
				break
			
			if not task.strip():
				continue
			
			# Handle commands
			if task.startswith('switch '):
				new_model = task[7:].strip()
				if new_model:
					current_model = new_model
					print(f"🔄 Switched to model: {current_model}")
				continue
			
			elif task.lower() == 'browser on':
				browser_enabled = True
				print("🌐 Browser automation enabled")
				continue
			
			elif task.lower() == 'browser off':
				browser_enabled = False
				print("🌐 Browser automation disabled")
				continue
			
			elif task.lower() == 'gif on':
				gif_enabled = True
				print("🎬 GIF recording enabled")
				continue
			
			elif task.lower() == 'gif off':
				gif_enabled = False
				print("🎬 GIF recording disabled")
				continue
			
			elif task.lower() == 'models':
				print("\n📋 Available models:")
				print("  • gpt-4o-mini (fast, cost-effective)")
				print("  • gpt-4o (most capable)")
				print("  • claude-3-sonnet (anthropic)")
				print("  • gemini-pro (google)")
				print("  • llama3-70b-8192 (groq)")
				print("  • llama2 (ollama local)")
				continue
			
			elif task.lower() == 'help':
				print("\n📚 Help:")
				print("  • Just type what you want the AI to do")
				print("  • The AI can browse websites, extract information, fill forms")
				print("  • Use 'browser on' to enable browser automation")
				print("  • Use 'gif on' to record actions as GIF")
				print("  • Use 'switch <model>' to change AI model")
				continue
			
			# Process the task
			print(f"🤖 Working on: {task}")
			
			status_indicators = []
			if browser_enabled:
				status_indicators.append("🌐 Browser")
			if gif_enabled:
				status_indicators.append("🎬 GIF")
			if status_indicators:
				print(f"   Features: {' '.join(status_indicators)}")
			
			try:
				# Create agent with current settings
				agent_options = {
					'task': task,
					'llm': ChatOpenAI(model=current_model),
				}
				
				if browser_enabled:
					try:
						from browser_use.browser import BrowserSession
						session = BrowserSession(headless=not gif_enabled)  # Show browser if recording GIF
						agent_options['browser_session'] = session
					except ImportError:
						print("⚠️ Browser features not available. Install with: pip install 'nvrunx[browser]'")
				
				if gif_enabled:
					agent_options['gif_recording'] = True
				
				agent = Agent(**agent_options)
				
				result = await agent.run()
				print(f"✅ Completed: {result}")
				
				if gif_enabled and browser_enabled:
					print("🎬 Check for GIF recording in output directory")
				
			except Exception as e:
				print(f"❌ Error: {e}")
				print("💡 Try using a different model or disabling browser features")
				
	except KeyboardInterrupt:
		print("\n👋 Goodbye!")
	except Exception as e:
		print(f"❌ Error: {e}")


if __name__ == '__main__':
	main()