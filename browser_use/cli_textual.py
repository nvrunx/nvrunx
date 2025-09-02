"""Rich textual CLI interface for nvrunx."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

try:
	from textual.app import App, ComposeResult
	from textual.binding import Binding
	from textual.containers import Container, Horizontal, Vertical
	from textual.widgets import (
		Button, Footer, Header, Input, Log, RichLog, Select, Static, TextArea
	)
	from textual.reactive import reactive
	from rich.console import Console
	from rich.text import Text
	from rich.panel import Panel
	from rich.progress import Progress, SpinnerColumn, TextColumn
	from rich.syntax import Syntax
	from rich.json import JSON
	TEXTUAL_AVAILABLE = True
except ImportError:
	# Fallback classes for when textual is not installed
	TEXTUAL_AVAILABLE = False
	class App: 
		def __init__(self, **kwargs): pass
	class ComposeResult: pass
	class Container: pass
	class Horizontal: pass
	class Vertical: pass
	class Button: 
		class Pressed:
			def __init__(self): self.button = None
	class Footer: pass 
	class Header: pass
	class Input: pass
	class Log: pass
	class RichLog: pass
	class Select: 
		class Changed:
			def __init__(self): 
				self.select = None
				self.value = None
	class Static: pass
	class TextArea: 
		class Changed:
			def __init__(self): self.text_area = None
	class Binding: pass
	def reactive(default): 
		return default
	class Console:
		def __init__(self): pass
	class Text: pass
	class Panel: pass

from browser_use import Agent, ChatOpenAI, ChatAnthropic, ChatGoogle, ChatGroq, ChatOllama
from browser_use.config import CONFIG


class NvrunxTUI(App):
	"""Textual User Interface for nvrunx."""
	
	def __init__(self, **kwargs: Any):
		if not TEXTUAL_AVAILABLE:
			raise ImportError("Textual library not available. Install with: pip install 'nvrunx[cli]'")
		super().__init__(**kwargs)
		self.console = Console()
		self.agent: Optional[Agent] = None
		self.session_history: list[str] = []
		
		# Set attributes that would normally be set by class definition
		self.current_model = "gpt-4o-mini"
		self.is_working = False
		
		# Set CSS and bindings if textual is available
		if TEXTUAL_AVAILABLE:
			self.CSS = """
			.container {
				layout: vertical;
				height: 100%;
			}
			
			.header {
				height: 3;
				background: $primary;
			}
			
			.main {
				layout: horizontal;
				height: 1fr;
			}
			
			.sidebar {
				width: 30%;
				background: $surface;
				padding: 1;
			}
			
			.content {
				width: 70%;
				padding: 1;
			}
			
			.chat-log {
				height: 1fr;
				border: solid $accent;
				margin-bottom: 1;
			}
			
			.input-area {
				height: 4;
				border: solid $primary;
			}
			
			.status {
				height: 3;
				background: $surface-lighten-1;
				padding: 1;
			}
			
			.model-select {
				margin-bottom: 1;
			}
			
			.action-buttons {
				layout: horizontal;
				height: 3;
				margin-top: 1;
			}
			
			Button {
				margin-right: 1;
			}
			
			Input {
				width: 1fr;
			}
			"""
			
			self.BINDINGS = [
				Binding("ctrl+c", "quit", "Quit"),
				Binding("ctrl+l", "clear_log", "Clear Log"),
				Binding("ctrl+s", "save_session", "Save Session"),
				Binding("enter", "send_message", "Send", key_display="Enter"),
				Binding("escape", "focus_input", "Focus Input"),
			]
	
	def compose(self) -> ComposeResult:
		"""Compose the UI layout."""
		with Container(classes="container"):
			yield Header(show_clock=True, classes="header")
			
			with Container(classes="main"):
				# Sidebar with controls
				with Vertical(classes="sidebar"):
					yield Static("🤖 nvrunx AI Browser", classes="title")
					
					# Model selection
					yield Select([
						("OpenAI GPT-4o-mini", "gpt-4o-mini"),
						("OpenAI GPT-4o", "gpt-4o"),
						("Anthropic Claude", "claude-3-sonnet"),
						("Google Gemini", "gemini-pro"),
						("Groq Llama3", "llama3-70b-8192"),
						("Ollama", "llama2"),
					], value="gpt-4o-mini", classes="model-select", id="model_select")
					
					# Action buttons
					with Container(classes="action-buttons"):
						yield Button("New Session", id="new_session", variant="primary")
						yield Button("Save Session", id="save_session", variant="success")
					
					with Container(classes="action-buttons"):
						yield Button("Clear Log", id="clear_log", variant="warning")
						yield Button("Settings", id="settings", variant="default")
					
					# Status information
					with Container(classes="status"):
						yield Static("Status: Ready", id="status_text")
						yield Static("Model: GPT-4o-mini", id="model_text")
						yield Static("Sessions: 0", id="session_count")
				
				# Main content area
				with Vertical(classes="content"):
					# Chat log
					yield RichLog(classes="chat-log", id="chat_log", highlight=True)
					
					# Input area
					yield TextArea(
						placeholder="Type your request here... (Ctrl+Enter to send)",
						classes="input-area",
						id="message_input"
					)
			
			yield Footer()
	
	async def on_ready(self) -> None:
		"""Initialize the application."""
		self.log_message("🚀 nvrunx AI Browser Assistant Ready!")
		self.log_message("Type your request and press Ctrl+Enter to send.")
		
		# Check for API keys
		self.check_api_keys()
		
		# Focus on input
		self.query_one("#message_input").focus()
	
	def log_message(self, message: str, style: str = "white") -> None:
		"""Add a message to the chat log."""
		chat_log = self.query_one("#chat_log", RichLog)
		chat_log.write(Text(message, style=style))
	
	def log_panel(self, content: Any, title: str = "", style: str = "blue") -> None:
		"""Add a panel to the chat log."""
		chat_log = self.query_one("#chat_log", RichLog)
		panel = Panel(content, title=title, border_style=style)
		chat_log.write(panel)
	
	def check_api_keys(self) -> None:
		"""Check available API keys and warn if missing."""
		missing_keys = []
		
		if not CONFIG.OPENAI_API_KEY:
			missing_keys.append("OPENAI_API_KEY")
		if not getattr(CONFIG, 'ANTHROPIC_API_KEY', None):
			missing_keys.append("ANTHROPIC_API_KEY")
		if not getattr(CONFIG, 'GOOGLE_API_KEY', None):
			missing_keys.append("GOOGLE_API_KEY")
		if not getattr(CONFIG, 'GROQ_API_KEY', None):
			missing_keys.append("GROQ_API_KEY")
		
		if missing_keys:
			self.log_message(
				f"⚠️  Missing API keys: {', '.join(missing_keys)}",
				style="yellow"
			)
			self.log_message(
				"Set them in your .env file to use all models.",
				style="yellow"
			)
	
	def update_status(self, status: str) -> None:
		"""Update the status text."""
		status_widget = self.query_one("#status_text", Static)
		status_widget.update(f"Status: {status}")
	
	def update_model_display(self) -> None:
		"""Update the model display text."""
		model_widget = self.query_one("#model_text", Static)
		model_widget.update(f"Model: {self.current_model}")
	
	async def on_select_changed(self, event: Select.Changed) -> None:
		"""Handle model selection change."""
		if event.select.id == "model_select":
			self.current_model = str(event.value)
			self.update_model_display()
			self.log_message(f"🔄 Switched to model: {self.current_model}", style="cyan")
	
	async def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button presses."""
		button_id = event.button.id
		
		if button_id == "new_session":
			await self.action_new_session()
		elif button_id == "save_session":
			await self.action_save_session()
		elif button_id == "clear_log":
			await self.action_clear_log()
		elif button_id == "settings":
			await self.action_settings()
	
	async def action_send_message(self) -> None:
		"""Send a message to the AI agent."""
		if self.is_working:
			self.log_message("⚠️  Already processing a request, please wait...", style="yellow")
			return
		
		message_input = self.query_one("#message_input", TextArea)
		message = message_input.text.strip()
		
		if not message:
			return
		
		# Clear input
		message_input.clear()
		
		# Log user message
		self.log_panel(
			Text(message, style="white"),
			title="🧑 You",
			style="blue"
		)
		
		# Update status
		self.is_working = True
		self.update_status("Working...")
		
		try:
			# Create agent with selected model
			llm = self.get_llm_for_model(self.current_model)
			if not llm:
				self.log_message(f"❌ Model {self.current_model} not available", style="red")
				return
			
			self.agent = Agent(task=message, llm=llm)
			
			# Show progress
			self.log_message("🤖 Processing your request...", style="cyan")
			
			# Run agent
			result = await self.agent.run()
			
			# Log result
			self.log_panel(
				Text(str(result), style="green"),
				title="🤖 Assistant",
				style="green"
			)
			
			# Add to session history
			self.session_history.append(f"User: {message}")
			self.session_history.append(f"Assistant: {result}")
			
			# Update session count
			session_count = self.query_one("#session_count", Static)
			session_count.update(f"Sessions: {len(self.session_history) // 2}")
			
		except Exception as e:
			self.log_message(f"❌ Error: {e}", style="red")
			logging.exception("Error processing request")
		finally:
			self.is_working = False
			self.update_status("Ready")
	
	def get_llm_for_model(self, model: str) -> Optional[Any]:
		"""Get the appropriate LLM instance for the selected model."""
		try:
			if model.startswith("gpt-"):
				if not CONFIG.OPENAI_API_KEY:
					self.log_message("❌ OpenAI API key not found", style="red")
					return None
				return ChatOpenAI(model=model)
			
			elif model.startswith("claude-"):
				anthropic_key = getattr(CONFIG, 'ANTHROPIC_API_KEY', None)
				if not anthropic_key:
					self.log_message("❌ Anthropic API key not found", style="red")
					return None
				return ChatAnthropic(model=model, api_key=anthropic_key)
			
			elif model.startswith("gemini-"):
				google_key = getattr(CONFIG, 'GOOGLE_API_KEY', None)
				if not google_key:
					self.log_message("❌ Google API key not found", style="red")
					return None
				return ChatGoogle(model=model, api_key=google_key)
			
			elif model.startswith("llama"):
				if "groq" in model or "8192" in model:
					groq_key = getattr(CONFIG, 'GROQ_API_KEY', None)
					if not groq_key:
						self.log_message("❌ Groq API key not found", style="red")
						return None
					return ChatGroq(model=model, api_key=groq_key)
				else:
					# Local Ollama
					return ChatOllama(model=model)
			
			else:
				self.log_message(f"❌ Unknown model: {model}", style="red")
				return None
				
		except Exception as e:
			self.log_message(f"❌ Error creating LLM: {e}", style="red")
			return None
	
	async def action_new_session(self) -> None:
		"""Start a new session."""
		self.session_history.clear()
		await self.action_clear_log()
		self.log_message("🆕 Started new session", style="cyan")
		
		# Update session count
		session_count = self.query_one("#session_count", Static)
		session_count.update("Sessions: 0")
	
	async def action_save_session(self) -> None:
		"""Save the current session."""
		if not self.session_history:
			self.log_message("⚠️  No session to save", style="yellow")
			return
		
		try:
			# Create sessions directory
			sessions_dir = Path("sessions")
			sessions_dir.mkdir(exist_ok=True)
			
			# Generate filename
			from datetime import datetime
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			filename = sessions_dir / f"session_{timestamp}.txt"
			
			# Save session
			with open(filename, 'w', encoding='utf-8') as f:
				f.write(f"nvrunx Session - {datetime.now()}\n")
				f.write(f"Model: {self.current_model}\n")
				f.write("-" * 50 + "\n\n")
				
				for entry in self.session_history:
					f.write(entry + "\n\n")
			
			self.log_message(f"💾 Session saved to: {filename}", style="green")
			
		except Exception as e:
			self.log_message(f"❌ Error saving session: {e}", style="red")
	
	async def action_clear_log(self) -> None:
		"""Clear the chat log."""
		chat_log = self.query_one("#chat_log", RichLog)
		chat_log.clear()
		self.log_message("🧹 Log cleared", style="cyan")
	
	async def action_settings(self) -> None:
		"""Show settings information."""
		settings_info = f"""
🔧 Settings & Configuration

Current Model: {self.current_model}
Working: {self.is_working}
Session Entries: {len(self.session_history)}

Available Models:
- OpenAI GPT-4o-mini ({'✅' if CONFIG.OPENAI_API_KEY else '❌'})
- OpenAI GPT-4o ({'✅' if CONFIG.OPENAI_API_KEY else '❌'})
- Anthropic Claude ({'✅' if getattr(CONFIG, 'ANTHROPIC_API_KEY', None) else '❌'})
- Google Gemini ({'✅' if getattr(CONFIG, 'GOOGLE_API_KEY', None) else '❌'})
- Groq Llama3 ({'✅' if getattr(CONFIG, 'GROQ_API_KEY', None) else '❌'})
- Ollama (Local) ✅

Keybindings:
- Ctrl+C: Quit
- Ctrl+L: Clear Log  
- Ctrl+S: Save Session
- Ctrl+Enter: Send Message
- Escape: Focus Input
		"""
		
		self.log_panel(
			Text(settings_info.strip(), style="white"),
			title="⚙️  Settings",
			style="blue"
		)
	
	async def action_focus_input(self) -> None:
		"""Focus the input area."""
		self.query_one("#message_input").focus()
	
	async def on_text_area_changed(self, event: TextArea.Changed) -> None:
		"""Handle text area changes."""
		if event.text_area.id == "message_input":
			# Check for Ctrl+Enter
			pass  # This would need special key handling
	
	async def action_quit(self) -> None:
		"""Quit the application."""
		self.exit()


async def run_textual_cli():
	"""Run the textual CLI interface."""
	try:
		app = NvrunxTUI()
		await app.run_async()
	except ImportError:
		print("⚠️ Textual UI addon not installed. Install with: pip install 'nvrunx[cli]'")
		return False
	except Exception as e:
		print(f"❌ Error running textual CLI: {e}")
		return False
	return True


if __name__ == "__main__":
	asyncio.run(run_textual_cli())