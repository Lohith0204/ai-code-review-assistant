from openai import OpenAI
from app.core.models import ReviewResult
import json
import os
import re
from typing import Dict, List, Any

class ReviewService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def review_code(self, context_chunks: str) -> ReviewResult:
        """
        Main entry point for code review.
        Checks for DEMO_MODE or falls back to simulation on API failure.
        """
        # 1. Check for forced Demo Mode
        if os.getenv("DEMO_MODE", "false").lower() == "true":
            print("⚠️ Demo Mode Active: Skipping OpenAI call.")
            return self._simulate_responsive_review(context_chunks)

        prompt = (
            "You are a senior software engineer performing a code review.\n"
            "Analyze the following code context and provide structured feedback.\n"
            "Return ONLY a JSON object with keys: 'summary', 'risks' (list), 'suggestions' (list), 'affected_files' (list).\n"
            "Do not return markdown formatting like ```json ... ```, just the raw JSON string.\n\n"
            f"Code Context:\n{context_chunks}"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            content = response.choices[0].message.content.strip()
            
            # Cleanup potential markdown fencing
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            data = json.loads(content)
            return ReviewResult(**data)

        except Exception as e:
            # 2. Automatic Fallback to Demo Mode on ANY failure
            print(f"❌ OpenAI API Failed: {str(e)}")
            print("🔄 Falling back to Rule-Based Analysis Engine.")
            return self._simulate_responsive_review(context_chunks)

    def _simulate_responsive_review(self, context: str) -> ReviewResult:
        """
        Orchestrates the rule-based simulation:
        1. Extract Signals (Static Analysis)
        2. Construct Review (Persona Generation)
        """
        signals = self._extract_signals(context)
        return self._construct_review(signals)

    def _extract_signals(self, context: str) -> Dict[str, Any]:
        """
        Step 1: Signal Extraction Layer
        Analyzes raw code context for patterns, complexity, and risks.
        """
        return {
            "line_count": len(context.splitlines()),
            "functions": re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', context),
            "classes": re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', context),
            "has_print": bool(re.search(r'\bprint\(', context)),
            "has_eval": bool(re.search(r'\b(eval|exec)\(', context)),
            "has_secrets": bool(re.search(r'(?i)(password|secret|api_key|token)\s*=', context)),
            "has_docstrings": '"""' in context or "'''" in context,
            "has_todos": bool(re.search(r'\bTODO\b', context)),
            "has_exceptions": bool(re.search(r'\btry:|except\s+', context)),
            "division_no_guard": bool(re.search(r'/\s*[a-zA-Z0-9_]+', context)) and not re.search(r'\btry:', context),
            "complexity": "High" if len(context) > 2000 else "Moderate" if len(context) > 500 else "Low"
        }

    def _construct_review(self, signals: Dict[str, Any]) -> ReviewResult:
        """
        Step 2: Review Construction Layer
        Synthesizes extracted signals into a valid Senior Engineer review.
        """
        # --- Generate Summary ---
        if signals["functions"]:
            focus_area = f"targeting key logic in `{signals['functions'][0]}()`"
            if len(signals["functions"]) > 1:
                focus_area += f" and {len(signals['functions']) - 1} other function(s)"
        else:
            focus_area = "analyzing the provided script structure"

        summary = (
            f"⚠️ **DEMO MODE: Rule-Based Static Analysis**\n\n"
            f"I have completed a simulated review {focus_area}. "
            f"The submitted change set introduces {signals['line_count']} lines of {signals['complexity'].lower()}-complexity code. "
            "The architecture appears sound, though there are specific improvements needed for production readiness."
        )

        # --- Generate Critical Risks ---
        risks = []
        if signals['has_eval']:
            risks.append("🚨 **Critical Security Risk**: Detected usage of `eval()` or `exec()`. This allows arbitrary code execution and should be replaced with safer alternatives immediately.")
        
        if signals['has_secrets']:
            risks.append("🔒 **Secret Leakage**: Hardcoded sensitive credentials (passwords/keys) detected. Use environment variables or a secret manager.")
            
        if signals['division_no_guard'] and not signals['has_exceptions']:
            risks.append("⚠️ **Runtime Safety**: Division operations detected without explicit `try-except` blocks. This risks `ZeroDivisionError` in edge cases.")

        if not signals['has_exceptions'] and signals['complexity'] in ["Moderate", "High"]:
             risks.append("📉 **Error Handling**: The codebase lacks robust exception handling mechanisms, which may lead to ungraceful failures in production.")
        
        # Fallback if code is clean
        if not risks:
            risks.append("✅ **Security**: No obvious OWASP top 10 vulnerabilities detected in the analyzed snippet.")

        # --- Generate Suggestions ---
        suggestions = []
        if signals['has_print']:
            suggestions.append("📝 **Observability**: Replace `print()` statements with a structured `logging` configuration (e.g., `logger.info()`) to enable better debugging in deployment.")
            
        if signals['has_todos']:
            suggestions.append("🚧 **Maintenance**: There are unresolved `TODO` comments. Ensure these are tracked in the backlog before merging.")
            
        if not signals['has_docstrings'] and signals['functions']:
             func_name = signals['functions'][0]
             suggestions.append(f"📖 **Documentation**: The function `{func_name}` lacks a docstring. Add PEP-257 compliant documentation to explain arguments and return values.")

        if signals['complexity'] == "High":
            suggestions.append("🏗️ **Refactoring**: The module size is growing large. Consider breaking it down into smaller, single-responsibility components.")

        # Fallback suggestion
        if not suggestions:
            suggestions.append("✨ **Style**: Code adheres to general Pythonic conventions. Consider adding type hints for better developer experience.")

        # --- Affected Files ---
        # Since we analyze chunks, we simulate file detection based on class/func names
        affected_files = sorted([f"{name}.py" for name in signals['classes']] + ["module.py"])

        return ReviewResult(
            summary=summary,
            risks=risks,
            suggestions=suggestions,
            affected_files=affected_files[:3] # Limit to 3 for UI cleanliness
        )
