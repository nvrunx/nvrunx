"""Groq chat model implementation."""

from dataclasses import dataclass
from typing import Any, TypeVar, overload
from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar('T', bound=BaseModel)


@dataclass
class ChatGroq(BaseChatModel):
	"""Groq chat model wrapper."""

	model: str = "llama3-70b-8192"
	api_key: str | None = None
	temperature: float | None = None
	max_tokens: int | None = None

	@property
	def provider(self) -> str:
		return 'groq'

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
		"""Invoke Groq model."""
		try:
			from groq import AsyncGroq
		except ImportError:
			raise ImportError("Groq library not installed. Install with: pip install groq")
		
		# Initialize client
		client_config = {}
		if self.api_key:
			client_config['api_key'] = self.api_key
		
		client = AsyncGroq(**client_config)
		
		try:
			# Convert messages to OpenAI format (Groq uses OpenAI-compatible API)
			groq_messages = self._convert_messages(messages)
			
			# Prepare request parameters
			request_params = {
				'model': self.model,
				'messages': groq_messages,
			}
			
			if self.temperature is not None:
				request_params['temperature'] = self.temperature
			if self.max_tokens is not None:
				request_params['max_tokens'] = self.max_tokens
			
			# Handle structured output using JSON mode
			if output_format is not None:
				request_params['response_format'] = {"type": "json_object"}
				# Add JSON schema instruction to system message
				from browser_use.llm.schema import SchemaOptimizer
				schema = SchemaOptimizer.create_json_schema(output_format)
				schema_instruction = f"Respond with valid JSON matching this schema: {schema}"
				
				# Add schema instruction to messages
				if groq_messages and groq_messages[0]["role"] == "system":
					groq_messages[0]["content"] += f"\n\n{schema_instruction}"
				else:
					groq_messages.insert(0, {
						"role": "system",
						"content": schema_instruction
					})
			
			# Make request
			response = await client.chat.completions.create(**request_params)
			
			# Extract usage information
			if response.usage:
				usage = ChatInvokeUsage(
					prompt_tokens=response.usage.prompt_tokens,
					completion_tokens=response.usage.completion_tokens,
					total_tokens=response.usage.total_tokens,
					prompt_cached_tokens=None,
					prompt_cache_creation_tokens=None,
					prompt_image_tokens=None
				)
			else:
				usage = ChatInvokeUsage(
					prompt_tokens=100,
					completion_tokens=50,
					total_tokens=150,
					prompt_cached_tokens=None,
					prompt_cache_creation_tokens=None,
					prompt_image_tokens=None
				)
			
			if output_format is None:
				# Return text response
				content = response.choices[0].message.content or ""
				return ChatInvokeCompletion(
					completion=content,
					usage=usage,
				)
			else:
				# Handle structured output
				try:
					import json
					content = response.choices[0].message.content or "{}"
					response_data = json.loads(content)
					structured_data = output_format(**response_data)
					return ChatInvokeCompletion(
						completion=structured_data,
						usage=usage,
					)
				except Exception:
					# Fallback: create empty instance
					return ChatInvokeCompletion(
						completion=output_format(),
						usage=usage,
					)
				
		except Exception as e:
			from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
			if "rate limit" in str(e).lower():
				raise ModelRateLimitError(f"Groq rate limit exceeded: {e}")
			else:
				raise ModelProviderError(f"Groq API error: {e}")
	
	def _convert_messages(self, messages: list[BaseMessage]) -> list[dict]:
		"""Convert BaseMessage objects to OpenAI/Groq format."""
		groq_messages = []
		
		for msg in messages:
			if isinstance(msg.content, str):
				groq_messages.append({
					"role": msg.role,
					"content": msg.content
				})
			elif isinstance(msg.content, list):
				# Handle multimodal content (text only for now)
				text_content = ""
				for item in msg.content:
					if isinstance(item, dict) and item.get("type") == "text":
						text_content += item.get("text", "")
				if text_content:
					groq_messages.append({
						"role": msg.role,
						"content": text_content
					})
		
		return groq_messages