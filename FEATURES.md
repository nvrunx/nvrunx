# nvrunx Enhanced Features

This document describes the comprehensive enhancements implemented in nvrunx for browser automation, AI integration, and developer tooling.

## 🌐 Browser Session Management

Advanced browser automation with Playwright integration:

```python
from browser_use.browser import BrowserSession, BrowserProfile

# Create and start browser session
session = BrowserSession(
    browser_type="chromium",  # chromium, firefox, webkit
    headless=False,
    cdp_enabled=True,  # Enable Chrome DevTools Protocol
    viewport={"width": 1280, "height": 720}
)

await session.start()
await session.navigate("https://example.com")
await session.click("button#submit")
await session.type_text("input[name='search']", "nvrunx")
screenshot = await session.screenshot(full_page=True)
await session.close()
```

### Browser Profiles

Create reusable browser configurations:

```python
profile = BrowserProfile(
    name="mobile_chrome",
    browser_type="chromium",
    viewport={"width": 375, "height": 667},
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
)

session = profile.create_session()
```

## 🔍 DOM Extraction and Manipulation

Advanced DOM tools for web scraping and automation:

```python
from browser_use.dom import DomService

# Initialize DOM service with browser session
dom_service = DomService(page=session.page)

# Extract complete DOM tree
dom_tree = await dom_service.extract_dom_tree()
print(f"Found {len(dom_tree.elements)} elements")

# Find elements by text content
search_results = await dom_service.find_elements_by_text("Search", exact_match=False)

# Find interactive elements
buttons = await dom_service.find_interactive_elements(['button', 'a'])

# Extract forms and their fields
forms = await dom_service.extract_forms()

# Extract all links
links = await dom_service.extract_links(filter_domain="example.com")

# Interact with elements
await dom_service.click_element("button#submit")
await dom_service.fill_input("input[name='email']", "user@example.com")
await dom_service.scroll_to_element("#bottom")
```

### DOM Data Structures

Rich metadata for every DOM element:

```python
@dataclass
class DOMElement:
    tag_name: str
    attributes: Dict[str, Any]
    text_content: str
    inner_html: str
    xpath: str
    css_selector: str
    bounding_box: Optional[Dict[str, float]]
    is_visible: bool
    is_interactive: bool
```

## 🧠 LLM Provider Implementations

Complete implementations for multiple AI providers:

### OpenAI (Fully Featured)
```python
from browser_use.llm.openai.chat import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    max_completion_tokens=2000
)
```

### Anthropic Claude
```python
from browser_use.llm.anthropic.chat import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-sonnet",
    api_key="your-api-key",
    max_tokens=4000,
    temperature=0.7
)
```

### Google Gemini
```python
from browser_use.llm.google.chat import ChatGoogle

llm = ChatGoogle(
    model="gemini-pro",
    api_key="your-api-key",
    temperature=0.5
)
```

### Groq (High-Speed Inference)
```python
from browser_use.llm.groq.chat import ChatGroq

llm = ChatGroq(
    model="llama3-70b-8192",
    api_key="your-api-key",
    temperature=0.3
)
```

### Ollama (Local Models)
```python
from browser_use.llm.ollama.chat import ChatOllama

llm = ChatOllama(
    model="llama2",
    base_url="http://localhost:11434",
    temperature=0.7
)
```

### Structured Output Support

All providers support structured output using Pydantic models:

```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    description: str

# Get structured response
response = await llm.ainvoke(messages, output_format=SearchResult)
result = response.completion  # SearchResult instance
```

## 🖥️ Enhanced CLI Interface

### Basic CLI with Advanced Features

```bash
# Interactive mode with browser automation
nvrunx --ui basic --browser --gif

# Single task with specific model
nvrunx --prompt "Search for Python tutorials" --model gpt-4o

# Rich textual UI
nvrunx --ui textual
```

### Commands in Interactive Mode

- `switch <model>` - Change AI model
- `browser on/off` - Toggle browser automation
- `gif on/off` - Toggle GIF recording
- `models` - List available models
- `help` - Show help

### Textual UI Features

Rich terminal interface with:
- Real-time model switching
- Session management
- Progress indicators  
- Settings panel
- Keybindings (Ctrl+C, Ctrl+L, Ctrl+S)

## 🎬 GIF Recording

Record browser automation as annotated GIFs:

```python
from browser_use.recorder import BrowserRecorder, RecordingSettings

# Create recorder
recorder = BrowserRecorder(
    browser_session=session,
    output_dir="recordings"
)

# Configure recording
settings = RecordingSettings(
    fps=2,
    max_duration=60.0,
    scale_factor=0.5,  # Reduce file size
    optimize=True
)

# Start recording
await recorder.start_recording("my_session")

# Perform actions (automatically recorded)
await session.navigate("https://example.com")
await recorder.record_action("Navigated to homepage")

await session.click("button#search")
await recorder.record_action("Clicked search button")

# Stop and save GIF
gif_path = await recorder.stop_recording()
print(f"Saved: {gif_path}")
```

### Recording Features

- **Frame annotation** - Add action descriptions to frames
- **Configurable quality** - Adjust FPS, duration, scaling
- **Automatic optimization** - Reduce file sizes
- **Action tracking** - Visual indicators for user actions

## 🔌 MCP Server Implementation

Complete Model Context Protocol server for AI integration:

