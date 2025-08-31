# nvrunx

<h1 align="center">Enable AI to control your browser 🤖</h1>

[![GitHub stars](https://img.shields.io/github/stars/nvrunx/nvrunx?style=social)](https://github.com/nvrunx/nvrunx/stargazers)

🌤️ AI-powered browser automation made simple and accessible!

# Quick start

With pip (Python>=3.11):

```bash
pip install nvrunx
```

If you don't already have Chrome or Chromium installed, you can also download the latest Chromium using playwright's install shortcut:

```bash
uvx playwright install chromium --with-deps --no-shell
```

Spin up your agent:

```python
import asyncio
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, ChatOpenAI

async def main():
    agent = Agent(
        task="Find the number of stars of the nvrunx repo",
        llm=ChatOpenAI(model="gpt-4.1-mini"),
    )
    await agent.run()

asyncio.run(main())
```

Add your API keys for the provider you want to use to your `.env` file.

```bash
OPENAI_API_KEY=
```

# Features

## 🤖 AI Browser Control
- Complete browser automation with AI agents
- Support for complex web interactions
- Smart element detection and interaction
- Screenshot and visual feedback

## 🔌 Multiple LLM Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Groq
- Ollama (Local models)
- Azure OpenAI

## 🛠️ Rich Tooling
- CLI interface with rich terminal UI
- Browser session management
- DOM extraction and manipulation
- File system integration
- Screenshot capabilities

## 🔗 Integration Features  
- Model Context Protocol (MCP) support
- Docker containerization
- Comprehensive logging and observability
- Extensible action system

# Vision

Tell your computer what to do, and it gets it done.

## Roadmap

### Agent
- [ ] Make agent 3x faster
- [ ] Reduce token consumption (system prompt, DOM state)

### DOM Extraction
- [ ] Enable interaction with all UI elements
- [ ] Improve state representation for UI elements so that any LLM can understand what's on the page

### Workflows
- [ ] Let user record a workflow - which we can rerun with browser-use as a fallback

### User Experience
- [ ] Create various templates for tutorial execution, job application, QA testing, social media, etc. which users can just copy & paste.

### Parallelization
- [ ] Human work is sequential. The real power of a browser agent comes into reality if we can parallelize similar tasks.

## Contributing

We love contributions! Feel free to open issues for bugs or feature requests.

## Local Setup

To set up for development:

```bash
git clone https://github.com/nvrunx/nvrunx.git
cd nvrunx
pip install -e ".[all]"
```

`main` is the primary development branch with frequent changes. For production use, install a stable [versioned release](https://github.com/nvrunx/nvrunx/releases) instead.

---

## Citation

If you use nvrunx in your research or project, please cite:

```bibtex
@software{nvrunx2024,
  author = {nvrunx},
  title = {nvrunx: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/nvrunx/nvrunx}
}
```

## 🔗 Connect with me

<p align="center">
  <a href="https://x.com/goluKumar613994" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/twitter.svg" alt="goluKumar613994" height="30" width="40" /></a>
  <a href="mailto:nvrunxbdueub@gmail.com" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/gmail.svg" alt="nvrunxbdueub@gmail.com" height="30" width="40" /></a>
  <a href="https://www.youtube.com/@MSP_Explained" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/youtube.svg" alt="@MSP_Explained" height="30" width="40" /></a>
</p>

<div align="center">
Made with ❤️ by nvrunx
</div>