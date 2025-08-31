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
		"""Placeholder Ollama implementation."""
		usage = ChatInvokeUsage(
			prompt_tokens=100,
			completion_tokens=50, 
			total_tokens=150,
			prompt_cached_tokens=None,
			prompt_cache_creation_tokens=None,
			prompt_image_tokens=None
		)
		
		if output_format is None:
			return ChatInvokeCompletion(
				completion="This is a placeholder response from Ollama",
				usage=usage,
			)
		else:
			return ChatInvokeCompletion(
				completion=output_format(),
				usage=usage,
			)