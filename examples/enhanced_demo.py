#!/usr/bin/env python3
"""
Example script demonstrating nvrunx enhanced capabilities.

This example shows:
1. Browser session management
2. DOM extraction and manipulation
3. GIF recording
4. Multiple LLM providers
"""

import asyncio
import os
from browser_use.browser import BrowserSession
from browser_use.dom import DomService
from browser_use.recorder import BrowserRecorder
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use import Agent


async def browser_automation_example():
    """Demonstrate browser automation with recording."""
    print("🌐 Starting browser automation example...")
    
    # Create browser session
    session = BrowserSession(
        browser_type="chromium",
        headless=False,  # Show browser for demo
        viewport={"width": 1280, "height": 720}
    )
    
    try:
        # Start browser
        await session.start()
        print("✅ Browser started")
        
        # Initialize DOM service
        dom_service = DomService(page=session.page)
        print("✅ DOM service initialized")
        
        # Initialize recorder (if PIL/imageio available)
        recorder = BrowserRecorder(session, output_dir="./examples/recordings")
        
        # Start recording
        recording_started = await recorder.start_recording("demo_session")
        if recording_started:
            print("🎬 Recording started")
        
        # Navigate to a page
        await session.navigate("https://example.com")
        print(f"✅ Navigated to: {await session.get_page_title()}")
        
        # Record action
        if recording_started:
            await recorder.record_action("Navigated to example.com")
        
        # Extract DOM
        dom_tree = await dom_service.extract_dom_tree()
        print(f"✅ DOM extracted: {len(dom_tree.elements)} elements, {dom_tree.metadata['interactive_elements']} interactive")
        
        # Find elements
        links = await dom_service.find_interactive_elements(['a'])
        print(f"✅ Found {len(links)} links")
        
        # Take screenshot
        screenshot = await session.screenshot()
        print(f"✅ Screenshot taken: {len(screenshot)} bytes")
        
        # Stop recording
        if recording_started:
            gif_path = await recorder.stop_recording()
            if gif_path:
                print(f"🎬 Recording saved: {gif_path}")
        
    finally:
        await session.close()
        print("✅ Browser closed")


async def llm_providers_example():
    """Demonstrate multiple LLM providers."""
    print("\n🧠 Testing LLM providers...")
    
    # Test message
    from browser_use.llm.messages import UserMessage
    messages = [UserMessage(content="Hello, how are you?")]
    
    # Test available providers
    providers = []
    
    # OpenAI (if API key available)
    if os.getenv('OPENAI_API_KEY'):
        from browser_use.llm.openai.chat import ChatOpenAI
        providers.append(("OpenAI", ChatOpenAI(model="gpt-4o-mini")))
    
    # Test each provider
    for name, provider in providers:
        try:
            result = await provider.ainvoke(messages)
            print(f"✅ {name}: {result.completion[:50]}...")
        except Exception as e:
            print(f"⚠️ {name}: {e}")


async def ai_agent_example():
    """Demonstrate AI agent with browser automation."""
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OpenAI API key required for AI agent example")
        return
    
    print("\n🤖 Testing AI Agent with browser automation...")
    
    try:
        # Create agent
        agent = Agent(
            task="Go to example.com and tell me what you see",
            llm=ChatOpenAI(model="gpt-4o-mini")
        )
        
        # Run agent
        result = await agent.run()
        print(f"✅ Agent completed: {result}")
        
    except Exception as e:
        print(f"⚠️ Agent error: {e}")


async def main():
    """Run all examples."""
    print("🚀 nvrunx Enhanced Capabilities Demo")
    print("=" * 50)
    
    try:
        # Browser automation example
        await browser_automation_example()
        
        # LLM providers example
        await llm_providers_example()
        
        # AI agent example
        await ai_agent_example()
        
        print("\n✅ All examples completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")


if __name__ == "__main__":
    # Create examples directory
    os.makedirs("examples/recordings", exist_ok=True)
    
    # Run examples
    asyncio.run(main())