### Start MCP Server
```bash
python -m browser_use.mcp.server
```

### Available Tools

1. **Browser Management**
   - `browser_start` - Start browser session
   - `browser_close` - Close browser
   - `browser_navigate` - Navigate to URL
   - `browser_screenshot` - Take screenshot

2. **DOM Manipulation**
   - `dom_extract` - Extract DOM tree
   - `dom_find_elements` - Find elements by text
   - `dom_click` - Click elements
   - `dom_fill_input` - Fill form inputs

3. **Recording**
   - `recording_start` - Start GIF recording
   - `recording_stop` - Stop recording

4. **AI Integration**
   - `ai_agent_run` - Execute AI automation task

### MCP Resources

- `nvrunx://session/info` - Browser session information
- `nvrunx://dom/current` - Current page DOM
- `nvrunx://recording/info` - Recording status

### Example MCP Client Usage

```python
# Using with Claude Desktop, VS Code, or other MCP clients
{
  "mcpServers": {
    "nvrunx": {
      "command": "python",
      "args": ["-m", "browser_use.mcp.server"],
      "cwd": "/path/to/nvrunx"
    }
  }
}
```

## 📦 Installation

### Base Installation
```bash
pip install nvrunx
```

### With Browser Automation
```bash
pip install "nvrunx[browser]"
playwright install  # Install browser binaries
```

### With GIF Recording
```bash
pip install "nvrunx[gif]"
```

### With Rich CLI
```bash
pip install "nvrunx[cli]"
```

### Complete Installation
```bash
pip install "nvrunx[all]"
playwright install
```

## 🔧 Configuration

### Environment Variables

```bash
# LLM API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
export GROQ_API_KEY="your-groq-key"

# Browser Configuration
export BROWSER_TYPE="chromium"  # chromium, firefox, webkit
export BROWSER_HEADLESS="true"

# Recording Settings
export RECORDING_FPS="2"
export RECORDING_QUALITY="80"
```

### Configuration File

Create `.env` file in your project:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
BROWSER_TYPE=chromium
BROWSER_HEADLESS=false
RECORDING_OUTPUT_DIR=./recordings
```

## 🚀 Examples

### Complete Browser Automation

```python
import asyncio
from browser_use import Agent, ChatOpenAI
from browser_use.browser import BrowserSession
from browser_use.recorder import BrowserRecorder

async def automate_search():
    # Create browser session
    session = BrowserSession(headless=False)
    recorder = BrowserRecorder(session)
    
    try:
        await session.start()
        await recorder.start_recording("search_demo")
        
        # Use AI agent for automation
        agent = Agent(
            task="Go to Google, search for 'nvrunx github', and click the first result",
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser_session=session
        )
        
        result = await agent.run()
        gif_path = await recorder.stop_recording()
        
        print(f"Task completed: {result}")
        print(f"Recording saved: {gif_path}")
        
    finally:
        await session.close()

asyncio.run(automate_search())
```

### Multi-Provider AI Comparison

```python
from browser_use.llm import ChatOpenAI, ChatAnthropic, ChatGoogle
from browser_use.llm.messages import UserMessage

async def compare_providers():
    providers = [
        ("OpenAI", ChatOpenAI(model="gpt-4o-mini")),
        ("Anthropic", ChatAnthropic(model="claude-3-sonnet")),
        ("Google", ChatGoogle(model="gemini-pro"))
    ]
    
    question = [UserMessage(content="Explain quantum computing in simple terms")]
    
    for name, provider in providers:
        response = await provider.ainvoke(question)
        print(f"\n{name}: {response.completion[:200]}...")
```

## 📊 Performance & Limitations

### Browser Session
- **Startup time**: ~2-3 seconds for Chromium
- **Memory usage**: ~100-200MB per session
- **Concurrent sessions**: Limited by system resources

### DOM Extraction
- **Large pages**: Can handle 10k+ elements
- **Processing time**: ~100-500ms for typical pages
- **Memory efficient**: Streaming extraction available

### GIF Recording
- **File sizes**: 1-10MB for 30-second recordings
- **Frame rates**: 1-10 FPS recommended
- **Duration limits**: Configurable, 60s default

### LLM Providers
- **Rate limits**: Varies by provider
- **Response times**: 1-10 seconds typical
- **Token limits**: Respects model limits
- **Error handling**: Comprehensive retry logic

## 🛠️ Troubleshooting

### Common Issues

1. **Browser won't start**
   ```bash
   playwright install  # Install browser binaries
   ```

2. **PIL/imageio not found** (for GIF recording)
   ```bash
   pip install "nvrunx[gif]"
   ```

3. **MCP server connection failed**
   - Check Python path in MCP client config
   - Verify nvrunx installation
   - Check for port conflicts

4. **LLM API errors**
   - Verify API keys are set
   - Check rate limits
   - Ensure model names are correct

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in CLI
nvrunx --debug --prompt "your task"
```

## 🤝 Contributing

The enhanced nvrunx framework provides a solid foundation for browser automation and AI integration. Key areas for contribution:

1. **Additional LLM providers** - Add more AI services
2. **Browser extensions** - Enhanced automation capabilities  
3. **Recording formats** - Support for MP4, WebM
4. **Testing frameworks** - Automated testing tools
5. **Documentation** - More examples and tutorials

## 📄 License

MIT License - see LICENSE file for details.