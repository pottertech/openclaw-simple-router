#!/usr/bin/env python3
"""
Local LLM Router - Dynamic model selection based on prompt complexity
Lightweight alternative to smart-router with Ollama-only routing
"""

import re
import sys
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class RoutingDecision:
    model: str
    reason: str
    estimated_tier: str

class LocalRouter:
    """Simple rule-based router for Ollama models."""
    
    def __init__(self):
        # Model capabilities and identifiers
        self.models = {
            "simple": {
                "name": "qwen2.5:7b-instruct",
                "aliases": ["qwen2.5:7b", "fast", "cheap"],
                "strengths": ["quick_answers", "summaries", "formatting", "simple_qa"],
                "cost_factor": 0.1,
                "speed": "fast"
            },
            "medium": {
                "name": "kimi-k2.5:cloud",
                "aliases": ["kimi", "balanced"],
                "strengths": ["general_chat", "analysis", "explanations", "planning"],
                "cost_factor": 0.5,
                "speed": "medium"
            },
            "coding": {
                "name": "deepseek-v3.2:cloud",
                "aliases": ["deepseek-coder", "coder", "developer"],
                "strengths": ["coding", "debugging", "architecture", "complex_logic", "algorithms"],
                "cost_factor": 0.8,
                "speed": "medium"
            },
            "complex": {
                "name": "deepseek-v3.2:cloud",
                "aliases": ["deepseek", "strong", "reasoning"],
                "strengths": ["reasoning", "math", "complex_analysis", "research"],
                "cost_factor": 1.0,
                "speed": "slow"
            }
        }
        
        # Regex patterns for classification
        self.patterns = {
            "simple_greeting": re.compile(r'^\s*(hi|hello|hey|morning|evening)\s*$', re.I),
            "simple_qa": re.compile(r'^(what|where|when|who|how)\s+(is|are|was|were|does|do|did|can|could|would|will)\s+[^?]{1,50}\??$', re.I),
            "summary_request": re.compile(r'(summarize|summarise|tl;dr|brief|short version)', re.I),
            "formatting_only": re.compile(r'(format|reformat|fix indentation|pretty print|json format)', re.I),
            
            "coding_simple": re.compile(r'(fix syntax|missing semicolon|indent|spacing|format)', re.I),
            "coding_medium": re.compile(r'(write (a|an|the) function|create (a|an) script|implement|refactor|debug|error in)', re.I),
            "coding_complex": re.compile(r'(architecture|design pattern|algorithm|optimize|performance|complex system|microservices|distributed)', re.I),
            "coding_advanced": re.compile(r'(write (a|an) (class|module|library|api|framework)|build (a|an) (app|application|service)|full implementation)', re.I),
            
            "math": re.compile(r'(calculate|compute|solve|equation|formula|math|algebra|calculus|statistics)', re.I),
            "research": re.compile(r'(research|analyze deeply|comprehensive|detailed analysis|literature review)', re.I),
            
            "code_included": re.compile(r'```[\w]*\n', re.I),
            "multiple_files": re.compile(r'(multiple files|several files|file structure|project structure|folder)', re.I),
        }
    
    def classify(self, prompt: str) -> RoutingDecision:
        """Classify prompt and return routing decision."""
        
        prompt_lower = prompt.lower()
        prompt_len = len(prompt)
        
        # Quick regex-based classification
        scores = {
            "simple": 0,
            "medium": 0,
            "coding": 0,
            "complex": 0
        }
        
        # Check for simple patterns (route to cheap model)
        if self.patterns["simple_greeting"].match(prompt):
            return RoutingDecision(
                model=self.models["simple"]["name"],
                reason="Simple greeting - use cheapest model",
                estimated_tier="SIMPLE"
            )
        
        if self.patterns["simple_qa"].match(prompt) and prompt_len < 100:
            scores["simple"] += 3
        
        if self.patterns["summary_request"].search(prompt) and prompt_len < 500:
            scores["simple"] += 2
            
        if self.patterns["formatting_only"].search(prompt) and prompt_len < 300:
            scores["simple"] += 3
        
        # Check for coding patterns
        has_code = self.patterns["code_included"].search(prompt)
        
        if self.patterns["coding_simple"].search(prompt):
            scores["simple"] += 2  # Simple fixes can use cheap model
            
        if self.patterns["coding_medium"].search(prompt):
            if has_code:
                scores["coding"] += 3  # Debugging with code context
            else:
                scores["medium"] += 2
                
        if self.patterns["coding_complex"].search(prompt):
            scores["coding"] += 4
            scores["complex"] += 2
            
        if self.patterns["coding_advanced"].search(prompt):
            scores["coding"] += 5
            scores["complex"] += 3
        
        # Multiple code blocks or files = complex coding
        code_blocks = len(self.patterns["code_included"].findall(prompt))
        if code_blocks >= 2:
            scores["coding"] += 2
        if code_blocks >= 4:
            scores["complex"] += 2
            
        if self.patterns["multiple_files"].search(prompt):
            scores["coding"] += 3
        
        # Length heuristics
        if prompt_len > 2000:
            scores["complex"] += 2
            scores["coding"] += 1
        elif prompt_len > 1000:
            scores["medium"] += 1
            
        if prompt_len < 200:
            scores["simple"] += 1
        
        # Math and research
        if self.patterns["math"].search(prompt):
            scores["complex"] += 3
            
        if self.patterns["research"].search(prompt):
            scores["complex"] += 4
        
        # Determine winner
        max_score = max(scores.values())
        
        if max_score == 0:
            # Default to medium for unclear cases
            return RoutingDecision(
                model=self.models["medium"]["name"],
                reason="Unclear classification - default to balanced model",
                estimated_tier="MEDIUM"
            )
        
        # Find which tier has max score
        for tier in ["complex", "coding", "medium", "simple"]:
            if scores[tier] == max_score:
                return RoutingDecision(
                    model=self.models[tier]["name"],
                    reason=f"Matched patterns: {self._explain_scores(scores)}",
                    estimated_tier=tier.upper()
                )
        
        # Fallback
        return RoutingDecision(
            model=self.models["medium"]["name"],
            reason="Fallback to balanced model",
            estimated_tier="MEDIUM"
        )
    
    def _explain_scores(self, scores: Dict[str, int]) -> str:
        """Convert scores to human-readable explanation."""
        parts = []
        for tier, score in sorted(scores.items(), key=lambda x: -x[1]):
            if score > 0:
                parts.append(f"{tier}={score}")
        return ", ".join(parts)
    
    def should_upgrade_coder(self, prompt: str, current_model: str) -> (Optional[str], str):
        """
        Check if we should upgrade from kimi-k2.5 to qwen3-coder for coding tasks.
        Returns tuple of (better model name or None, reason string).
        """
        if "kimi" not in current_model.lower() and "qwen2.5" not in current_model.lower():
            return None, "Already using specialized model"
        
        prompt_lower = prompt.lower()
        
        # Strong coding indicators - always upgrade
        strong_indicators = [
            (r'\brefactor\b', "Refactoring request"),
            (r'\boptimize\b.*\b(code|function|performance|query)\b', "Optimization request"),
            (r'(implement|write|create|build).*\b(api|endpoint|class|library|framework)\b', "Implementation request"),
            (r'\balgorithm\b', "Algorithm design"),
            (r'\bdata structure\b', "Data structures"),
            (r'\bmicroservices?\b', "Microservices architecture"),
            (r'\bdesign pattern\b', "Design patterns"),
            (r'(debug|fix|solve).*\berror\b', "Error debugging"),
        ]
        
        for pattern, reason in strong_indicators:
            if re.search(pattern, prompt_lower):
                return self.models["coding"]["name"], reason
        
        # Check for code blocks with specific keywords
        code_keywords = r'\b(async|await|def|class|import|function|return|if|for|while|try|except)\b'
        if re.search(r'```[\w]*\n', prompt_lower) and re.search(code_keywords, prompt_lower):
            return self.models["coding"]["name"], "Contains code blocks"
        
        # Medium coding indicators - upgrade if combined with other signs
        medium_indicators = [
            r'\bcode\b.*\b(write|create|generate)\b',
            r'\bpython\b.*\b(write|function|script)\b',
            r'\bjavascript\b.*\b(write|function|code)\b',
            r'\bsql\b.*\b(query|optimize|write)\b',
        ]
        
        medium_matches = sum(1 for p in medium_indicators if re.search(p, prompt_lower))
        if medium_matches >= 1:
            return self.models["coding"]["name"], "Coding context detected"
        
        return None, "Not a coding task requiring specialized model"
    
    def get_model_for_prompt(self, prompt: str, prefer_coding: bool = False) -> str:
        """
        Main entry point: Get the best model for a prompt.
        
        Args:
            prompt: The user prompt
            prefer_coding: If True, upgrade to coder model for coding tasks
        
        Returns:
            Model name string ready for OpenClaw
        """
        decision = self.classify(prompt)
        
        # Check if we should upgrade to coder model
        if prefer_coding:
            upgrade, _ = self.should_upgrade_coder(prompt, decision.model)
            if upgrade:
                return upgrade
        
        return decision.model
    
    def route_info(self, prompt: str, prefer_coding: bool = False) -> Dict[str, Any]:
        """Get full routing information including reasoning."""
        decision = self.classify(prompt)
        
        result = {
            "model": decision.model,
            "tier": decision.estimated_tier,
            "reason": decision.reason,
            "prefer_coding": prefer_coding
        }
        
        if prefer_coding:
            upgrade, upgrade_reason = self.should_upgrade_coder(prompt, decision.model)
            if upgrade:
                result["model"] = upgrade
                result["upgraded_from"] = decision.model
                result["upgrade_reason"] = upgrade_reason
        
        return result


def main():
    """CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local LLM Router")
    parser.add_argument("--prompt", "-p", required=True, help="The prompt to classify")
    parser.add_argument("--coding", "-c", action="store_true", help="Prefer coding model for coding tasks")
    parser.add_argument("--info", "-i", action="store_true", help="Show full routing info")
    
    args = parser.parse_args()
    
    router = LocalRouter()
    
    if args.info:
        info = router.route_info(args.prompt, prefer_coding=args.coding)
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        model = router.get_model_for_prompt(args.prompt, prefer_coding=args.coding)
        print(model)


if __name__ == "__main__":
    main()
