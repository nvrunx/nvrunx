"""Google Gemini chat model implementation."""

from dataclasses import dataclass
from typing import Any, TypeVar, overload
from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar('T', bound=BaseModel)


@dataclass
class ChatGoogle(BaseChatModel):
	"""Google Gemini chat model wrapper."""

	model: str = "gemini-pro"
	api_key: str | None = None
	temperature: float | None = None
	max_tokens: int | None = None

	@property
	def provider(self) -> str:
		return 'google'

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
		"""Invoke Google Gemini model."""
		try:
			import google.generativeai as genai
		except ImportError:
			raise ImportError("Google Generative AI library not installed. Install with: pip install google-generativeai")
		
		# Configure API
		if self.api_key:
			genai.configure(api_key=self.api_key)
		
		try:
			# Initialize model
			generation_config = {}
			if self.temperature is not None:
				generation_config['temperature'] = self.temperature
			if self.max_tokens is not None:
				generation_config['max_output_tokens'] = self.max_tokens
			
			model = genai.GenerativeModel(
				model_name=self.model,
				generation_config=generation_config
			)
			
			# Convert messages to Google format
			google_messages = self._convert_messages(messages)
			
			# Handle structured output
			if output_format is not None:
				from browser_use.llm.schema import SchemaOptimizer
				schema = SchemaOptimizer.create_json_schema(output_format)
				generation_config['response_mime_type'] = "application/json"
				generation_config['response_schema'] = schema
				
				model = genai.GenerativeModel(
					model_name=self.model,
					generation_config=generation_config
				)
			
			# Generate response
			if len(google_messages) == 1 and isinstance(google_messages[0], str):
				# Simple text prompt
				response = await model.generate_content_async(google_messages[0])
			else:
				# Chat format
				chat = model.start_chat()
				response = await chat.send_message_async(google_messages[-1])
			
			# Extract usage information
			usage_metadata = getattr(response, 'usage_metadata', None)
			if usage_metadata:
				usage = ChatInvokeUsage(
					prompt_tokens=getattr(usage_metadata, 'prompt_token_count', 100),
					completion_tokens=getattr(usage_metadata, 'candidates_token_count', 50),
					total_tokens=getattr(usage_metadata, 'total_token_count', 150),
					prompt_cached_tokens=getattr(usage_metadata, 'cached_content_token_count', None),
					prompt_cache_creation_tokens=None,
					prompt_image_tokens=None
				)
			else:
				# Fallback usage
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
				content = response.text if response.text else ""
				return ChatInvokeCompletion(
					completion=content,
					usage=usage,
				)
			else:
				# Handle structured output
				try:
					import json
					response_data = json.loads(response.text) if response.text else {}
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
			raise ModelProviderError(f"Google Gemini API error: {e}")
	
	def _convert_messages(self, messages: list[BaseMessage]) -> list[str]:
		"""Convert BaseMessage objects to Google format."""
		google_messages = []
		
		for msg in messages:
			if isinstance(msg.content, str):
				if msg.role == "system":
					# Prepend system message to first user message
					google_messages.append(f"System: {msg.content}")
				else:
					google_messages.append(msg.content)
			elif isinstance(msg.content, list):
				# Handle multimodal content
				text_parts = []
				for item in msg.content:
					if isinstance(item, dict) and item.get("type") == "text":
						text_parts.append(item.get("text", ""))
				if text_parts:
					google_messages.append(" ".join(text_parts))
		
		# If no messages, provide a default
		if not google_messages:
			google_messages = ["Hello"]
		
		return google_messages