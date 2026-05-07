#!/usr/bin/env python3
"""
Neshama CLI

Command-line interface for Neshama personality operating system.
"""

import argparse
import sys
import os
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_banner():
    """Print the Neshama banner."""
    print("=" * 60)
    print("  🔮 Neshama - AI Agent Personality Operating System")
    print("=" * 60)
    print()


def get_version():
    """Get the current version of Neshama."""
    from neshama import __version__
    return __version__


def version(args):
    """Show version information."""
    print_banner()
    print(f"  Version: {get_version()}")
    print()
    print("  Neshama is an AI Agent personality operating system")
    print("  that gives agents a soul through the OCEAN model,")
    print("  emotion engine, and layered memory architecture.")
    print()
    print("  Repository: https://github.com/neshama/neshama")
    print("  Documentation: https://neshama.github.io/neshama/")
    print()


def get_config_dir():
    """Get the Neshama configuration directory."""
    home = Path.home()
    config_dir = home / ".neshama"
    return config_dir


def get_providers():
    """Get list of available LLM providers."""
    try:
        from model_adapter.providers import list_providers
        return list_providers()
    except ImportError:
        # Fallback provider list if model_adapter not available
        return [
            "openai", "anthropic", "gemini",
            "dashscope", "zhipu", "minimax",
            "volcengine", "qianfan", "xinghuo",
            "hunyuan", "moonshot", "deepseek",
            "xai", "groq", "mistral",
            "cohere", "huggingface", "nvidia",
            "openrouter", "siliconflow", "cloudflare"
        ]


def get_provider_display_name(provider_id):
    """Get display name for a provider."""
    provider_names = {
        "openai": "OpenAI (GPT-4, GPT-3.5)",
        "anthropic": "Anthropic (Claude)",
        "gemini": "Google Gemini",
        "dashscope": "Alibaba DashScope (Qwen)",
        "zhipu": "Zhipu AI (GLM)",
        "minimax": "MiniMax",
        "volcengine": "VolcEngine (Doubao)",
        "qianfan": "Baidu Qianfan (ERNIE)",
        "xinghuo": "iFlytek Spark",
        "hunyuan": "Tencent Hunyuan",
        "moonshot": "Moonshot (Kimi)",
        "deepseek": "DeepSeek",
        "xai": "xAI (Grok)",
        "groq": "Groq",
        "mistral": "Mistral AI",
        "cohere": "Cohere",
        "huggingface": "HuggingFace",
        "nvidia": "NVIDIA NIM",
        "openrouter": "OpenRouter",
        "siliconflow": "SiliconFlow",
        "cloudflare": "Cloudflare Workers AI"
    }
    return provider_names.get(provider_id, provider_id)


def get_themes():
    """Get list of available themes."""
    return [
        ("ocean", "🌊 Ocean Blue", "Classic blue theme with ocean vibes"),
        ("spring", "🌸 Spring Blossom", "Fresh pink and green spring theme"),
        ("midnight", "🌙 Midnight", "Dark theme with midnight blue"),
        ("cyberpunk", "🤖 Cyberpunk", "Neon cyberpunk aesthetic"),
        ("sunset", "🌅 Sunset", "Warm orange sunset colors"),
        ("forest", "🌲 Forest", "Natural green forest theme"),
        ("slate", "🗿 Slate", "Minimalist slate gray"),
        ("purple", "💜 Purple Haze", "Elegant purple theme")
    ]


