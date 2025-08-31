"""Exception definitions for browser-use."""


class BrowserUseException(Exception):
	"""Base exception class for browser-use."""

	pass


class ActionNotExecutableError(BrowserUseException):
	"""Raised when an action cannot be executed."""

	pass