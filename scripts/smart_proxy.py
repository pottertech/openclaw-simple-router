#!/usr/bin/env python3
"""
Smart OpenClaw Proxy - Dynamic routing with local/regex classification
Replaces direct Ollama calls with intelligent model selection
"""

import json
import sys
import subprocess
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from local_router import LocalRouter

def get_routed_model(prompt: str, force_coding: bool = False) -> str:
    """Get the appropriate model for a prompt."""
    router = LocalRouter()
    return router.get_model_for_prompt(prompt, prefer_coding=force_coding)

def chat_with_routing(messages: list, force_coding: bool = False) -> str:
    """
    Chat with automatic model routing based on prompt content.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        force_coding: Force coder model for coding tasks
    
    Returns:
        Generated response
    """
    # Get the last user message for routing
    last_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_message = msg.get("content", "")
            break
    
    if not last_message:
        # Fallback to default
        model = "kimi-k2.5:cloud"
    else:
        model = get_routed_model(last_message, force_coding)
    
    # Use clawdbot to generate
    full_prompt = "\n\n".join([
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in messages
    ])
    
    try:
        result = subprocess.run(
            ["clawdbot", "generate", "--model", f"ollama/{model}", full_prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"[Error: Request timed out using {model}]"
    except Exception as e:
        return f"[Error: {str(e)}]"

def main():
    """Process input from stdin (for integration)."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", "-p", help="Single prompt mode")
    parser.add_argument("--coding", "-c", action="store_true", help="Prefer coder model")
    parser.add_argument("--show-model", "-s", action="store_true", help="Only show selected model")
    parser.add_argument("--test", "-t", action="store_true", help="Test mode with example prompts")
    
    args = parser.parse_args()
    
    router = LocalRouter()
    
    if args.test:
        test_prompts = [
            "Hi there!",
            "What's the weather today?",
            "Summarize this article: [short text]",
            "Fix the indentation in this code",
            "Write a Python function to calculate fibonacci numbers",
            "Debug this error: IndexError in my list",
            "Design a microservices architecture for an e-commerce app",
            "Refactor this code to use async/await",
            "How do I optimize a database query?",
            "Explain quantum computing",
        ]
        
        for prompt in test_prompts:
            info = router.route_info(prompt, prefer_coding=args.coding)
            print(f"\n📝 Prompt: {prompt[:50]}...")
            print(f"   Model: {info['model']}")
            print(f"   Tier: {info['tier']}")
            if 'upgraded_from' in info:
                print(f"   ↗️  Upgraded from {info['upgraded_from']}")
        return
    
    if args.show_model:
        if not args.prompt:
            print("Error: --prompt required with --show-model")
            sys.exit(1)
        model = router.get_model_for_prompt(args.prompt, prefer_coding=args.coding)
        print(model)
        return
    
    if args.prompt:
        # Single prompt mode
        msg = [{"role": "user", "content": args.prompt}]
        response = chat_with_routing(msg, force_coding=args.coding)
        print(response)
    else:
        # Read from stdin (JSON format)
        try:
            data = json.load(sys.stdin)
            messages = data.get("messages", [])
            force_coding = data.get("coding", False)
            response = chat_with_routing(messages, force_coding=force_coding)
            print(response)
        except json.JSONDecodeError:
            print("Error: Invalid JSON input", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
