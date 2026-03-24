"""AI assistance for app generation using LLMs."""

import json
from typing import Optional, Dict, Any, List
import anthropic
import openai


class AIHelper:
    """Helper class for AI-assisted code generation."""

    # Default model identifiers per provider
    DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_OPENAI_MODEL = "gpt-4-turbo-preview"

    # Default generation parameters
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_ENHANCEMENT_MAX_TOKENS = 8192
    DEFAULT_OPENAI_TEMPERATURE = 0.3

    def __init__(
        self,
        provider: str = "anthropic",
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize AI helper.

        Args:
            provider: AI provider to use ("anthropic" or "openai")
            anthropic_key: Anthropic API key
            openai_key: OpenAI API key
            model: Override the default model for the chosen provider
            temperature: Override the default temperature (OpenAI only; Anthropic uses its default)
            max_tokens: Override the default max_tokens for generation
        """
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_tokens = max_tokens

        if self.provider == "anthropic":
            if not anthropic_key:
                raise ValueError("Anthropic API key required for provider 'anthropic'")
            self.client = anthropic.Anthropic(api_key=anthropic_key)
            self.model = model or self.DEFAULT_ANTHROPIC_MODEL
        elif self.provider == "openai":
            if not openai_key:
                raise ValueError("OpenAI API key required for provider 'openai'")
            self.client = openai.OpenAI(api_key=openai_key)
            self.model = model or self.DEFAULT_OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    def generate_component(
        self,
        component_type: str,
        requirements: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate a React component using AI.

        Args:
            component_type: Type of component (e.g., "navbar", "sidebar", "chat")
            requirements: Natural language requirements for the component
            context: Context information (app_name, platform_key, etc.)

        Returns:
            Generated component code as a string
        """
        prompt = self._build_component_prompt(component_type, requirements, context)

        if self.provider == "anthropic":
            return self._generate_with_anthropic(prompt)
        elif self.provider == "openai":
            return self._generate_with_openai(prompt)

    def enhance_component(
        self,
        existing_code: str,
        enhancement_request: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Enhance existing component code using AI.

        Args:
            existing_code: Existing component code
            enhancement_request: What to enhance or add
            context: Context information

        Returns:
            Enhanced component code
        """
        prompt = f"""You are an expert React developer working with Next.js 15 and TypeScript.

Enhance the following component based on this request:
{enhancement_request}

Context:
- App name: {context.get("app_name")}
- Platform: {context.get("platform_key")}
- Uses @iblai/iblai-js SDK (imports from @iblai/iblai-js/data-layer, @iblai/iblai-js/web-containers, @iblai/iblai-js/web-utils)

Existing code:
```tsx
{existing_code}
```

Return ONLY the enhanced component code, no explanations."""

        if self.provider == "anthropic":
            return self._generate_with_anthropic(prompt)
        elif self.provider == "openai":
            return self._generate_with_openai(prompt)

    def enhance_app(
        self,
        files: Dict[str, str],
        prompt: str,
        context: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Enhance multiple generated files based on a user prompt.

        Sends all enhanceable files in a single LLM call for consistency.

        Args:
            files: Dictionary of relative filename → file content
            prompt: User's enhancement prompt (e.g., "make this app for kids")
            context: Context information (app_name, platform_key, etc.)

        Returns:
            Dictionary of relative filename → enhanced file content
        """
        files_block = ""
        for filename, content in files.items():
            files_block += f"\n--- FILE: {filename} ---\n{content}\n"

        llm_prompt = f"""You are an expert React/Next.js developer customizing an IBL.ai agent chat application.

The user wants the following customization applied to this app:
"{prompt}"

App context:
- App name: {context.get("app_name")}
- Platform: {context.get("platform_key")}
- Uses Next.js 15 App Router, TypeScript, Tailwind CSS
- SDK: @iblai/iblai-js (imports from @iblai/iblai-js/data-layer, @iblai/iblai-js/web-containers, @iblai/iblai-js/web-utils)
- Local UI components imported from @/components/ui/*

Here are the files to customize:
{files_block}

RULES:
1. Do NOT change any import statements — keep all imports exactly as they are
2. Do NOT remove existing functionality or change component prop interfaces
3. Do NOT change hook calls (useAdvancedChat, useParams, etc.) or their arguments
4. DO modify: text/copy, CSS classes, color values, suggested prompts, icons (from lucide-react), metadata, placeholders, labels
5. For globals.css: you may change HSL color values for CSS custom properties to match the theme
6. Keep all TypeScript types intact
7. Maintain the exact same component structure and exports

Return a JSON object where keys are the filenames and values are the complete modified file contents.
Return ONLY valid JSON, no markdown formatting, no code fences, no explanations.

Example format:
{{"app/globals.css": "...", "components/navbar.tsx": "..."}}"""

        enhancement_tokens = self.max_tokens or self.DEFAULT_ENHANCEMENT_MAX_TOKENS

        if self.provider == "anthropic":
            response = self._generate_with_anthropic(
                llm_prompt, max_tokens=enhancement_tokens
            )
        elif self.provider == "openai":
            response = self._generate_with_openai(
                llm_prompt, max_tokens=enhancement_tokens
            )

        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # If JSON parsing fails, return original files unchanged
        return files

    def _build_component_prompt(
        self,
        component_type: str,
        requirements: str,
        context: Dict[str, Any],
    ) -> str:
        """Build a prompt for component generation."""
        return f"""You are an expert React developer creating components for an IBL.ai agent application.

Generate a {component_type} component with these requirements:
{requirements}

Context:
- App name: {context.get("app_name")}
- Platform key: {context.get("platform_key")}
- Agent ID: {context.get("mentor_id", "N/A")}
- Uses Next.js 15 App Router with TypeScript
- Available SDK: @iblai/iblai-js (imports from @iblai/iblai-js/data-layer, @iblai/iblai-js/web-containers, @iblai/iblai-js/web-utils)
- UI components from: @iblai/iblai-js/web-containers/components/ui/*
- Hooks from: @iblai/iblai-js/web-utils (useAdvancedChat, useTenantContext, etc.)

Requirements:
1. Use TypeScript with proper types
2. Follow React best practices (hooks, functional components)
3. Use Tailwind CSS for styling
4. Import UI components from @iblai/iblai-js/web-containers/components/ui/*
5. Use "use client" directive if needed
6. Include proper error handling
7. Make it accessible (WCAG 2.1 AA)

Return ONLY the component code, no explanations or markdown formatting."""

    def _generate_with_anthropic(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> str:
        """Generate code using Anthropic's Claude."""
        resolved_max_tokens = max_tokens or self.max_tokens or self.DEFAULT_MAX_TOKENS

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": resolved_max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        message = self.client.messages.create(**kwargs)

        # Extract text content from response
        content = message.content[0].text if message.content else ""
        return self._clean_code_response(content)

    def _generate_with_openai(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> str:
        """Generate code using OpenAI's GPT."""
        resolved_max_tokens = max_tokens or self.max_tokens or self.DEFAULT_MAX_TOKENS
        resolved_temperature = (
            self.temperature
            if self.temperature is not None
            else self.DEFAULT_OPENAI_TEMPERATURE
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=resolved_max_tokens,
            temperature=resolved_temperature,
        )

        content = response.choices[0].message.content or ""
        return self._clean_code_response(content)

    def _clean_code_response(self, response: str) -> str:
        """Clean up AI response to extract just the code."""
        # Remove markdown code blocks if present
        if "```" in response:
            # Extract content between code fences
            parts = response.split("```")
            if len(parts) >= 3:
                code = parts[1]
                # Remove language identifier if present
                if code.startswith("tsx\n") or code.startswith("typescript\n"):
                    code = "\n".join(code.split("\n")[1:])
                return code.strip()

        return response.strip()

    def suggest_improvements(
        self,
        component_code: str,
        component_type: str,
    ) -> List[str]:
        """
        Get AI suggestions for improving a component.

        Args:
            component_code: The component code to analyze
            component_type: Type of component

        Returns:
            List of improvement suggestions
        """
        prompt = f"""Analyze this {component_type} React component and suggest specific improvements.

Component code:
```tsx
{component_code}
```

Focus on:
1. Performance optimizations
2. Accessibility improvements
3. Code organization
4. Error handling
5. TypeScript type safety
6. React best practices

Return a JSON array of suggestion strings. Each suggestion should be specific and actionable.
Example: ["Add error boundary for robustness", "Memoize expensive calculations with useMemo"]

Return ONLY the JSON array, no other text."""

        if self.provider == "anthropic":
            response = self._generate_with_anthropic(prompt)
        elif self.provider == "openai":
            response = self._generate_with_openai(prompt)

        try:
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else []
        except json.JSONDecodeError:
            # Fallback: split by newlines if JSON parsing fails
            return [line.strip() for line in response.split("\n") if line.strip()]
