"""Browser session management with Playwright/CDP integration."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

try:
	from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
except ImportError:
	Playwright = Browser = BrowserContext = Page = None
	async_playwright = None

try:
	import cdp_use
	from cdp_use import CDPSession
except ImportError:
	CDPSession = None


class BrowserSession:
	"""Enhanced browser session management with Playwright/CDP support."""
	
	def __init__(
		self,
		browser_type: str = "chromium",
		headless: bool = True,
		cdp_enabled: bool = False,
		viewport: Optional[dict] = None,
		user_agent: Optional[str] = None,
		**kwargs: Any
	):
		self.logger = logging.getLogger(f'{__name__}.BrowserSession')
		self.browser_type = browser_type
		self.headless = headless
		self.cdp_enabled = cdp_enabled
		self.viewport = viewport or {"width": 1280, "height": 720}
		self.user_agent = user_agent
		self.extra_args = kwargs
		
		# Playwright objects
		self.playwright: Optional[Playwright] = None
		self.browser: Optional[Browser] = None
		self.context: Optional[BrowserContext] = None
		self.page: Optional[Page] = None
		
		# CDP session if enabled
		self.cdp_session: Optional[CDPSession] = None
		
		self._started = False
	
	async def start(self) -> None:
		"""Start browser session."""
		if self._started:
			self.logger.warning("Browser session already started")
			return
			
		self.logger.info(f"Starting {self.browser_type} browser session (headless={self.headless})")
		
		if async_playwright is None:
			raise ImportError("Playwright not installed. Install with: pip install playwright")
		
		try:
			# Initialize Playwright
			self.playwright = await async_playwright().start()
			
			# Get browser
			if self.browser_type == "chromium":
				browser_launcher = self.playwright.chromium
			elif self.browser_type == "firefox":
				browser_launcher = self.playwright.firefox
			elif self.browser_type == "webkit":
				browser_launcher = self.playwright.webkit
			else:
				raise ValueError(f"Unsupported browser type: {self.browser_type}")
			
			# Launch options
			launch_options = {
				"headless": self.headless,
				**self.extra_args
			}
			
			# Add CDP support if enabled
			if self.cdp_enabled and self.browser_type == "chromium":
				launch_options["args"] = launch_options.get("args", []) + [
					"--remote-debugging-port=9222"
				]
			
			self.browser = await browser_launcher.launch(**launch_options)
			
			# Create context
			context_options = {
				"viewport": self.viewport,
			}
			if self.user_agent:
				context_options["user_agent"] = self.user_agent
				
			self.context = await self.browser.new_context(**context_options)
			
			# Create page
			self.page = await self.context.new_page()
			
			# Initialize CDP session if enabled
			if self.cdp_enabled and CDPSession is not None and self.browser_type == "chromium":
				try:
					self.cdp_session = CDPSession("http://localhost:9222")
					await self.cdp_session.connect()
					self.logger.info("CDP session initialized")
				except Exception as e:
					self.logger.warning(f"Failed to initialize CDP session: {e}")
			
			self._started = True
			self.logger.info("Browser session started successfully")
			
		except Exception as e:
			self.logger.error(f"Failed to start browser session: {e}")
			await self.close()
			raise
	
	async def close(self) -> None:
		"""Close browser session."""
		if not self._started:
			return
			
		self.logger.info("Closing browser session")
		
		try:
			# Close CDP session
			if self.cdp_session:
				try:
					await self.cdp_session.disconnect()
				except Exception as e:
					self.logger.warning(f"Error closing CDP session: {e}")
			
			# Close Playwright objects
			if self.page:
				await self.page.close()
			if self.context:
				await self.context.close()
			if self.browser:
				await self.browser.close()
			if self.playwright:
				await self.playwright.stop()
				
		except Exception as e:
			self.logger.error(f"Error closing browser session: {e}")
		finally:
			self.page = None
			self.context = None
			self.browser = None
			self.playwright = None
			self.cdp_session = None
			self._started = False
			
		self.logger.info("Browser session closed")
	
	async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
		"""Navigate to URL."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		self.logger.info(f"Navigating to: {url}")
		await self.page.goto(url, wait_until=wait_until)
	
	async def wait_for_selector(self, selector: str, timeout: float = 30000) -> Any:
		"""Wait for element to appear."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		return await self.page.wait_for_selector(selector, timeout=timeout)
	
	async def click(self, selector: str) -> None:
		"""Click element."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		await self.page.click(selector)
	
	async def type_text(self, selector: str, text: str) -> None:
		"""Type text into element."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		await self.page.fill(selector, text)
	
	async def get_page_content(self) -> str:
		"""Get page HTML content."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		return await self.page.content()
	
	async def get_page_title(self) -> str:
		"""Get page title."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		return await self.page.title()
	
	async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> bytes:
		"""Take screenshot."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		return await self.page.screenshot(path=path, full_page=full_page)
	
	async def evaluate_script(self, script: str) -> Any:
		"""Evaluate JavaScript on the page."""
		if not self.page:
			raise RuntimeError("Browser session not started")
			
		return await self.page.evaluate(script)
	
	async def get_cookies(self) -> list[dict]:
		"""Get all cookies."""
		if not self.context:
			raise RuntimeError("Browser session not started")
			
		return await self.context.cookies()
	
	async def add_cookie(self, cookie: dict) -> None:
		"""Add cookie."""
		if not self.context:
			raise RuntimeError("Browser session not started")
			
		await self.context.add_cookies([cookie])
	
	@asynccontextmanager
	async def managed_session(self) -> AsyncGenerator["BrowserSession", None]:
		"""Context manager for browser session."""
		try:
			await self.start()
			yield self
		finally:
			await self.close()


class BrowserProfile:
	"""Browser profile configuration for consistent sessions."""
	
	def __init__(
		self,
		name: str,
		browser_type: str = "chromium",
		headless: bool = True,
		viewport: Optional[dict] = None,
		user_agent: Optional[str] = None,
		locale: Optional[str] = None,
		timezone: Optional[str] = None,
		permissions: Optional[list[str]] = None,
		**kwargs: Any
	):
		self.name = name
		self.browser_type = browser_type
		self.headless = headless
		self.viewport = viewport or {"width": 1280, "height": 720}
		self.user_agent = user_agent
		self.locale = locale
		self.timezone = timezone
		self.permissions = permissions or []
		self.extra_options = kwargs
	
	def create_session(self, **overrides: Any) -> BrowserSession:
		"""Create a browser session with this profile."""
		options = {
			"browser_type": self.browser_type,
			"headless": self.headless,
			"viewport": self.viewport,
			"user_agent": self.user_agent,
			**self.extra_options,
			**overrides
		}
		
		return BrowserSession(**options)