---
name: openclaw-simple-router
description: Lightweight rule-based LLM router for dynamic model selection. Automatically routes prompts to optimal Ollama models (qwen2.5:7b, kimi-k2.5, deepseek-v3.2) based on content analysis using regex patterns. Use when needing cost-effective model selection, automatic tier classification, or coding task detection for local LLM inference.
---

# OpenClaw Simple Router

Lightweight rule-based router for Ollama models. Replaces expensive cloud routing with fast local regex classification.

## Architecture

4-tier model selection based on prompt analysis:

| Tier | Model | Cost | Use For | Speed |
|------|-------|------|---------|-------|
| **SIMPLE** | `qwen2.5:7b-instruct` | Cheapest | Greetings, summaries, simple Q&A, formatting | ⚡ Fast |
| **MEDIUM** | `kimi-k2.5:cloud` | Medium | General chat, explanations, analysis | 🔄 Medium |
| **CODING** | `deepseek-v3.2:cloud` | Higher | Code generation, debugging, architecture | 🔄 Medium |
| **COMPLEX** | `deepseek-v3.2:cloud` | Highest | Reasoning, math, complex analysis | 🐌 Slower |

## Pattern Detection

### Auto-routing triggers

**SIMPLE tier:**
- Simple greetings ("Hi", "Hello")
- Short questions (<100 chars)
- Summary requests
- Formatting-only tasks

**MEDIUM tier:**
- General explanations
- Analysis requests
- Planning questions

**CODING tier (with `--coding` flag):**
- "refactor", "optimize"
- "implement API/class"
- "debug error"
- Code blocks with keywords
- Design patterns

**COMPLEX tier:**
- Math problems
- Research requests
- Long prompts (>2000 chars)

## Usage

### CLI

```bash
# Get best model for prompt
python3 scripts/local_router.py --prompt "Hi there!"
# Output: qwen2.5:7b-instruct

# Show routing info
python3 scripts/local_router.py --prompt "Debug this" --coding --info
# Output: {"model": "deepseek-v3.2:cloud", "tier": "CODING", ...}

# Force coding detection
python3 scripts/auto_proxy.py --prompt "Write a function" --coding

# Test all patterns
python3 scripts/smart_proxy.py --test --coding
```

### Python API

```python
from scripts.local_router import LocalRouter

router = LocalRouter()

# Get model
model = router.get_model_for_prompt("How do I bake bread?")
# Returns: "qwen2.5:7b-instruct"

# With coding upgrade
model = router.get_model_for_prompt("Refactor this code", prefer_coding=True)
# Returns: "deepseek-v3.2:cloud"

# Full info
info = router.route_info("Debug error", prefer_coding=True)
# Returns: {"model": "...", "tier": "...", "reason": "..."}
```

### Integration with OpenClaw

```python
import subprocess

# Route and generate
model = subprocess.check_output([
    "python3", "scripts/auto_proxy.py",
    "--raw", "--prompt", user_prompt
]).decode().strip()

# Use with OpenClaw
response = clawdbot.generate(f"ollama/{model}", prompt)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/local_router.py` | Core router with regex patterns |
| `scripts/auto_proxy.py` | CLI for routing decisions |
| `scripts/smart_proxy.py` | Full routing with test mode |

## Files

- `SKILL.md` - This file
- `scripts/local_router.py` - Core classifier
- `scripts/auto_proxy.py` - CLI wrapper
- `scripts/smart_proxy.py` - Testing and integration