def init_config(args):
    """Interactive configuration wizard for neshama init."""
    print_banner()
    print("  Welcome to Neshama! Let's set up your configuration.")
    print()
    print("  This wizard will help you configure:")
    print("    • Default LLM Provider")
    print("    • API Key")
    print("    • Default Theme")
    print()
    print("  Press Ctrl+C at any time to cancel.")
    print()

    config = {}
    providers = get_providers()
    themes = get_themes()

    # Step 1: Select LLM Provider
    print("-" * 60)
    print("  Step 1/3: Select your default LLM Provider")
    print("-" * 60)
    print()
    print("  Available providers:")
    print()
    
    # Display providers in columns
    for i, provider in enumerate(providers):
        display_name = get_provider_display_name(provider)
        print(f"    {i+1:2d}. {display_name}")
    print()
    
    while True:
        try:
            choice = input(f"  Enter provider number (1-{len(providers)}) [1]: ").strip()
            if not choice:
                choice = "1"
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                config['provider'] = providers[idx]
                break
            print(f"  Please enter a number between 1 and {len(providers)}")
        except ValueError:
            print("  Please enter a valid number")

    print(f"  ✓ Selected: {get_provider_display_name(config['provider'])}")
    print()

    # Step 2: Enter API Key
    print("-" * 60)
    print("  Step 2/3: Enter your API Key")
    print("-" * 60)
    print()
    
    while True:
        api_key = input("  Enter API Key (will be stored securely): ").strip()
        if api_key:
            # Mask for display
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print(f"  ✓ API Key set: {masked}")
            config['api_key'] = api_key
            break
        print("  API Key cannot be empty")
    print()

    # Step 3: Select Theme
    print("-" * 60)
    print("  Step 3/3: Select your default theme")
    print("-" * 60)
    print()
    
    for i, (theme_id, theme_name, theme_desc) in enumerate(themes):
        print(f"    {i+1}. {theme_name}")
        print(f"       {theme_desc}")
    print()
    
    while True:
        try:
            choice = input(f"  Enter theme number (1-{len(themes)}) [1]: ").strip()
            if not choice:
                choice = "1"
            idx = int(choice) - 1
            if 0 <= idx < len(themes):
                config['theme'] = themes[idx][0]
                break
            print(f"  Please enter a number between 1 and {len(themes)}")
        except ValueError:
            print("  Please enter a valid number")

    print(f"  ✓ Selected theme: {themes[idx][1]}")
    print()

    # Generate config file
    print("-" * 60)
    print("  Generating configuration...")
    print("-" * 60)
    
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"
    
    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate YAML config
    import yaml
    config_data = {
        'version': get_version(),
        'model': {
            'provider': config['provider'],
            'api_key': config['api_key'],
            'model': '',  # Will be set based on provider
            'temperature': 0.7,
            'max_tokens': 4096
        },
        'theme': config['theme'],
        'language': 'en'
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    print()
    print(f"  ✓ Configuration saved to: {config_file}")
    print()
    
    # Ask to launch dashboard
    print("-" * 60)
    print("  Setup Complete!")
    print("-" * 60)
    print()
    print("  What would you like to do next?")
    print()
    print("    1. Launch Soul Panel (neshama dashboard)")
    print("    2. Start chat session (neshama run)")
    print("    3. Just exit (configuration is saved)")
    print()
    
    while True:
        try:
            choice = input("  Enter choice [1]: ").strip() or "1"
            if choice == "1":
                print()
                print("  Launching Soul Panel...")
                print()
                # Launch dashboard
                from neshama.web.launcher import launch_with_server
                launch_with_server(
                    host="127.0.0.1",
                    port=8420,
                    title="Neshama Soul Panel",
                    width=1280,
                    height=800,
                    debug=False
                )
                break
            elif choice == "2":
                print()
                print("  Starting chat session...")
                print()
                # Run chat
                run_args = argparse.Namespace(
                    config=None,
                    no_memory=False,
                    no_soul=False,
                    debug=False
                )
                run(run_args)
                break
            elif choice == "3":
                print()
                print("  Goodbye! Your configuration is saved.")
                print("  Run 'neshama dashboard' to start the Soul Panel anytime.")
                print()
                break
            else:
                print("  Please enter 1, 2, or 3")
        except (ValueError, KeyboardInterrupt):
            print()
            print("  Goodbye!")
            break


def init(args):
    """Initialize a new Neshama project."""
    if args.config:
        # Run configuration wizard
        init_config(args)
    else:
        # Run legacy init (create personality SKILL.md)
        from neshama.core.ocean import OceanManager
        from neshama.core.personality import Personality
        
        print("Initializing Neshama project...")
        print()
        
        # Get name
        name = args.name or input("Enter personality name: ").strip() or "MyAgent"
        
        # Get preset
        print()
        print("Available OCEAN presets:")
        presets = list(OceanManager.PRESETS.keys())
        for i, preset in enumerate(presets, 1):
            print(f"  {i}. {preset}")
        print()
        
        preset_choice = input(f"Choose preset (1-{len(presets)}) or enter custom: ").strip()
        
        try:
            preset_idx = int(preset_choice) - 1
            if 0 <= preset_idx < len(presets):
                preset = presets[preset_idx]
            else:
                preset = "neshama"
        except ValueError:
            preset = preset_choice.lower() or "neshama"
        
        # Create personality
        personality = Personality.from_preset(name, preset)
        
        # Save SKILL.md
        output_dir = args.output or "."
        skill_md_path = os.path.join(output_dir, "SKILL.md")
        personality.save_skill_md(skill_md_path)
        
        print()
        print(f"✓ Personality created: {name}")
        print(f"✓ SKILL.md saved to: {skill_md_path}")
        print()
        print("Personality summary:")
        print(personality.config.ocean.get_summary())


def run(args):
    """Run the Neshama chat loop."""
    from neshama.core.engine import NeshamaEngine, EngineConfig
    
    print_banner()
    
    # Create engine
    config = EngineConfig(
        engine_name="Neshama CLI",
        debug=args.debug,
        memory_enabled=not args.no_memory,
        soul_enabled=not args.no_soul,
    )
    
    if args.config:
        config.soul_config_path = args.config
    
    engine = NeshamaEngine(config)
    
    # Create session
    session = engine.create_session()
    print(f"Session created: {session.id}")
    print()
    
    # Welcome message
    print("Assistant: Hello! I'm Neshama, your AI companion.")
    print("           Type 'quit' or 'exit' to end the conversation.")
    print("           Type 'help' for available commands.")
    print()
    
    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Assistant: Goodbye! Take care! 👋")
                break
            
            elif user_input.lower() == 'help':
                print()
                print("Available commands:")
                print("  help   - Show this help message")
                print("  clear  - Clear conversation history")
                print("  quit   - Exit the chat")
                print("  stats  - Show memory statistics")
                print()
                continue
            
            elif user_input.lower() == 'clear':
                session.clear_history()
                print("Assistant: Conversation history cleared.")
                print()
                continue
            
            elif user_input.lower() == 'stats':
                if engine.memory:
                    stats = engine.memory.get_stats()
                    print()
                    print("Memory Statistics:")
                    print(f"  Short-term turns: {stats.short_term_count}")
                    print(f"  Long-term entries: {stats.long_term_count}")
                    print(f"  Preferences: {stats.preferences_count}")
                    print(f"  Habits: {stats.habits_count}")
                    print()
                continue
            
            # Process message
            response = engine.chat(user_input, session_id=session.id)
            
            print(f"Assistant: {response.content}")
            print()
            
            # Debug info
            if args.debug:
                print(f"[DEBUG] Response time: {response.latency_ms:.2f}ms")
                print()
        
        except KeyboardInterrupt:
            print("\n\nAssistant: Goodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()


def dashboard(args):
    """Start the Soul Panel desktop client."""
    try:
        from neshama.web.launcher import launch_with_server
    except ImportError:
        print("Error: Web dependencies not installed.")
        print("Please install with: pip install neshama[web]")
        sys.exit(1)
    
    print_banner()
    
    if args.debug:
        print("  Starting in DEBUG mode (browser)...")
        print(f"  URL: http://{args.host}:{args.port}")
        print()
    else:
        print("  Starting desktop client...")
        print()
    
    try:
        launch_with_server(
            host=args.host,
            port=args.port,
            title="Neshama Soul Panel",
            width=args.width,
            height=args.height,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\nSoul Panel stopped.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Neshama - AI Agent Personality Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  neshama init              Initialize a new personality (legacy mode)
  neshama init --config     Run interactive configuration wizard
  neshama dashboard         Start the Soul Panel desktop client
  neshama run                Start an interactive chat session
  neshama version            Show version information

For more help, see: https://neshama.github.io/neshama/
        """
    )
    
    # Add version action
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show version information"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.set_defaults(func=version)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Start chat session")
    run_parser.add_argument(
        "-c", "--config",
        help="Soul configuration file path"
    )
    run_parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable memory layer"
    )
    run_parser.add_argument(
        "--no-soul",
        action="store_true",
        help="Disable soul layer"
    )
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    run_parser.set_defaults(func=run)
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration or personality")
    init_parser.add_argument(
        "name", 
        nargs="?", 
        help="Personality name (legacy mode only)"
    )
    init_parser.add_argument(
        "-c", "--config",
        action="store_true",
        help="Run interactive configuration wizard"
    )
    init_parser.add_argument(
        "-o", "--output",
        help="Output directory (legacy mode only)"
    )
    init_parser.set_defaults(func=init)
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start Soul Panel desktop client")
    dashboard_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    dashboard_parser.add_argument(
        "-p", "--port",
        default=8420,
        type=int,
        help="Server port (default: 8420)"
    )
    dashboard_parser.add_argument(
        "--width",
        default=1280,
        type=int,
        help="Window width (default: 1280)"
    )
    dashboard_parser.add_argument(
        "--height",
        default=800,
        type=int,
        help="Window height (default: 800)"
    )
    dashboard_parser.add_argument(
        "--debug",
        action="store_true",
        help="Open in browser instead of desktop window (for development)"
    )
    dashboard_parser.set_defaults(func=dashboard)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        # No command specified, show help and version
        print_banner()
        print(f"  Version: {get_version()}")
        print()
        parser.print_help()
        print()
        print("Quick start:")
        print("  neshama init --config   Configure Neshama interactively")
        print("  neshama dashboard       Start Soul Panel desktop client")
        print("  neshama run             Start chat session")
        print()
        sys.exit(1)
    
    # Run the appropriate command
    args.func(args)


if __name__ == "__main__":
    main()
