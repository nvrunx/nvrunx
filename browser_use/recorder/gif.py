"""GIF recording capabilities for browser automation."""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

try:
	from PIL import Image
except ImportError:
	Image = None

try:
	import imageio
except ImportError:
	imageio = None

try:
	from playwright.async_api import Page
except ImportError:
	Page = None


@dataclass
class RecordingFrame:
	"""Represents a frame in the recording."""
	image_path: str
	timestamp: float
	action_description: Optional[str] = None


@dataclass
class RecordingSettings:
	"""Settings for GIF recording."""
	fps: int = 2
	max_duration: float = 60.0  # seconds
	max_frames: int = 120
	optimize: bool = True
	loop: int = 0  # 0 = infinite loop
	scale_factor: float = 0.5  # Scale down for smaller file size
	quality: int = 80


class GifRecorder:
	"""Records browser automation actions as animated GIFs."""
	
	def __init__(
		self,
		output_dir: str = "recordings",
		settings: Optional[RecordingSettings] = None,
		page: Optional[Page] = None
	):
		self.logger = logging.getLogger(f'{__name__}.GifRecorder')
		self.output_dir = Path(output_dir)
		self.settings = settings or RecordingSettings()
		self.page = page
		
		# Recording state
		self.is_recording = False
		self.frames: List[RecordingFrame] = []
		self.temp_dir: Optional[Path] = None
		self.start_time: Optional[float] = None
		self.recording_task: Optional[asyncio.Task] = None
		
		# Create output directory
		self.output_dir.mkdir(parents=True, exist_ok=True)
	
	async def start_recording(self, session_name: Optional[str] = None) -> bool:
		"""Start recording browser automation."""
		if Image is None or imageio is None:
			self.logger.error("PIL and imageio are required for GIF recording")
			return False
		
		if self.page is None:
			self.logger.error("No page instance provided for recording")
			return False
		
		if self.is_recording:
			self.logger.warning("Recording already in progress")
			return False
		
		self.logger.info("Starting GIF recording")
		
		# Setup
		self.is_recording = True
		self.frames.clear()
		self.start_time = time.time()
		
		# Create temporary directory for frames
		self.temp_dir = Path(tempfile.mkdtemp(prefix="nvrunx_recording_"))
		
		# Generate session name
		if not session_name:
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			session_name = f"session_{timestamp}"
		self.session_name = session_name
		
		# Start recording task
		self.recording_task = asyncio.create_task(self._recording_loop())
		
		return True
	
	async def stop_recording(self) -> Optional[str]:
		"""Stop recording and create GIF."""
		if not self.is_recording:
			self.logger.warning("No recording in progress")
			return None
		
		self.logger.info("Stopping GIF recording")
		self.is_recording = False
		
		# Cancel recording task
		if self.recording_task:
			self.recording_task.cancel()
			try:
				await self.recording_task
			except asyncio.CancelledError:
				pass
		
		# Create GIF from frames
		gif_path = await self._create_gif()
		
		# Cleanup temp directory
		if self.temp_dir:
			import shutil
			try:
				shutil.rmtree(self.temp_dir)
			except Exception as e:
				self.logger.warning(f"Failed to cleanup temp directory: {e}")
		
		return gif_path
	
	async def add_action_marker(self, description: str) -> None:
		"""Add an action marker to the current frame."""
		if not self.is_recording or not self.frames:
			return
		
		# Update the last frame with action description
		if self.frames:
			self.frames[-1].action_description = description
			self.logger.debug(f"Added action marker: {description}")
	
	async def _recording_loop(self) -> None:
		"""Main recording loop that captures frames."""
		frame_interval = 1.0 / self.settings.fps
		frame_count = 0
		
		try:
			while self.is_recording and frame_count < self.settings.max_frames:
				# Check duration limit
				if self.start_time and time.time() - self.start_time > self.settings.max_duration:
					self.logger.info("Recording duration limit reached")
					break
				
				# Capture frame
				await self._capture_frame(frame_count)
				frame_count += 1
				
				# Wait for next frame
				await asyncio.sleep(frame_interval)
				
		except asyncio.CancelledError:
			self.logger.debug("Recording loop cancelled")
		except Exception as e:
			self.logger.error(f"Error in recording loop: {e}")
	
	async def _capture_frame(self, frame_number: int) -> None:
		"""Capture a single frame."""
		if not self.page or not self.temp_dir:
			return
		
		try:
			# Take screenshot
			frame_path = self.temp_dir / f"frame_{frame_number:04d}.png"
			await self.page.screenshot(path=str(frame_path), full_page=False)
			
			# Create frame record
			frame = RecordingFrame(
				image_path=str(frame_path),
				timestamp=time.time()
			)
			
			self.frames.append(frame)
			self.logger.debug(f"Captured frame {frame_number}")
			
		except Exception as e:
			self.logger.warning(f"Failed to capture frame {frame_number}: {e}")
	
	async def _create_gif(self) -> Optional[str]:
		"""Create GIF from captured frames."""
		if not self.frames:
			self.logger.warning("No frames to create GIF from")
			return None
		
		try:
			# Output path
			gif_filename = f"{self.session_name}.gif"
			gif_path = self.output_dir / gif_filename
			
			self.logger.info(f"Creating GIF with {len(self.frames)} frames: {gif_path}")
			
			# Load and process images
			images = []
			for i, frame in enumerate(self.frames):
				try:
					# Load image
					img = Image.open(frame.image_path)
					
					# Scale down if needed
					if self.settings.scale_factor < 1.0:
						new_size = (
							int(img.width * self.settings.scale_factor),
							int(img.height * self.settings.scale_factor)
						)
						img = img.resize(new_size, Image.Resampling.LANCZOS)
					
					# Add action annotation if present
					if frame.action_description:
						img = self._add_action_annotation(img, frame.action_description)
					
					images.append(img)
					
				except Exception as e:
					self.logger.warning(f"Failed to process frame {i}: {e}")
			
			if not images:
				self.logger.error("No valid frames found")
				return None
			
			# Create GIF
			frame_duration = 1000 / self.settings.fps  # milliseconds
			
			images[0].save(
				gif_path,
				save_all=True,
				append_images=images[1:],
				duration=frame_duration,
				loop=self.settings.loop,
				optimize=self.settings.optimize
			)
			
			# Log file info
			file_size = gif_path.stat().st_size / 1024 / 1024  # MB
			self.logger.info(f"GIF created: {gif_path} ({file_size:.2f} MB)")
			
			return str(gif_path)
			
		except Exception as e:
			self.logger.error(f"Failed to create GIF: {e}")
			return None
	
	def _add_action_annotation(self, img: Image.Image, action: str) -> Image.Image:
		"""Add action annotation to image."""
		try:
			from PIL import ImageDraw, ImageFont
			
			# Create a copy
			annotated = img.copy()
			draw = ImageDraw.Draw(annotated)
			
			# Try to load a font
			font_size = max(12, int(img.height * 0.02))
			try:
				font = ImageFont.truetype("arial.ttf", font_size)
			except (OSError, ImportError):
				try:
					font = ImageFont.load_default()
				except:
					font = None
			
			# Add text with background
			if font:
				# Get text size
				bbox = draw.textbbox((0, 0), action, font=font)
				text_width = bbox[2] - bbox[0]
				text_height = bbox[3] - bbox[1]
				
				# Position at bottom of image
				x = 10
				y = img.height - text_height - 20
				
				# Draw background rectangle
				padding = 5
				draw.rectangle(
					[x - padding, y - padding, x + text_width + padding, y + text_height + padding],
					fill=(0, 0, 0, 180)
				)
				
				# Draw text
				draw.text((x, y), action, fill=(255, 255, 255), font=font)
			
			return annotated
			
		except Exception as e:
			self.logger.warning(f"Failed to add action annotation: {e}")
			return img
	
	def get_recording_stats(self) -> dict:
		"""Get recording statistics."""
		return {
			'is_recording': self.is_recording,
			'frame_count': len(self.frames),
			'duration': time.time() - self.start_time if self.start_time else 0,
			'fps': self.settings.fps,
			'output_dir': str(self.output_dir),
			'session_name': getattr(self, 'session_name', None)
		}


