"""DOM-related views and models."""

from typing import Any
from pydantic import BaseModel

# Default attributes to include when extracting DOM elements
DEFAULT_INCLUDE_ATTRIBUTES = [
	'aria-label',
	'title',
	'alt',
	'placeholder',
	'value',
	'href',
	'src',
	'type',
	'role'
]


class DOMInteractedElement(BaseModel):
	"""Represents an element that was interacted with."""
	
	tag: str
	attributes: dict[str, str] = {}
	
	@classmethod
	def load_from_enhanced_dom_tree(cls, element: Any) -> 'DOMInteractedElement':
		"""Load from enhanced DOM tree element."""
		return cls(tag='div', attributes={})


# Selector map type for DOM elements
DOMSelectorMap = dict[int, Any]