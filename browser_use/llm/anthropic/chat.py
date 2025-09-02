"""Anthropic Claude chat model implementation."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar('T', bound=BaseModel)


@dataclass
class ChatAnthropic(BaseChatModel):
	"""
	A wrapper around Anthropic's chat model.
	"""

	# Model configuration
	model: str
	max_tokens: int = 8192
	temperature: float | None = None
	top_p: float | None = None
	seed: int | None = None

	# Client initialization parameters
	api_key: str | None = None
	auth_token: str | None = None
	base_url: str | httpx.URL | None = None
	timeout: float | None = None
	max_retries: int = 10
	default_headers: Mapping[str, str] | None = None
	default_query: Mapping[str, object] | None = None

	# Static
	@property
	def provider(self) -> str:
		return 'anthropic'

	@property
	def name(self) -> str:
		return str(self.model)

	@overload
	async def ainvoke(self, messages: list[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]: ...

	@overload
	async def ainvoke(self, messages: list[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]: ...

	async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the model with the given messages.
		
		Args:
			messages: List of chat messages
			output_format: Optional Pydantic model class for structured output
			
		Returns:
			Either a string response or an instance of output_format
		"""
		try:
			import anthropic
		except ImportError:
			raise ImportError("Anthropic library not installed. Install with: pip install anthropic")
		
		# Initialize client
		client_config = {}
		if self.api_key:
			client_config['api_key'] = self.api_key
		if self.base_url:
			client_config['base_url'] = str(self.base_url)
		if self.timeout:
			client_config['timeout'] = self.timeout
		if self.max_retries:
			client_config['max_retries'] = self.max_retries
		if self.default_headers:
			client_config['default_headers'] = dict(self.default_headers)
		
		client = anthropic.AsyncAnthropic(**client_config)
		
		try:
			# Convert messages to Anthropic format
			anthropic_messages = self._convert_messages(messages)
			
			# Prepare request parameters
			request_params = {
				'model': self.model,
				'messages': anthropic_messages,
				'max_tokens': self.max_tokens,
			}
			
			if self.temperature is not None:
				request_params['temperature'] = self.temperature
			if self.top_p is not None:
				request_params['top_p'] = self.top_p
			if self.seed is not None:
				request_params['system'] = f"Random seed: {self.seed}"
			
			# Handle structured output
			if output_format is not None:
				# Use Anthropic's tool calling for structured output
				from browser_use.llm.schema import SchemaOptimizer
				
				schema = SchemaOptimizer.create_json_schema(output_format)
				request_params['tools'] = [{
					'name': 'structured_output',
					'description': f'Return data in {output_format.__name__} format',
					'input_schema': schema
				}]
				request_params['tool_choice'] = {'type': 'tool', 'name': 'structured_output'}
			
			# Make request
			response = await client.messages.create(**request_params)
			
			# Extract usage information
			usage = ChatInvokeUsage(
				prompt_tokens=response.usage.input_tokens,
				completion_tokens=response.usage.output_tokens,
				total_tokens=response.usage.input_tokens + response.usage.output_tokens,
				prompt_cached_tokens=getattr(response.usage, 'cache_read_input_tokens', None),
				prompt_cache_creation_tokens=getattr(response.usage, 'cache_creation_input_tokens', None),
				prompt_image_tokens=None
			)
			
			if output_format is None:
				# Return text response
				content = ""
				for block in response.content:
					if block.type == "text":
						content += block.text
				
				return ChatInvokeCompletion(
					completion=content,
					usage=usage,
				)
			else:
				# Handle structured output
				if response.content and len(response.content) > 0:
					for block in response.content:
						if block.type == "tool_use":
							try:
								structured_data = output_format(**block.input)
								return ChatInvokeCompletion(
									completion=structured_data,
									usage=usage,
								)
							except Exception as e:
								# Fallback: create empty instance
								return ChatInvokeCompletion(
									completion=output_format(),
									usage=usage,
								)
				
				# Fallback for structured output
				return ChatInvokeCompletion(
					completion=output_format(),
					usage=usage,
				)
				
		except anthropic.RateLimitError as e:
			raise ModelRateLimitError(f"Anthropic rate limit exceeded: {e}")
		except anthropic.APIError as e:
			raise ModelProviderError(f"Anthropic API error: {e}")
		except Exception as e:
			raise ModelProviderError(f"Unexpected error with Anthropic: {e}")
	
	def _convert_messages(self, messages: list[BaseMessage]) -> list[dict]:
		"""Convert BaseMessage objects to Anthropic message format."""
		anthropic_messages = []
		
		for msg in messages:
			if msg.role == "system":
				# Anthropic handles system messages differently
				continue
			elif msg.role == "user":
				role = "user"
			elif msg.role == "assistant":
				role = "assistant"
			else:
				continue
			
			# Handle content
			if isinstance(msg.content, str):
				anthropic_messages.append({
					"role": role,
					"content": msg.content
				})
			elif isinstance(msg.content, list):
				# Handle multimodal content
				content_blocks = []
				for item in msg.content:
					if isinstance(item, dict):
						if item.get("type") == "text":
							content_blocks.append({
								"type": "text",
								"text": item.get("text", "")
							})
						elif item.get("type") == "image_url":
							# Convert image for Anthropic
							image_data = item.get("image_url", {}).get("url", "")
							if image_data.startswith("data:"):
								# Extract base64 data
								media_type, base64_data = image_data.split(",", 1)
								content_blocks.append({
									"type": "image",
									"source": {
										"type": "base64",
										"media_type": media_type.split(":")[1].split(";")[0],
										"data": base64_data
									}
								})
				
				if content_blocks:
					anthropic_messages.append({
						"role": role,
						"content": content_blocks
					})
		
		return anthropic_messages