class BrowserRecorder:
	"""High-level browser recorder that integrates with browser sessions."""
	
	def __init__(self, browser_session, output_dir: str = "recordings"):
		self.browser_session = browser_session
		self.output_dir = output_dir
		self.gif_recorder: Optional[GifRecorder] = None
		self.logger = logging.getLogger(f'{__name__}.BrowserRecorder')
	
	async def start_recording(self, session_name: Optional[str] = None) -> bool:
		"""Start recording browser session."""
		if not hasattr(self.browser_session, 'page') or not self.browser_session.page:
			self.logger.error("Browser session has no page to record")
			return False
		
		# Create GIF recorder
		self.gif_recorder = GifRecorder(
			output_dir=self.output_dir,
			page=self.browser_session.page
		)
		
		return await self.gif_recorder.start_recording(session_name)
	
	async def stop_recording(self) -> Optional[str]:
		"""Stop recording and return GIF path."""
		if not self.gif_recorder:
			return None
		
		gif_path = await self.gif_recorder.stop_recording()
		self.gif_recorder = None
		return gif_path
	
	async def record_action(self, action_description: str) -> None:
		"""Record an action with description."""
		if self.gif_recorder:
			await self.gif_recorder.add_action_marker(action_description)
	
	def is_recording(self) -> bool:
		"""Check if currently recording."""
		return self.gif_recorder is not None and self.gif_recorder.is_recording
	
	def get_stats(self) -> dict:
		"""Get recording statistics."""
		if self.gif_recorder:
			return self.gif_recorder.get_recording_stats()
		return {'is_recording': False}