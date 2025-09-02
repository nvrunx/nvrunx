"""DOM extraction and manipulation service with advanced capabilities."""

import asyncio
import json
import logging
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

try:
	from bs4 import BeautifulSoup, Tag
	from bs4.element import NavigableString
except ImportError:
	BeautifulSoup = Tag = NavigableString = None

try:
	from playwright.async_api import Page
except ImportError:
	Page = None


@dataclass
class DOMElement:
	"""Represents a DOM element with metadata."""
	tag_name: str
	attributes: Dict[str, Any]
	text_content: str
	inner_html: str
	xpath: str
	css_selector: str
	bounding_box: Optional[Dict[str, float]] = None
	is_visible: bool = True
	is_interactive: bool = False


@dataclass  
class DOMTree:
	"""Represents a DOM tree structure."""
	url: str
	title: str
	elements: List[DOMElement]
	metadata: Dict[str, Any]


class DomService:
	"""Advanced DOM extraction and manipulation service."""
	
	def __init__(self, page: Optional[Page] = None, **kwargs: Any):
		self.logger = logging.getLogger(f'{__name__}.DomService')
		self.page = page
		self._dom_scripts_loaded = False
	
	async def _ensure_dom_scripts(self) -> None:
		"""Ensure DOM manipulation scripts are loaded."""
		if self._dom_scripts_loaded or not self.page:
			return
			
		# Inject DOM utility scripts
		dom_utils_script = """
		window.domUtils = {
			// Get element XPath
			getXPath: function(element) {
				if (!element) return '';
				if (element.id !== '') return `//*[@id="${element.id}"]`;
				
				let path = '';
				while (element && element.nodeType === Node.ELEMENT_NODE) {
					let index = 0;
					let hasFollowingSiblings = false;
					for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
						if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === element.nodeName) {
							index++;
						}
					}
					for (let sibling = element.nextSibling; sibling; sibling = sibling.nextSibling) {
						if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === element.nodeName) {
							hasFollowingSiblings = true;
							break;
						}
					}
					
					let tagName = element.nodeName.toLowerCase();
					let pathIndex = (index > 0 || hasFollowingSiblings) ? `[${index + 1}]` : '';
					path = '/' + tagName + pathIndex + path;
					
					element = element.parentNode;
				}
				return path;
			},
			
			// Get CSS selector
			getCSSSelector: function(element) {
				if (!element) return '';
				if (element.id) return `#${element.id}`;
				
				let selector = element.tagName.toLowerCase();
				if (element.className) {
					selector += '.' + element.className.split(' ').join('.');
				}
				
				return selector;
			},
			
			// Check if element is interactive
			isInteractive: function(element) {
				if (!element) return false;
				
				const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
				const tagName = element.tagName.toLowerCase();
				
				return interactiveTags.includes(tagName) || 
					   element.onclick !== null || 
					   element.getAttribute('onclick') !== null ||
					   element.getAttribute('role') === 'button' ||
					   element.tabIndex >= 0;
			},
			
			// Get element bounding box
			getBoundingBox: function(element) {
				if (!element) return null;
				const rect = element.getBoundingClientRect();
				return {
					x: rect.x,
					y: rect.y,
					width: rect.width,
					height: rect.height,
					top: rect.top,
					right: rect.right,
					bottom: rect.bottom,
					left: rect.left
				};
			},
			
			// Check if element is visible
			isVisible: function(element) {
				if (!element) return false;
				const style = window.getComputedStyle(element);
				return style.display !== 'none' && 
					   style.visibility !== 'hidden' && 
					   style.opacity !== '0' &&
					   element.offsetParent !== null;
			}
		};
		"""
		
		try:
			await self.page.evaluate(dom_utils_script)
			self._dom_scripts_loaded = True
			self.logger.debug("DOM utility scripts loaded")
		except Exception as e:
			self.logger.error(f"Failed to load DOM scripts: {e}")
			raise
	
	async def extract_dom_tree(self) -> DOMTree:
		"""Extract complete DOM tree with metadata."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		await self._ensure_dom_scripts()
		
		# Get page metadata
		url = self.page.url
		title = await self.page.title()
		
		# Extract all elements
		elements_data = await self.page.evaluate("""
			() => {
				const elements = [];
				const allElements = document.querySelectorAll('*');
				
				for (let i = 0; i < allElements.length; i++) {
					const el = allElements[i];
					if (!el.tagName) continue;
					
					const elementData = {
						tagName: el.tagName.toLowerCase(),
						attributes: {},
						textContent: el.textContent ? el.textContent.trim().substring(0, 500) : '',
						innerHTML: el.innerHTML ? el.innerHTML.substring(0, 1000) : '',
						xpath: window.domUtils.getXPath(el),
						cssSelector: window.domUtils.getCSSSelector(el),
						boundingBox: window.domUtils.getBoundingBox(el),
						isVisible: window.domUtils.isVisible(el),
						isInteractive: window.domUtils.isInteractive(el)
					};
					
					// Extract attributes
					for (let j = 0; j < el.attributes.length; j++) {
						const attr = el.attributes[j];
						elementData.attributes[attr.name] = attr.value;
					}
					
					elements.push(elementData);
				}
				
				return elements;
			}
		""")
		
		# Convert to DOMElement objects
		elements = []
		for data in elements_data:
			element = DOMElement(
				tag_name=data['tagName'],
				attributes=data['attributes'],
				text_content=data['textContent'],
				inner_html=data['innerHTML'],
				xpath=data['xpath'],
				css_selector=data['cssSelector'],
				bounding_box=data['boundingBox'],
				is_visible=data['isVisible'],
				is_interactive=data['isInteractive']
			)
			elements.append(element)
		
		# Additional metadata
		viewport_size = await self.page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
		
		metadata = {
			'viewport': viewport_size,
			'element_count': len(elements),
			'interactive_elements': sum(1 for el in elements if el.is_interactive),
			'visible_elements': sum(1 for el in elements if el.is_visible)
		}
		
		dom_tree = DOMTree(
			url=url,
			title=title,
			elements=elements,
			metadata=metadata
		)
		
		self.logger.info(f"Extracted DOM tree: {len(elements)} elements, {metadata['interactive_elements']} interactive")
		return dom_tree
	
	async def find_elements_by_text(self, text: str, exact_match: bool = False) -> List[DOMElement]:
		"""Find elements containing specific text."""
		dom_tree = await self.extract_dom_tree()
		
		matches = []
		for element in dom_tree.elements:
			element_text = element.text_content.lower()
			search_text = text.lower()
			
			if exact_match:
				if element_text == search_text:
					matches.append(element)
			else:
				if search_text in element_text:
					matches.append(element)
		
		self.logger.debug(f"Found {len(matches)} elements matching text: {text}")
		return matches
	
	async def find_interactive_elements(self, element_types: Optional[List[str]] = None) -> List[DOMElement]:
		"""Find all interactive elements, optionally filtered by type."""
		dom_tree = await self.extract_dom_tree()
		
		interactive_elements = [el for el in dom_tree.elements if el.is_interactive and el.is_visible]
		
		if element_types:
			element_types = [t.lower() for t in element_types]
			interactive_elements = [
				el for el in interactive_elements 
				if el.tag_name.lower() in element_types
			]
		
		self.logger.debug(f"Found {len(interactive_elements)} interactive elements")
		return interactive_elements
	
	async def click_element(self, selector: str) -> bool:
		"""Click an element by selector."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		try:
			await self.page.click(selector)
			self.logger.debug(f"Clicked element: {selector}")
			return True
		except Exception as e:
			self.logger.error(f"Failed to click element {selector}: {e}")
			return False
	
	async def fill_input(self, selector: str, value: str) -> bool:
		"""Fill an input element."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		try:
			await self.page.fill(selector, value)
			self.logger.debug(f"Filled input {selector} with value: {value}")
			return True
		except Exception as e:
			self.logger.error(f"Failed to fill input {selector}: {e}")
			return False
	
	async def extract_forms(self) -> List[Dict[str, Any]]:
		"""Extract all forms with their fields."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		forms_data = await self.page.evaluate("""
			() => {
				const forms = [];
				const formElements = document.querySelectorAll('form');
				
				for (let i = 0; i < formElements.length; i++) {
					const form = formElements[i];
					const formData = {
						action: form.action || '',
						method: form.method || 'GET',
						id: form.id || '',
						className: form.className || '',
						fields: []
					};
					
					// Extract form fields
					const inputs = form.querySelectorAll('input, select, textarea');
					for (let j = 0; j < inputs.length; j++) {
						const field = inputs[j];
						const fieldData = {
							type: field.type || field.tagName.toLowerCase(),
							name: field.name || '',
							id: field.id || '',
							placeholder: field.placeholder || '',
							required: field.required || false,
							value: field.value || ''
						};
						formData.fields.push(fieldData);
					}
					
					forms.push(formData);
				}
				
				return forms;
			}
		""")
		
		self.logger.debug(f"Extracted {len(forms_data)} forms")
		return forms_data
	
	async def extract_links(self, filter_domain: Optional[str] = None) -> List[Dict[str, Any]]:
		"""Extract all links, optionally filtered by domain."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		links_data = await self.page.evaluate("""
			() => {
				const links = [];
				const linkElements = document.querySelectorAll('a[href]');
				
				for (let i = 0; i < linkElements.length; i++) {
					const link = linkElements[i];
					const linkData = {
						href: link.href,
						text: link.textContent ? link.textContent.trim() : '',
						title: link.title || '',
						target: link.target || '_self'
					};
					links.push(linkData);
				}
				
				return links;
			}
		""")
		
		if filter_domain:
			links_data = [
				link for link in links_data 
				if filter_domain in link['href']
			]
		
		self.logger.debug(f"Extracted {len(links_data)} links")
		return links_data
	
	async def save_dom_tree(self, filepath: str) -> None:
		"""Save DOM tree to JSON file."""
		dom_tree = await self.extract_dom_tree()
		
		# Convert to serializable format
		data = {
			'url': dom_tree.url,
			'title': dom_tree.title,
			'metadata': dom_tree.metadata,
			'elements': [
				{
					'tag_name': el.tag_name,
					'attributes': el.attributes,
					'text_content': el.text_content,
					'inner_html': el.inner_html,
					'xpath': el.xpath,
					'css_selector': el.css_selector,
					'bounding_box': el.bounding_box,
					'is_visible': el.is_visible,
					'is_interactive': el.is_interactive
				}
				for el in dom_tree.elements
			]
		}
		
		Path(filepath).parent.mkdir(parents=True, exist_ok=True)
		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
		
		self.logger.info(f"Saved DOM tree to: {filepath}")
	
	async def wait_for_element(self, selector: str, timeout: float = 30000) -> bool:
		"""Wait for element to appear."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		try:
			await self.page.wait_for_selector(selector, timeout=timeout)
			self.logger.debug(f"Element appeared: {selector}")
			return True
		except Exception as e:
			self.logger.warning(f"Element did not appear within timeout: {selector}")
			return False
	
	async def scroll_to_element(self, selector: str) -> bool:
		"""Scroll to make element visible."""
		if not self.page:
			raise RuntimeError("No page instance available")
			
		try:
			await self.page.evaluate(f"""
				() => {{
					const element = document.querySelector('{selector}');
					if (element) {{
						element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
						return true;
					}}
					return false;
				}}
			""")
			self.logger.debug(f"Scrolled to element: {selector}")
			return True
		except Exception as e:
			self.logger.error(f"Failed to scroll to element {selector}: {e}")
			return False