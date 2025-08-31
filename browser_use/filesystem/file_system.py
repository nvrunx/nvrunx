"""File system integration."""

from pydantic import BaseModel


class FileSystemState(BaseModel):
	"""File system state information."""
	
	current_directory: str = "/"
	files_accessed: list[str] = []