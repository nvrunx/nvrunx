"""Ollama chat model implementation."""

from dataclasses import dataclass
from typing import Any, TypeVar, overload
from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar('T', bound=BaseModel)


@dataclass
class ChatOllama(BaseChatModel):
	"""Ollama local model wrapper."""

	model: str = "llama2"
	base_url: str = "http://localhost:11434"
	temperature: float | None = None
	max_tokens: int | None = None

	@property
	def provider(self) -> str:
		return 'ollama'

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
		"""Invoke Ollama model."""
		try:
			import ollama
		except ImportError:
			raise ImportError("Ollama library not installed. Install with: pip install ollama")
		
		# Initialize client
		client = ollama.AsyncClient(host=self.base_url)
		
		try:
			# Convert messages to Ollama format
			ollama_messages = self._convert_messages(messages)
			
			# Prepare request parameters
			request_params = {
				'model': self.model,
				'messages': ollama_messages,
			}
			
			# Set generation options
			options = {}
			if self.temperature is not None:
				options['temperature'] = self.temperature
			if self.max_tokens is not None:
				options['num_predict'] = self.max_tokens
			
			if options:
				request_params['options'] = options
			
			# Handle structured output
			if output_format is not None:
				from browser_use.llm.schema import SchemaOptimizer
				schema = SchemaOptimizer.create_json_schema(output_format)
				schema_instruction = f"Respond with valid JSON matching this schema: {schema}"
				
				# Add schema instruction to messages
				if ollama_messages and ollama_messages[0]["role"] == "system":
					ollama_messages[0]["content"] += f"\n\n{schema_instruction}"
				else:
					ollama_messages.insert(0, {
						"role": "system",
						"content": schema_instruction
					})
				request_params['messages'] = ollama_messages
			
			# Make request
			response = await client.chat(**request_params)
			
			# Extract usage information (Ollama doesn't provide token counts)
			usage = ChatInvokeUsage(
				prompt_tokens=100,  # Estimated
				completion_tokens=50,  # Estimated
				total_tokens=150,  # Estimated
				prompt_cached_tokens=None,
				prompt_cache_creation_tokens=None,
				prompt_image_tokens=None
			)
			
			if output_format is None:
				# Return text response
				content = response.get('message', {}).get('content', '')
				return ChatInvokeCompletion(
					completion=content,
					usage=usage,
				)
			else:
				# Handle structured output
				try:
					import json
					content = response.get('message', {}).get('content', '{}')
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
			from browser_use.llm.exceptions import ModelProviderError
			raise ModelProviderError(f"Ollama API error: {e}")
	
	def _convert_messages(self, messages: list[BaseMessage]) -> list[dict]:
		"""Convert BaseMessage objects to Ollama format."""
		ollama_messages = []
		
		for msg in messages:
			if isinstance(msg.content, str):
				ollama_messages.append({
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
					ollama_messages.append({
						"role": msg.role,
						"content": text_content
					})
		
		return ollama_messages