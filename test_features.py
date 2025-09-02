#!/usr/bin/env python3
"""
Quick test script for nvrunx enhanced features.

This script validates that all the new implementations work correctly
without requiring external dependencies like browser automation or API keys.
"""

import asyncio
import sys
from pathlib import Path


def test_imports():
    """Test all imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Browser session management
        from browser_use.browser import BrowserSession, BrowserProfile
        print("  ✅ Browser session classes")
        
        # DOM extraction
        from browser_use.dom import DomService
        from browser_use.dom.service import DOMElement, DOMTree
        print("  ✅ DOM service and data structures")
        
        # LLM providers
        from browser_use.llm.anthropic.chat import ChatAnthropic
        from browser_use.llm.google.chat import ChatGoogle
        from browser_use.llm.groq.chat import ChatGroq
        from browser_use.llm.ollama.chat import ChatOllama
        print("  ✅ All LLM providers")
        
        # CLI enhancements
        from browser_use.cli_textual import NvrunxTUI
        print("  ✅ Enhanced CLI components")
        
        # GIF recording
        from browser_use.recorder import GifRecorder, BrowserRecorder
        print("  ✅ GIF recording capabilities")
        
        # MCP server
        from browser_use.mcp.server import NvrunxMCPServer
        print("  ✅ MCP server implementation")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False


def test_data_structures():
    """Test data structures and basic functionality."""
    print("\n🏗️ Testing data structures...")
    
    try:
        from browser_use.dom.service import DOMElement, DOMTree
        
        # Test DOM element
        element = DOMElement(
            tag_name="div",
            attributes={"class": "test", "id": "example"},
            text_content="Hello World",
            inner_html="<span>Hello World</span>",
            xpath="//div[@id='example']",
            css_selector="#example",
            bounding_box={"x": 10, "y": 20, "width": 100, "height": 50},
            is_visible=True,
            is_interactive=False
        )
        
        # Test DOM tree
        dom_tree = DOMTree(
            url="https://example.com",
            title="Test Page",
            elements=[element],
            metadata={"element_count": 1, "interactive_elements": 0}
        )
        
        assert element.tag_name == "div"
        assert dom_tree.url == "https://example.com"
        assert len(dom_tree.elements) == 1
        
        print("  ✅ DOM data structures working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data structure error: {e}")
        return False


async def test_llm_providers():
    """Test LLM provider initialization."""
    print("\n🧠 Testing LLM providers...")
    
    try:
        from browser_use.llm.anthropic.chat import ChatAnthropic
        from browser_use.llm.google.chat import ChatGoogle
        from browser_use.llm.groq.chat import ChatGroq
        from browser_use.llm.ollama.chat import ChatOllama
        
        # Test provider initialization
        providers = [
            ("Anthropic", ChatAnthropic(model="claude-3-sonnet", api_key="test")),
            ("Google", ChatGoogle(model="gemini-pro", api_key="test")),
            ("Groq", ChatGroq(model="llama3-70b-8192", api_key="test")),
            ("Ollama", ChatOllama(model="llama2"))
        ]
        
        for name, provider in providers:
            assert provider.provider.lower() in name.lower()
            assert provider.name == provider.model
            print(f"  ✅ {name} provider ({provider.model})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ LLM provider error: {e}")
        return False


def test_browser_profile():
    """Test browser profile functionality."""
    print("\n🌐 Testing browser profiles...")
    
    try:
        from browser_use.browser import BrowserProfile
        
        # Create browser profile
        profile = BrowserProfile(
            name="test_profile",
            browser_type="chromium",
            headless=True,
            viewport={"width": 1280, "height": 720},
            user_agent="test-agent"
        )
        
        # Create session from profile
        session = profile.create_session()
        
        assert profile.name == "test_profile"
        assert session.browser_type == "chromium"
        assert session.headless is True
        
        print("  ✅ Browser profile creation")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Browser profile error: {e}")
        return False


def test_recording_settings():
    """Test recording configuration."""
    print("\n🎬 Testing recording settings...")
    
    try:
        from browser_use.recorder.gif import RecordingSettings
        
        settings = RecordingSettings(
            fps=3,
            max_duration=30.0,
            max_frames=90,
            optimize=True,
            scale_factor=0.7,
            quality=85
        )
        
        assert settings.fps == 3
        assert settings.max_duration == 30.0
        assert settings.optimize is True
        
        print("  ✅ Recording settings configuration")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Recording settings error: {e}")
        return False


def test_mcp_server():
    """Test MCP server initialization."""
    print("\n🔌 Testing MCP server...")
    
    try:
        from browser_use.mcp.server import NvrunxMCPServer
        
        server = NvrunxMCPServer()
        
        assert server.server.name == "nvrunx"
        assert server.browser_session is None  # Not started yet
        
        print("  ✅ MCP server initialization")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP server error: {e}")
        return False


def test_cli_help():
    """Test CLI help functionality."""
    print("\n🖥️ Testing CLI...")
    
    try:
        # Test CLI can be imported
        import browser_use.cli
        print("  ✅ Basic CLI components")
        
        # Test textual UI can be imported (may not be available)
        try:
            from browser_use.cli_textual import NvrunxTUI
            
            # Only create TUI instance if textual is available
            app = NvrunxTUI()
            assert app.current_model == "gpt-4o-mini"
            print("  ✅ Textual UI components")
        except ImportError:
            print("  ⚠️ Textual UI not available (optional dependency)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ CLI error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 nvrunx Enhanced Features Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Data Structures", test_data_structures),
        ("LLM Providers", test_llm_providers),
        ("Browser Profiles", test_browser_profile),
        ("Recording Settings", test_recording_settings),
        ("MCP Server", test_mcp_server),
        ("CLI Components", test_cli_help)
    ]
    
    results = []
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n📊 Test Results")
    print("-" * 20)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! nvrunx enhanced features are working correctly.")
        return 0
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        sys.exit(1)