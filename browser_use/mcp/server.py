"""Complete MCP (Model Context Protocol) server implementation for nvrunx."""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

try:
	from mcp.server import Server
	from mcp.server.models import InitializationOptions
	from mcp.server.stdio import stdio_server
	from mcp.types import (
		Resource, Tool, TextContent, ImageContent, EmbeddedResource,
		CallToolResult, ListResourcesResult, ListToolsResult, ReadResourceResult
	)
	import mcp.server.stdio
	import mcp.types as types
except ImportError:
	print("MCP library not installed. Install with: pip install mcp", file=sys.stderr)
	sys.exit(1)

from browser_use import Agent, ChatOpenAI
from browser_use.browser import BrowserSession
from browser_use.dom import DomService
from browser_use.recorder import BrowserRecorder


class NvrunxMCPServer:
	"""MCP server for nvrunx browser automation."""
	
	def __init__(self):
		self.logger = logging.getLogger(f'{__name__}.NvrunxMCPServer')
		self.server = Server("nvrunx")
		self.browser_session: Optional[BrowserSession] = None
		self.dom_service: Optional[DomService] = None
		self.recorder: Optional[BrowserRecorder] = None
		
		# Setup handlers
		self._setup_handlers()
	
	def _setup_handlers(self):
		"""Setup MCP server handlers."""
		
		@self.server.list_tools()
		async def handle_list_tools() -> List[Tool]:
			"""List available tools."""
			return [
				Tool(
					name="browser_navigate",
					description="Navigate to a URL in the browser",
					inputSchema={
						"type": "object",
						"properties": {
							"url": {
								"type": "string",
								"description": "URL to navigate to"
							},
							"wait_until": {
								"type": "string", 
								"description": "Wait condition (networkidle, domcontentloaded, load)",
								"default": "networkidle"
							}
						},
						"required": ["url"]
					}
				),
				Tool(
					name="browser_start",
					description="Start a browser session",
					inputSchema={
						"type": "object",
						"properties": {
							"headless": {
								"type": "boolean",
								"description": "Run browser in headless mode",
								"default": True
							},
							"browser_type": {
								"type": "string",
								"description": "Browser type (chromium, firefox, webkit)",
								"default": "chromium"
							}
						}
					}
				),
				Tool(
					name="browser_close",
					description="Close the browser session",
					inputSchema={"type": "object", "properties": {}}
				),
				Tool(
					name="dom_extract",
					description="Extract DOM tree structure from current page",
					inputSchema={"type": "object", "properties": {}}
				),
				Tool(
					name="dom_find_elements",
					description="Find elements by text content",
					inputSchema={
						"type": "object", 
						"properties": {
							"text": {
								"type": "string",
								"description": "Text to search for"
							},
							"exact_match": {
								"type": "boolean",
								"description": "Whether to match text exactly",
								"default": False
							}
						},
						"required": ["text"]
					}
				),
				Tool(
					name="dom_click",
					description="Click an element by CSS selector",
					inputSchema={
						"type": "object",
						"properties": {
							"selector": {
								"type": "string",
								"description": "CSS selector for the element"
							}
						},
						"required": ["selector"]
					}
				),
				Tool(
					name="dom_fill_input",
					description="Fill an input field",
					inputSchema={
						"type": "object",
						"properties": {
							"selector": {
								"type": "string", 
								"description": "CSS selector for the input"
							},
							"value": {
								"type": "string",
								"description": "Value to fill"
							}
						},
						"required": ["selector", "value"]
					}
				),
				Tool(
					name="browser_screenshot",
					description="Take a screenshot of the current page",
					inputSchema={
						"type": "object",
						"properties": {
							"full_page": {
								"type": "boolean",
								"description": "Capture full page or just viewport",
								"default": False
							}
						}
					}
				),
				Tool(
					name="recording_start",
					description="Start GIF recording of browser actions",
					inputSchema={
						"type": "object",
						"properties": {
							"session_name": {
								"type": "string",
								"description": "Name for the recording session"
							}
						}
					}
				),
				Tool(
					name="recording_stop",
					description="Stop GIF recording",
					inputSchema={"type": "object", "properties": {}}
				),
				Tool(
					name="ai_agent_run",
					description="Run an AI agent to perform a browser automation task",
					inputSchema={
						"type": "object",
						"properties": {
							"task": {
								"type": "string",
								"description": "Task description for the AI agent"
							},
							"model": {
								"type": "string",
								"description": "LLM model to use",
								"default": "gpt-4o-mini"
							}
						},
						"required": ["task"]
					}
				)
			]
		
		@self.server.call_tool()
		async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
			"""Handle tool calls."""
			try:
				if name == "browser_start":
					return await self._start_browser(**arguments)
				elif name == "browser_close":
					return await self._close_browser()
				elif name == "browser_navigate":
					return await self._navigate(**arguments)
				elif name == "browser_screenshot":
					return await self._screenshot(**arguments)
				elif name == "dom_extract":
					return await self._extract_dom()
				elif name == "dom_find_elements":
					return await self._find_elements(**arguments)
				elif name == "dom_click":
					return await self._click_element(**arguments)
				elif name == "dom_fill_input":
					return await self._fill_input(**arguments)
				elif name == "recording_start":
					return await self._start_recording(**arguments)
				elif name == "recording_stop":
					return await self._stop_recording()
				elif name == "ai_agent_run":
					return await self._run_ai_agent(**arguments)
				else:
					return CallToolResult(
						content=[TextContent(
							type="text",
							text=f"Unknown tool: {name}"
						)],
						isError=True
					)
					
			except Exception as e:
				self.logger.error(f"Error calling tool {name}: {e}")
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Error: {e}"
					)],
					isError=True
				)
		
		@self.server.list_resources()
		async def handle_list_resources() -> List[Resource]:
			"""List available resources."""
			resources = []
			
			# Session info resource
			resources.append(Resource(
				uri="nvrunx://session/info",
				name="Browser Session Info",
				description="Current browser session information"
			))
			
			# DOM resource if session active
			if self.browser_session and hasattr(self.browser_session, 'page') and self.browser_session.page:
				resources.append(Resource(
					uri="nvrunx://dom/current",
					name="Current DOM",
					description="Current page DOM structure"
				))
			
			# Recording info if available
			if self.recorder:
				resources.append(Resource(
					uri="nvrunx://recording/info",
					name="Recording Info",
					description="Current recording session information"
				))
			
			return resources
		
		@self.server.read_resource()
		async def handle_read_resource(uri: str) -> ReadResourceResult:
			"""Handle resource reading."""
			try:
				if uri == "nvrunx://session/info":
					return await self._get_session_info()
				elif uri == "nvrunx://dom/current":
					return await self._get_current_dom()
				elif uri == "nvrunx://recording/info":
					return await self._get_recording_info()
				else:
					return ReadResourceResult(
						contents=[TextContent(
							type="text",
							text=f"Unknown resource: {uri}"
						)]
					)
			except Exception as e:
				self.logger.error(f"Error reading resource {uri}: {e}")
				return ReadResourceResult(
					contents=[TextContent(
						type="text",
						text=f"Error reading resource: {e}"
					)]
				)
	
	async def _start_browser(self, headless: bool = True, browser_type: str = "chromium") -> CallToolResult:
		"""Start browser session."""
		if self.browser_session:
			return CallToolResult(
				content=[TextContent(
					type="text", 
					text="Browser session already active"
				)]
			)
		
		try:
			self.browser_session = BrowserSession(
				browser_type=browser_type,
				headless=headless
			)
			await self.browser_session.start()
			
			# Initialize DOM service
			if hasattr(self.browser_session, 'page'):
				self.dom_service = DomService(page=self.browser_session.page)
			
			# Initialize recorder
			self.recorder = BrowserRecorder(
				browser_session=self.browser_session,
				output_dir="recordings"
			)
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Browser session started ({browser_type}, headless={headless})"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Failed to start browser: {e}"
				)],
				isError=True
			)
	
	async def _close_browser(self) -> CallToolResult:
		"""Close browser session."""
		if not self.browser_session:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No browser session active"
				)]
			)
		
		try:
			await self.browser_session.close()
			self.browser_session = None
			self.dom_service = None
			self.recorder = None
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="Browser session closed"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Error closing browser: {e}"
				)],
				isError=True
			)
	
	async def _navigate(self, url: str, wait_until: str = "networkidle") -> CallToolResult:
		"""Navigate to URL."""
		if not self.browser_session:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No browser session active. Use browser_start first."
				)],
				isError=True
			)
		
		try:
			await self.browser_session.navigate(url, wait_until=wait_until)
			title = await self.browser_session.get_page_title()
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Navigated to {url}. Page title: {title}"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Navigation failed: {e}"
				)],
				isError=True
			)
	
	async def _screenshot(self, full_page: bool = False) -> CallToolResult:
		"""Take screenshot."""
		if not self.browser_session:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No browser session active"
				)],
				isError=True
			)
		
		try:
			import base64
			screenshot_bytes = await self.browser_session.screenshot(full_page=full_page)
			screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
			
			return CallToolResult(
				content=[
					ImageContent(
						type="image",
						data=screenshot_b64,
						mimeType="image/png"
					),
					TextContent(
						type="text",
						text=f"Screenshot captured ({'full page' if full_page else 'viewport'})"
					)
				]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Screenshot failed: {e}"
				)],
				isError=True
			)
	
	async def _extract_dom(self) -> CallToolResult:
		"""Extract DOM structure."""
		if not self.dom_service:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No DOM service available. Start browser first."
				)],
				isError=True
			)
		
		try:
			dom_tree = await self.dom_service.extract_dom_tree()
			
			# Create summary
			summary = {
				"url": dom_tree.url,
				"title": dom_tree.title,
				"element_count": len(dom_tree.elements),
				"interactive_elements": sum(1 for el in dom_tree.elements if el.is_interactive),
				"visible_elements": sum(1 for el in dom_tree.elements if el.is_visible)
			}
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"DOM extracted successfully:\n{json.dumps(summary, indent=2)}"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"DOM extraction failed: {e}"
				)],
				isError=True
			)
	
	async def _find_elements(self, text: str, exact_match: bool = False) -> CallToolResult:
		"""Find elements by text."""
		if not self.dom_service:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No DOM service available"
				)],
				isError=True
			)
		
		try:
			elements = await self.dom_service.find_elements_by_text(text, exact_match)
			
			results = []
			for el in elements[:10]:  # Limit to first 10 results
				results.append({
					"tag": el.tag_name,
					"text": el.text_content[:100],
					"xpath": el.xpath,
					"css_selector": el.css_selector,
					"visible": el.is_visible,
					"interactive": el.is_interactive
				})
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Found {len(elements)} elements matching '{text}':\n{json.dumps(results, indent=2)}"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Element search failed: {e}"
				)],
				isError=True
			)
	
	async def _click_element(self, selector: str) -> CallToolResult:
		"""Click element."""
		if not self.dom_service:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No DOM service available"
				)],
				isError=True
			)
		
		try:
			success = await self.dom_service.click_element(selector)
			
			if success:
				# Record action if recording
				if self.recorder and self.recorder.is_recording():
					await self.recorder.record_action(f"Clicked: {selector}")
				
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Successfully clicked element: {selector}"
					)]
				)
			else:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Failed to click element: {selector}"
					)],
					isError=True
				)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Click failed: {e}"
				)],
				isError=True
			)
	
	async def _fill_input(self, selector: str, value: str) -> CallToolResult:
		"""Fill input field."""
		if not self.dom_service:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No DOM service available"
				)],
				isError=True
			)
		
		try:
			success = await self.dom_service.fill_input(selector, value)
			
			if success:
				# Record action if recording
				if self.recorder and self.recorder.is_recording():
					await self.recorder.record_action(f"Filled: {selector} = {value}")
				
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Successfully filled input {selector} with: {value}"
					)]
				)
			else:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Failed to fill input: {selector}"
					)],
					isError=True
				)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Fill input failed: {e}"
				)],
				isError=True
			)
	
	async def _start_recording(self, session_name: Optional[str] = None) -> CallToolResult:
		"""Start GIF recording."""
		if not self.recorder:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No recorder available. Start browser first."
				)],
				isError=True
			)
		
		try:
			success = await self.recorder.start_recording(session_name)
			
			if success:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Recording started: {session_name or 'default'}"
					)]
				)
			else:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text="Failed to start recording"
					)],
					isError=True
				)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Recording start failed: {e}"
				)],
				isError=True
			)
	
	async def _stop_recording(self) -> CallToolResult:
		"""Stop GIF recording."""
		if not self.recorder:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text="No recorder available"
				)],
				isError=True
			)
		
		try:
			gif_path = await self.recorder.stop_recording()
			
			if gif_path:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text=f"Recording stopped. GIF saved to: {gif_path}"
					)]
				)
			else:
				return CallToolResult(
					content=[TextContent(
						type="text",
						text="Recording stopped (no GIF created)"
					)]
				)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"Stop recording failed: {e}"
				)],
				isError=True
			)
	
	async def _run_ai_agent(self, task: str, model: str = "gpt-4o-mini") -> CallToolResult:
		"""Run AI agent."""
		try:
			agent_options = {
				'task': task,
				'llm': ChatOpenAI(model=model),
			}
			
			if self.browser_session:
				agent_options['browser_session'] = self.browser_session
			
			agent = Agent(**agent_options)
			result = await agent.run()
			
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"AI Agent completed task:\n\nTask: {task}\nResult: {result}"
				)]
			)
		
		except Exception as e:
			return CallToolResult(
				content=[TextContent(
					type="text",
					text=f"AI agent failed: {e}"
				)],
				isError=True
			)
	
	async def _get_session_info(self) -> ReadResourceResult:
		"""Get session information."""
		if not self.browser_session:
			info = {"status": "No browser session active"}
		else:
			info = {
				"status": "Browser session active",
				"url": self.browser_session.page.url if hasattr(self.browser_session, 'page') and self.browser_session.page else "No page",
				"title": await self.browser_session.get_page_title() if hasattr(self.browser_session, 'page') and self.browser_session.page else "No title",
			}
		
		return ReadResourceResult(
			contents=[TextContent(
				type="text",
				text=json.dumps(info, indent=2)
			)]
		)
	
	async def _get_current_dom(self) -> ReadResourceResult:
		"""Get current DOM."""
		if not self.dom_service:
			return ReadResourceResult(
				contents=[TextContent(
					type="text",
					text="No DOM service available"
				)]
			)
		
		try:
			dom_tree = await self.dom_service.extract_dom_tree()
			
			# Create simplified DOM representation
			dom_data = {
				"url": dom_tree.url,
				"title": dom_tree.title,
				"metadata": dom_tree.metadata,
				"elements": [
					{
						"tag": el.tag_name,
						"text": el.text_content[:200],
						"xpath": el.xpath,
						"visible": el.is_visible,
						"interactive": el.is_interactive
					}
					for el in dom_tree.elements[:50]  # Limit to first 50 elements
				]
			}
			
			return ReadResourceResult(
				contents=[TextContent(
					type="text",
					text=json.dumps(dom_data, indent=2)
				)]
			)
		
		except Exception as e:
			return ReadResourceResult(
				contents=[TextContent(
					type="text",
					text=f"Error getting DOM: {e}"
				)]
			)
	
	async def _get_recording_info(self) -> ReadResourceResult:
		"""Get recording information."""
		if not self.recorder:
			info = {"status": "No recorder available"}
		else:
			info = self.recorder.get_stats()
		
		return ReadResourceResult(
			contents=[TextContent(
				type="text",
				text=json.dumps(info, indent=2)
			)]
		)
	
	async def run(self):
		"""Run the MCP server."""
		async with stdio_server() as (read_stream, write_stream):
			await self.server.run(
				read_stream,
				write_stream,
				InitializationOptions(
					server_name="nvrunx",
					server_version="0.7.0",
					capabilities=self.server.get_capabilities(
						notification_options=None,
						experimental_capabilities={}
					)
				)
			)


async def main():
	"""Main entry point for MCP server."""
	logging.basicConfig(level=logging.INFO)
	
	server = NvrunxMCPServer()
	await server.run()


if __name__ == "__main__":
	asyncio.run(main())