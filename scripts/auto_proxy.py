#!/usr/bin/env python3
"""
Auto-Proxy Router - Automatically routes prompts to optimal Ollama models
Integrates with Clawdbot via tool calls

Usage:
    python3 auto_proxy.py --prompt "Your question here"
    python3 auto_proxy.py --prompt "Your question" --coding  # Force coding upgrade
    
Returns: JSON with {model, response, metadata}
"""

import json
import sys
import argparse
from pathlib import Path

# Add scripts dir
sys.path.insert(0, str(Path(__file__).parent))
from local_router import LocalRouter

def route_and_generate(prompt: str, coding: bool = False, raw: bool = False):
    """
    Route prompt to best model and generate response.
    
    Args:
        prompt: User prompt
        coding: Force coding model for coding tasks
        raw: Return just the text, no JSON wrapper
    
    Returns:
        JSON string or raw text
    """
    router = LocalRouter()
    
    # Get routing decision
    info = router.route_info(prompt, prefer_coding=coding)
    model = info['model']
    
    # Build the full model name for Ollama
    model_name = f"ollama/{model}"
    
    if raw:
        print(model)
        return
    
    result = {
        "prompt": prompt,
        "model_used": model,
        "model_full": model_name,
        "tier": info.get('tier', 'UNKNOWN'),
        "routing_reason": info.get('reason', ''),
        "upgraded": 'upgraded_from' in info,
        "upgrade_reason": info.get('upgrade_reason', '')
    }
    
    print(json.dumps(result, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Auto-Proxy Router")
    parser.add_argument("--prompt", "-p", required=True, help="The prompt to route")
    parser.add_argument("--coding", "-c", action="store_true", help="Prefer coding model")
    parser.add_argument("--raw", "-r", action="store_true", help="Output just model name")
    parser.add_argument("--info", "-i", action="store_true", help="Show routing info only")
    
    args = parser.parse_args()
    
    if args.info and not args.raw:
        # Just show routing info
        router = LocalRouter()
        info = router.route_info(args.prompt, prefer_coding=args.coding)
        print(json.dumps(info, indent=2))
    elif args.raw:
        # Output just model name
        router = LocalRouter()
        model = router.get_model_for_prompt(args.prompt, prefer_coding=args.coding)
        print(model)
    else:
        # Full routing + generation metadata
        route_and_generate(args.prompt, coding=args.coding)

if __name__ == "__main__":
    main()
